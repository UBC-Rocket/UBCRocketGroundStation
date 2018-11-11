import array
import matplotlib.pyplot as plt
from decimal import *
from matplotlib.ticker import FormatStrFormatter
import struct
import Plotter

RADIOSET = None


#A class to represent data with a time stamp
class DATA:
	def __init__(self, data, time):
		self.data = data
		self.time = time

#these functions are wrappers for the global variable
def initialize():
	global RADIOSET
	RADIOSET = initializeRadioSet()
	return
def addData(data):
	global RADIOSET
	RADIOSET = addToRadioSet(data, RADIOSET)
	return
def printToFile():
	radioSetToFile(RADIOSET)
	return


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

		# Plot new Pressure data
		if character == 'P':
			Plotter.plot(addData.time, addData.data)

		for i in range (0, length): 
			s = radioSet[i][0]
			if s[0] == character:
				radioSet[i].append(addData)
				break

	return radioSet

#creates a file names "Radio_Data.csv" which contains all values in the working radio set in csv format
#currently there is no character for a sensor lacking data for a time, may need to change to a space
#Will take a longish time to execute, only bother running if you are done reading data
def radioSetToFile(radioSet):
	file = open("Radio_Data.csv", "w")
	sensors = len(radioSet)-1
	#write the titles
	string = ""
	for i in range (0, sensors):
		string = string + radioSet[i][0]+","
	string = string + radioSet[sensors][0]+"\n"
	file.write(string)

	#write the data
	#time is the first row
	timestamps = len(radioSet[0])
	#going through each time
	for i in range (1, timestamps):
		string = str(radioSet[0][i]) + "," #set first part to time

		#going down the row of sensors
		for j in range (1, sensors+1):
			#now check each data point for the sensor to see if you can add data, else add just , 
			datapoints = len(radioSet[j])
			#there are no datapoints for the sensors
			if datapoints == 1:
				if j == sensors:
					string = string + "\n"
				else:
					string = string + ","
			#there are dtapoints for the sensors
			else:
				#go through all the datapoints and see if the time matches the time at the start of the row 
				for k in range (1, datapoints):
					#data time is equal to current time, add it to the row and leave the for loop
					if radioSet[j][k].time == radioSet[0][i]:
						if j == sensors:
							string = string + str(radioSet[j][k].data) + "\n"
						else :
							string = string + str(radioSet[j][k].data) + ","
						break
					#data time has past current time, add no data  to the row and leave the loop
					elif radioSet[j][k].time > radioSet[0][i]:
						if j == sensors:
							string = string + "\n"
						else :
							string = string + ","
						break
					#time has past data time so no data is added for sensor 
					elif k == (datapoints-1):
						if j == sensors:
							string = string + "\n"
						else :
							string = string + ","
		file.write(string)
	file.close()

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















