#!/usr/bin/env python
# encoding: utf-8

"""
imgscraper.py - download an imgur album (top X images)

provides a cli tool to download images from an imgur album

GPL2 License
Copyright Erik Ekedahl <erik@trouserenthusiast.com>
"""

import urllib.request
import re
import sys
import os

usage_msg = '''
Download the images from an imgur.com album/directory

Format:
$ python imgscraper.py [album URL] [destination folder]

Example:
$ python imgscraper.py /r/bigcatgifs bigkitties

NOTE: the url of 'http://imgur.com' is assumed so you don't need to imput it.

If the destination folder is ommitted the album/directory name will be used.
(for example if /r/bigcatgifs is used a folder bigcatgifs will be created
in the current working directory).
'''

class ImgurScraper:
  
  def scrape(self,albumUrl):
    self.albumUrl = albumUrl

    response = urllib.request.urlopen('http://imgur.com/' + self.albumUrl)

    if response.getcode() != 200:
      raise Exception("Error reading imgur, error code %d" % response.getcode())

    html = response.read()

    page = html.decode(response.info().get_param('charset','utf8'))

    self.imgList = re.findall('<a class="image-list-link" href="' + self.albumUrl + '\/([\w\d]+)"',page)

  def imgCount(self):
    return len(self.imgList)
    


  def downloadImages(self,destinationFolder):
    if not os.path.exists(destinationFolder):
      os.makedirs(destinationFolder)

    for image in self.imgList:
      imageUrl = "http://i.imgur.com/%s" % (image)
      print("Now getting: " + imageUrl + "\n")

      extList = ('.gif','.gifv','.mp4','.png','.jpg','.jpeg')
      
      
      for ext in extList:
        try:
          # Attempt getting the file
          imgRes = urllib.request.urlopen(imageUrl + ext)

          if imgRes.getcode() == 200:
            with open("%s/%s%s" % (destinationFolder,image,ext), 'wb') as f:
              f.write(imgRes.read())
              f.flush()
              f.close()
            break
        except:
          print("image not found in format " + ext)
        
if __name__ == '__main__':
  args = sys.argv

  if len(args) == 1:
    # print out the usage message and exit:
    print(usage_msg)
    exit()

  try:
    # start the class
    scraper = ImgurScraper()
    if len(args) == 3:
      albumFolder = args[2]
    else:
      # attempt to use the album/directory name for the folder
      albumFolder = re.match("\/r\/(\w+)",args[1]).groups()[0]
    
    # scrape the album page for all the image links.
    scraper.scrape(args[1])

    if scraper.imgCount() > 0:
      scraper.downloadImages(albumFolder)
    else:
      print("No images in the album, sorry.")
  
  except Exception as ex:
    print("Issue running scraper:")
    print(ex.args)
    print(ex)

