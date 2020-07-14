# Author: Adrian Shedley
# Date 28 may 2020
# Purpose: Provide a massive speed upgrade for reading in CWA file types.
#   Additionally handles the writing of the Catman BIN data from the sensors.
# Last changed 6 July 2020, Adrian Shedley

import numpy as np
from datetime import datetime
import ProgressPrinter as pbar
# Layout
# 1) Load file
# 2) File is read into memory
# 3) File is operated on, converted to numpy array, and original is destroyed.

def readToMem(filePath, loggerInfo=None, cols=['X', 'Y', 'Z']):
    """ Reads all the data from a logger and returns a numpy array object"""
    current_time = datetime.now().strftime("%H:%M:%S")
    print("Read", filePath, "(", current_time, ")")

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
        #if i % (sectors // 4) == 0:
            #print("Read ", round(100.0 * i / sectors, 1), "% complete")
            #print(i/(sectors // 100))
        if i % (sectors // 100) == 0:
            pbar.printProgressBar(round((100.0 * i)/sectors, 0), 100, prefix="Read File", printEnd=" ")

        imp = np.frombuffer(memmap[headerOffset + i * sectorSize : headerOffset + (i+1) * sectorSize - 2], offset=30, dtype=layout)
        masterArray[i * samplesPerSector : (i+1) * samplesPerSector] = imp

    memmap.release()

    current_time = datetime.now().strftime("%H:%M:%S")
    print("Read Complete. (", current_time, ")")
    return masterArray.view(np.int16).reshape(masterArray.shape + (-1,)).transpose().astype(np.float64, casting='safe')

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
    print("Write Channel Start. (", current_time, ")")

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

    for i in range(numChannels):
        iScale = scaleFactors[i//3]  # First three channels take scaleFactor[0], 4-6 take scaleFactor[1] etc

        if sizeBytes == 2:
            maxVal = arrayIn[i].max() / iScale
            minVal = arrayIn[i].min() / iScale
            rangeVal = maxVal - minVal

            #print("File max at", arrayIn[i].argmax(), maxVal)
            #print("File min at", arrayIn[i].argmin(), minVal)

            # Write the min and max values for catman to use
            fp.write(minVal.astype('float64').tobytes())
            fp.write(maxVal.astype('float64').tobytes())

            # Write the data in levels between 0 and [divisor]
            fp.write(((arrayIn[i] / iScale - minVal)*(divisor/rangeVal)).astype(type).tobytes())
        else:
            fp.write((arrayIn[i]/ iScale).astype(type).tobytes())
        #print("Logger Channel", cols[i], "written")
        pbar.printProgressBar((100.0 / numChannels) * (i + 1), 100, prefix="Write File", printEnd=" ")

    lastPos = fp.tell()
    fp.close()

    current_time = datetime.now().strftime("%H:%M:%S")
    print("Writing complete. (", current_time, ")")
    return lastPos