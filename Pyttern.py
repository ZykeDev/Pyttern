#!python3

import sys
import math
import random
from random import randint

from PIL import Image
from PIL import ImageFilter

WIDTH = 800
HEIGHT = 800

SPP = 8	#Squares per Pixel

MINBASE = 50
MAXBASE = 255
VARIANCE = 1.5 #Max color variance
DARKNESS = 0.8 #Max darkness

FUZZINESS = 1 #Fuzziness index
SHARPNESS = 2 #Sharpness index

CLOUDSIZE = 12 #Max cloud radius
CLOUD_CHANCE = 0.1 #Chance of a cloud forming


#Darkens a triplet by factor, keeping it within bounds
def darken(baseValues, factor):
	vlist = list()
	for v in baseValues:
		v = round(v * factor)
		if v < MINBASE: v = MINBASE
		if v > MAXBASE: v = MAXBASE
		vlist.append(v)
	return tuple(vlist)


#Calculates similar values based on the distance from the base value
def equalize(baseValues, targetValues, distance):
	baseValues = list(baseValues)
	targetValues = list(targetValues)

	#weight = (distance / CLOUDSIZE * SPP) + 1

	for v in range(len(baseValues)):
		baseValues[v] = round(((baseValues[v]) + targetValues[v]*1.5) / (1+1.5))

	return tuple(baseValues)




#Smoothes the current pixel with the values of the relative top/left pixels + far one
def diagonalPass(color, pixels, i, j):
	topl = pixels[i-1, j-1]
	top = pixels[i, j-1]
	left = pixels[i-1, j]
	far = pixels[i-2, j-2]

	newColor = list()
	for x in range(3):
		newColor.append(round((topl[x]*2 + top[x]*2 + far[x]*2 + left[x] + color[x]) / 8))

	return tuple(newColor)


#Smoothes the current pixel with the (weighted) values of the pixels around
def arealPass(pixels, i, j):
	color = [p for p in pixels[i, j]]

	#Check for edge cases
	if i <= 4 or j <= 4 or i >= WIDTH-5 or j >= HEIGHT-5:
		return tuple(color)
	
	top = pixels[i, j-1]
	topl = pixels[i-1, j-1]
	topr = pixels[i+1, j-1]

	left = pixels[i-1, j]
	right = pixels[i+1, j]

	bot = pixels[i, j+1]
	botl = pixels[i-1, j+1]
	botr = pixels[i+1, j+1]

	farTL = pixels[i-3, j-3]
	farTR = pixels[i+3, j-3]
	farBL = pixels[i-3, j+3]
	farBR = pixels[i+3, j+3]
	
	newColor = list()
	for x in range(3):
		upper = (topl[x] + top[x] + topr[x]) * SHARPNESS
		mid   = (left[x] + right[x]) 		 * SHARPNESS/2
		lower = (botl[x] + bot[x] + botr[x]) * SHARPNESS

		extra  = (farTL[x] + farTR[x] + farBL[x] + farBR[x]) * FUZZINESS
		newColor.append(round((color[x] + upper + mid + lower + extra) / (9 + FUZZINESS * 4 + SHARPNESS * 8)))
	return tuple(newColor)


def formCloud(pixels, i, j):
	#darken pixels in a radius = CLOUDSIZE
	radius = CLOUDSIZE * SPP
	targetColor = pixels[i, j]

	for x in range(i - radius, i + radius, SPP):
		for y in range(j - radius, j + radius, SPP):
			randRadius = randint(round(radius/2), radius) #Randomize the radius
		
			if x >= 0 and y >= 0 and x + CLOUDSIZE <= WIDTH and y + CLOUDSIZE <= HEIGHT:
				distance = math.sqrt(math.pow((x-i), 2) + math.pow((y-j), 2))
			
				if distance <= randRadius:
					
					color = equalize(pixels[x, y], targetColor, distance)				
					for h in range(SPP): #Fill the SPP block
						for k in range(SPP):
							pixels[x+h, y+k] = color
							

	return pixels

	
		







#Creates a random bitmap with diagonal smoothing over a single pass
def diagonalSmooth_SinglePass():
	#Init the image
	img = Image.new('RGB', (WIDTH, HEIGHT), "black")

	print("Building pixels...")

	pixels = img.load() # create the pixel map
	base = (randint(MINBASE, MAXBASE), randint(MINBASE, MAXBASE), randint(MINBASE, MAXBASE))

	for i in range(img.size[0]):
		for j in range(img.size[1]):

			color = tuple([round(b * random.uniform(0.01, VARIANCE)) for b in base])

			factor = abs(math.cos(i + j + random.uniform(0, 5)))
			if factor < DARKNESS : factor = DARKNESS

			if i <= 1 or j <= 1 or i >= img.size[0]-2 or j >= img.size[1]-2:
				pixels[i, j] = darken(color, factor)
			else:
				pixels[i, j] = diagonalPass(darken(color, factor), pixels, i, j)

	img = img.crop((2, 2, WIDTH, HEIGHT))
	print("Image complete")

	return img



#Creates a random bitmap and applies an areal smoothing
def arealSmooth():
	#Init the image
	img = Image.new('RGB', (WIDTH, HEIGHT), "black")

	print("Building pixels...")

	pixels = img.load() # create the pixel map
	base = (randint(MINBASE, MAXBASE), randint(MINBASE, MAXBASE), randint(MINBASE, MAXBASE))
	#base = (60, 60, 200)

	for i in range(img.size[0]):
		for j in range(img.size[1]):

			color = tuple([round(b * random.uniform(0.01, VARIANCE)) for b in base])

			factor = abs(math.cos(i + j + random.uniform(0, 5)))
			if factor < DARKNESS : factor = DARKNESS
			
			pixels[i, j] = darken(color, factor)

	print("Appling Aereal Smoothnig...")
	for i in range(img.size[0]):
		for j in range(img.size[1]):
			pixels[i, j] = arealPass(pixels, i, j)
	
	img = img.crop((5, 5, WIDTH-5, HEIGHT-5))
	print("Image complete")

	return img




#Creates a random bitmap
def darknessSmooth():
	#Init the image
	img = Image.new('RGB', (WIDTH, HEIGHT), "black")

	print("Building pixels...")

	pixels = img.load() # create the pixel map
	base = (randint(MINBASE, MAXBASE), randint(MINBASE, MAXBASE), randint(MINBASE, MAXBASE))

	#Color the pixels in steps of SPP
	for i in range(0, img.size[0], SPP):
		for j in range(0, img.size[1], SPP):
			factor = random.uniform(DARKNESS, 1.1)
			color = base

			for x in range(SPP):
				for y in range(SPP):
					pixels[i+x, j+y] = darken(color, factor)

	print("Image complete")

	return img


#Creates a random bitmap with random clouds
def cloudySmooth():
	#Init the image
	img = Image.new('RGB', (WIDTH, HEIGHT), "black")

	print("Building pixels...")

	pixels = img.load() # create the pixel map
	base = (randint(MINBASE, MAXBASE), randint(MINBASE, MAXBASE), randint(MINBASE, MAXBASE))

	cloudNuclei = []
	chance = round((WIDTH+HEIGHT) * CLOUD_CHANCE)
			
	#Color the pixels in steps of SPP
	for i in range(0, img.size[0], SPP):
		for j in range(0, img.size[1], SPP):

			#Chose random color & darkness factor
			factor = random.uniform(DARKNESS, 1.1)
			color = base

			#Select the cloud nuclei
			isCloudChance = randint(0, chance)

			if isCloudChance == chance:
				cloudNuclei.append((i, j))
				#factor = 1
				#color = (0,0,0)	

			
			color = darken(color, factor)
			for x in range(SPP): #Fill the SPP block
				for y in range(SPP):
					pixels[i+x, j+y] = color

	#First pass for cloud nuclei
	for v in range(0, img.size[0], SPP):
		for u in range(0, img.size[1], SPP):
			if (v, u) in cloudNuclei:
				pixels = formCloud(pixels, v, u)
				#formCloud(pixels, v, u)



	#print(cloudNuclei)

	print("Image complete")

	return img



#img = diagonalSmooth_SinglePass()
#img = arealSmooth()
img = cloudySmooth()



img.save("test.bmp")

