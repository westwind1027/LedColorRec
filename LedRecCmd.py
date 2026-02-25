# -*- coding: utf-8 -*-

# Version 1.0 --- 2022/1/25 init by Glynn.Li
# Update --- 2023/1/12 by Glynn.Li  --- 1. Add cam_reverse; 2. Check cam_set before using. 3. Add "csv_create" in prj_setting 
# Update --- 2023/2/1 by Glynn.Li --- 1. use cv2.CAP_PROP_BRIGHTNESS instead 10 in cap.set() function.
# Update --- 2023/2/20 by Glynn.Li --- 1. fix the error report when ROI is empty.
# Update --- 2023/4/21 by Glynn.Li --- 1. Add BOX location finetune

#导入程序运行必须模块
import yaml
import argparse
import cv2
import os
import time
import csv
import sys
from pathlib import Path

# 将当前路径加入至path中
FILE = Path(__file__).absolute()
sys.path.append(FILE.parents[0].as_posix())

# 分辨颜色的专用模块
from utils.colorprocess import ColorReg, Rgb2Hsv, ImgProcess, IsColor, IsColorEnhance

# 解析项目参数
def ParseOpt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--camyaml', type=str, default='configs/camera_setting.yaml', help='select camera setting file')
    parser.add_argument('--roiyaml', type=str, default='configs/roi_setting.yaml', help='select ROI setting file')
    parser.add_argument('--prjyaml', type=str, default='configs/prj_setting.yaml', help='select project setting file')
    opt = parser.parse_args()
    # opt.imgsz *= 2 if len(opt.imgsz) == 1 else 1  # expand
    return opt

opt = ParseOpt()
# 载入环境变量
with open(opt.prjyaml, encoding='utf-8') as f:
    prj_setting = yaml.load(f, Loader=yaml.FullLoader)
with open(opt.camyaml, encoding='utf-8') as f:
    cam_set = yaml.load(f, Loader=yaml.FullLoader)
with open(opt.roiyaml, encoding='utf-8') as f:
    roi_setting = yaml.load(f, Loader=yaml.FullLoader)

result_dict = {} # 结果字典
err_info = '' # 错误信息


# 开启摄像头
def OpenCam():
    # 摄像头设置初始化
    # with open(camyaml, encoding='utf-8') as f:
    #     cam_set = yaml.load(f, Loader=yaml.FullLoader)
    # print(str(cam_set))
    cap = cv2.VideoCapture(cam_set['cam_id'], cv2.CAP_DSHOW)
    if 'cam_frame_width' in cam_set.keys():
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,cam_set['cam_frame_width'])
    if 'cam_frame_height' in cam_set.keys():
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT,cam_set['cam_frame_height'])
    if 'cam_fps' in cam_set.keys():
        cap.set(cv2.CAP_PROP_FPS,cam_set['cam_fps'])
    if 'cam_brightness' in cam_set.keys():
        cap.set(cv2.CAP_PROP_BRIGHTNESS,cam_set['cam_brightness']) # CAP_PROP_BRIGHTNESS=10, //!< Brightness of the image (only for those cameras that support).
    if 'cam_contrast' in cam_set.keys():
        cap.set(cv2.CAP_PROP_CONTRAST,cam_set['cam_contrast']) # CAP_PROP_CONTRAST=11, //!< Contrast of the image (only for cameras).
    if 'cam_saturation' in cam_set.keys():
        cap.set(cv2.CAP_PROP_SATURATION,cam_set['cam_saturation']) # CAP_PROP_SATURATION=12, //!< Saturation of the image (only for cameras).
    if 'cam_hue' in cam_set.keys():
        cap.set(cv2.CAP_PROP_HUE,cam_set['cam_hue']) # CAP_PROP_HUE=13, //!< Hue of the image (only for those cameras that support).
    if 'cam_gain' in cam_set.keys():
        cap.set(cv2.CAP_PROP_GAIN,cam_set['cam_gain']) # CAP_PROP_GAIN=14, //!< Gain of the image (only for those cameras that support).
    if 'cam_exposure' in cam_set.keys():
        cap.set(cv2.CAP_PROP_EXPOSURE,cam_set['cam_exposure']) # CAP_PROP_EXPOSURE=15, //!< Exposure (only for those cameras that support).
    if 'cam_temperature' in cam_set.keys():
        cap.set(cv2.CAP_PROP_TEMPERATURE,cam_set['cam_temperature']) # CAP_PROP_TEMPERATURE=23
    # cap.set(27,cam_set['cam_zoom']) # CAP_PROP_ZOOM=27,
    # cap.set(28,cam_set['cam_focus']) # CAP_PROP_FOCUS=28,
    return cap


# 将结果写入csv文件中
def CreateCSV(csv_content):
    if not os.path.exists(prj_setting['result_path']):
        os.mkdir(prj_setting['result_path'])
    csv_name = prj_setting['result_path']+'CamLedColor_'+ str(time.strftime("%Y%m%d%H%M%S", time.localtime())) + '.csv'
    if type(csv_content) == type({'a':1}): # 如传来的是字典类型的测试结果
        with open(csv_name, 'w', newline='') as f:
            csv.writer(f).writerow(('led_num','color'))
            for i in csv_content:
                csv.writer(f).writerow((i, csv_content[i]))
    else: # 如传来的是异常
        with open(csv_name, 'w', newline='') as f:
            csv.writer(f).writerow(('error', csv_content))


def Run(cap):
    # with open(roiyaml, encoding='utf-8') as f:
    #     roi_setting = yaml.load(f, Loader=yaml.FullLoader)
    # print(str(roi_setting))
    if cap.isOpened():
        while 1:
            prj_setting["cam_skip"] -= 1
            ret, cam_image = cap.read()
            if prj_setting["cam_skip"] <= 0:
                if ret:
                    info_list = ''
                    do_finetune = True
                    # 将BOX画在图像上
                    for i in range(prj_setting['sample_count']):
                        ret, cam_image = cap.read()
                        if cam_set['cam_reverse'] == 1:
                            cam_image = cv2.rotate(cam_image, cv2.ROTATE_180) # 摄像头图片旋转180度
                        if 'roi' in roi_setting.keys(): # 如果有roi则只显示roi区域图像
                            if len(roi_setting['roi']) != 0:
                                roi_ = roi_setting['roi'][0]
                                cam_image = cam_image[roi_[0][1]:roi_[1][1], roi_[0][0]:roi_[1][0], :]
                        box_id = 0
                        for i in roi_setting["boxes"]:
                            # 如所有BOX在x或y轴方向有位移补偿，则需要加入补偿值
                            # print(self.roi_setting["x_offset"], type(self.roi_setting["x_offset"]))
                            if roi_setting["x_offset"] != 0:
                                i = [(i[0][0] + roi_setting["x_offset"], i[0][1]), (i[1][0] + roi_setting["x_offset"], i[1][1])]
                            if roi_setting["y_offset"] != 0:
                                i = [(i[0][0], i[0][1] + roi_setting["y_offset"]), (i[1][0], i[1][1] + roi_setting["y_offset"])]
                            # 如所有BOX在x或y轴方向需要缩放，则需要加入缩放值
                            if roi_setting["x_size"] != 0:
                                i = [(i[0][0], i[0][1]), (i[1][0] + roi_setting["x_size"], i[1][1])]
                            if roi_setting["y_size"] != 0:
                                i = [(i[0][0], i[0][1]), (i[1][0], i[1][1] + roi_setting["y_size"])]
                            if roi_setting["is_finetune"]:
                                if box_id == 0 and do_finetune:
                                    ft_box = i
                                    raw_cam = cam_image.copy()
                            box_id += 1
                            boximg_color_info = ImgProcess(cam_image[i[0][1]:i[1][1], i[0][0]:i[1][0], :]) # 计算box框中的图片颜色分布
                            # 如有置信度增强设置，则使用增强算法
                            if roi_setting["conf_enhance"] == 1:
                                box_color, color_rate = IsColorEnhance(boximg_color_info, roi_setting["color_threshold"], roi_setting["noise_weight"])
                            else:
                                box_color, color_rate = IsColor(boximg_color_info, roi_setting["color_threshold"], roi_setting["noise_weight"])
                            info_list += 'box%d_%s_%f'%(box_id,box_color,color_rate) + str(boximg_color_info) + '\n' # 将BOX颜色信息存入info_list中
                            if 'box_%d'%box_id in result_dict:
                                if box_color in result_dict['box_%d'%box_id]:
                                    result_dict['box_%d'%box_id][box_color] += 1
                                else:
                                    result_dict['box_%d'%box_id][box_color] = 1
                            else:
                                result_dict['box_%d'%box_id] = {box_color:1}
                            cv2.rectangle(cam_image, i[0], i[1], prj_setting["box_color"][box_color], prj_setting["boxline_width"]) # 参数依次是:图像，左上起始点元组，右下终止点元组，边框颜色，边框线宽
                            # cv2.putText(cam_image, 'box%d'%box_id, (i[0][0],i[0][1]-5), cv2.FONT_HERSHEY_SIMPLEX, 1, prj_setting["box_color"][box_color], 1) # 参数依次是:图像，label文字，左上起始点元组，字体，字体大小，字体颜色，字体粗细
                            cv2.putText(cam_image, '%d'%box_id, (i[0][0],i[0][1]-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, prj_setting["box_color"][box_color], 1)
                        # showimg_scaled = cv2.resize(cam_image, (int(cam_image.shape[1]/4), int(cam_image.shape[0]/4))) # 缩小图像用于显示
                        # if is_finetune = True, proceed finetune to get a good location.
                        if roi_setting["is_finetune"]:
                            if do_finetune:
                                ft_box_final = ((ft_box[0][0]-roi_setting["finetune_range"],ft_box[0][1]-roi_setting["finetune_range"]), (ft_box[1][0]+roi_setting["finetune_range"],ft_box[1][1]+roi_setting["finetune_range"]))
                                # box1_finetune_range = raw_cam[(ft_box[0][1]-roi_setting["finetune_range"]):(ft_box[1][1]+roi_setting["finetune_range"]), (ft_box[0][0]-roi_setting["finetune_range"]):(ft_box[1][0]+roi_setting["finetune_range"]), :]
                                box1_finetune_range = raw_cam[ft_box_final[0][1]:ft_box_final[1][1], ft_box_final[0][0]:ft_box_final[1][0], :]
                                gray = cv2.cvtColor(box1_finetune_range, cv2.COLOR_BGR2GRAY)
                                gray_gauss = cv2.GaussianBlur(gray, (5, 5), 0)
                                minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(gray_gauss)
                                # cv2.circle(box1_finetune_range, maxLoc, 1, (0,0,255), 1)
                                # cv2.circle(box1_finetune_range, (10, 10), 1, (0,0,255), 1)
                                # cv2.imshow("Gray", box1_finetune_range)
                                # cv2.waitKey(0)
                                # if cam_set["cam_reverse"] == 1:
                                roi_setting["x_offset"] = roi_setting["x_offset"] - (int((ft_box_final[1][0]-ft_box_final[0][0])/2) - maxLoc[0])
                                roi_setting["y_offset"] = roi_setting["y_offset"] - (int((ft_box_final[1][1]-ft_box_final[0][1])/2) - maxLoc[1])
                                do_finetune = False
                        showimg_scaled = cv2.resize(cam_image, (800, 600)) # 暂定结果显示窗口大小为800*600,之后可将此参数定义在prj_yaml中
                        cv2.imshow('camled', showimg_scaled)
                        cv2.waitKey(prj_setting['cap_delay'])
                    with open('info_list.txt', 'w') as f:
                        f.write(info_list)
                    break
                else:
                    err_info = "The camera does not open!"
                    return
    else:
        err_info = "The camera does not open!"
        print(err_info)
        return
    cap.release()
    cv2.destroyAllWindows()


def Main(opt):
    # print(opt.camyaml)
    # print(opt.roiyaml)
    # 按camyaml中的设置打开camera
    cap = OpenCam()
    # 处理图像
    Run(cap)
    # 处理result_dict，生成最终结果
    for i in result_dict:
        result_dict[i], color_count = max(result_dict[i].items(), key=lambda x:x[1])
        if color_count<prj_setting['color_count']:
            result_dict[i] = 'others'
    print(result_dict)
    if prj_setting['csv_create'] == 1:
        CreateCSV(result_dict)


if __name__ == "__main__":
    # opt = ParseOpt()
    Main(opt)
