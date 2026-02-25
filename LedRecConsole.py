# -*- coding: utf-8 -*-

# Version 1.0 --- 2022/1/25 init by Glynn.Li
# Version 1.1 --- 2023/1/13 by Glynn.Li --- 1.Add "ROI","CAM","Project" tables.
# Update --- 2023/1/17 by Glynn.Li --- 1. Add load yaml file check for cam.yaml, roi.yaml, prj.yaml.
# Update --- 2023/2/1 by Glynn.Li --- 1. Delete a label in prj_setting table; 2. use cv2.CAP_PROP_BRIGHTNESS instead 10 in cap.set() function. 3. print project setting file name at the beginning.
# Update --- 2023/2/7 by Glynn.Li --- 1. Add ROI range label, add ROI X,Y,W,H error report; 2. disable some button in ROI setting table when no video.
# Update --- 2023/2/8 by Glynn.Li --- 1. Add warning message when box width or height < 1 pixel.
# Update --- 2023/3/31 by Glynn.Li --- 1. Add draw ROI range function; 2. Change the left,right,up,down button stlye.
# Update --- 2023/4/4 by Glynn.Li --- 1. Add password check when save or saveas buttons are clicked. Add pw in prj_setting.yaml
# Update --- 2023/4/21 by Glynn.Li --- 1. Add BOX location finetune
# Update --- 2023/4/28 by Glynn.Li --- 1. Fix memory consume bug; 2. Modify draw ROI range function.

#导入程序运行必须模块
import yaml, argparse # pip install pyyaml -i https://mirrors.aliyun.com/pypi/simple
import cv2 # pip install opencv-python

#PyQt5中使用的基本控件都在PyQt5.QtWidgets模块中
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QRectF, QPoint
from PyQt5.QtGui import QPixmap, QPen, QPolygon, QIcon, QPainter, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QInputDialog, QLineEdit


import sys
from pathlib import Path

# 将当前路径加入至path中
FILE = Path(__file__).absolute()
sys.path.append(FILE.parents[0].as_posix())

# 分辨颜色的专用模块
from utils.colorprocess import ImgProcess, IsColor, IsColorEnhance
#导入designer工具生成的cam_led_color_pyqt5模块
from cam_led_color_pyqt5 import Ui_cam_led_color_pyqt5


class MyMainForm(QMainWindow, Ui_cam_led_color_pyqt5): 
    def __init__(self, opt, parent=None):
        super(MyMainForm, self).__init__(parent)
        self.opt = opt
        self.timer_camera = QtCore.QTimer()
        self.setupUi(self)
        
        self.opencam_btn.clicked.connect(self.opencam)    #添加opencam_btn按钮信号和槽。
        self.pause_btn.clicked.connect(self.pause_ui)    #添加pause_btn按钮信号和槽。
        self.reset_btn.clicked.connect(self.reset_ui)    #添加reset_btn按钮信号和槽。
        self.timer_camera.timeout.connect(self.feedback_qt)     #若定时器结束，则调用feedback_qt()
        self.close_btn.clicked.connect(self.all_close)  #若该按键被点击，则关闭程序
        self.CamLoadFileButton.clicked.connect(self.open_cam_file) # 选择需要载入的camera setting文件
        self.ROILoadFileButton.clicked.connect(self.open_roi_file) # 选择需要载入的roi setting文件
        self.PrjLoadFileButton.clicked.connect(self.open_prj_file) # 选择需要载入的project setting文件
        self.CamSaveButton.clicked.connect(lambda: self.save_file(self.CamLoadFileContentText.toPlainText(), self.opt.camyaml)) # 槽函数传参可以使用lambda的方式
        self.CamSaveAsButton.clicked.connect(lambda: self.saveas_file(self.CamLoadFileContentText.toPlainText(), self.CamLoadFiletextBrowser)) # 槽函数传参可以使用lambda的方式
        self.PrjSaveButton.clicked.connect(lambda: self.save_file(self.PrjLoadFileContentText.toPlainText(), self.opt.prjyaml))
        self.PrjSaveAsButton.clicked.connect(lambda: self.saveas_file(self.PrjLoadFileContentText.toPlainText(), self.PrjLoadFiletextBrowser))
        self.ROISaveButton.clicked.connect(self.roi_save_file)
        self.ROISaveAsButton.clicked.connect(self.roi_saveas_file)
        self.CamApplyButton.clicked.connect(self.camsetbutton_apply)
        self.SingleUpButton.clicked.connect(lambda: self.sbox_move("up"))
        self.SingleDownButton.clicked.connect(lambda: self.sbox_move("down"))
        self.SingleLeftButton.clicked.connect(lambda: self.sbox_move("left"))
        self.SingleRightButton.clicked.connect(lambda: self.sbox_move("right"))
        self.SingleBox_x.returnPressed.connect(lambda: self.sbox_move("jump"))
        self.SingleBox_y.returnPressed.connect(lambda: self.sbox_move("jump"))
        self.SingleBoxWidthlineEdit.returnPressed.connect(lambda: self.sbox_move("jump"))
        self.SingleBoxHeightlineEdit.returnPressed.connect(lambda: self.sbox_move("jump"))
        self.SingleSizePlusButton.clicked.connect(lambda: self.sbox_size_change("bigger"))
        self.SingleSizeMinusButton.clicked.connect(lambda: self.sbox_size_change("smaller"))
        self.SinglecomboBox.currentIndexChanged.connect(self.comboBox_change)
        self.AddBoxButton.clicked.connect(lambda: self.box_add_or_del("add"))
        self.DeleteBoxButton.clicked.connect(lambda: self.box_add_or_del("del"))
        
        self.X_offset_lineEdit.returnPressed.connect(lambda: self.allbox_move("jump"))
        self.Y_offset_lineEdit.returnPressed.connect(lambda: self.allbox_move("jump"))
        self.AllUpButton.clicked.connect(lambda: self.allbox_move("up"))
        self.AllDownButton.clicked.connect(lambda: self.allbox_move("down"))
        self.AllLeftButton.clicked.connect(lambda: self.allbox_move("left"))
        self.AllRightButton.clicked.connect(lambda: self.allbox_move("right"))
        self.X_size_lineEdit.returnPressed.connect(lambda: self.allbox_size_change("jump"))
        self.Y_size_lineEdit.returnPressed.connect(lambda: self.allbox_size_change("jump"))
        self.AllSizePlusButton.clicked.connect(lambda: self.allbox_size_change("bigger"))
        self.AllSizeMinusButton.clicked.connect(lambda: self.allbox_size_change("smaller"))
        self.AllDeleteButton.clicked.connect(self.allbox_del)
        
        self.FineTuneCheckBox.clicked.connect(self.is_finetune)
        self.FineTuneApplyButton.clicked.connect(self.finetune_apply)
        
        # 创建三角形形状的QPolygon对象
        triangle_up = QPolygon([QPoint(-10, -5), QPoint(0, -20), QPoint(10, -5)])
        triangle_down = QPolygon([QPoint(-10, 5), QPoint(0, 20), QPoint(10, 5)])
        triangle_left = QPolygon([QPoint(-5, -10), QPoint(-20, 0), QPoint(-5, 10)])
        triangle_right = QPolygon([QPoint(5, -10), QPoint(20, 0), QPoint(5, 10)])
        
        self.SingleUpButton.setText('')
        self.SingleDownButton.setText('')
        self.SingleLeftButton.setText('')
        self.SingleRightButton.setText('')
        self.SingleUpButton.setCheckable(True)
        self.SingleUpButton.setAutoExclusive(True)
        self.SingleUpButton.setStyleSheet("QPushButton { border: none; }")
        self.SingleDownButton.setCheckable(True)
        self.SingleDownButton.setAutoExclusive(True)
        self.SingleDownButton.setStyleSheet("QPushButton { border: none; }")
        self.SingleLeftButton.setCheckable(True)
        self.SingleLeftButton.setAutoExclusive(True)
        self.SingleLeftButton.setStyleSheet("QPushButton { border: none; }")
        self.SingleRightButton.setCheckable(True)
        self.SingleRightButton.setAutoExclusive(True)
        self.SingleRightButton.setStyleSheet("QPushButton { border: none; }")
        
        self.AllUpButton.setText('')
        self.AllDownButton.setText('')
        self.AllLeftButton.setText('')
        self.AllRightButton.setText('')
        self.AllUpButton.setCheckable(True)
        self.AllUpButton.setAutoExclusive(True)
        self.AllUpButton.setStyleSheet("QPushButton { border: none; }")
        self.AllDownButton.setCheckable(True)
        self.AllDownButton.setAutoExclusive(True)
        self.AllDownButton.setStyleSheet("QPushButton { border: none; }")
        self.AllLeftButton.setCheckable(True)
        self.AllLeftButton.setAutoExclusive(True)
        self.AllLeftButton.setStyleSheet("QPushButton { border: none; }")
        self.AllRightButton.setCheckable(True)
        self.AllRightButton.setAutoExclusive(True)
        self.AllRightButton.setStyleSheet("QPushButton { border: none; }")
        
        # 为每个按钮设置三角形形状的图标
        self.paint_triangle_button(self.SingleUpButton, triangle_up)
        self.paint_triangle_button(self.SingleDownButton, triangle_down)
        self.paint_triangle_button(self.SingleLeftButton, triangle_left)
        self.paint_triangle_button(self.SingleRightButton, triangle_right)
        
        self.paint_triangle_button(self.AllUpButton, triangle_up)
        self.paint_triangle_button(self.AllDownButton, triangle_down)
        self.paint_triangle_button(self.AllLeftButton, triangle_left)
        self.paint_triangle_button(self.AllRightButton, triangle_right)
        
        self.ROIApplyButton.clicked.connect(self.ROI_apply)
        self.ROIDeleteButton.clicked.connect(self.ROI_delete)
        self.ROIAddButton.clicked.connect(self.ROI_add)
        
        self.ConfApplyButton.clicked.connect(self.conf_apply)
        # self.pix = QPixmap('afg_logo.jpg') # 设置AFG LOGO
        # self.afg_logo.setPixmap(self.pix) # 设置AFG LOGO
        # self.afg_logo.setScaledContents(True) # 设置AFG LOGO
        
        # 定义图像展示窗口
        self.scene = QtWidgets.QGraphicsScene()
        self.video_stream = QtWidgets.QGraphicsView(self.scene, self)
        self.video_stream.setGeometry(QtCore.QRect(0, 0, 800, 600))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.video_stream.sizePolicy().hasHeightForWidth())
        self.video_stream.setSizePolicy(sizePolicy)
        self.video_stream.setStyleSheet("background-color: rgb(180, 180, 180);")
        self.video_stream.setObjectName("video_stream")
        self.video_stream.mousePressEvent = self.mousePressEvent
        self.video_stream.mouseReleaseEvent = self.mouseReleaseEvent
        self.video_stream.mouseMoveEvent = self.mouseMoveEvent
        self.video_stream.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.video_stream.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.draw_box = False
        self.current_rect_item = None
        self.mouse_pressed = False
        self.start_pos = None
        self.end_pos = None
        
        self.slot_init()    #初始化槽函数


    # UI界面初始化
    def slot_init(self):
        self.timer_camera.stop() # 时钟停止
        # video_stream视频框初始化
        # self.video_stream.setPixmap(QtGui.QPixmap("")) # 移除图片
        self.scene.clear()
        self.info_list = "" # 清空信息缓存
        self.info_text.setText("") # 清空信息显示框
        # self.video_stream.setStyleSheet("background-color:grey") # 背景设为灰色
        # self.video_stream.setText('请点击右下角“开启摄像头”按钮，等待图像接入。')
        # self.cursor_end(self.camset_display)
        self.opencam_btn.setEnabled(True) # “开启摄像头”按钮enable
        self.pause_btn.setEnabled(False) # “暂停”按钮disable
        self.reset_btn.setEnabled(False) # “重置”按钮disable
        self.pause_btn.setText('暂停')
        self.AddBoxButton.setEnabled(False)
        self.DeleteBoxButton.setEnabled(False)
        self.AllDeleteButton.setEnabled(False)
        self.ROIApplyButton.setEnabled(False)
        # self.ROIAddButton.setEnabled(False)
        self.ROIDeleteButton.setEnabled(False)
        self.rect = None
        
        
        with open(self.opt.camyaml, encoding='utf-8') as f:
            camsetting_content = f.read()
        self.CamLoadFileContentText.setText(camsetting_content) # Show the camera setting at text box of the camera parameter table.
        self.CamLoadFiletextBrowser.setText(self.opt.camyaml)
        with open(self.opt.roiyaml, encoding='utf-8') as f:
            self.roi_setting = yaml.load(f, Loader=yaml.FullLoader)
        self.roi_setting_load() # Load the ROI parameter into the ROI parameter table.
        self.ROILoadFiletextBrowser.setText(self.opt.roiyaml)
        with open(self.opt.prjyaml, encoding='utf-8') as f:
            prjsetting_content = f.read()
        self.PrjLoadFileContentText.setText(prjsetting_content) # Show the project setting at text box of the project parameter table.
        self.PrjLoadFiletextBrowser.setText(self.opt.prjyaml)
        with open(self.opt.camyaml, encoding='utf-8') as f:
            self.cam_setting = yaml.load(f, Loader=yaml.FullLoader)
        with open(self.opt.prjyaml, encoding='utf-8') as f:
            self.prj_setting = yaml.load(f, Loader=yaml.FullLoader)

    
    def check_password(self):
        dialog = QInputDialog()
        dialog.setWindowTitle("密码确认")
        dialog.setTextEchoMode(QLineEdit.Password)
        dialog.setLabelText("请输入密码:")
        # dialog.setWindowFlags(Qt.WindowStaysOnTopHint)
        with open(self.opt.prjyaml, encoding='utf-8') as f:
            check_pw = yaml.load(f, Loader=yaml.FullLoader)
        if dialog.exec_():
            if dialog.textValue() == check_pw['check_pw']:
                return True
            else:
                QMessageBox.information(self, "消息框", "密码错误，配置未保存！", QMessageBox.Yes)
                return False

    def is_finetune(self):
        if self.FineTuneCheckBox.isChecked():
            self.FineTuneRangeEdit.setEnabled(True)
        else:
            self.FineTuneRangeEdit.setText("")
            self.FineTuneRangeEdit.setEnabled(False)
            
            
    def finetune_apply(self):
        if self.FineTuneCheckBox.isChecked():
            self.roi_setting['is_finetune'] = True
            if int(self.FineTuneRangeEdit.text()) < 0:
                QMessageBox.information(self, "消息框", "定位优化范围需大于等于0pix", QMessageBox.Yes)
            else:
                self.roi_setting['finetune_range'] = int(self.FineTuneRangeEdit.text())
        else:
            self.roi_setting['is_finetune'] = False
            self.roi_setting['finetune_range'] = ''
            


    # 重写按钮的paintEvent方法以绘制三角形形状
    def paint_triangle_button(self, button, triangle):
        size = triangle.boundingRect().size()
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(triangle.translated(-triangle.boundingRect().topLeft()))
        painter.end()
        button.setIcon(QIcon(pixmap))
        button.setIconSize(size)


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.draw_box and self.video_stream.geometry().contains(event.pos()):
            self.mouse_pressed = True
            self.start_pos = event.pos()
            if self.current_rect_item:
                self.scene.removeItem(self.current_rect_item)
            self.current_rect_item = self.scene.addRect(0, 0, 0, 0, QPen(Qt.red, 4))

    def mouseMoveEvent(self, event):
        if self.mouse_pressed and self.current_rect_item:
            if self.video_stream.geometry().contains(event.pos()):
                self.end_pos = event.pos()
                self.rect = self.rect_from_points(self.start_pos, self.end_pos)
                self.current_rect_item.setRect(self.rect)
            else:
                self.mouse_pressed = False
                self.end_pos = event.pos()
                self.rect = self.rect_from_points(self.start_pos, self.end_pos)
                self.current_rect_item.setRect(self.rect)
                self.draw_box = False
                self.ROIAddButton.setEnabled(True)
                self.setCursor(Qt.ArrowCursor)
                print("Selected region: ", self.rect)
                self.ROIlineEdit_x.setText(str(int(self.rect.x()*self.x_rate)))
                self.ROIlineEdit_y.setText(str(int(self.rect.y()*self.y_rate)))
                self.ROIlineEdit_w.setText(str(int(self.rect.width()*self.x_rate)))
                self.ROIlineEdit_h.setText(str(int(self.rect.height()*self.y_rate)))
                

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.draw_box and self.current_rect_item:
            if self.video_stream.geometry().contains(event.pos()):
                self.mouse_pressed = False
                self.end_pos = event.pos()
                self.rect = self.rect_from_points(self.start_pos, self.end_pos)
                self.current_rect_item.setRect(self.rect)
                self.draw_box = False
                self.ROIAddButton.setEnabled(True)
                self.setCursor(Qt.ArrowCursor)
                print("Selected region: ", self.rect)
                self.ROIlineEdit_x.setText(str(int(self.rect.x()*self.x_rate)))
                self.ROIlineEdit_y.setText(str(int(self.rect.y()*self.y_rate)))
                self.ROIlineEdit_w.setText(str(int(self.rect.width()*self.x_rate)))
                self.ROIlineEdit_h.setText(str(int(self.rect.height()*self.y_rate)))
            else:
                pass

    def rect_from_points(self, p1, p2):
        x = min(p1.x(), p2.x())
        y = min(p1.y(), p2.y())
        w = abs(p1.x() - p2.x())
        h = abs(p1.y() - p2.y())
        return QRectF(x, y, w, h)


    def ROI_add(self):
        self.draw_box = True
        self.ROIAddButton.setEnabled(False)
        self.setCursor(Qt.CrossCursor)
        self.current_rect_item = None
        self.rect = None
        if self.roi_setting["roi"]:
            self.ROI_delete()
        if self.timer_camera.isActive():
            self.timer_camera.stop() # 时钟停止
        self.feedback_qt()
        
        # if self.timer_camera.isActive():
        #     self.timer_camera.stop() # 时钟停止
        

    def allbox_del(self):
        self.roi_setting["boxes"] = []
        self.refresh_boxes()


    def ROI_apply(self):
        if self.ROIlineEdit_x.text() == "" or self.ROIlineEdit_y.text() == "" or self.ROIlineEdit_w.text() == "" or self.ROIlineEdit_h.text() == "":
            QMessageBox.information(self, "消息框", "ROI设置中的4个输入框不可留空。", QMessageBox.Yes)
        else:
            if int(self.ROIlineEdit_w.text()) < 200 or int(self.ROIlineEdit_h.text()) < 100:
                QMessageBox.information(self, "消息框", "ROI的宽度需大于200pix，高度需大于100pix", QMessageBox.Yes)
            elif int(self.ROIlineEdit_x.text())+ int(self.ROIlineEdit_w.text()) > self.cap.get(cv2.CAP_PROP_FRAME_WIDTH):
                QMessageBox.information(self, "消息框", "ROI的设置X+W,超出了相机图片的宽度。", QMessageBox.Yes)
            elif int(self.ROIlineEdit_y.text())+ int(self.ROIlineEdit_h.text()) > self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT):
                QMessageBox.information(self, "消息框", "ROI的设置Y+H,超出了相机图片的高度。", QMessageBox.Yes)
            else:
                self.rect = None
                roi_box = [(int(self.ROIlineEdit_x.text()), int(self.ROIlineEdit_y.text())), (int(self.ROIlineEdit_x.text()) + int(self.ROIlineEdit_w.text()), int(self.ROIlineEdit_y.text()) + int(self.ROIlineEdit_h.text()))]
                self.roi_setting["roi"] = []
                self.roi_setting["roi"].append(roi_box)
                if not self.timer_camera.isActive():
                    self.timer_camera.start(10) # 时钟恢复

    def ROI_delete(self):
        self.roi_setting["roi"] = []
        self.ROIlineEdit_x.setText("")
        self.ROIlineEdit_y.setText("")
        self.ROIlineEdit_w.setText("")
        self.ROIlineEdit_h.setText("")

    def conf_apply(self):
        if self.ThresholdlineEdit.text() == "" or self.NoiseWeightlineEdit.text() == "":
            QMessageBox.information(self, "消息框", "置信度与噪音权重中的2个输入框不可留空。", QMessageBox.Yes)
        else:
            if float(self.ThresholdlineEdit.text()) > 1 or float(self.ThresholdlineEdit.text()) < 0:
                QMessageBox.information(self, "消息框", "颜色阈值取值需在 0 到 1之间。 建议在 0.5 至 0.8 之间。", QMessageBox.Yes)
            else:
                self.roi_setting["color_threshold"] = float(self.ThresholdlineEdit.text())
            if float(self.NoiseWeightlineEdit.text()) > 1 or float(self.NoiseWeightlineEdit.text()) < 0:
                QMessageBox.information(self, "消息框", "噪音权重取值需在 0 到 1之间。 目前是将 黑色，灰色，与不可识别 的颜色默认为噪音。\n此数值越大，则代表噪音在结果计算中的权重越大。如果此数值设置为1，则表示不会降低噪音的权重。\n如果此数值设置为0，则表示完全忽略噪音。\n建议设置在 0.01 至 0.5之间，具体请根据实际图片情况。", QMessageBox.Yes)
            else:
                self.roi_setting["noise_weight"] = float(self.NoiseWeightlineEdit.text())
            self.roi_setting["conf_enhance"] = self.ConfEnhanceCheckBox.isChecked()


    def allbox_move(self, move_direct):
        if self.SinglecomboBox.currentText() != "":
            step_size = int(self.AllStep.text())
            if move_direct == "up":
                self.Y_offset_lineEdit.setText(str(int(self.Y_offset_lineEdit.text()) - step_size))
            elif move_direct == "down":
                self.Y_offset_lineEdit.setText(str(int(self.Y_offset_lineEdit.text()) + step_size))
            elif move_direct == "left":
                self.X_offset_lineEdit.setText(str(int(self.X_offset_lineEdit.text()) - step_size))
            elif move_direct == "right":
                self.X_offset_lineEdit.setText(str(int(self.X_offset_lineEdit.text()) + step_size))
            else:
                pass
            self.roi_setting["x_offset"] = int(self.X_offset_lineEdit.text())
            self.roi_setting["y_offset"] = int(self.Y_offset_lineEdit.text())
        
    def allbox_size_change(self, b_or_s):
        if self.SinglecomboBox.currentText() != "":
            step_size = int(self.AllStep.text())
            if b_or_s == "bigger":
                new_w = int(self.X_size_lineEdit.text()) + step_size
                new_h = int(self.Y_size_lineEdit.text()) + step_size
            elif b_or_s == "smaller":
                new_w = int(self.X_size_lineEdit.text()) - step_size
                new_h = int(self.Y_size_lineEdit.text()) - step_size
            else:
                new_w = int(self.X_size_lineEdit.text())
                new_h = int(self.Y_size_lineEdit.text())
            self.X_size_lineEdit.setText(str(new_w))
            self.Y_size_lineEdit.setText(str(new_h))
            self.roi_setting["x_size"] = int(self.X_size_lineEdit.text())
            self.roi_setting["y_size"] = int(self.Y_size_lineEdit.text())

    def box_add_or_del(self, add_or_del):
        if add_or_del == "add":
            if self.roi_setting['roi'] != []:
                x_ = int((self.roi_setting['roi'][0][1][0] - self.roi_setting['roi'][0][0][0]) / 2)
                y_ = int((self.roi_setting['roi'][0][1][1] - self.roi_setting['roi'][0][0][1]) / 2)
            else:
                x_ = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH) / 2)
                y_ = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) / 2)
            self.roi_setting["boxes"].append([(x_, y_), (x_ + 20, y_ + 20)])  
            self.refresh_boxes()
            self.SinglecomboBox.setCurrentIndex(len(self.roi_setting["boxes"]) - 1)
        else:
            if self.SinglecomboBox.currentText() != "":
                box_id = self.SinglecomboBox.currentIndex()
                self.roi_setting["boxes"].pop(box_id)
                self.refresh_boxes()

    def sbox_move(self, move_direct):
        if self.SinglecomboBox.currentText() != "":
            box_id = self.SinglecomboBox.currentIndex()
            step_size = int(self.SingleStep.text())
            if move_direct == "up":
                new_value = int(self.SingleBox_y.text()) - step_size
                self.SingleBox_y.setText(str(new_value))
            elif move_direct == "down":
                new_value = int(self.SingleBox_y.text()) + step_size
                self.SingleBox_y.setText(str(new_value))
            elif move_direct == "left":
                new_value = int(self.SingleBox_x.text()) - step_size
                self.SingleBox_x.setText(str(new_value))
            elif move_direct == "right":
                new_value = int(self.SingleBox_x.text()) + step_size
                self.SingleBox_x.setText(str(new_value))
            else:
                pass
            if int(self.SingleBoxWidthlineEdit.text()) < 1 or int(self.SingleBoxHeightlineEdit.text()) < 1:
                QMessageBox.information(self, "消息框", "BOX的宽度或高度不可低于1pix,请填入不低于1pix的值，并回车。", QMessageBox.Yes)
            update_box = [(int(self.SingleBox_x.text()), int(self.SingleBox_y.text())), (int(self.SingleBox_x.text()) + int(self.SingleBoxWidthlineEdit.text()), int(self.SingleBox_y.text()) + int(self.SingleBoxHeightlineEdit.text()))]
            self.roi_setting["boxes"][box_id] = update_box
        # print(self.roi_setting["boxes"])

    def sbox_size_change(self, b_or_s):
        if self.SinglecomboBox.currentText() != "":
            box_id = self.SinglecomboBox.currentIndex()
            step_size = int(self.SingleStep.text())
            if b_or_s == "bigger":
                new_w = int(self.SingleBoxWidthlineEdit.text()) + step_size
                new_h = int(self.SingleBoxHeightlineEdit.text()) + step_size
            else:
                new_w = int(self.SingleBoxWidthlineEdit.text()) - step_size
                new_h = int(self.SingleBoxHeightlineEdit.text()) - step_size
            if new_w < 1 or new_h < 1:
                QMessageBox.information(self, "消息框", "BOX的宽度或高度不可低于1pix。", QMessageBox.Yes)
            else:
                self.SingleBoxWidthlineEdit.setText(str(new_w))
                self.SingleBoxHeightlineEdit.setText(str(new_h))
            update_box = [(int(self.SingleBox_x.text()), int(self.SingleBox_y.text())), (int(self.SingleBox_x.text()) + int(self.SingleBoxWidthlineEdit.text()), int(self.SingleBox_y.text()) + int(self.SingleBoxHeightlineEdit.text()))]
            self.roi_setting["boxes"][box_id] = update_box
            

    def comboBox_change(self):
        if self.SinglecomboBox.currentText() != "":
        # box_id = self.SinglecomboBox.currentText()
            box_id = self.SinglecomboBox.currentIndex()
            self.SingleBox_x.setText(str(self.roi_setting["boxes"][box_id][0][0]))
            self.SingleBox_y.setText(str(self.roi_setting["boxes"][box_id][0][1]))
            box_w = self.roi_setting["boxes"][box_id][1][0] - self.roi_setting["boxes"][box_id][0][0]
            box_h = self.roi_setting["boxes"][box_id][1][1] - self.roi_setting["boxes"][box_id][0][1]
            self.SingleBoxWidthlineEdit.setText(str(box_w))
            self.SingleBoxHeightlineEdit.setText(str(box_h))
        else:
            self.SingleBox_x.setText("0")
            self.SingleBox_y.setText("0")
            self.SingleBoxWidthlineEdit.setText("0")
            self.SingleBoxHeightlineEdit.setText("0")

    def roi_setting_load(self):
        if self.SingleStep.text() == "":
            self.SingleStep.setText("1")
        if self.AllStep.text() == "":
            self.AllStep.setText("1")
        self.refresh_boxes()
        self.X_offset_lineEdit.setText(str(self.roi_setting["x_offset"]))
        self.Y_offset_lineEdit.setText(str(self.roi_setting["y_offset"]))
        self.X_size_lineEdit.setText(str(self.roi_setting["x_size"]))
        self.Y_size_lineEdit.setText(str(self.roi_setting["y_size"]))
        if 'roi' in self.roi_setting.keys(): # 如果有roi则只显示roi区域图像
            if self.roi_setting['roi'] != []:
                self.ROIlineEdit_x.setText(str(self.roi_setting["roi"][0][0][0]))
                self.ROIlineEdit_y.setText(str(self.roi_setting["roi"][0][0][1]))
                roi_w = self.roi_setting["roi"][0][1][0] - self.roi_setting["roi"][0][0][0]
                roi_h = self.roi_setting["roi"][0][1][1] - self.roi_setting["roi"][0][0][1]
                self.ROIlineEdit_w.setText(str(roi_w))
                self.ROIlineEdit_h.setText(str(roi_h))
            else:
                self.ROIlineEdit_x.setText("")
                self.ROIlineEdit_y.setText("")
                self.ROIlineEdit_w.setText("")
                self.ROIlineEdit_h.setText("")
        else:
            self.ROIlineEdit_x.setText("")
            self.ROIlineEdit_y.setText("")
            self.ROIlineEdit_w.setText("")
            self.ROIlineEdit_h.setText("")
        self.ThresholdlineEdit.setText(str(self.roi_setting["color_threshold"]))
        self.NoiseWeightlineEdit.setText(str(self.roi_setting["noise_weight"]))
        self.ConfEnhanceCheckBox.setChecked(self.roi_setting["conf_enhance"])
        self.FineTuneCheckBox.setChecked(self.roi_setting["is_finetune"])
        self.FineTuneRangeEdit.setText(str(self.roi_setting["finetune_range"]))
        self.is_finetune()
        
        
    def refresh_boxes(self):
        box_list = [str(x) for x in range(1, len(self.roi_setting["boxes"])+1)]
        self.SinglecomboBox.clear()
        self.SinglecomboBox.addItems(box_list)
        # print("current index = %s"%self.SinglecomboBox.currentIndex())
        
    def roi_save_file(self):
        if self.check_password():
            with open(self.opt.roiyaml, 'w', encoding='utf-8') as f:
                yaml.dump(self.roi_setting, f)
            QMessageBox.information(self, "消息框", "保存成功", QMessageBox.Yes)
        
    def roi_saveas_file(self):
        if self.check_password():
            file_name = QFileDialog.getSaveFileName(self,'保存文件','','Yaml files(*.yaml)')
            if file_name[0] != "":
                with open(file_name[0], "w", encoding='utf-8') as f:
                    yaml.dump(self.roi_setting, f)
                QMessageBox.information(self, "消息框", "保存成功", QMessageBox.Yes)
                self.opt.roiyaml = file_name[0]
                self.ROILoadFiletextBrowser.setText(file_name[0])

    def save_file(self, src_content, dst_file):
        if self.check_password():
            with open(dst_file, "w", encoding='utf-8') as f:
                f.write(src_content)
            QMessageBox.information(self, "消息框", "保存成功", QMessageBox.Yes)

    def saveas_file(self, src_content, textBrowser_id):
        if self.check_password():
            file_name = QFileDialog.getSaveFileName(self,'保存文件','','Yaml files(*.yaml)')
            if file_name[0] != "":
                with open(file_name[0], "w", encoding='utf-8') as f:
                    f.write(src_content)
                textBrowser_id.setText(file_name[0])
                QMessageBox.information(self, "消息框", "保存成功", QMessageBox.Yes)
            

    def camset_apply(self):
        try:
            type(self.cap)
        except:
            self.cap = cv2.VideoCapture(self.cam_setting['cam_id'], cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap.open(self.cam_setting['cam_id'], cv2.CAP_DSHOW)
        cam_feedback = ''
        if 'cam_frame_width' in self.cam_setting.keys():
            cam_frame_width = self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,self.cam_setting['cam_frame_width'])
            cam_feedback += "cam_frame_width = %s\n" % cam_frame_width
        if 'cam_frame_height' in self.cam_setting.keys():
            cam_frame_height = self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT,self.cam_setting['cam_frame_height'])
            cam_feedback += "cam_frame_height = %s\n" % cam_frame_height
        if 'cam_fps' in self.cam_setting.keys():
            cam_fps = self.cap.set(cv2.CAP_PROP_FPS,self.cam_setting['cam_fps'])
            cam_feedback += "cam_fps = %s\n" % cam_fps
        if 'cam_brightness' in self.cam_setting.keys():
            cam_brightness = self.cap.set(cv2.CAP_PROP_BRIGHTNESS,self.cam_setting['cam_brightness']) # CAP_PROP_BRIGHTNESS=10, //!< Brightness of the image (only for those cameras that support).
            cam_feedback += "cam_brightness = %s\n" % cam_brightness
        if 'cam_contrast' in self.cam_setting.keys():
            cam_contrast = self.cap.set(cv2.CAP_PROP_CONTRAST ,self.cam_setting['cam_contrast']) # CAP_PROP_CONTRAST=11, //!< Contrast of the image (only for cameras).
            cam_feedback += "cam_contrast = %s\n" % cam_contrast
        if 'cam_saturation' in self.cam_setting.keys():
            cam_saturation = self.cap.set(cv2.CAP_PROP_SATURATION,self.cam_setting['cam_saturation']) # CAP_PROP_SATURATION=12, //!< Saturation of the image (only for cameras).
            cam_feedback += "cam_saturation = %s\n" % cam_saturation
        if 'cam_hue' in self.cam_setting.keys():
            cam_hue = self.cap.set(cv2.CAP_PROP_HUE,self.cam_setting['cam_hue']) # CAP_PROP_HUE=13, //!< Hue of the image (only for those cameras that support).
            cam_feedback += "cam_hue = %s\n" % cam_hue
        if 'cam_gain' in self.cam_setting.keys():
            cam_gain = self.cap.set(cv2.CAP_PROP_GAIN,self.cam_setting['cam_gain']) # CAP_PROP_GAIN=14, //!< Gain of the image (only for those cameras that support).
            cam_feedback += "cam_gain = %s\n" % cam_gain
        if 'cam_exposure' in self.cam_setting.keys():
            cam_exposure = self.cap.set(cv2.CAP_PROP_EXPOSURE,self.cam_setting['cam_exposure']) # CAP_PROP_EXPOSURE=15, //!< Exposure (only for those cameras that support).
            cam_feedback += "cam_exposure = %s\n" % cam_exposure
        if 'cam_temperature' in self.cam_setting.keys():
            cam_temperature = self.cap.set(cv2.CAP_PROP_TEMPERATURE,self.cam_setting['cam_temperature']) # CAP_PROP_TEMPERATURE=23,
            cam_feedback += "cam_temperature = %s\n" % cam_temperature
        self.CamApplyFeedbackInfo.setText(cam_feedback)
        self.label_picwh.setText("Width: %d, Heigth: %d" % (self.cap.get(cv2.CAP_PROP_FRAME_WIDTH), self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        # self.CamApplyFeedbackInfo.setText("cam_frame_width = %s\ncam_frame_height = %s\ncam_fps = %s\ncam_brightness = %s\ncam_contrast = %s\ncam_saturation = %s\ncam_hue = %s\ncam_gain = %s\ncam_exposure = %s\ncam_temperature = %s" % (cam_frame_width, cam_frame_height, cam_fps, cam_brightness, cam_contrast, cam_saturation, cam_hue, cam_gain, cam_exposure, cam_temperature))
        # self.cap.set(9,0)
        # self.cap.set(39,0) # CAP_PROP_AUTOFOCUS=39
        # self.cap.set(27,self.cam_setting['cam_zoom']) # CAP_PROP_ZOOM=27,
        # self.cap.set(28,self.cam_setting['cam_focus']) # CAP_PROP_FOCUS=28,

    # check the var is defined or not
    def isset(self, v):
        try:
            type(eval(v))
        except:
            return 0
        else:
            return 1


    def camsetbutton_apply(self):
        with open("configs/temp_camset.yaml", "w", encoding='utf-8') as f:
            f.write(self.CamLoadFileContentText.toPlainText())
        with open("configs/temp_camset.yaml", encoding='utf-8') as f:
            self.cam_setting = yaml.load(f, Loader=yaml.FullLoader)
        self.camset_apply()

    def check_yaml_file(self, yaml_setting, items):
        for i in items:
            if i not in yaml_setting.keys():
                return False, i
        return True, None

    def open_cam_file(self):
        camfile_name = QFileDialog.getOpenFileName(self,'选择文件','','Yaml files(*.yaml)')
        if camfile_name[0] != "":
            self.opt.camyaml = camfile_name[0]
            with open(self.opt.camyaml, encoding='utf-8') as f:
                camsetting_content = f.read()
            with open(self.opt.camyaml, encoding='utf-8') as f:
                yaml_setting = yaml.load(f, Loader=yaml.FullLoader)
            cam_items = ['cam_id', 'cam_reverse']
            isOK, lost_item = self.check_yaml_file(yaml_setting, cam_items)
            if isOK:
                self.cam_setting = yaml_setting
                self.CamLoadFileContentText.setText(camsetting_content)
                self.CamLoadFiletextBrowser.setText(camfile_name[0])
            else:
                QMessageBox.information(self, "消息框", "打开的cam yaml文件中未包含%s字段，请检查是否载入了错误的文件。 cam_yaml文件应包含所有以下字段%s" % (lost_item ,str(cam_items)), QMessageBox.Yes)

    def open_roi_file(self):
        roifile_name = QFileDialog.getOpenFileName(self,'选择文件','','Yaml files(*.yaml)')
        if roifile_name[0] != "":
            self.opt.roiyaml = roifile_name[0]
            self.ROILoadFiletextBrowser.setText(roifile_name[0])
            with open(self.opt.roiyaml, encoding='utf-8') as f:
                yaml_setting = yaml.load(f, Loader=yaml.FullLoader)
            roi_items = ['boxes', 'color_threshold', 'conf_enhance', 'noise_weight', 'roi', 'x_offset', 'x_size', 'y_offset', 'y_size', 'is_finetune', 'finetune_range']
            isOK, lost_item = self.check_yaml_file(yaml_setting, roi_items)
            if isOK:
                self.roi_setting = yaml_setting  
                self.roi_setting_load()
            else:
                QMessageBox.information(self, "消息框", "打开的roi yaml文件中未包含%s字段，请检查是否载入了错误的文件。 roi yaml文件应包含所有以下字段%s" % (lost_item ,str(roi_items)), QMessageBox.Yes)
    
    def open_prj_file(self):
        prjfile_name = QFileDialog.getOpenFileName(self,'选择文件','','Yaml files(*.yaml)')
        if prjfile_name[0] != "":
            self.opt.prjyaml = prjfile_name[0]
            with open(self.opt.prjyaml, encoding='utf-8') as f:
                prjsetting_content = f.read()
            with open(self.opt.prjyaml, encoding='utf-8') as f:
                yaml_setting = yaml.load(f, Loader=yaml.FullLoader)
            prj_items = ['box_color', 'cam_skip', 'boxline_width', 'cap_delay', 'sample_count', 'color_count', 'csv_create', 'result_path']
            isOK, lost_item = self.check_yaml_file(yaml_setting, prj_items)
            if isOK:
                self.prj_setting = yaml_setting
                self.PrjLoadFileContentText.setText(prjsetting_content)
                self.PrjLoadFiletextBrowser.setText(prjfile_name[0])
            else:
                QMessageBox.information(self, "消息框", "打开的prj yaml文件中未包含%s字段，请检查是否载入了错误的文件。 prj yaml文件应包含所有以下字段%s" % (lost_item ,str(prj_items)), QMessageBox.Yes)


    def pause_ui(self):
        if self.timer_camera.isActive():
            self.timer_camera.stop() # 时钟停止
            self.pause_btn.setText('播放')
        else:
            self.timer_camera.start(10) # 时钟恢复
            self.pause_btn.setText('暂停')
        

    def reset_ui(self):
        if self.cap.isOpened():
            self.cap.release()
        self.slot_init()
        

    # 开启摄像头
    def opencam(self):
        # 摄像头设置初始化
        self.camset_apply()
        self.timer_camera.start(10)
        self.pause_btn.setEnabled(True) # “暂停”按钮enable
        self.reset_btn.setEnabled(True) # “重置”按钮enable
        self.AddBoxButton.setEnabled(True)
        self.DeleteBoxButton.setEnabled(True)
        self.AllDeleteButton.setEnabled(True)
        self.ROIApplyButton.setEnabled(True)
        self.ROIAddButton.setEnabled(True)
        self.ROIDeleteButton.setEnabled(True)
        self.opencam_btn.setEnabled(False) # “开启摄像头”按钮disable

        
    # 每30MS刷新QT窗口各控件状态
    def feedback_qt(self):
        self.info_list = ""
        # 图像传递至qt label(video_stream)
        if self.cap.isOpened():
            ret, cam_image = self.cap.read()
            try:
                type(eval(self.x_rate))
            except:
                cam_width = len(cam_image[0])
                cam_height = len(cam_image)
                self.x_rate = cam_width/self.video_stream.width()
                self.y_rate = cam_height/self.video_stream.height()
            else:
                pass
            if self.cam_setting['cam_reverse'] == 1:
                cam_image = cv2.rotate(cam_image, cv2.ROTATE_180) # 摄像头图片旋转180度
            if 'roi' in self.roi_setting.keys(): # 如果有roi则只显示roi区域图像
                if self.roi_setting['roi'] != []:
                    roi_ = self.roi_setting['roi'][0]
                    if roi_[1][0] > self.cap.get(cv2.CAP_PROP_FRAME_WIDTH) or roi_[1][1] > self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT):
                        QMessageBox.information(self, "消息框", "ROI的设置X+W,超出了相机图片的宽度，或Y+H,超出了相机图片的高度。请重新设定ROI的X,Y,W,H值。" , QMessageBox.Yes)
                        self.roi_setting['roi'] = []
                    else:
                        cam_image = cam_image[roi_[0][1]:roi_[1][1], roi_[0][0]:roi_[1][0], :]
            self.prj_setting['cam_skip'] -= 1
            if self.prj_setting['cam_skip'] <= 0:
                if ret:
                    # 将BOX画在图像上
                    box_id = 0
                    for i in self.roi_setting["boxes"]:
                        # 如所有BOX在x或y轴方向有位移补偿，则需要加入补偿值
                        # print(self.roi_setting["x_offset"], type(self.roi_setting["x_offset"]))
                        if self.roi_setting["x_offset"] != 0:
                            i = [(i[0][0] + self.roi_setting["x_offset"], i[0][1]), (i[1][0] + self.roi_setting["x_offset"], i[1][1])]
                        if self.roi_setting["y_offset"] != 0:
                            i = [(i[0][0], i[0][1] + self.roi_setting["y_offset"]), (i[1][0], i[1][1] + self.roi_setting["y_offset"])]
                        # 如所有BOX在x或y轴方向需要缩放，则需要加入缩放值
                        if self.roi_setting["x_size"] != 0:
                            i = [(i[0][0], i[0][1]), (i[1][0] + self.roi_setting["x_size"], i[1][1])]
                        if self.roi_setting["y_size"] != 0:
                            i = [(i[0][0], i[0][1]), (i[1][0], i[1][1] + self.roi_setting["y_size"])]
                        box_id += 1
                        boximg_color_info = ImgProcess(cam_image[i[0][1]:i[1][1], i[0][0]:i[1][0], :]) # 计算box框中的图片颜色分布
                        # 如有置信度增强设置，则使用增强算法
                        if self.roi_setting["conf_enhance"] == 1:
                            box_color, color_rate = IsColorEnhance(boximg_color_info, self.roi_setting["color_threshold"], self.roi_setting["noise_weight"])
                        else:
                            box_color, color_rate = IsColor(boximg_color_info, self.roi_setting["color_threshold"], self.roi_setting["noise_weight"])
                        self.info_list += 'box%d_%s_%f'%(box_id,box_color,color_rate) + str(boximg_color_info) + '\n' # 将BOX颜色信息存入info_list中
                        if box_id - 1 == self.SinglecomboBox.currentIndex():
                            cv2.rectangle(cam_image, i[0], i[1], self.prj_setting["box_color"]["green"], self.prj_setting["boxline_width"]) # 选中的BOX显示为绿色
                        else:
                            cv2.rectangle(cam_image, i[0], i[1], self.prj_setting["box_color"][box_color], self.prj_setting["boxline_width"]) # 参数依次是:图像，左上起始点元组，右下终止点元组，边框颜色，边框线宽
                        # cv2.putText(cam_image, 'box%d'%box_id, (i[0][0],i[0][1]-5), cv2.FONT_HERSHEY_SIMPLEX, 1, self.prj_setting["box_color"][box_color], 1) # 参数依次是:图像，label文字，左上起始点元组，字体，字体大小，字体颜色，字体粗细
                        cv2.putText(cam_image, '%d'%box_id, (i[0][0],i[0][1]-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.prj_setting["box_color"][box_color], 1)
                    # if self.rect:
                        # print("video output add box:", self.rect)
                        # print(len(cam_image[0]), len(cam_image))
                        # cam_width = len(cam_image[0])
                        # cam_height = len(cam_image)
                        # self.x_rate = cam_width/self.video_stream.width()
                        # self.y_rate = cam_height/self.video_stream.height()
                        # rect_box = [[self.rect.x(), self.rect.y()], [self.rect.x()+self.rect.width(), self.rect.y()+self.rect.height()]]
                        # rect_box = [[int(rect_box[0][0]*self.x_rate), int(rect_box[0][1]*self.y_rate)], [int(rect_box[1][0]*self.x_rate), int(rect_box[1][1]*self.y_rate)]]
                        # cv2.rectangle(cam_image, rect_box[0], rect_box[1], self.prj_setting["box_color"]["red"], self.prj_setting["boxline_width"])
                    show = cam_image
                    show = cv2.cvtColor(show,cv2.COLOR_BGR2RGBA) #视频色彩转换回RGB，这样才是现实的颜色
                    showImage = QtGui.QImage(show.data,show.shape[1],show.shape[0],QtGui.QImage.Format_RGBA8888) #把读取到的视频数据变成QImage形式
                    showImage = QPixmap(showImage).scaled(self.video_stream.width(), self.video_stream.height()) # 将图片按照控件大小进行缩放
                    # self.video_stream.setScaledContents(True)
                    self.scene.clear() # if no this command, the memory will be consumed until hang.
                    self.scene.addPixmap(showImage)
                    # self.video_stream.setPixmap(QtGui.QPixmap.fromImage(showImage))  #往显示视频的Label里 显示QImage
                    # self.video_stream.lower()
                    self.update()

        self.info_text.setText(self.info_list) # 在信息框中显示量测数据
        self.cursor_end(self.info_text) # 下拉至最下方显示最新信息

    def cursor_end(self, browser_id):
        # info_display滑块移至最下方
        cursor = browser_id.textCursor()
        pos = len(browser_id.toPlainText())
        cursor.setPosition(pos)
        browser_id.setTextCursor(cursor)


    # 关闭程序窗口与console窗口
    def all_close(self):
        # if self.trd_live:
            # trd_stop.append('end')
            # time.sleep(1)
            # self.stop_thread(self.trd)
        self.close()


def ParseOpt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--camyaml', type=str, default='configs/camera_setting.yaml', help='select camera setting file')
    parser.add_argument('--roiyaml', type=str, default='configs/roi_setting.yaml', help='select ROI setting file')
    parser.add_argument('--prjyaml', type=str, default='configs/prj_setting.yaml', help='select Project setting file')
    opt = parser.parse_args()
    # opt.imgsz *= 2 if len(opt.imgsz) == 1 else 1  # expand
    return opt


if __name__ == "__main__":
    opt = ParseOpt()
    print(opt.camyaml)
    print(opt.roiyaml)
    print(opt.prjyaml)
    #固定的，PyQt5程序都需要QApplication对象。sys.argv是命令行参数列表，确保程序可以双击运行
    app = QApplication(sys.argv)
    #初始化
    myWin = MyMainForm(opt)
    #将窗口控件显示在屏幕上
    myWin.show()
    #程序运行，sys.exit方法确保程序完整退出。
    sys.exit(app.exec_())
