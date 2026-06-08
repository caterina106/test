#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
人脸追踪 + 舵机控制 核心模块
从原始 Client.py 中提取
依赖：PyQt5, VideoStreaming (Video.py), Command (Command.py)
"""

from PyQt5.QtCore import QTimer
from Command import COMMAND as cmd


class FaceTrackingServoController:
    """
    人脸追踪 + 舵机控制器
    需要传入一个已连接的 TCP 对象（VideoStreaming 实例）
    """

    # 协议字符
    END_CHAR = '\n'
    INTERVAL_CHAR = '#'

    def __init__(self, tcp_client):
        """
        :param tcp_client: VideoStreaming 实例，需已调用 StartTcpClient()
        """
        self.TCP = tcp_client

        # 舵机初始角度
        self.servo1 = 90   # 水平方向（左右）
        self.servo2 = 90   # 垂直方向（上下）

        # 追踪开关
        self.tracking_enabled = False

        # 定时器：约 30fps 刷新一次视频帧并执行追踪
        self.timer = QTimer()
        self.timer.timeout.connect(self._on_timer_tick)

    # ------------------------------------------------------------------ #
    #  公开接口                                                             #
    # ------------------------------------------------------------------ #

    def start(self):
        """启动视频刷新定时器"""
        self.timer.start(34)   # ~29.4 fps

    def stop(self):
        """停止定时器"""
        self.timer.stop()

    def toggle_tracking(self):
        """切换追踪开关，返回当前状态"""
        self.tracking_enabled = not self.tracking_enabled
        return self.tracking_enabled

    def set_servo(self, servo_id: int, angle: int):
        """
        直接设置舵机角度并发送命令
        :param servo_id: 0 = 水平, 1 = 垂直
        :param angle: 目标角度
        """
        angle = max(0, min(180, angle))
        if servo_id == 0:
            self.servo1 = angle
        else:
            self.servo2 = angle
        self.TCP.sendData(
            cmd.CMD_SERVO
            + self.INTERVAL_CHAR + str(servo_id)
            + self.INTERVAL_CHAR + str(angle)
            + self.END_CHAR
        )

    def home(self):
        """舵机归中（90°）"""
        self.set_servo(0, 90)
        self.set_servo(1, 90)

    # ------------------------------------------------------------------ #
    #  内部逻辑                                                             #
    # ------------------------------------------------------------------ #

    def _on_timer_tick(self):
        """
        定时器回调：
        1. 读取最新帧中的人脸坐标（由 VideoStreaming 解析）
        2. 若追踪已开启，则调用追踪逻辑
        """
        if self.tracking_enabled:
            face_x = self.TCP.face_x   # VideoStreaming 内部更新
            face_y = self.TCP.face_y
            self._find_face(face_x, face_y)

    def _find_face(self, face_x: float, face_y: float):
        """
        追踪核心逻辑：
        将人脸坐标归一化到 [-1, 1]，计算偏差后驱动舵机

        坐标系约定（与原始代码一致）：
          - 画面宽 800px，中心 x = 400
          - 画面高 600px，中心 y = 300

        :param face_x: 人脸中心 x 像素坐标（0 表示未检测到）
        :param face_y: 人脸中心 y 像素坐标（0 表示未检测到）
        """
        if face_x == 0 and face_y == 0:
            return  # 未检测到人脸，不移动

        # 归一化到 [-1, 1]
        offset_x = float(face_x / 400 - 0.5) * 2
        offset_y = float(face_y / 300 - 0.5) * 2

        # 死区：人脸已在中心附近，不必微调
        DEAD_ZONE = 0.15
        if abs(offset_x) < DEAD_ZONE and abs(offset_y) < DEAD_ZONE:
            return

        # 计算舵机增量（水平 4°/格，垂直 4°/格，y 轴取反）
        delta_x = int(4 * offset_x)
        delta_y = int(-4 * offset_y)

        new_servo1 = max(0,   min(180, self.servo1 + delta_x))
        new_servo2 = max(80,  min(180, self.servo2 + delta_y))  # 垂直限位 80~180

        # 只在角度真正变化时发送命令，减少无效通信
        if new_servo1 != self.servo1:
            self.set_servo(0, new_servo1)

        if new_servo2 != self.servo2:
            self.set_servo(1, new_servo2)