#!/usr/bin/python
import time
import os
import sys
import subprocess
time.sleep(140)
subprocess.call("/home/pi/button.sh >> /home/pi/logButton.txt")
