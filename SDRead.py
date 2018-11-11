import array
import matplotlib.pyplot as plt
from decimal import *
from matplotlib.ticker import FormatStrFormatter
import struct

#Given file must be in csv format with the sensor titles as the first line, there must be as many sensors as data objects per line
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
	for i in range (0, l):
		if line[i] != ',' and i != l-1:
			name = name +line[i]
		
		else:
			newlist = list()
			newlist.append(name)
			dataSet.append(newlist)
			
			name = ""
	return dataSet

def addDataToSet(dataSet ,line):
	l=len(line)
	name = ""
	commas =0
	for i in range (0, l):
			if line[i] != ',':
				name = name + line[i]
			else:
				dataSet[commas].append(name)
				commas= commas+1
				name=""
	return dataSet

	#graph sensor data with time on the x axis
def graphSensorVsTime(SensorNum, dataSet):
	fig, ax = plt.subplots()
	plt.ylabel(dataSet[SensorNum][0])
	plt.xlabel('time')
	#make a set that is only data without the title
	Set = dataSet[SensorNum][1:]
	length= len(Set)
	

	for i in range (0, length):
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

	for i in range (0, length):
		plt.plot(setX[i], float(setY[i]), 'ro')
	plt.show()
	plt.draw()
	return
#prints all sensor titles
def printSensors(dataSet):
	for i in range (0, len(dataSet)):
		print( "[" + str(i) + "] : " + dataSet[i][0])
	return
#prints all data in line
def printDataLine(line):
	#for i in range (0, len(dataSet)):

	return


def printInstructions():
	print("graph : Pick sensor to graph against time")
	print("graph against : Pick sensor to grap against sensor")
	print("get max 'int' : Gives the maximum value of the data from this sensor number")
	print("get min 'int' : Gives the minimum value of the data from this sensor number")
	return

print("What file would you like to read from?")
string = input()
dataSet = sortDataFromSD(string)
#print(dataSet)

printSensors(dataSet)
graphSensorVsTime(0, dataSet)

