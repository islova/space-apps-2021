# Copyright JAIA 2021 <https://github.com/islova/space-apps-2021>
# This file generates txt files with the debris tracked by CelesTrak

from flask import redirect, render_template, request, session
from functools import wraps
from skyfield.api import load, wgs84, EarthSatellite

import os
import sqlite3
import shutil


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
	def __init__(self, latitude, longitude, elevation, id_):
		self.id = id_
		self.latitude = latitude
		self.longitude = longitude
		self.elevation = elevation


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


# Creates txt/ dir in working directory
def create_txt_dir():
	dir_name = "txt"
	path = os.path.join(wd, dir_name)
	os.mkdir(path)


# Generates the tle file
def gen_TLE():
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
		gen_TLE()

	counter = 0
	num = 0
	name = ''
	l1 = ''
	l2 = ''
	debris_dic = {	"id" : [],
					"name": [],
					"lat": [],
					"long" : [],
					"elev" : []
					}

	f = open(lse_file, 'r')
	for line in f:  # Loops through the tle txt file
		if counter % 3 == 0:
			if name != '':
				num += 1
				debris = EarthSatellite(l1, l2, '', ts)
				geocentric = debris.at(t)
				subpoint = wgs84.subpoint(geocentric)
				debris_dic['id'].append(num)
				debris_dic['name'].append(name)
				debris_dic['lat'].append(subpoint.latitude.degrees)
				debris_dic['long'].append(subpoint.longitude.degrees)
				debris_dic['elev'].append(subpoint.elevation.km)
				'''cur.execute("INSERT INTO junk (id, latitude, longitude, elevation) VALUES (:id, :latitude, :longitude, :elevation)", {"id" : num, "latitude": subpoint.latitude.degrees, "longitude" :
    					subpoint.longitude.degrees, "elevation" : subpoint.elevation.km})'''
    		name = line.rstrip()
		elif counter % 3 == 1:
			l1 = line
		elif counter % 3 == 2:
			l2 = line
		counter += 1
		'''conn.commit()'''
	global total_debris
	total_debris = num
	f.close()
	
	return(debris_dic)


# Generates a file with future positions
def gen_future_pos():
	ts = load.timescale()
	t = ts.now()  # Time at moment of execution

	num = 0
	counter = 0
	name = ''
	l1 = ''
	l2 = ''

	if os.path.isfile(future_pos_file):
		os.remove(future_pos_file)

	f_r = open(lse_file, 'r')  # tle file
	f_a = open(future_pos_file, 'a')  # File with future positions
	for line in f_r:
		if counter % 3 == 0:
			if name != '':
				for current_time in range(collision_interval_time):  # Increments by 1 minute every repetition
					t_utc = t.utc_datetime()
					t_utc += timedelta(minutes=current_time)  # Increments time by 1 minute
					t_new = ts.from_datetime(t_utc)
					debris = EarthSatellite(l1, l2, '', ts)
					geocentric = debris.at(t_new)
					subpoint = wgs84.subpoint(geocentric)
					pos_str = str(num) + '  ' + name + ',' + str(subpoint.latitude.degrees) + ',' + str(subpoint.longitude.degrees) + ',' + str(subpoint.elevation.km)
					f_a.write(pos_str + '\n')
				f_a.write('\n')
				num += 1
			name = line.rstrip()
		elif counter % 3 == 1:
			l1 = line
		elif counter % 3 == 2:
			l2 = line
		counter += 1

	f_r.close()
	f_a.close()


# Determines wether a debris is too close to another based on the file previously generated
def check_collision_risk():

	positions_list = []  # List with all future positions
	counter = 0
	f_r = open(future_pos_file, 'r')
	for line in f_r:
		temp = line.split(',')
		if temp[0] != '\n':
			temp.pop(0)
			temp[2].rstrip()
			positions_list.append(Position(float(temp[0]), float(temp[1]), float(temp[2]), counter))
		else:
			counter += 1

	for instant in range(collision_interval_time):  # Loops through the list of positions and determines if they are too close to each other
		for current in range(1, total_debris):
			if (positions_list[instant].is_nearby(positions_list[current * collision_interval_time])):
				print("Debris id:", positions_list[instant].id, \
					"might collide with debris id:", positions_list[current * collision_interval_time].id, \
					"at time interval number", instant)


gen_coords()
if enable_gen_future_pos:
	gen_future_pos()
if os.path.isfile(future_pos_file):
	check_collision_risk()



'''conn.close()'''

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
