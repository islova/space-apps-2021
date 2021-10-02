# Copyright JAIA 2021 <https://github.com/islova/space-apps-2021>
# This file generates txt files with the debris tracked by CelesTrak

from skyfield.api import load, wgs84, EarthSatellite
import os
import shutil

wd = "../"  # Where the txt/ directory will be created
common_name = 'cosmos-2251-debris'  # Name of the txt with the LSE (make sure this matches the file name at Celestrak)
common_txt_name = common_name + '.txt'  # Common_name + .txt
txt_path = wd + 'txt/'  # Path of the txt/ directory
lse_file = txt_path + common_name + '.txt'  # Name of the file with the LSEs
coords_file = txt_path + common_name + '-coords.txt'  # Name of the file with coordinates


# Creates txt/ dir in working directory
def create_txt_dir():
	dir_name = "txt"
	path = os.path.join(wd, dir_name)
	os.mkdir(path)


# Generates the LSE file
def gen_LSE():
	url_list = ['https://celestrak.com/NORAD/elements/' + common_txt_name]
	if not os.path.isdir(txt_path):
		create_txt_dir()
	for i in url_list:
		load.tle_file(i)
	shutil.move('./' + common_txt_name, txt_path + common_txt_name)


# Generates the file with coordinates
def gen_coords():
	ts = load.timescale()
	t = ts.now()

	if not os.path.isfile(lse_file):
		gen_LSE()

	counter = 0
	l1 = ''
	l2 = ''
	debris_list = []

	f = open(lse_file, 'r')
	for line in f:  # Loops through the LSE txt file
		if counter % 3 == 0:
			if l1 != '':
				debris = EarthSatellite(l1, l2, '', ts)
				geocentric = debris.at(t)
				subpoint = wgs84.subpoint(geocentric)
				coords_str = str(subpoint.latitude.degrees) + ',' + str(subpoint.longitude.degrees) + ',' + str(subpoint.elevation.km)
				debris_list.append(coords_str)  # Appends the coords as a string (latitude,longitude,elevation) to a list
		elif counter % 3 == 1:
			l1 = line
		elif counter % 3 == 2:
			l2 = line
		counter += 1
	f.close()
	
	f = open(coords_file, 'w')
	for line in debris_list:  # Loops through the coords list and writes its contents inside the coords file
		f.write(line + '\n')


gen_coords()