# -*- coding: GB2312 -*-

import cv2
import time
import threading
from multiprocessing.dummy import Pool as ThreadPool
import numpy as np
from collections import deque
from time import sleep
 
# 接收摄影机串流影像，采用多线程的方式，降低缓冲区栈图帧的问题。
class ipcamCapture:
    def __init__(self, URL):
        self.Frame = []
        self.URL = URL
        self.status = False
        self.isstop = False
		
	# 摄影机连接。
        self.capture = cv2.VideoCapture(URL)
 
    def start(self):
	# 把程序放进子线程，daemon=True 表示该线程会随着主线程关闭而关闭。
        print('ipcam started!')
        threading.Thread(target=self.queryframe, daemon=True, args=()).start()
 
    def stop(self):
	# 记得要设计停止无限循环的开关。
        self.isstop = True
        print('ipcam stopped!')
   
    def getframe(self):
	# 当有需要影像时，再回传最新的影像。
        return self.Frame
        
    def queryframe(self):
        while (not self.isstop):
            self.status, self.Frame = self.capture.read()            
        self.capture.release()
 
def image_infer(source_id):
    i = source_id
    try:
        frame = ipcams[i].getframe() 
        #**************do someting with the frame**************#
        # Fortunately,global variables can be used here!       #
        # eg.                                                  #
        # 1.object detection                                   # 
        # 2.segmentation                                       #
        # 3.classify                                           #
        # 4...                                                 #
        ########################################################
        recent_Frames[i].append(frame)  # 最终结果放入缓存队列
    except Exception as e:
        Nosignal_wall_paper = np.zeros((400,720,3))
        cv2.putText(Nosignal_wall_paper,'NOSIGNALS',(100,250),cv2.FONT_HERSHEY_SIMPLEX,3,(0,255,0),15)
        recent_Frames[i].append(Nosignal_wall_paper)
        print(e.__traceback__.tb_lineno,e.args)               
 
def multi_infer(source_ids):
    pool = ThreadPool(8)
    while True:
        start_time = time.time()
        pool.map(image_infer,source_ids)
        print('用时共 %s ms' % ((time.time() - start_time)*1000))
        # 多线程无法在内部show图像,所以把图像结果缓存到队列中,最后一起显示
        for i,Frame in enumerate(recent_Frames):
            cv2.imshow(URLS[i],cv2.resize(Frame[0],(1920,1080)))  # 队列第一帧
            cv2.waitKey(1)
 
if __name__ == "__main__":
    URLS = [
    "rtsp://admin:bjkjdx12@192.168.31.101:554",
    "rtsp://admin:bjkjdx12@192.168.31.102:554"]  # rtsp地址列表
 
    ipcams = []  # 摄像机对象列表
    recent_Frames = [deque(maxlen=10) for _ in range(len(URLS))]  # 存放结果图像的队列
    source_ids = list(range(len(URLS)))  # rtsp源编号
    for URL in URLS:
        # 连接摄影机
        ipc = ipcamCapture(URL)
        ipcams.append(ipc)
    for ipcam in ipcams:
        # 启动子线程
        ipcam.start()
    # 暂停1秒，确保影像已经填充
    time.sleep(1)
    # 使用无穷循环撷取影像，直到按下Esc键结束
    multi_infer(source_ids)
