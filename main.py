# -*- coding: GB2312 -*-

import cv2
import time
import threading
from multiprocessing.dummy import Pool as ThreadPool
import numpy as np
from collections import deque
import pyrealsense2 as rs
from pynput import keyboard
print("Environment is Ready")

#**************Prepare for rscam**************#

# Creating a Pipeline
pipe = rs.pipeline()                      # Create a pipeline
cfg = rs.config()                         # Create a default configuration
print("Pipeline is created")

# Find RealSense Devices
print("Searching Devices..")
selected_devices = []                     # Store connected device(s)

for d in rs.context().devices:
    selected_devices.append(d)
    print(d.get_info(rs.camera_info.name))
if not selected_devices:
    print("No RealSense device is connected!")

# Find Depth and RGB Sensors
rgb_sensor = depth_sensor = None

for device in selected_devices:                         
    print("Required sensors for device:", device.get_info(rs.camera_info.name))
    for s in device.sensors:                              # Show available sensors in each device
        if s.get_info(rs.camera_info.name) == 'RGB Camera':
            print(" - RGB sensor found")
            rgb_sensor = s                                # Set RGB sensor
        if s.get_info(rs.camera_info.name) == 'Stereo Module':
            depth_sensor = s                              # Set Depth sensor
            print(" - Depth sensor found")

# Displaying Depth and Color Frames
colorizer = rs.colorizer()                                # Mapping depth data into RGB color space
profile = pipe.start(cfg)                                 # Configure and start the pipeline

for _ in range(10):                                       # Skip first frames to give syncer and auto-exposure time to adjust
    frameset = pipe.wait_for_frames()

#**************Prepare for ipcam**************#

class ipcamCapture:
    def __init__(self, URL):
        self.Frame = []
        self.URL = URL
        self.status = False
        self.isstop = False
		
        self.capture = cv2.VideoCapture(URL)

    def start(self):
        print(self.URL + ' ipcam started!')
        threading.Thread(target=self.queryframe, daemon=True, args=()).start()

    def stop(self):
        self.isstop = True
        print(self.URL + ' ipcam stopped!')

    def getframe(self):
        return self.Frame

    def queryframe(self):
        while (not self.isstop):
            self.status, self.Frame = self.capture.read()            
        self.capture.release()

def image_infer(source_id):
    i = source_id
    try:
        frame = ipcams[i].getframe()
        recent_Frames[i].append(frame)
    except Exception as e:
        Nosignal_wall_paper = np.zeros((400,720,3))
        cv2.putText(Nosignal_wall_paper,'NOSIGNALS',(100,250),cv2.FONT_HERSHEY_SIMPLEX,3,(0,255,0),15)
        recent_Frames[i].append(Nosignal_wall_paper)
        print(e.__traceback__.tb_lineno,e.args)

#**************Keyboard listener**************#

def on_press(key):
    global KEY
    try:
        if key == keyboard.Key.space:
            KEY = 'SPACE'
        if key == keyboard.Key.enter:
            KEY = 'ENTER'

    except AttributeError:
        print(f'-{key}- is pressed')

def on_release(key):
    if key == keyboard.Key.esc:
        # Press Esc to exit listening
        return False

def start_listener():
    with keyboard.Listener(
        on_press=on_press,
        on_release=on_release) as listener:
        listener.join()

#**************Main function**************#

if __name__ == "__main__":
    URLS = [
    "rtsp://admin:bjkjdx12@192.168.31.101:554",
    "rtsp://admin:bjkjdx12@192.168.31.102:554"]
 
    ipcams = []
    recent_Frames = [deque(maxlen=10) for _ in range(len(URLS))]
    source_ids = list(range(len(URLS)))
    for URL in URLS:
        ipc = ipcamCapture(URL)
        ipcams.append(ipc)
    for ipcam in ipcams:
        ipcam.start()
    time.sleep(1)
    pool = ThreadPool(8)

    print('1.press Space to pause capturing')
    print('2.press Space again to continue capturing')
    print('3.Press Enter to close windows')

    KEY = 'none'
    listener_thread = threading.Thread(target=start_listener)
    listener_thread.start()

    pause_flag = True

    while True:
        pool.map(image_infer,source_ids)

        frameset = pipe.wait_for_frames()                     # Read frames from the file, packaged as a frameset
        depth_frame = frameset.get_depth_frame()              # Get depth frame
        color_frame = frameset.get_color_frame()              # Get RGB frame

        if depth_frame:
            depth_image = np.asanyarray(colorizer.colorize(depth_frame).get_data())
        if color_frame:
            rgb_image = np.asanyarray(color_frame.get_data())

        depth_dim = depth_image.shape
        rgb_dim = rgb_image.shape

        # If depth and rgb resolutions are different, resize rgb image to match depth image for display
        if depth_dim != rgb_dim:
            resized_rgb_image = cv2.resize(rgb_image, dsize=(depth_dim[1], depth_dim[0]), interpolation=cv2.INTER_AREA)
            images = np.hstack((resized_rgb_image, depth_image))
        else:
            images = np.hstack((rgb_image, depth_image))

        # Show images
        if pause_flag:
            cv2.namedWindow('RealSense D455', cv2.WINDOW_AUTOSIZE)
            cv2.imshow('RealSense D455', cv2.cvtColor(images, cv2.COLOR_RGB2BGR))
            cv2.waitKey(1)
            for i,Frame in enumerate(recent_Frames):
                cv2.namedWindow(URLS[i][-18:-4], cv2.WINDOW_AUTOSIZE)
                cv2.imshow(URLS[i][-18:-4],cv2.resize(Frame[0],(960,540)))
                cv2.waitKey(1)

        # Keyboard operation
        if KEY == 'SPACE' and pause_flag is True:       # press 'space' to pause capturing
            KEY = 'none'
            pause_flag = False
            print('Now is pause')
        elif KEY == 'SPACE' and pause_flag is False:    # press 'space' again to continue capturing
            KEY = 'none'
            pause_flag = True
            print('Now is continue')
        elif KEY == 'ENTER':                            # press 'enter' to close the windows and end loop
            cv2.destroyAllWindows()
            break

    print('Please press Esc to exit')
    listener_thread.join()

    print('Done')
