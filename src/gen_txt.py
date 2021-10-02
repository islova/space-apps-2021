# Copyright JAIA 2021 <https://github.com/islova/space-apps-2021>
# This file generates txt files with the debris tracked by CelesTrak

from skyfield.api import load, wgs84, EarthSatellite
import os
import shutil

wd = "../"
common_name = 'cosmos-2251-debris'
common_txt_name = common_name + '.txt'
txt_path = wd + 'txt'
lse_file = txt_path + '/' + common_name + '.txt'
coords_file = txt_path + '/' + common_name + '-coords.txt'


def create_txt_dir():
	dir_name = "txt"
	path = os.path.join(wd, dir_name)
	os.mkdir(path)


def gen_LSE():
	url_list = ['https://celestrak.com/NORAD/elements/' + common_txt_name]
	if not os.path.isdir(txt_path):
		create_txt_dir()
	for i in url_list:
		load.tle_file(i)
	shutil.move('./' + common_txt_name, txt_path + '/' + common_txt_name)


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
	for line in f:
		if counter % 3 == 0:
			if l1 != '':
				debris = EarthSatellite(l1, l2, '', ts)
				geocentric = debris.at(t)
				subpoint = wgs84.subpoint(geocentric)
				coords_str = str(subpoint.latitude.degrees) + ',' + str(subpoint.longitude.degrees) + ',' + str(subpoint.elevation.km)
				debris_list.append(coords_str)
		elif counter % 3 == 1:
			l1 = line
		elif counter % 3 == 2:
			l2 = line
		counter += 1
	f.close()
	
	f = open(coords_file, 'w')
	for line in debris_list:
		f.write(line + '\n')


gen_coords()