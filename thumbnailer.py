'''
* Copyright (c) 2013 Jeremy Parks. All rights reserved.
*
* Permission is hereby granted, free of charge, to any person obtaining a
* copy of this software and associated documentation files (the "Software"),
* to deal in the Software without restriction, including without limitation
* the rights to use, copy, modify, merge, publish, distribute, sublicense,
* and/or sell copies of the Software, and to permit persons to whom the
* Software is furnished to do so, subject to the following conditions:
*
* The above copyright notice and this permission notice shall be included in
* all copies or substantial portions of the Software.
*
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
* IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
* FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
* AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
* LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
* FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
* DEALINGS IN THE SOFTWARE.

Author: xanthic42
Date Created: 25/08/2012
Purpose: To create a thumbnail preview of a video file
'''

import os, subprocess
from PIL import Image

def makeSS(path,filename,num):

	theFile = os.path.join(path,filename)
	
	# Get information about the video file
	cmnd = ['ffprobe',theFile]
	out, out2 = subprocess.Popen(cmnd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
	
	# Create the labels for our video
	size = subprocess.Popen(['du',theFile], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
	bytesize = float(size[0].split('\t')[0])
	actualsize = ""
	if bytesize > 1024: # Larger than 1Mb?
		if bytesize > 1048576: # Larger than 1 GB?
			actualsize = ("%.2fGB" % (bytesize/1048576))
		else:
			actualsize = ("%.2fMB" % (bytesize/1024))
	else:
		actualsize = str(bytesize)
	
	duration = str(out2.split('Duration:')[1].split(',')[0].strip())
	videostream = out2.split('Video:')
	audiostream = out2.split('Audio:')

	# convert to seconds, used to overlay time in video
	secs = duration.split('.')[0].split(':')
	seconds = (int(secs[0])*60+int(secs[1]))*60+int(secs[2])

	# Properly escape special characters
	theFile = theFile.replace(' ','\ ').replace('(','\(').replace(')','\)').replace("'","\\\'").replace('"','\\\"').replace('&','\&').replace('[','\[').replace(']','\]')
	
	# store our temperary files here
	os.system('mkdir temp'+str(num)+'') 

	# figure out how many thumbnails we are making
	nNails = (seconds/180) + (seconds/180)%2
	if nNails < 10:
		nNails = 10
	elif nNails > 26:
		nNails = 26
			
	# generate our individual thumbnails
	x = 0
	while x < nNails:
		os.system('ffmpegthumbnailer -i '+theFile+' -o temp'+str(num)+'/s'+format(x,'02d')+'.jpg -s400 -t '+str(1+98.9/nNails*x))
		ttime = (seconds*(1+98.9/nNails*x)/100)
		h = int(ttime/60/60)
		m = int((ttime-3600*h)/60)
		s = int(ttime-3600*h-60*m)
		tempstr = (("%02d:%02d:%02d") % (h,m,s))
		os.system('convert -pointsize 20 -fill Black -stroke White -strokewidth 2 -draw "text 5,29 \''+tempstr+'\'" \
			-strokewidth 0 -stroke None -draw "text 5,29 \''+tempstr+'\'" \'temp'+str(num)+'/s'+format(x,'02d')+'.jpg\' \'temp'+str(num)+'/s'+format(x,'02d')+'.jpg\'')
		x +=1

	# Get the 'y' size of one of our previews so that the final thumbnail image scales nicely
	im = Image.open('temp'+str(num)+'/s00.jpg')
	# Generate our montage of thumbnails
	os.system('montage +frame +shadow +label -tile 2x'+str(nNails/2)+' -geometry 400x'+str(im.size[1])+'+1+1 -background black temp'+str(num)+'/*.jpg temp'+str(num)+'/0.jpg')

	# Generate a white image and attach it to the top of our montage
	os.system('convert -size 800x'+str(55+(len(videostream)+len(audiostream)-2)*15)+' xc:white temp'+str(num)+'/e1.jpg')
	os.system('convert -append temp'+str(num)+'/e1.jpg temp'+str(num)+'/0.jpg temp'+str(num)+'/0.jpg')

	# Add file information to our montage
	mystr = 'convert'
	mystr += ' -draw \'text 5,15 "File Name: '+filename.replace("\'","`")+'"\''
	mystr += ' -draw "text 5,30 \'Size: '+actualsize+'\'"'
	mystr += ' -draw "text 5,45 \'Duration: '+duration+'\'"'
	x = 60
	for i in range(1,len(videostream)):
		mystr += ' -draw "text 5,'+str(x)+' \'Video'+str(i)+': '+videostream[i].split('\n')[0].strip()+'\'"'
		x += 15
	
	for i in range(1,len(audiostream)):
		mystr += ' -draw "text 5,'+str(x)+' \'Audio'+str(i)+': '+audiostream[i].split('\n')[0].strip()+'\'"'
		x += 15
	mystr += ' temp'+str(num)+'/0.jpg \'thumbs/'+os.path.splitext(filename)[0].replace("\'","`")+'.jpg\''
	os.system(mystr)

	# delete temp dir as it is no longer needed
	os.system('rm -rf temp'+str(num)+'')


##TODO:
# take args for width of each thumbnail
# total number of thumbnails
# thumbnails every x duration or percent
# arrangement of tiles(x*y)
# Take a diractory as input or a specific file.
def main():
	cmnd = ['cat','/etc/mime.types']
	p = subprocess.Popen(cmnd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

	out, out2 = p.communicate()	
	formats = []
	
	# Generate a list of valid video file extensions
	for line in out.split('\n'):
		if line.split('/')[0] == 'video':
			if len(line.split('\t')) > 1:
				for item in line.split('\t')[-1].split(' '):
					formats.append('.'+item)
	
	# store our final files in this directory local to where the script is ran
	os.system('mkdir thumbs') 
	
	# So each execution uses a different temp dir
	num = 0
	for r,d,f in os.walk('/media/virtual/'):
		for files in f:
			if os.path.splitext(files)[1] in formats:
				print files
				##TODO: Figure out why ffmpegthumbnailer fails on some files and remove this
				#       hack to skip over files that fail, but will also suppress other errors.
				try:
					makeSS(r,files, num)
				except:
					print "Failed on", files
				num += 1

if __name__=='__main__':
	main()
