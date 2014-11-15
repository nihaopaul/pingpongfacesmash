#!/usr/bin/python -OO

import cv2

import numpy as np
import sys

''' this one will fuck you up! it's actually pillow and not pil, 
	make sure you dont have PIL installed, 
	if you do, trash it and install pillow '''
from PIL import Image

import array

from geventwebsocket.handler import WebSocketHandler
from gevent import pywsgi
import gevent

import io

import time
import threading
import hashlib
import re



#VIDEO_FORMAT = cv2.FOURCC('I', 'Y', 'U', 'V')
#FACE_FILE = "faces.mdl"

exitapp = False

class Cam:
	'class for camera operations so we can reuse it multiple times'
	width = 0
	height = 0
	def __init__(self, id):
		self.id = id
		self.camera = cv2.VideoCapture(id)



		if not self.camera.isOpened():
			print("Error initializing Capture: " + str(id))
			sys.exit(1)



		self.capture()



	def capture(self):
		self.rval,self.image = self.camera.read() 
		

		if not self.rval:
			print("cannot read camera")
			sys.exit(1)
		else:
			cv2.flip(self.image, 1,self.image)
			cv2.cvtColor(self.image,cv2.COLOR_XYZ2BGR,self.image)

			return self.image





def handle_echo_client(ws):
	'''this is the call that makes the call to the camera for a frame, returns when dead, it's blocking!'''
	global abe

	while True:
		msg = ws.receive()
		if msg:
			imghash, mbuffer = abe.list()
			ws.send(mbuffer, True)


		else:
			'''if no message then it's a dead socket and should just exit.. stupid problem'''
			break

		


def app(environ, start_response):

	if environ['PATH_INFO'] == "/video":

		handle_echo_client(environ['wsgi.websocket'])
	else:
		headers = [('Content-Type', 'text/html')]
		page = open('face.html', 'r').read()
		start_response("200", headers)

		#print("404, PATH_INFO: %s" %  environ["PATH_INFO"])
		#start_response("404 Not Found", [])
		
		p = re.compile( '(__ADDRESS__)')
		page = p.sub(environ['HTTP_HOST'], page)

		return page
		#return []

class abeAck(threading.Thread):
	''' OpenCV stuff '''
	def __init__(self, threadID, name, counter):
		''' this launches a thread so we're not blocking the server code '''
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.counter = counter

		print "setup Abe"
		self.cam = Cam(0)

		self.img, self.label = [], []
		self.id = 0
		self.model = cv2.createFisherFaceRecognizer()


	def list(self):
		''' this should return an array of binary images in json form, 
			but i just send one back :D because i'm lazy to write the client 
			side code for this and track clients '''
		result = []
		imghash = False


		if len(self.img):
			thisArray = self.img[-1]
			img = Image.fromarray(thisArray)

			output = io.BytesIO()
			img.save(output, format='JPEG')

			imghash = hashlib.sha1(output.getvalue()).hexdigest()

			result = output.getvalue()


		return imghash, result


	def run(self):
		print "running Abe"

		while not exitapp:

			img1 = self.cam.capture()
			abed = self.predict(img1)



		


	def detect(self,img, cascade):
		gray = self.to_grayscale(img)
		rects = cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=4, minSize=(30, 30))
		if len(rects) == 0:
			return []
		return rects

	def detect_faces(self,img):
		cascade = cv2.CascadeClassifier("haarcascades/haarcascade_frontalface_alt.xml")
		return self.detect(img, cascade)

	def to_grayscale(self,img):
		gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
		gray = cv2.equalizeHist(gray)
		return gray

	def contains_face(self,img):
		return len(self.detect_faces(img)) > 0
	  
	def crop_faces(self, img, faces):
		for face in faces:
			x, y, h, w = [result for result in face]
	    	return img[y:y+h,x:x+w]

	def train(self):
		self.model.train(self.img,np.asarray(self.label))
		#self.model.save(FACE_FILE) 	#dont save the model to disk

	def predict(self,cv_image):
		''' limit is what max data will we store in the training model, 
			if this is too large the model will not pick out too many new faces, 
			if it's too low we'll get too many positive hits, 10-20 is efficient as we might have 6 hits per face '''
		faces = self.detect_faces(cv_image)
		limit = 20

		''' we'll use this just for buffer to start up '''
		if len(faces) > 0 and len(self.img) <= limit:
			cropped = self.crop_faces(cv_image, faces)
			grayscale = self.to_grayscale(cropped)
			resized = cv2.resize(grayscale, (100,100))

			self.img.append(resized)
			self.label.append(self.id)
			self.id +=1

		if len(faces) > 0 and len(self.img) == limit:
			self.train()

		if len(faces) > 0 and len(self.img) > limit:

			cropped = self.crop_faces(cv_image, faces)
			grayscale = self.to_grayscale(cropped)
			resized = cv2.resize(grayscale, (100,100))

			prediction = self.model.predict(resized)
			''' if we're not sure, lets snap a photo of them and add them to the record, 
				and perhaps retrain at this stage, the 2800 is very optimistic that we have a new face, 
				predicitions on heads lower than this will result in duplicates, 
				but we can use this to train against, its up to you '''

			if (prediction[1] > 2800):
				print(prediction[1])

				if len(self.img) > limit: 
					'''	some clean up as the label needs to be incremental.. 
						a bit silly to call it a label '''
					if self.id > limit:
						self.id = 0


					self.img[self.id] = resized
					self.label[self.id] = self.id
					self.id +=1	
					
				else:
					self.img.append(resized)
					self.label.append(self.id)
					self.id +=1

				self.train()


				return cropped

		return False





if __name__ == '__main__':


	'''start up all the threads we need'''
	abe = abeAck(1, "Abe", 1)
	abe.start()


	while True:
		'do nothin!'
 		try:
			server = pywsgi.WSGIServer(('', 9000), app, handler_class=WebSocketHandler)
			server.serve_forever()
		except KeyboardInterrupt:
			exitapp = True
			raise



