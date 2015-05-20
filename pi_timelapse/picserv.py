# The MIT License (MIT)
# 
# Copyright (c) 2015 Erik Ekedahl
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

import io
import socket
import struct
from PIL import Image
import time
import datetime
import os

PIC_PATH = "/Users/erikekedahl/Pictures/airplane"

# Start a socket listening for connections on 0.0.0.0:8000 (0.0.0.0 means
# all interfaces)
server_socket = socket.socket()
server_socket.bind(('0.0.0.0', 8000))
#server_socket.settimeout(10.0)
server_socket.listen(0)



img_count = 0

while True:
    # Accept a single connection and make a file-like object out of it
    connection = server_socket.accept()[0].makefile('rb')
    
    date_obj = datetime.date.today()
    tmp_pic_dir = "%s/%s_%s_%s" % (PIC_PATH,date_obj.year,date_obj.month,date_obj.day)
    full_pic_dir = tmp_pic_dir
    part = 1
    while os.path.exists(full_pic_dir):
        part = part + 1
        full_pic_dir = "%s_part_%s" % (tmp_pic_dir,part)
    
    os.mkdir(full_pic_dir)
    if os.path.exists(full_pic_dir) == False:
        print ("Error creating directory!")
    else:
        img_count = 0
        os.chdir(full_pic_dir)
        try:
            print("about to start pic loop")
            while True:
                img_count = img_count + 1
                # Read the length of the image as a 32-bit unsigned int. If the
                # length is zero, quit the loop
                
                image_len = struct.unpack('<L', connection.read(4))[0]
                
                if not image_len:
                  break
                # Construct a stream to hold the image data and read the image
                # data from the connection
                image_stream = io.BytesIO()
                image_stream.write(connection.read(image_len))
                # Rewind the stream, open it as an image with PIL and do some
                # processing on it
                image_stream.seek(0)
                image = Image.open(image_stream)
                
                image.save( "img{0:05}.jpg".format( img_count ) )
                
        finally:
            connection.close()
            print("saved %s images as part of this capture." % img_count)

server_socket.close()
