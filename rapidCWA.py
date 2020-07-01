# Author: Adrian Shedley
# Date 28 may 2020
# Purpose: Provide a massive speed upgrade for reading in CWA file types

import numpy as np
from numpy.lib import recfunctions as rfn
from datetime import datetime

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
        if i % (sectors // 10) == 0:
            print("Read ", round(100.0 * i / sectors, 1), "% complete")

        imp = np.frombuffer(memmap[headerOffset + i * sectorSize : headerOffset + (i+1) * sectorSize - 2], offset=30, dtype=layout)
        masterArray[i * samplesPerSector : (i+1) * samplesPerSector] = imp

    memmap.release()

    current_time = datetime.now().strftime("%H:%M:%S")
    print("Read Complete.(", current_time, ")")
    return masterArray

def writeToFile(arrayIn, filePath, offsetBytes=0, sizeBytes=8, cols=['X', 'Y', 'Z']):

    current_time = datetime.now().strftime("%H:%M:%S")
    print("Channel Writing start (", current_time, ")")

    if not filePath.endswith(".bin"):
        filePath += ".bin"

    fp = open(filePath, 'ab+')
    numChannels = len(cols)

    type = 'float64'
    if (sizeBytes == 4):
        type = 'float32'
    elif (sizeBytes == 2):
        type = 'float16'

    fp.seek(offsetBytes)

    # print(len(arrayIn[cols[0]]))
    # print(arrayIn[cols[0]].astype(type).itemsize)

    for i in range(numChannels):
        print("Logger Channel", cols[i], "written")
        fp.write((arrayIn[cols[i]].astype(type) / 2048.0).tobytes())

    fp.close()

    current_time = datetime.now().strftime("%H:%M:%S")
    print("Writing complete. (", current_time, ")")


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