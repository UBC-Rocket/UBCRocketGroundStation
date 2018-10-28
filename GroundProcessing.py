import array
import matplotlib.pyplot as plt
from decimal import *
from matplotlib.ticker import FormatStrFormatter


#A class to represent data with a time stamp
class DATA:
	def __init__(self, data, time):
		self.data = data
		self.time = time


#given file name, returns 2d list where the rows are individual sensor's data and the first colomn is the name of the sensor and the rest are the data at timestamp column# 
#The following 3 functions are all for getting data from the SD card
#Format return dataset[Sensor][time/data]
def sortDataFromSD(string):
	file = open(string , "r")
	line = file.readline()
	dataSet = setUpDataSet(line)
	name=""
	commas=0
	while 1:
		line = file.readline()
		if line == "":
			break
		dataSet = addDataToSet(dataSet, line)

	return dataSet
		
#creates a 2d list with the titles 
#SHOULD BE USED WITH THE FIRST TITLE LINE ONLY
def setUpDataSet(line):
	dataSet = list()
	l = len(line)
	name=""
	for i in range (0, l-1):
		if line[i] != ',':
			name = name +line[i]
		else:
			newlist = list()
			newlist.append(name)
			dataSet.append(newlist)
			name = ""
	return dataSet
#adds a line of data to an already established data set
#SHOULD BE USED WITH DATA LINES ONLY FOR USEFUL DATA 
def addDataToSet(dataSet ,line):
	l=len(line)
	name = ""
	commas =0
	for i in range (0, l-1):
			if line[i] != ',':
				name = name + line[i]
			else:
				dataSet[commas].append(name)
				commas= commas+1
				name=""
	return dataSet

#the following functions are for getting data from the radio connection
#creates working radio set radioset[sensor][data]
#the first characters are ascii identifiers for radio communication
#The time list contains floats with the timestamp
#All other catagories use the ADT DATA which contain data and timestamp internal variables
#this allows data for some sensors to be sent periodically 
def initializeRadioSet():
	radioSet = list()
	a = ['X Accelerometer - Acceleration X (g)']
	b = ['Y Accelerometer - Acceleration Y (g)']
	c = ['Z Accelerometer - Acceleration Z (g)']
	d = ['P Barometer - Pressure (mbar)']
	e = ['~ Barometer - Temperature (C)']
	f = ['T Temperature Sensor - Temperature (C)']
	g = ['x IMU - Acceleration X (g)']
	h = ['y IMU - Acceleration Y (g)']
	i = ['z IMU - Acceleration Z (g)']
	j = ['@ IMU - Angular Velocity X (rad/s)']
	k = ['# IMU - Angular Velocity Y (rad/s)']
	l = ['$ IMU - Angular Velocity Z (rad/s)']
	m = ['% IMU - Magnetism X (uT)']
	n = ['^ IMU - Magnetism Y (uT)']
	o = ['& IMU - Magnetism Z (uT)']
	p = ['* IMU - Temperature (C)']
	q = ['L GPS - Latitude']
	r = ['l GPS - Longitude']
	s = ['A GPS - Altitude']
	t = ['t Time']

	#time is always the first list for easy access 
	radioSet.append(t)
	radioSet.append(a)
	radioSet.append(b)
	radioSet.append(c)
	radioSet.append(d)
	radioSet.append(e)
	radioSet.append(f)
	radioSet.append(g)
	radioSet.append(h)
	radioSet.append(i)
	radioSet.append(j)
	radioSet.append(k)
	radioSet.append(l)
	radioSet.append(m)
	radioSet.append(n)
	radioSet.append(o)
	radioSet.append(p)
	radioSet.append(q)
	radioSet.append(r)
	radioSet.append(s)
	

	return radioSet


#radioData takes in a list of 5 numbers between 0 and 255 representing bytes
#The first byte is the identifier and the remainder are a float representing the data
#returns the updated radioSet set
def addToRadioSet(radioData, radioSet):

	character = chr(radioData[0])
	#turns d into a float from decimal representation of 4 sepreate bytes in a list
	data = radioData[1:5]
	b= struct.pack('4B', *data)
	c=struct.unpack('>f', b)
	d=c[0]
	if character == 't':
		radioSet[0].append(d)
	else: 
		length = len(radioSet[0])
		time = radioSet[0][length-1]
		#create a data point with the the latest time
		length = len(radioSet)
		addData = DATA(d, time)
		for i in range (0, length-1): 
			s = radioSet[i][0]
			if s[0] == character:
				radioSet[i].append(addData)
				break

	return radioSet

def radioSetToFile(radioSet):
	file = open("Radio_Data.csv", "w")
	sensors = len(radioSet)-1
	for i in range (0, sensors-1):
		file.write(radioSet[i][0]+",", end="")
	return





#graph sensor data with time on the x axis
def graphSensorVsTime(SensorNum, dataSet):
	fig, ax = plt.subplots()
	plt.ylabel(dataSet[SensorNum][0])
	plt.xlabel('time')
	#make a set that is only data without the title
	Set = dataSet[SensorNum][1:]
	length= len(Set)
	

	for i in range (0, length-1):
		plt.plot(i, float(Set[i]), 'ro')
	plt.show()
	plt.draw()
	return

#graph sensornum1 on x axis and sensor num 2 on y axis 
def graphSensorVsSensor(SensorNum1, SensorNum2, dataSet):
	fig, ax = plt.subplots()
	plt.xlabel(dataSet[SensorNum1][0])
	plt.ylabel(dataSet[SensorNum2][0])

	setX = dataSet[SensorNum1][1:]
	setY = dataSet[SensorNum2][1:]
	length= len(setX)

	for i in range (0, length-1):
		plt.plot(setX[i], float(setY[i]), 'ro')
	plt.show()
	plt.draw()
	return


def printSensors(dataSet):
	for i in range (0, len(dataSet)-1):
		print( "[" + str(i) + "] : " + dataSet[i][0])
	return

def printInstructions():
	print("graph : Pick sensor to graph against time")
	print("graph against : Pick sensor to grap against sensor")
	print("get max 'int' : Gives the maximum value of the data from this sensor number")
	print("get min 'int' : Gives the minimum value of the data from this sensor number")
	return





# print("What file would you like to read from?")
# string = input()
# dataSet = sortDataFromSD(string)





# graphSensorVsTime(0 , dataSet)
# print("write yeet")
# string = input()
# if string == "yeet":
# 	print("YYYEEEEEETT")



# printSensors(dataSet)
# string = input
# print(string)

# while string != "exit":
# 	#printInstructions();
# 	string = input
# 	print(string)
















#dataSet = sortDataFromSD("DATALOG.csv")

#graphSensorVsTime(0, dataSet)















