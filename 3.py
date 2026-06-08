#!/usr/bin/python
# -*- coding: utf-8 -*-
import cv2
import time
from threading import Thread
from PIL import Image
from Command import COMMAND as cmd
from Thread import *
from Video import *
from PyQt5 import QtCore
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtGui import QPixmap
import sys
 
 
class FaceTrackingWindow(QMainWindow):
    def __init__(self, host_ip):
        super().__init__()
        self.endChar = '\n'
        self.intervalChar = '#'
 
        self.h = host_ip
        self.TCP = VideoStreaming()
 
        # 舵机初始角度
        self.servo1 = 90  # 水平
        self.servo2 = 90  # 垂直
 
        # 视频显示
        self.label_Video = QLabel(self)
        self.label_Video.setPixmap(QPixmap('image/Raspberry_4WD_M_Car.png'))
        self.setCentralWidget(self.label_Video)
 
        # 追踪开关（默认开启）
        self.tracking_enabled = True
 
        # 定时器：~30fps 刷新画面 + 执行追踪
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timer)
        self.timer.start(34)
 
        # 连接到小车
        self._connect()
 
    # ------------------------------------------------------------------ #
    #  连接                                                                #
    # ------------------------------------------------------------------ #
 
    def _connect(self):
        self.TCP.StartTcpClient(self.h)
        try:
            self.streaming = Thread(target=self.TCP.streaming, args=(self.h,))
            self.streaming.start()
        except Exception as e:
            print('video error:', e)
 
    # ------------------------------------------------------------------ #
    #  定时器回调                                                           #
    # ------------------------------------------------------------------ #
 
    def _on_timer(self):
        self.TCP.video_Flag = False
        try:
            if self._is_valid_jpg('video.jpg'):
                self.label_Video.setPixmap(QPixmap('video.jpg'))
                if self.tracking_enabled:
                    self._find_face(self.TCP.face_x, self.TCP.face_y)
        except Exception as e:
            print(e)
        self.TCP.video_Flag = True
 
    # ------------------------------------------------------------------ #
    #  人脸追踪核心逻辑                                                     #
    # ------------------------------------------------------------------ #
 
    def _find_face(self, face_x, face_y):
        if face_x == 0 and face_y == 0:
            return  # 未检测到人脸
 
        # 归一化到 [-1, 1]
        offset_x = float(face_x / 400 - 0.5) * 2
        offset_y = float(face_y / 300 - 0.5) * 2
 
        # 死区：人脸已在中心，不移动
        if abs(offset_x) < 0.15 and abs(offset_y) < 0.15:
            return
 
        # 计算舵机增量
        delta_x = int(4 * offset_x)
        delta_y = int(-4 * offset_y)
 
        self.servo1 = max(0,   min(180, self.servo1 + delta_x))
        self.servo2 = max(80,  min(180, self.servo2 + delta_y))
 
        # 发送舵机命令
        self.TCP.sendData(
            cmd.CMD_SERVO + self.intervalChar + '0'
            + self.intervalChar + str(self.servo1) + self.endChar
        )
        self.TCP.sendData(
            cmd.CMD_SERVO + self.intervalChar + '1'
            + self.intervalChar + str(self.servo2) + self.endChar
        )
 
    # ------------------------------------------------------------------ #
    #  工具                                                                #
    # ------------------------------------------------------------------ #
 
    def _is_valid_jpg(self, jpg_file):
        try:
            if jpg_file.split('.')[-1].lower() == 'jpg':
                with open(jpg_file, 'rb') as f:
                    buf = f.read()
                    if not buf.startswith(b'\xff\xd8'):
                        return False
                    elif buf[6:10] in (b'JFIF', b'Exif'):
                        if not buf.rstrip(b'\0\r\n').endswith(b'\xff\xd9'):
                            return False
                    else:
                        Image.open(f).verify()
        except:
            return False
        return True
 
    def closeEvent(self, event):
        self.timer.stop()
        try:
            stop_thread(self.streaming)
        except:
            pass
        self.TCP.StopTcpcClient()
 
 
if __name__ == '__main__':
    HOST_IP = "192.168.x.x"   # <-- 改成你的小车 IP
 
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    window = FaceTrackingWindow(HOST_IP)
    window.show()
    sys.exit(app.exec_())
 