#!/usr/bin/env python2.7

import cv2
import numpy as np


cascade = cv2.CascadeClassifier("/usr/local/share/OpenCV/haarcascades/haarcascade_frontalface_alt.xml")
direction = 'unknown'
w = 0
h = 0

camera = cv2.VideoCapture(0)
cv2.namedWindow('faces')

def detect(img):
	rects = cascade.detectMultiScale(img, scaleFactor=1.3, minNeighbors=4, minSize=(30, 30))
	if len(rects) == 0:
		return []
	rects[:,2:] += rects[:,:2]
	return rects

def getsize(img):
	h, w = img.shape[:2]
	return w, h

def draw_rects(img, rects, color):
	for x1, y1, x2, y2 in rects:
		cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
		width = x2 - x1
		offset = x1 + (width/2)

		if (offset > (w/2)+5):
			direction = 'LEFT'
		elif (offset < (w/2)-5):
			direction = 'RIGHT'
		else:
			direction = 'DUCK!'

		#draw_str(img, (x1-(width/2), y1), direction )
		print direction

def draw_str(dst, (x, y), s):
	cv2.putText(dst, s, (x+1, y+1), cv2.FONT_HERSHEY_PLAIN, 1.0, (0, 0, 0), thickness = 2, lineType=cv2.CV_AA)
	cv2.putText(dst, s, (x, y), cv2.FONT_HERSHEY_PLAIN, 1.0, (255, 255, 255), lineType=cv2.CV_AA)

if __name__ == "__main__":

	a,b = camera.read() 
	w,h = getsize(b)
	cv2.waitKey(30)

	while True:
		'do nothing'
		a,b = camera.read() 
		cv2.flip(b, 1,b)

		gray = cv2.cvtColor(b, cv2.COLOR_RGB2GRAY)
		gray = cv2.equalizeHist(gray)
		rects = detect(gray)
		
		vis = b.copy()
		draw_rects(vis, rects, (255, 255, 255))
		
		
		#cv2.imshow('faces', vis)
		cv2.waitKey(60)
		