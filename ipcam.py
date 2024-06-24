# -*- coding: GB2312 -*-

import cv2
import time
import threading
from multiprocessing.dummy import Pool as ThreadPool
import numpy as np
from collections import deque
from time import sleep
 
# ������Ӱ������Ӱ�񣬲��ö��̵߳ķ�ʽ�����ͻ�����ջͼ֡�����⡣
class ipcamCapture:
    def __init__(self, URL):
        self.Frame = []
        self.URL = URL
        self.status = False
        self.isstop = False
		
	# ��Ӱ�����ӡ�
        self.capture = cv2.VideoCapture(URL)
 
    def start(self):
	# �ѳ���Ž����̣߳�daemon=True ��ʾ���̻߳��������̹߳رն��رա�
        print('ipcam started!')
        threading.Thread(target=self.queryframe, daemon=True, args=()).start()
 
    def stop(self):
	# �ǵ�Ҫ���ֹͣ����ѭ���Ŀ��ء�
        self.isstop = True
        print('ipcam stopped!')
   
    def getframe(self):
	# ������ҪӰ��ʱ���ٻش����µ�Ӱ��
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
        recent_Frames[i].append(frame)  # ���ս�����뻺�����
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
        print('��ʱ�� %s ms' % ((time.time() - start_time)*1000))
        # ���߳��޷����ڲ�showͼ��,���԰�ͼ�������浽������,���һ����ʾ
        for i,Frame in enumerate(recent_Frames):
            cv2.imshow(URLS[i],cv2.resize(Frame[0],(1920,1080)))  # ���е�һ֡
            cv2.waitKey(1)
 
if __name__ == "__main__":
    URLS = [
    "rtsp://admin:bjkjdx12@192.168.31.101:554",
    "rtsp://admin:bjkjdx12@192.168.31.102:554"]  # rtsp��ַ�б�
 
    ipcams = []  # ����������б�
    recent_Frames = [deque(maxlen=10) for _ in range(len(URLS))]  # ��Ž��ͼ��Ķ���
    source_ids = list(range(len(URLS)))  # rtspԴ���
    for URL in URLS:
        # ������Ӱ��
        ipc = ipcamCapture(URL)
        ipcams.append(ipc)
    for ipcam in ipcams:
        # �������߳�
        ipcam.start()
    # ��ͣ1�룬ȷ��Ӱ���Ѿ����
    time.sleep(1)
    # ʹ������ѭ��ߢȡӰ��ֱ������Esc������
    multi_infer(source_ids)
