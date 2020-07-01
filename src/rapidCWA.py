# Author: Adrian Shedley
# Date 28 may 2020
# Purpose: Provide a massive speed upgrade for reading in CWA file types

import numpy as np
from numpy.lib import recfunctions as rfn


# Layout
# 1) Load file
# 2) File is read into memory
# 3) File is operated on, converted to numpy array, and original is destroyed.

def method1(filePath):

    # ndarray setup
    cols = ['x', 'y', 'z']
    types = ['i2'] * len(cols)
    typesOutput = ['f8'] * len(cols)
    layout = np.dtype({'names': cols, 'formats': types})
    layoutOutput = np.dtype({'names': cols, 'formats': types})

    # Load file directly to ram
    fp = open(filePath, "rb")
    memmap = memoryview(fp.read())
    fp.close()

    print(len(memmap))

    headerOffset = 1024
    sectorSize = 512

    sectors = (len(memmap) - headerOffset) // sectorSize

    samplesPerSector = 80

    samples = sectors * samplesPerSector
    print(samples)

    op = 10

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