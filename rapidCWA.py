# Author: Adrian Shedley
# Date 28 may 2020
# Purpose: Provide a massive speed upgrade for reading in CWA file types

import numpy as np
from numpy.lib import recfunctions as rfn
from datetime import datetime
from scipy import interpolate
import Resampler

# Layout
# 1) Load file
# 2) File is read into memory
# 3) File is operated on, converted to numpy array, and original is destroyed.

def readToMem(filePath, loggerInfo=None, cols=['X', 'Y', 'Z']):
    """ Reads all the data from a logger and returns a numpy array object"""
    current_time = datetime.now().strftime("%H:%M:%S")
    print("Reading ", filePath, "(", current_time, ")")

    headerOffset = 1024
    sectorSize = 512
    samplesPerSector = loggerInfo['first']['samplesPerSector']

    types = ['i2'] * len(cols)  # The 2byte integer layout
    layout = np.dtype({'names': cols, 'formats': types})  # Name the columns of the array

    fp = open(filePath, "rb")  # Open the file in read bytes mode
    memmap = memoryview(fp.read())
    fp.close()

    fileSize = len(memmap)
    sectors = (fileSize - headerOffset) // sectorSize
    samples = sectors * samplesPerSector

    masterArray = np.zeros((samples, ), dtype=layout)

    for i in range(sectors):
        if i % (sectors // 4) == 0:
            print("Read ", round(100.0 * i / sectors, 1), "% complete")

        imp = np.frombuffer(memmap[headerOffset + i * sectorSize : headerOffset + (i+1) * sectorSize - 2], offset=30, dtype=layout)
        masterArray[i * samplesPerSector : (i+1) * samplesPerSector] = imp

    memmap.release()

    current_time = datetime.now().strftime("%H:%M:%S")
    print("Read Complete.(", current_time, ")")
    return masterArray.view(np.int16).reshape(masterArray.shape + (-1,)).transpose()

def writeToFile(arrayIn, filePath, loggerInfo=None, offsetBytes=0, sizeBytes=8, cols=['X', 'Y', 'Z']):

    first = loggerInfo['first']
    numChannels = first['channels']

    scaleFactors = []
    if numChannels >= 6:
        scaleFactors.append(first['gyroScale'])
        scaleFactors.append(first['accelScale'])
        if numChannels >= 9:
            scaleFactors.append(first['magScale'])
    elif numChannels >= 3:
        scaleFactors.append(first['accelScale'])


    current_time = datetime.now().strftime("%H:%M:%S")
    print("Channel Writing start (", current_time, ")")

    if not filePath.endswith(".bin"):
        filePath += ".bin"

    fp = open(filePath, 'ab+')

    type = 'float64'
    divisor = 1
    if sizeBytes == 4:
        type = 'float32'
    elif sizeBytes == 2:
        type = 'uint16'
        divisor = pow(2, 16-1) - 1

    fp.seek(offsetBytes)

    # For 2 byte files, the method is slightly different
    # 8 byte float min
    # 8 byte float max
    # Data points between 0 and 2^(16-1)-1 for 2byte


    # print(len(arrayIn[cols[0]]))
    # print(arrayIn[cols[0]].astype(type).itemsize)

    for i in range(numChannels):
        iScale = scaleFactors[i//3]  # First three channels take scaleFactor[0], 4-6 take scaleFactor[1] etc

        if sizeBytes == 2:
            maxVal = arrayIn[i].max() / iScale
            minVal = arrayIn[i].min() / iScale
            rangeVal = maxVal - minVal

            # Write the min and max values for catman to use
            fp.write(minVal.astype('float64').tobytes())
            fp.write(maxVal.astype('float64').tobytes())

            # Write the data in levels between 0 and [divisor]
            fp.write(((arrayIn[i] / iScale - minVal)*(divisor/rangeVal)).astype(type).tobytes())
        else:
            fp.write((arrayIn[i]/ iScale).astype(type).tobytes())
        print("Logger Channel", cols[i], "written")

    fp.close()

    current_time = datetime.now().strftime("%H:%M:%S")
    print("Writing complete. (", current_time, ")")


def resample_linear(arrayIn, targetStart, targetStop, targetFreq, logger, cols=['X', 'Y', 'Z']):

    numSamples = logger['file']['numSamples']
    numChannels = int(logger['first']['channels'])
    dataSet = Resampler.DataSet(logger['first']['timestamp'], logger['last']['timestamp'], numSamples, numChannels, None)

    types = ['i2'] * numChannels  # The 2byte integer layout
    layout = np.dtype({'names': cols, 'formats': types})  # Name the columns of the array

    oStartTime = int(dataSet.startTime * 1e9)
    oStopTime = int(dataSet.stopTime * 1e9)
    #oDuration = int(oStopTime - oStartTime)  # Time in whole nanosectons
    oSamples = dataSet.numSamples
    oFreq = dataSet.numSamples / (dataSet.stopTime - dataSet.startTime)
    #oDt = int((1.0 / oFreq) * 1e9)  # Delta time in nanoseconds

    tStartTime = int(targetStart * 1e9)
    tStopTime = int(targetStop * 1e9)
    tFreq = targetFreq
    tSamples = int((tStopTime - tStartTime) * tFreq / 1e9)
    print(oStartTime, oStopTime, oFreq, oSamples)
    print(tStartTime, tStopTime, tFreq, tSamples)
    tDt = int((1.0 / tFreq) * 1e9)  # Target delta time in nanoseconds

    oX = np.arange(oStartTime, oStopTime-1e9/oFreq, 1e9/oFreq)
    xnew = np.arange(tStartTime, tStopTime-(1e9/tFreq), 1e9/tFreq)

    print(len(oX), len(arrayIn), len(xnew))
    print(oX.dtype)
    print(arrayIn.shape)

    linInter = interpolate.interp1d(oX, arrayIn, copy=True)

    output = linInter(xnew)
    print(output.shape)

    outarray = np.zeros((numChannels, len(xnew)))

    return output


def method1(filePath):

    # Output startint time
    current_time = datetime.now().strftime("%H:%M:%S.%f")
    print("Start time =", current_time)

    # ndarray setup - the numpy array dimensions and cols
    cols = ['x', 'y', 'z']
    types = ['i2'] * len(cols)  # The 2byte integer layout
    #  typesOutput = ['f8'] * len(cols)
    layout = np.dtype({'names': cols, 'formats': types})
    #  layoutOutput = np.dtype({'names': cols, 'formats': types})

    # Load file directly to ram
    fp = open(filePath, "rb")
    memmap = memoryview(fp.read())
    fp.close()

    fileSize = len(memmap)
    print("File size", fileSize)

    headerOffset = 1024
    sectorSize = 512
    samplesPerSector = 80

    sectors = (fileSize - headerOffset) // sectorSize
    samples = sectors * samplesPerSector
    print("Samples=",samples)

    op = 1 #  Number of times to BRUTE force -> simulate a massive file
    masterArray = np.zeros((samples*op, ), dtype=layout)

    for i in range(sectors*op):
        imp = np.frombuffer(memmap[headerOffset + i//op * sectorSize : headerOffset + ((i//op)+1) * sectorSize - 2], offset=30, dtype=layout)
        masterArray[i * samplesPerSector : (i+1) * samplesPerSector] = imp

    memmap.release()
    #print(len(masterArray['x']))
    #print(masterArray['y'][0:160] / 2048.0)

    f = open(filePath + ".bin", 'wb')

    numChannels = 3

    for i in range(numChannels):
        f.write((masterArray[cols[i]] / 2048.0).tobytes())

    f.close()

    current_time = datetime.now().strftime("%H:%M:%S.%f")
    print("End time =", current_time)

    #print(len(imp))

    #
    #print(imp['data'])

    #restruct = rfn.unstructured_to_structured(arr, layout, copy=False)
    #print(restruct)

    #doubles = np.float_(restruct['x'] / 2040)

    #print(doubles)

    #arr = np.array([(1, 3, 4), (3, 2, 4)], dtype=layout)

    #print(arr)
    #print(arr['x'])