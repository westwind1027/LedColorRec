import cv2
# import numpy as np

def ColorReg(H,S,V):
    if S>=43 and S<=255:
        if V>=46 and V<=255:
            if H>=0 and H<=10:
                return "red"
            elif H>=11 and H<=29:
                return "yellow"
            elif H>=30 and H<=77:
                return "green"
            elif H>=78 and H<=99:
                return "cyan"
            elif H>=100 and H<=124:
                return "blue"
            elif H>=125 and H<=155:
                return "purple"
            elif H>=156 and H<=180:
                return "red"
            else:
                return "others"
        else:
            return "black"
    elif S>=0 and S<=30:
        if V>=221 and V<=255:
            return "white"
        elif V>=46 and V<=220:
            return "gray"
        else:
            return "black"
    else:
        if V>=46 and V<=220:
            return "gray"
        else:
            return "black"


def Rgb2Hsv(r, g, b):
    r, g, b = r/255.0, g/255.0, b/255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    m = mx-mn
    if mx == mn:
        h = 0
    elif mx == r:
        if g >= b:
            h = ((g-b)/m)*60
        else:
            h = ((g-b)/m)*60 + 360
    elif mx == g:
        h = ((b-r)/m)*60 + 120
    elif mx == b:
        h = ((r-g)/m)*60 + 240
    if mx == 0:
        s = 0
    else:
        s = m/mx
    v = mx
    H = h / 2
    S = s * 255.0
    V = v * 255.0
    return H, S, V

def ImgProcess(im_p):
    # im_c = np.zeros(im_p.shape, dtype=int) + 255 # 创建一张与目标图片大小相同的全白图片
    color_sum = {}
    _i = -1
    for i in im_p:
        _i += 1
        _j = -1
        for j in i:
            _j += 1
            h_, s_, v_ = Rgb2Hsv(j[2], j[1], j[0])
            iscolor = ColorReg(h_, s_, v_)
            if iscolor not in color_sum:
                color_sum[iscolor] = 1
            else:
                color_sum[iscolor] += 1
            # if iscolor == "gray":
                # im_c[_i,_j] = j
    # cv2.imwrite('gray_img.jpg',im_c)
    return color_sum


def IsColor(image, color_threshold, noise_weight):
    color_info = image.copy()
    # 降低黑色权重
    if "black" in color_info:
        color_info['black'] = int(color_info['black'] * noise_weight)
    if "gray" in color_info:
        color_info['gray'] = int(color_info['gray'] * noise_weight)
    if "others" in color_info:
        color_info['others'] = int(color_info['others'] * noise_weight)
    # 计算剩余最大值占比
    if color_info != {}:
        sum_ = sum(color_info.values())
        max_color, max_ = max(color_info.items(), key=lambda x:x[1])
        if max_/sum_ >= color_threshold:
            return max_color, round(max_/sum_, 2)
        else:
            return "others", round(max_/sum_, 2)
    else:
        return "others", 0.00


def IsColorEnhance(image, color_threshold, noise_weight):
    color_info = image.copy()
    # 统计除噪音色外的其他所有色彩，并将样本数全部置于目标色彩。
    color_info_2 = image.copy()
    color_info_3 = {}
    # 去掉噪音色
    if "black" in color_info_2:
        color_info_2.pop('black')
    if "gray" in color_info_2:
        color_info_2.pop('gray')
    if "others" in color_info_2:
        color_info_2.pop('others')
    if color_info_2 != {}:
        color_count = 0
        for i in color_info_2:
            color_count += color_info_2[i]
        max_color, max_ = max(color_info_2.items(), key=lambda x:x[1])
        color_info_3[max_color] = color_count

    # 降低黑色权重
    if "black" in color_info:
        color_info_3['black'] = int(color_info['black'] * noise_weight)
    if "gray" in color_info:
        color_info_3['gray'] = int(color_info['gray'] * noise_weight)
    if "others" in color_info:
        color_info_3['others'] = int(color_info['others'] * noise_weight)
    # 计算剩余最大值占比
    if color_info_3 != {}:
        sum_ = sum(color_info_3.values())
        max_color, max_ = max(color_info_3.items(), key=lambda x:x[1])
        if max_/sum_ >= color_threshold:
            return max_color, round(max_/sum_, 2)
        else:
            return "others", round(max_/sum_, 2)
    else:
        return "others", 0.00
        


def main():
    im0 = cv2.imread(r"images\1.JPG", cv2.IMREAD_UNCHANGED)
    print(str(ImgProcess(im0)))

if __name__ == "__main__":
    main()
