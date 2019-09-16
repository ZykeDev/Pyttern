#!python3

import sys
import time
import math
import random
from random import randint
from enum import Enum
import Colors

from PIL import Image
from PIL import ImageFilter

import pixelsort
# python3 pixelsort.py examples/image.jpg -i edges -t 250

WIDTH = 1600
HEIGHT = 1600

SPP = 8 # Squares per Pixel

MINBASE = 12
MAXBASE = 255
VARIANCE = 1.5 # Max color variance
DARKNESS = 0.2 # Max darkness

FUZZINESS = 1 # Fuzziness index
SHARPNESS = 2 # Sharpness index
SMEAR = 0.7   # Equalization smear index. The higher the less smooth
BLOOM = 1.1   # Equalization bloom index. The lower the more bloom. Suggested value = 1

CLOUDSIZE_MAX = 32 # Max cloud radius
CLOUDSIZE_MIN = 4 # Min cloud radius
CLOUD_CHANCE = 0.04 # Chance of a cloud forming. The lower the more likely
ACCENT_CHANCE = 25 # Chance of a cloud inverting colors (%)

# Image building types
class Type(Enum):
	AREAL = 1
	CLOUDY = 2
	DICHROMATIC = 3
	DIAGONAL = 4

# Darkens a triplet by a factor, keeping it within bounds
def darken(baseValues, factor):
	vlist = list()
	for v in baseValues:
		v = round(v * factor)
		if v < MINBASE: v = MINBASE
		if v > MAXBASE: v = MAXBASE
		vlist.append(v)
	return tuple(vlist)


# Calculates similar values based on the distance from the base value
def equalize(baseValues, targetValues, distance):
	baseValues = list(baseValues)
	targetValues = list(targetValues)

	for v in range(len(baseValues)):
		baseValues[v] = round(((baseValues[v]) + targetValues[v] * SMEAR) / (BLOOM + SMEAR))

	return tuple(baseValues)


# Smoothes the current pixel with the values of the relative top/left pixels + far one
def diagonalColor(color, pixels, i, j):
	topl = pixels[i-1, j-1]
	top = pixels[i, j-1]
	left = pixels[i-1, j]
	far = pixels[i-2, j-2]

	newColor = list()
	for x in range(3):
		newColor.append(round((topl[x]*2 + top[x]*2 + far[x]*2 + left[x] + color[x]) / 8))

	return tuple(newColor)


# Smoothes the current pixel with the weighted values of the pixels around
def weightedColor(pixels, i, j):
	color = [p for p in pixels[i, j]]

	# Check for edge cases
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




# ---------------------------------------------------------------------------- #


# Creates a random bitmap with diagonal smoothing over a single pass
def diagonalSmooth_SinglePass():
	# Init the image
	img = Image.new('RGB', (WIDTH, HEIGHT), "black")

	print("Building pixels...")

	pixels = img.load() # Create the pixel map
	base = (randint(MINBASE, MAXBASE), randint(MINBASE, MAXBASE), randint(MINBASE, MAXBASE))

	for i in range(img.size[0]):
		for j in range(img.size[1]):

			color = tuple([round(b * random.uniform(0.01, VARIANCE)) for b in base])

			factor = abs(math.cos(i + j + random.uniform(0, 5)))
			if factor < DARKNESS : factor = DARKNESS

			if i <= 1 or j <= 1 or i >= img.size[0]-2 or j >= img.size[1]-2:
				pixels[i, j] = darken(color, factor)
			else:
				pixels[i, j] = diagonalColor(darken(color, factor), pixels, i, j)

	img = img.crop((2, 2, WIDTH, HEIGHT))
	print("Image complete")

	return img


# ---------------------------------------------------------------------------- #


# Applies an areal pass
def arealPass(w, h, base, pixels):
	for i in range(w):
		for j in range(h):

			color = tuple([round(b * random.uniform(0.01, VARIANCE)) for b in base])

			factor = abs(math.cos(i + j + random.uniform(0, 5)))
			if factor < DARKNESS : factor = DARKNESS
			
			pixels[i, j] = darken(color, factor)

	return pixels


# Applies an areal smoothing
def arealSmooth(w, h, pixels):
	print("Appling Aereal Smoothing...")
	for i in range(w):
		for j in range(h):
			pixels[i, j] = diagonalColor(pixels, i, j)

	return pixels


# ---------------------------------------------------------------------------- #


# Creates a random bitmap with darkened areas 				TODO Streamline
def darknessSmooth():
	# Init the image
	img = Image.new('RGB', (WIDTH, HEIGHT), "black")

	print("Building pixels...")

	pixels = img.load() # create the pixel map
	base = (randint(MINBASE, MAXBASE), randint(MINBASE, MAXBASE), randint(MINBASE, MAXBASE))

	# Color the pixels in steps of SPP
	for i in range(0, img.size[0], SPP):
		for j in range(0, img.size[1], SPP):
			factor = random.uniform(DARKNESS, 1.1)
			color = base

			for x in range(SPP):
				for y in range(SPP):
					pixels[i+x, j+y] = darken(color, factor)

	print("Image complete")

	return img


# ---------------------------------------------------------------------------- #


# Applies a cloudy pass
def cloudyPass(w, h, base, pixels, passes):
	cloudNuclei = []
	chance = round((WIDTH+HEIGHT) * CLOUD_CHANCE)
	
	# Color the pixels in steps of SPP
	for x in range(passes):
		print("Appling cloudy pass #", x+1)
		for i in range(0, w, SPP):
			for j in range(0, h, SPP):

				# Chose random color & darkness factor
				factor = random.uniform(DARKNESS, 1.1)

				# Select the cloud nuclei
				isCloudChance = randint(0, chance)

				if isCloudChance == chance:
					cloudNuclei.append((i, j))	
				
				color = darken(base, factor)
				for x in range(SPP): # Fill the SPP block
					for y in range(SPP):
						pixels[i+x, j+y] = color
	return [pixels, cloudNuclei]


# Applies a cloudy smooth
def cloudySmooth(w, h, pixels, cloudNuclei):
	print("Smoothing clouds...")
	# First pass for cloud nuclei
	for x in range(1): #Placeholder for multiple smoothing
		for v in range(0, w, SPP):
			for u in range(0, h, SPP):
				if (v, u) in cloudNuclei:
					pixels = formCloud(pixels, v, u)

	return pixels


# Darkens the pixels in an area to create a cloud shape
def formCloud(pixels, i, j):
	#darken pixels in a radius = CLOUDSIZE_MAX
	radius = CLOUDSIZE_MAX * SPP
	targetColor = pixels[i, j]

	#Accent
	if randint(0, 100) < ACCENT_CHANCE:
		targetColor = [abs(255 - t) for t in targetColor]
	
	for x in range(i - radius, i + radius, SPP):
		for y in range(j - radius, j + radius, SPP):
			randRadius = randint(round(radius/4), radius) #Randomize the radius
		
			if x >= 0 and y >= 0 and x <= WIDTH and y <= HEIGHT:
				distance = math.sqrt(math.pow((x-i), 2) + math.pow((y-j), 2))
			
				if distance <= randRadius:
					
					color = equalize(pixels[x, y], targetColor, distance)				
					for h in range(SPP): #Fill the SPP block
						for k in range(SPP):
							pixels[x+h, y+k] = color
							
	return pixels


# ---------------------------------------------------------------------------- #


# Applies a dichromatic cloud pass
def dichromaticPass(w, h, base, pixels, passes):
	# Init cloud coordinates
	cloudNuclei = []
	# Rescale the cloud chance relative to the size
	chance = round((WIDTH + HEIGHT) * CLOUD_CHANCE)
	SINGLE_CLOUD = True
	# Color the pixels in steps of SPP
	for x in range(passes):
		print("Appling dichromatic pass #", x + 1)
		for i in range(0, w, SPP):
			for j in range(0, h, SPP):

				# Chose random color & darkness factor
				factor = random.uniform(DARKNESS, 1.1)

				# Select the cloud nuclei
				isCloudChance = randint(0, chance)

				if isCloudChance == chance:
					cloudNuclei.append((i, j))	

				for x in range(SPP): #Fill the SPP block
					for y in range(SPP):
						pixels[i+x, j+y] = base

	return [pixels, cloudNuclei]


# Applies a cloudy smooth
def dichromaticSmooth(w, h, accent, pixels, cloudNuclei):
	print("Smoothing cloud accents...")
	# First pass for cloud nuclei
	for x in range(1): # Placeholder for multiple smoothing
		for v in range(0, w, SPP):
			for u in range(0, h, SPP):
				if (v, u) in cloudNuclei:
					pixels = formDichromaticCloud(pixels, v, u, accent)
						
	return pixels


# Darkens the pixels in an area to create a cloud shape
def formDichromaticCloud(pixels, i, j, accent):
	# Create a cloud of a random diameter
	radius = randint(CLOUDSIZE_MIN, CLOUDSIZE_MAX) * SPP
	targetColor = pixels[i, j]
	
	# Accent
	if randint(0, 100) < ACCENT_CHANCE:
		targetColor = accent

	for x in range(i - radius, i + radius, SPP):
		for y in range(j - radius, j + radius, SPP):
			# Within the boundaries of the image
			if x >= 0 and y >= 0 and x < WIDTH and y < HEIGHT:
				# Randomize the radius
				randRadius = randint(round(radius/1.4), radius)
				# Make sure it's a circle with Pythagoras
				distance = math.sqrt(math.pow((x-i), 2) + math.pow((y-j), 2))
				
				if distance <= randRadius:
					color = equalize(pixels[x, y], targetColor, distance)	
					# Fill the SPP block			
					for h in range(SPP):
						for k in range(SPP):
							pixels[x+h, y+k] = color
							
	return pixels


# ---------------------------------------------------------------------------- #


def buildImg(type, passes = 1):
	# Init the image
	img = Image.new('RGB', (WIDTH, HEIGHT), "black")

	print("Building pixels...")

	pixels = img.load() # Create the pixel map
	base = (randint(MINBASE, MAXBASE), randint(MINBASE, MAXBASE), randint(MINBASE, MAXBASE))
	w = img.size[0]
	h = img.size[1]

	
	if type == Type.AREAL:
		# Apply pass
		pixels = arealPass(w, h, base, pixels)
		# Apply smoothing
		pixels = arealSmooth(w, h, pixels)

	elif type == Type.CLOUDY:
		# Apply pass
		[pixels, cn] = cloudyPass(w, h, base, pixels, passes)
		# Apply smoothing
		pixels = cloudySmooth(w, h, pixels, cn)

	elif type == Type.DICHROMATIC:
		base, accent = Colors.Dichromias.ARGON_PURPLE

		# Apply pass
		[pixels, cn] = dichromaticPass(w, h, base, pixels, passes)
		# Apply smoothing
		pixels = dichromaticSmooth(w, h, accent, pixels, cn)

	else :
		print("Error:", type, "is not a valid type.")
		exit()

	return img

# Main function to startup
def main(randRotation = False):
	s_time = int(time.time())

	img = buildImg(Type.DICHROMATIC, 1)
	if randRotation == True:
		img = img.rotate(random.choice([0, 90, 180, 270])) # Randomly rotate the img

	print("Image completed in", int(time.time()) - s_time, "seconds.")

	img.save("result.png")

main()