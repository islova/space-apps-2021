# Copyright JAIA 2021 <https://github.com/islova/space-apps-2021>
# This file generates txt files with the debris tracked by CelesTrak

from skyfield.api import load, wgs84, EarthSatellite
import os
import sqlite3
import shutil
from flask import redirect, render_template, request, session
from functools import wraps


'''conn = sqlite3.connect('debris.db')
cur = conn.cursor()'''

# ---------- GLOBAL CONSTANTS ----------
wd = "../"  # Where the txt/ directory will be created
common_name = 'cosmos-2251-debris'  # Name of the txt with the tle (make sure this matches the file name at Celestrak)
common_txt_name = common_name + '.txt'  # Common_name + .txt
txt_path = wd + 'txt/'  # Path of the txt/ directory
lse_file = txt_path + common_name + '.txt'  # Name of the file with the LSEs
future_pos_file = txt_path + common_name + '-future-pos.txt'  # Name of the file with the future positions

collision_interval_km = 0.15  # Difference in elevation in which debris will be considered as might_collide
collision_interval_time = 60  # Minutes into the future for which positions will be calculated

enable_gen_future_pos = False  # When this is enabled, the .txt file for future positions is generated

total_debris = 0  # <-- global variable
# --------------------------------------


# Class that defines a position
class Position:
	def __init__(self, latitude, longitude, elevation, id_, name):
		self.id = id_
		self.latitude = latitude
		self.longitude = longitude
		self.elevation = elevation
		self.name = name

	# Determines if the position is too similar to another
	# The latitude and longitude are rounded, the elevation is measured with an error margin of size "collision_interval_km"
	def is_nearby(self, other):
		result = False
		try:  # Might be NaN
			if round(self.latitude) == round(other.latitude) and \
			 round(self.longitude) == round(self.longitude) and \
			 self.elevation - collision_interval_km <= other.elevation <= self.elevation + collision_interval_km:
				result = True
		except ValueError:
			pass
		return result

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

# Generates a dictionary with current positions
def gen_coords():

	ts = load.timescale()
	t = ts.now()

	if not os.path.isfile(lse_file):
		gen_LSE()

	counter = 0
	num = 0
	name = ''
	l1 = ''
	l2 = ''
	debris_dic = {	"id" : [],
					"name": [],
					"lat": [],
					"long" : [],
					"elev" : [],
					"tle1" : [],
					"tle2" : []
					}
	satellites = []

	f = open(lse_file, 'r')
	for line in f:  # Loops through the LSE txt file
		if counter % 3 == 0:
			if name != '':
				num += 1
				debris = EarthSatellite(l1, l2, '', ts)
				satellites.append(debris)
				geocentric = debris.at(t)
				subpoint = wgs84.subpoint(geocentric)
				debris_dic['id'].append(num)
				debris_dic['name'].append(name)
				debris_dic['lat'].append(subpoint.latitude.degrees)
				debris_dic['long'].append(subpoint.longitude.degrees)
				debris_dic['elev'].append(subpoint.elevation.km)
			name = line.rstrip()
		elif counter % 3 == 1:
			l1 = line
			debris_dic['tle1'].append(l1)
		elif counter % 3 == 2:
			l2 = line
			debris_dic['tle2'].append(l2)
		counter += 1
	f.close()
	return(debris_dic, satellites, num)

def get_distances():
	coords, satellites, num = gen_coords()
	ts = load.timescale()
	t = ts.now()

	if not os.path.isfile(lse_file):
		gen_LSE()
	nearest = {
				'distance': [],
				'deb1': [],
				'deb2': [],
				"tle1" : [],
				"tle2" : [],
				"tle3" : [],
				"tle4" : []
			}

	pair_amount = 0
	for i in range(150):
		for j in range(i + 1, 151):
			if i != j:
				position1 = (satellites[i]).at(t)
				position2 = (satellites[j]).at(t)
				distance = (position2 - position1).distance().km
				if(distance < 200):
					nearest['distance'].append(distance)
					nearest['deb1'].append(coords['name'][i])
					nearest['deb2'].append(coords['name'][j])
					nearest['tle1'].append(coords['tle1'][i])
					nearest['tle2'].append(coords['tle2'][i])
					nearest['tle3'].append(coords['tle1'][j])
					nearest['tle4'].append(coords['tle2'][j])
					pair_amount += 1
	return(nearest, pair_amount)

# Determines wether a debris is too close to another based on the file previously generated
def check_risk(amount):

	risk = {
			"deb1": [],
			"deb2": [],
			"instant": [],
			"name1":[],
			"name2":[]
			}
	positions_list = []  # List with all future positions
	counter = 0
	f_r = open(future_pos_file, 'r')
	for line in f_r:
		temp = line.split(',')
		if temp[0] != '\n':
			temp_temp = temp[0].split('  ')
			temp.pop(0)
			temp[2].rstrip()
			positions_list.append(Position(float(temp[0]), float(temp[1]), float(temp[2]), counter, temp_temp[1]))
		else:
			counter += 1
	f_r.close()

	num = 0
	for instant in range(collision_interval_time):  # Loops through the list of positions and determines if they are too close to each other
		for current in range(1, 1000):
			if (positions_list[instant].is_nearby(positions_list[current * collision_interval_time])):
				risk['deb1'].append(positions_list[instant].id)
				risk['deb2'].append(positions_list[current * collision_interval_time].id)
				risk['instant'].append(instant)
				risk['name1'].append(positions_list[instant].name)
				risk['name2'].append(positions_list[current * collision_interval_time].name)
				num += 1
				print("Debris id:", positions_list[instant].id, \
					"might collide with debris id:", positions_list[current * collision_interval_time].id, \
					"at time interval number", instant)
	print(risk)
	return(risk, num)

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function