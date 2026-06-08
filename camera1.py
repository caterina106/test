#!/usr/bin/python 
# -*- coding: utf-8 -*-
import numpy as np
import cv2

from pca9685 import PCA9685

class Servo:
    def __init__(self):
        self.pwm_frequency = 50
        self.initial_pulse = 1500
        self.pwm_channel_map = {
            '0': 8,
            '1': 9,
            '2': 10,
            '3': 11,
            '4': 12,
            '5': 13,
            '6': 14,
            '7': 15
        }
        self.pwm_servo = PCA9685(0x40, debug=True)
        self.pwm_servo.set_pwm_freq(self.pwm_frequency)
        for channel in self.pwm_channel_map.values():
            self.pwm_servo.set_servo_pulse(channel, self.initial_pulse)

    def set_servo_pwm(self, channel: str, angle: int, error: int = 10) -> None:
        angle = int(angle)
        if channel not in self.pwm_channel_map:
            raise ValueError(f"Invalid channel: {channel}. Valid channels are {list(self.pwm_channel_map.keys())}.")
        pulse = 2500 - int((angle + error) / 0.09) if channel == '0' else 500 + int((angle + error) / 0.09)
        self.pwm_servo.set_servo_pulse(self.pwm_channel_map[channel], pulse)

# But just for camera (servo 0 and Servo 1)
pwm_servo = Servo()
servo1 = 90
servo2 = 90

face_cascade = cv2.CascadeClassifier(r'haarcascade_frontalface_default.xml')# detect face model

cap = cv2.VideoCapture(0) 

def find_Face(face_x,face_y): # Tracking Logic
        global servo1,servo2
        if face_x!=0 and face_y!=0:
            offset_x=float(face_x/400-0.5)*2 # normalize to [-1, 1]
            offset_y=float(face_y/300-0.5)*2 # normalize to [-1, 1]
            delta_degree_x = int(4* offset_x)  # how much to move horizontally
            delta_degree_y = int(-4 * offset_y) # how much to move vertically
            servo1=servo1+delta_degree_x
            servo2=servo2+delta_degree_y
            if servo1 > 180:
                servo1 = 180
            elif servo1 < 0:
                servo1 = 0
            
            if servo2 > 180:
                servo2 = 180
            elif servo2 < 0:
                servo2 = 0

            if offset_x > -0.15 and offset_y >-0.15 and offset_x < 0.15 and offset_y <0.15:
                pass # face is centered, don't move
            else:
                pwm_servo.set_servo_pwm('0', servo1)
                pwm_servo.set_servo_pwm('1', servo2)

while True:
     ret,frame = cap.read()
     img = frame # default frame
     if ret:
          gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
          faces = face_cascade.detectMultiScale(gray,1.3,5) #detec face 
          if len(faces)>0 :
                for (x,y,w,h) in faces:
                    face_x=float(x+w/2.0) # get face_x,face_y
                    face_y=float(y+h/2.0)
                    img= cv2.circle(frame, (int(face_x),int(face_y)), int((w+h)/4), (0, 255, 0), 2) # highlight face
                    find_Face(face_x,face_y)
          else:
            face_x=0
            face_y=0
            
     cv2.imshow('camera',img)
     if cv2.waitKey(1)&0xFF == ord('q'): # from claude
          break
cap.release()
cv2.destroyAllWindows()
          


