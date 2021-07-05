#Import libraries
from scipy.spatial import distance as dist
from imutils.video import VideoStream
from imutils import face_utils
import winrt.windows.devices.geolocation as wdg, asyncio
import numpy as np
import argparse
import imutils
import time
import sys
import os
import smtplib
import subprocess
import dlib
import cv2
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime


#To get the current location of the system
async def getCoords():
    locator = wdg.Geolocator()
    pos = await locator.get_geoposition_async()
    return [pos.coordinate.latitude, pos.coordinate.longitude]
    
def getLoc():
    return asyncio.run(getCoords())


class PassOver(Exception): pass


def call_python_file(vehnum, drivername):
    print('call')
    x = getLoc()
    print("latitude: ", x[0])
    print("logitude: ", x[1])
    locvalue = str(x[0]) + " " + str(x[1])
    
    now = datetime.now()
    now = str(now)
    subject = 'Alert!'
    body = "Hello, Your driver, " + drivername + ", on Vehicle number, " + vehnum +", has been recorded tired at " + now + " IST. The locational coordinates are " + locvalue
    msg = f'Subject: {subject}\n\n{body}'

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login("sabarimathavan24@gmail.com", "Sabari1724!")
    server.sendmail("sabarimathavan24@gmail.com", "sabarimathavan.rb2018@vitstudent.ac.in", msg)
    server.quit()

    datavalue = {'name': drivername, 'vehicle number': vehnum, 'time': now, 'location':locvalue}
    db.collection('record').document(vehnum).set(datavalue)

    subprocess.check_call([sys.executable, "finding_places.py", locvalue])
    raise PassOver


#To detect the opening and closing of eyes
def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])

    C = dist.euclidean(eye[0], eye[3])

    ear = (A + B) / (2.0 * C)

    return ear


#To detect the EAR value
def final_ear(shape):
    (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
    (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

    leftEye = shape[lStart:lEnd]
    rightEye = shape[rStart:rEnd]

    leftEAR = eye_aspect_ratio(leftEye)
    rightEAR = eye_aspect_ratio(rightEye)

    ear = (leftEAR + rightEAR) / 2.0
    return (ear, leftEye, rightEye)


#Main function
print("Welcome!\n")
print("Enter the Vehicle number:")
vehnum = input()
print("Enter your name:")
drivername = input()


cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


ap = argparse.ArgumentParser()
ap.add_argument("-w", "--webcam", type=int, default=0,
                help="index of webcam on system")
args = vars(ap.parse_args())

EYE_AR_THRESH = 0.25
EYE_AR_CONSEC_FRAMES = 30
COUNTER = 0

detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")    #Faster but less accurate
predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')

print("-> Starting Video Stream")
vs = VideoStream(src=args["webcam"]).start()
time.sleep(1.0)


#Drowsiness detection
try: 
    while True:
        frame = vs.read()
        frame = imutils.resize(frame, width=450)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        rects = detector.detectMultiScale(gray, scaleFactor=1.1, 
            minNeighbors=5, minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE)

        for (x, y, w, h) in rects:
            rect = dlib.rectangle(int(x), int(y), int(x + w),int(y + h))
            
            shape = predictor(gray, rect)
            shape = face_utils.shape_to_np(shape)

            eye = final_ear(shape)
            ear = eye[0]
            leftEye = eye [1]
            rightEye = eye[2]


            leftEyeHull = cv2.convexHull(leftEye)
            rightEyeHull = cv2.convexHull(rightEye)
            cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
            cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)

            cv2.putText(frame, "EAR: {:.2f}".format(ear), (300, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            if ear < EYE_AR_THRESH:
                COUNTER += 1
                cv2.putText(frame, "DROWSINESS ALERT!", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                if COUNTER >= EYE_AR_CONSEC_FRAMES:
                    call_python_file(vehnum, drivername)

            else:
                COUNTER = 0
                alarm_status = False



        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

    cv2.destroyAllWindows()
    vs.stop()

except PassOver:
    pass
