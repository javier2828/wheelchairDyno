#!/usr/bin/python

# librariers needed to plot recorded data
import csv
import matplotlib.pyplot as plt
import numpy as np
#from scipy import integrate
from scipy.optimize import curve_fit
from PIL import Image, ImageDraw, ImageFont
import time
from datetime import date
import os
import random
# initialize string names
INTERVAL = 1
torqueString = '(lbf-in)'
forceString = '(lbf)'
speedString = '(mph)'
distanceString = '(miles)'
caloricString = '(Cal)'
wheelString = '(in)'
#----------opne file----------------------------
with open('/home/pi/results.csv') as csvfile:
    readCSV = csv.reader(csvfile, delimiter=',')
    speed1 = list(map(float, next(readCSV)))
    speed2 = list(map(float, next(readCSV))) # import variable data
    torque1 = list(map(float, next(readCSV)))
    torque2 = list(map(float, next(readCSV)))
    calories = list(map(float, next(readCSV)))
    max_speed = list(map(float, next(readCSV)))
    max_torque = list(map(float, next(readCSV)))
    max_force = list(map(float, next(readCSV)))
    distance = list(map(float, next(readCSV)))
with open('/var/www/html/size.txt') as txtfile: # get wheel size
    readTXT = csv.reader(txtfile, delimiter=',')
    size = next(readTXT)
    size = size[0]
with open('/var/www/html/units.txt') as txtfile: # get current unit
    readTXT = csv.reader(txtfile, delimiter=',')
    unitType = next(readTXT)
with open('/var/www/html/session.txt') as txtfile: # get session id
    readTXT = csv.reader(txtfile, delimiter=',')
    sessionID = next(readTXT)
    sessionID = sessionID[0]
#---------------computations----------------------------------
if (unitType[0] == 1): # set strings based on unit type. for image file
    torqueString = '(N-cm)'
    forceString = '(N)'
    speedString = '(kph)'
    distanceString = '(km)'
    caloricString = '(kCal)'
    wheelString = '(cm)'
    size = round(float(size)*2.54,1)
    
if (unitType[0] == 0):
    torqueString = '(lbf-in)'
    forceString = '(lbf)'
    speedString = '(mph)'
    distanceString = '(miles)'
    caloricString = '(Cal)'
    wheelString = '(in)'


def func(x, b): # assumed model for force versus speed graph. exponential in nature
    return max_force[0] * np.exp(-b * x)
    
# carry out info to get derived info
avgSpeed = np.array(speed1)*0.5 + np.array(speed2)*0.5
avgTorque = np.array(torque1)*0.5 + np.array(torque2)*0.5
timeArray = np.arange(0,len(speed1),INTERVAL)
distanceArray = 0.00036*2*np.cumsum(avgSpeed)
forceArray1 = 6.56*np.array(torque1)
forceArray2 = 6.56*np.array(torque2)
avgForce = np.array(forceArray1)*0.5 + np.array(forceArray2)*0.5
totalTime = time.strftime('%H:%M:%S', time.gmtime(len(speed1)))
# exit if no actual nonzero data is recorded
if (max_torque[0] == 0 or max_speed[0] == 0):
    exit()

# pi does not have Real time clock so day info is not correct. buy RTC for PI
#----------create directory-------------------
newPath = '/var/www/html/data/session'+sessionID
os.makedirs(newPath)
# infer parameters of model from data using Least Squares
popt = curve_fit(func, speed2, forceArray2)
speedArray = np.arange(0, max_speed[0], 0.1)
#-------------figures-----------------------------------
plt.figure(1)
plt.plot(timeArray, speed1, label = "Left Motor")
plt.plot(timeArray, speed2, label = "Right Motor")
plt.xlabel('Time (s)')
plt.ylabel('Speed '+speedString)
plt.title('Speed vs Time')
plt.legend()
plt.savefig(newPath+'/speed_graph.png', dpi=300)

plt.figure(2)
plt.plot(timeArray, torque2, label = "Right Motor")
plt.plot(timeArray, torque1, label = "Left Motor")
plt.xlabel('Time (s)')
plt.ylabel('Torque '+torqueString)
plt.title('Torque vs Time')
plt.legend()
plt.savefig(newPath+'/torque_graph.png', dpi=300)

plt.figure(3)
plt.plot(timeArray, distanceArray, label = "Distance")
plt.xlabel('Time (s)')
plt.ylabel('Distance '+distanceString)
plt.title('Distance vs Time')
plt.legend()
plt.savefig(newPath+'/distance_graph.png', dpi=300)

plt.figure(4)
plt.plot(speedArray, func(speedArray, popt[0]))
plt.xlabel('Speed '+speedString)
plt.ylabel('Force '+forceString)
plt.title('Force vs Speed')
plt.savefig(newPath+'/force_graph.png', dpi=300)
#------------result image-------------------------------
image = Image.open('/home/pi/background.png')
draw = ImageDraw.Draw(image)
title = ImageFont.truetype('/home/pi/Roboto-Medium.ttf', size=50)
normal = ImageFont.truetype('/home/pi/Roboto-Medium.ttf', size=25)
color = 'rgb(255, 255, 255)' # black color
draw.text((200, 50), "Workout Session", fill=color, font=title)
draw.text((100, 150), 'Session ID: '+sessionID, fill=color, font=normal)
draw.text((100, 200), 'Duration: '+totalTime, fill=color, font=normal)
draw.text((100, 250), 'Calories '+caloricString+': '+str(calories[0]), fill=color, font=normal)
draw.text((100, 300), 'Distance '+distanceString+': '+str(distance[0]), fill=color, font=normal)
draw.text((100, 350), 'Wheel Size '+wheelString+': '+str(size), fill=color, font=normal)
draw.text((400, 150), 'Max Speed '+speedString+': '+str(max_speed[0]), fill=color, font=normal)
draw.text((400, 200), 'Max Torque '+torqueString+': '+str(max_torque[0]), fill=color, font=normal)
draw.text((400, 250), 'Max Force '+forceString+': '+str(max_force[0]), fill=color, font=normal)
draw.text((400, 300), 'Average Speed '+speedString+': '+str(round(np.mean(avgSpeed),1)), fill=color, font=normal)
draw.text((400, 350), 'Average Torque '+torqueString+': '+str(round(np.mean(avgTorque),1)), fill=color, font=normal)
draw.text((400, 400), 'Average Force '+forceString+': '+str(round(np.mean(avgForce),1)), fill=color, font=normal)
image.save(newPath+'/session_overview.png')

sessionID = float(sessionID)+1
with open('/var/www/html/session.txt', 'w') as f:
    f.write('%d' % sessionID)

#plt.show()
