#!/usr/bin/python

#this file will get values from adc and publish to server. controls 
# pwm difficulty level as well so sends signal to gate driver

# libraries needed for gathering data from pcb and publishing to server
import os
import time
import sys
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import paho.mqtt.client as mqtt
import json
import time
import csv
import subprocess
import pigpio

# information for local server
THINGSBOARD_HOST = '0.0.0.0'
ACCESS_TOKEN = 'GQvSluZPK8UXJHA4NMPv' 
# channels from ADC pins
leftSpeedChannel = 0;
rightSpeedChannel = 1;
leftTorqueChannel = 2;
rightTorqueChannel = 3;
leftVoltage = 5;
rightVoltage = 6;
# communicate adc via spi
mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(0,0))
# initialize some parameters
max_speed = 0
max_torque = 0
gain = 0;
torqueGain = 0;
calories = 0
distance = 0
tau = 6.28
timer = '00:00:00'
level = 0
currentLevel = 0
buttonState = 1
data = []
l_speed = []
r_speed = []
l_torque = []
r_torque = []
# start pi object for gpio control
pi1 = pigpio.pi()
pi1.set_mode(5, pigpio.OUTPUT) # broadcom numbers 5,6 left set 17,27 right
pi1.set_mode(6, pigpio.OUTPUT)
pi1.set_mode(17, pigpio.OUTPUT)
pi1.set_mode(27, pigpio.OUTPUT)
# initial state for level 1
pi1.write(5, 1)
pi1.write(6, 1)
pi1.write(17, 1)
pi1.write(27, 1)

# Data capture and upload interval in seconds. Less interval will eventually hang device
INTERVAL=1
# what the thingsboard server will receive
sensor_data = {'Left Motor Speed': 0, 'Right Motor Speed': 0, 'Left Motor Torque': 0, 'Right Motor Torque': 0,
 'Max Force': 0, 'Max Speed': 0, 'Calories': 0, 'Timer': 0, 'Distance': 0, 'Max Torque': 0,
 'Left Motor Speed G.': 0, 'Right Motor Speed G.': 0, 'Left Motor Torque G.': 0, 'Right Motor Torque G.': 0, 'Level': 1}

next_reading = time.time() 

client = mqtt.Client()

# Set access token
client.username_pw_set(ACCESS_TOKEN)


# Connect to ThingsBoard using default MQTT port and 60 seconds keepalive interval
client.connect(THINGSBOARD_HOST, 1883, 60)

client.loop_start()

try:
    while True:
        
        try: # read wheel size. set to 27 in case file happens to not exist or is rewritten
                with open('/var/www/html/size.txt') as csvfile:
                        readCSV = csv.reader(csvfile, delimiter=',')
                        wheelSize = map(float, next(readCSV))
                wheelSize = wheelSize[0]
        except:
                wheelSize = 27    
        
        try: # read unit. If file is removed and resaved just set to imperial temporarly
                with open('/var/www/html/units.txt') as csvfile:
                        readCSV = csv.reader(csvfile, delimiter=',')
                        unitType = map(float, next(readCSV))
                unitType = unitType[0]
        except:
                unitType = 0
                
        try: # read current level. File is rewritten when control knob used. set lvl1 as default in case of error
                with open('/var/www/html/level.txt') as csvfile:
                        readCSV = csv.reader(csvfile, delimiter=',')
                        currentLevel = map(float, next(readCSV))
                currentLevel = currentLevel[0]
        except:
                currentLevel = 1
                
        if (currentLevel != level): # if level from file does not match program state
                if (currentLevel == 1):
                        pi1.hardware_PWM(18, 100000, 0*10000) # set pwm channel to correct duty cycle
                        pi1.write(5, 1)
                        pi1.write(6, 1)
                        pi1.write(17, 1) # set all mosfets on to get 1/6 gain i.e. 30V max
                        pi1.write(27, 1)
                        gain = 6
                        torqueGain = 0.1
                if (currentLevel == 2):
                        pi1.hardware_PWM(18, 100000, 75*10000) # pin 18 is PWM0 or physical pin 12
                        pi1.write(5, 1)
                        pi1.write(6, 0) #set gain to 1/3 to get 15V max (0,1,0,1)
                        pi1.write(17, 1)
                        pi1.write(27, 0)
                        gain = 2
                        torqueGain = 1
                if (currentLevel == 3):
                        pi1.hardware_PWM(18, 100000, 80*10000) # freq is set to 100kHz to prevent motor whine
                        pi1.write(5, 1)
                        pi1.write(6, 0) # set gain to 1/2 to get 10V max
                        pi1.write(17, 1)
                        pi1.write(27, 0)
                        gain = 2
                        torqueGain = 5
                if (currentLevel == 4):
                        pi1.hardware_PWM(18, 100000, 85*10000) # 88 is duty cycle here
                        pi1.write(5, 1)
                        pi1.write(6, 0) # set gain to 1/2 to get 10V max (1,0,1,0)
                        pi1.write(17, 1)
                        pi1.write(27, 0)
                        gain = 2
                        torqueGain = 5
                if (currentLevel == 5):
                        pi1.hardware_PWM(18, 100000, 90*10000)
                        pi1.write(5, 1)
                        pi1.write(6, 0) # mosfets off to get full motor voltage
                        pi1.write(17, 1)
                        pi1.write(27, 0)
                        gain = 2
                        torqueGain = 5
                if (currentLevel == 6):
                        pi1.hardware_PWM(18, 100000, 100*10000) 
                        pi1.write(5, 0)
                        pi1.write(6, 0) # 5v max
                        pi1.write(17, 0)
                        pi1.write(27, 0)
                        gain = 1
                        torqueGain = 1
                level = currentLevel

        #speed1 = mcp.read_adc(leftSpeedChannel) #tachs are turned off via jumper pin so not needed for now
        #speed2 = mcp.read_adc(rightSpeedChannel) # speed currently replaced by back emf value
        torque1 = mcp.read_adc(leftTorqueChannel) # read adc value for currents
        torque2 = mcp.read_adc(rightTorqueChannel)
        speed1 = mcp.read_adc(leftVoltage) # read motor voltage
        speed2 = mcp.read_adc(rightVoltage)
        
        # perform necessary conversions from raw numerical value
        speed1 = float(speed1)*5/1023;
        speed2 = float(speed2)*5/1023;
        torque1 = float(torque1)*5/1023;
        torque2 = float(torque2)*5/1023;
        #speed1 = speed1/(5.0*80000.0*0.1e-6); tach speed conversions to get frequency from voltage value (Hz)
        #speed2 = speed2/(5.0*80000.0*0.1e-6);
        speed1 = speed1*gain*10 # get rad/s value from voltage
        speed2 = speed2*gain*10 # EMF = Ke*w therefore w=10*EMF
        
        # start counting calories
        #if (speed1>1.34 and torque1>0.47) or (speed2>1.34 and torque2>0.47):
        calories = calories + ((torque1*speed1*INTERVAL*0.5*(1/tau) + torque2*speed2*INTERVAL*0.5*(1/tau))/41.84)*2
        #elif (speed1>1.34 and torque1<0.47) or (speed2>1.34 and torque2<0.47):
        calories = calories + ((1*speed1*INTERVAL*0.5*(1/tau) + 1*speed2*INTERVAL*0.5*(1/tau))/41.84)*2
        
        #speed1 = speed1*0.0746*1.5; tach conversions to go from Hz to mph
        #speed2 = speed2*0.0746*1.5;
        
        speed1 = speed1*0.025*3.6*0.62; # convert rad/s to m/s to kph to mph
        speed2 = speed2*0.025*3.6*0.62; # convert rad/s to m/s to kph to mph
        torque1 = torque1*0.96*1.2; # convert Nm to lbf in. mostly the same
        torque2 = torque2*0.96*1.2;
        
        # noise filtering
        if speed1 <= 0.47 and speed2<= 0.47:
                speed1 = 0
                speed2 = 0;       
        if torque1 <= 0.47 and torque2<= 0.47:
                torque1 = 0
                torque2 = 0;
                
        torque1 = 0.05*torque1*(wheelSize) # scale torque depending on wheelsize
        torque2 = 0.05*torque2*(wheelSize) # 0.05 is to scale the inch number
        
        if (level >=1 and level <= 5):
                try:
                        torque1 = 0.33*speed1*torqueGain
                except:
                        torque1=0
                try:
                        torque2 = 0.33*speed2*torqueGain
                except:
                        torque2=0
        else:
                try:
                       speed1 = 0.1*torque1
                except:
                        speed1=0
                try:
                        speed2 = 0.1*torque2
                except:
                        speed2=0
        #if (torque1>= 6.3 or torque2 >= 6.3):
           #     torque1=0
            #    torque2=0
        
        # save max states if current values beat best values
        if speed1 > max_speed:
                max_speed = speed1
        if speed2 > max_speed:
                max_speed = speed2
        if torque1 > max_torque:
                max_torque = torque1
        if torque2 > max_torque:
                max_torque = torque2
        # record distance. combination of both rollers independent.
        # scale factor for reasonable values
        distance = distance + (speed1 + speed2)*0.00036;
             
        try: # get button state of whether or not to record data
                state = subprocess.check_output(['tail', '-1', '/home/pi/log'])
        except:
                state = "0\n";
                
        if (state == "0\n"): # for imperial values
                t0 = time.time() # start timer
                if (buttonState == 1 ):
                        data.append(l_speed) # append variables to list to be saved
                        data.append(r_speed)
                        data.append(l_torque)
                        data.append(r_torque)
                        if (unitType == 0):
                                data.append([round(calories,1)])
                                data.append([round(max_speed,1)])
                                data.append([round(max_torque,1)])
                                data.append([round(max_torque*6.56,1)])
                                data.append([round(distance,1)])
                        if (unitType == 1):
                                data.append([round(calories,1)])
                                data.append([round(max_speed*1.6,1)])
                                data.append([round(max_torque*11.3,1)])
                                data.append([round(max_torque*6.56*11.3,1)])
                                data.append([round(distance*1.6,1)])                                
                         # save results to csv file       
                        with open("/home/pi/results.csv", "wb") as f:
                                writer = csv.writer(f)
                                writer.writerows(data)
                        timer = '00:00:00' # reset timer and stat information
                        max_speed = 0
                        max_torque = 0
                        calories = 0
                        distance = 0
                        subprocess.call("/home/pi/plot.sh") # generate graphs and data
                        buttonState = -buttonState
                        
                        
        if (state == "1\n"): # do this once timing complete
                t1 = time.time() # end time
                total = round(t1-t0)
                timer = time.strftime('%H:%M:%S', time.gmtime(total))
                if (unitType == 0):
                        l_speed.extend([round(speed1,1)])
                        r_speed.extend([round(speed2,1)])
                        l_torque.extend([round(torque1,1)])
                        r_torque.extend([round(torque2,1)])
                if (unitType == 1):
                        l_speed.extend([round(speed1/0.62,1)])
                        r_speed.extend([round(speed2/0.62,1)])
                        l_torque.extend([round(torque1*11.3,1)])
                        r_torque.extend([round(torque2*11.3,1)])
                   # save values to list     
                if buttonState == -1:
                        data = []
                        l_speed = []
                        r_speed = [] # reset data
                        l_torque = []
                        r_torque = []
                        buttonState = -buttonState
                        calories = 0
                        max_torque = 0
                        max_speed = 0
                        distance = 0
                       
        #print(speed1) # display in terminal
        #print(u"Left Motor Speed: {:g}\u00b0C, Right Motor Speed: {:g}%".format(speed1, speed2)
        if (unitType == 0): # save variables to json format
                sensor_data['Left Motor Speed'] = str(round(speed1, 1))+' mph'
                sensor_data['Right Motor Speed'] = str(round(speed2, 1))+' mph'
                sensor_data['Left Motor Torque'] = str(round(torque1, 1))+' lbf-in'
                sensor_data['Right Motor Torque'] = str(round(torque2, 1))+'  lbf-in'
                sensor_data['Left Motor Speed G.'] = speed1
                sensor_data['Right Motor Speed G.'] = speed2
                sensor_data['Left Motor Torque G.'] = torque1
                sensor_data['Right Motor Torque G.'] = torque2
                sensor_data['Max Force'] = str(round(max_torque*6.56, 1))+' lbf'
                sensor_data['Max Speed'] = str(round(max_speed, 1))+' mph'
                sensor_data['Calories'] = str(round(calories, 1))+' Cal'
                sensor_data['Timer'] = timer
                sensor_data['Distance'] = str(round(distance, 1))+' miles'
                sensor_data['Max Torque'] = str(round(max_torque, 1))+' lbf-in'
                sensor_data['Level'] = level
                
        if (unitType == 1): # imperial data
                sensor_data['Left Motor Speed'] = str(round(speed1/0.62, 1))+' kph'
                sensor_data['Right Motor Speed'] = str(round(speed2/0.62, 1))+' kph'
                sensor_data['Left Motor Torque'] = str(round(torque1*11.3, 1))+' N-cm'
                sensor_data['Right Motor Torque'] = str(round(torque2*11.3, 1))+'  N-cm'
                sensor_data['Left Motor Speed G.'] = speed1*1.6
                sensor_data['Right Motor Speed G.'] = speed2*1.6
                sensor_data['Left Motor Torque G.'] = torque1*11.3
                sensor_data['Right Motor Torque G.'] = torque2*11.3
                sensor_data['Max Force'] = str(round(max_torque*6.56*11.3, 1))+' N'
                sensor_data['Max Speed'] = str(round(max_speed*1.6, 1))+' kph'
                sensor_data['Calories'] = str(round(calories, 1))+' kCal'
                sensor_data['Timer'] = timer
                sensor_data['Distance'] = str(round(distance*1.6, 1))+' km'
                sensor_data['Max Torque'] = str(round(max_torque*11.3, 1))+' N-cm'
                sensor_data['Level'] = level

        # Sending humidity and temperature data to ThingsBoard
        client.publish('v1/devices/me/telemetry', json.dumps(sensor_data), 1)

        next_reading += INTERVAL
        sleep_time = next_reading-time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
except KeyboardInterrupt:
    pass

client.loop_stop()
client.disconnect()
