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

def method2(filePath):
    # Requires 2x the file size as memory size
    pass

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