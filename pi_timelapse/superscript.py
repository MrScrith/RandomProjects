# The MIT License (MIT)
#
# Copyright (c) 2015 Erik
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import RPi.GPIO as GPIO
import time
import os
import datetime
import picamera
import io
import socket
import struct

SHUTDOWN = 5
SWITCH   = 7
RED      = 11
GREEN    = 13
BLUE     = 15

LIGHT_ON  = 1
LIGHT_OFF = 0

# 720p
WIDTH  = 1280
HEIGHT = 720

# 1080p
#WIDTH  = 1920
#HEIGHT = 1080
NETWORK_PATH = "eriks_macbook_pro.local"
PIC_PATH = "/media/picdrv/pics"

TIMELAPSE_INTERVAL = 3

def setup():
  GPIO.setmode(GPIO.BOARD)
  GPIO.setwarnings(False)
  # setup the input
  GPIO.setup(SWITCH,GPIO.IN,GPIO.PUD_UP)
  GPIO.setup(SHUTDOWN,GPIO.IN)
  # setup the output
  GPIO.setup(RED,GPIO.OUT)
  GPIO.setup(GREEN,GPIO.OUT)
  GPIO.setup(BLUE,GPIO.OUT)
  cleanup()

def shutdown():
  cleanup()
  GPIO.cleanup()

def cleanup():
  GPIO.output(RED,LIGHT_OFF)
  GPIO.output(GREEN,LIGHT_OFF)
  GPIO.output(BLUE,LIGHT_OFF)

def tl_to_network(client_socket):
  # make a file object out of the socket to make it easier to interact with it
  conn = client_socket.makefile('wb')
  try:
    with picamera.PiCamera() as cam:
      # set green light on so we know we are all good
      GPIO.output(GREEN,LIGHT_ON)

      # set camera attributes
      cam.resolution = (WIDTH,HEIGHT) # set the resolution for the images
      cam.vflip = True # Flip the image
      cam.hflip = True # Not mirror the image
      # allow the camera to stabalize
      time.sleep(2)

      stream = io.BytesIO()
      for f in cam.capture_continuous(stream, 'jpeg'):
        # Write the length of the stream to the connection and flush it to make sure it sends
        conn.write(struct.pack('<L',stream.tell()))
        conn.flush()
        # rewind the stream and send
        stream.seek(0)
        conn.write(stream.read())
        if GPIO.input(SWITCH) == True:
          break
        time.sleep(TIMELAPSE_INTERVAL)
        stream.seek(0)
        stream.truncate()
    
    conn.write(struct.pack('<L',0))
  finally:
    conn.close()
    client_socket.close()



def tl_to_drive():
  date_obj = datetime.date.today()
  tmp_pic_dir = "%s/%s_%s_%s" % (PIC_PATH,date_obj.year,date_obj.month,date_obj.day)
  full_pic_dir = tmp_pic_dir
  part = 1
  while os.path.exists(full_pic_dir) == True:
    # Make sure I haven't already started a directory, and if so start a "part_N" directory
    part = part + 1
    full_pic_dir = "%s_part_%s" % (tmp_pic_dir,part)
  
  # Path should be unique, create it and change current dir to this path
  os.mkdir(full_pic_dir)
  if os.path.exists(full_pic_dir) == False:
    print("ERROR")
    GPIO.output(RED,LIGHT_ON)
  else:
    # Set current directory (where the pics will be stored)
    os.chdir(full_pic_dir)
    
    with picamera.PiCamera() as cam:
      # Set the blue light on so we know we are all good
      GPIO.output(BLUE,LIGHT_ON)

      # set camera attributes
      cam.resolution = (WIDTH,HEIGHT) # set the resolution
      cam.vflip = True # flip the image
      # allow the camera to stabalize
      time.sleep(2)
      # Keep taking pics until the switch is turned off
      start = int(time.clock() * 100)
      for filename in cam.capture_continuous('img_{counter:05d}.jpg'):
        end = int(time.clock() * 100)
        print("capture took %s for %s " % (end-start,filename))
        if GPIO.input(SWITCH) == True:
          break
        time.sleep(TIMELAPSE_INTERVAL)
        start = int(time.clock() * 100)

def wait_and_see():
  while GPIO.input(SHUTDOWN) == True:
    if GPIO.input(SWITCH) == False:
      # Switch turned on
      if os.path.exists(PIC_PATH):
        # drive exists, save to there.
        tl_to_drive()
      else:
        # Create the socket
        tsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:        
          tsock.connect(("10.0.1.13",8000))
          tl_to_network(tsock)
        except:
          # exception, nothing works, illuminate red light
          GPIO.output(RED,LIGHT_ON)
        finally:
          tsock.close()
    else:
      cleanup()
    time.sleep(5)

if __name__ == "__main__":
  setup()
  wait_and_see()
  cleanup()
  shutdown()
  os.system("shutdown now -h")
