# Copyright JAIA 2021
# This .py generates .txt files containing TLEs of all objects orbiting earth that are currently being tracked by CelesTrak 

from skyfield.api import load, wgs84, EarthSatellite

url_list = ['http://celestrak.com/NORAD/elements/debris.txt', 
			'http://celestrak.com/NORAD/elements/stations.txt']

for i in url_list:
	load.tle_file(i)
