# Author Adrian Shedley
# date 27 May 2020
# Controller file to prepare data to be resampled, and then write it out to file.

import cwa_metadata as CWA   # cwa file type converter
import bin_data as BIN  # bin file type converter

import os

import Resampler
import Multithread

from struct import *

def resample_logger_data(inParam: []):
    logger = inParam[0]
    filePath = inParam[1]
    loggerOutputOffset = inParam[2]
    rzStart = inParam[3]
    rzStop = inParam[4]
    rzSamples = inParam[5]
    rzFreq = inParam[6]
    convertTask:Multithread.Task = inParam[7]
    resampleTask:Multithread.Task = inParam[8]

    # Data Chunks
    sectorSize = 512
    headerSize = 1024
    # Exctract logger variables
    filename = logger['filePath']
    numSamples = logger['file']['numSamples']
    numSectors = logger['file']['numSectors']
    samplesPerSector = logger['file']['samplesPerSector']
    accelUnit = int(logger['first']['accelUnit'])
    numChannels = int(logger['first']['channels'])

    # Open file and offset header
    file = open(filename, "rb")
    file.seek(0, 2)
    fileSize = file.tell()
    file.seek(headerSize)
    chunkSize = 100  # Number of sectors to read
    headerOffset = headerSize

    numSectors = 0
    if fileSize >= headerSize:
        numSectors = (fileSize - headerSize) // 512

    # Read data sectors and populate as required
    #values = bytearray(numSamples * 8 * numChannels)
    #v2mem = memoryview(values)
    chunk = bytearray()
    toBeResampled = [[0] * numSectors * samplesPerSector for i in range(numChannels)]

    for sector in range(numSectors):
        if sector % chunkSize == 0:
            chunk = file.read(sectorSize * chunkSize)  # Read x sectors from file

        chunkOffset = sectorSize * (sector % chunkSize)

        dataSector = CWA.cwa_data(chunk[chunkOffset: chunkOffset + sectorSize], extractData=True)

        if (sector % (numSectors // 25) == 0):
            print("Logger", logger['header']['deviceId'], "at", round(100.0 * sector / numSectors, 1), "%")
            #Multithread.update_ID(convertTask.taskID, round(100.0 * sector / numSectors))

        sectorOffset = sector * samplesPerSector * 8

        # For each of the channels and each of the samples
        for chan in range(numChannels):
            for sample in range(samplesPerSector):
                startOffset = sectorOffset + chan * 8 * numSamples + sample * 8
                # Get data back from the file either accels, gyros or mag channels
                if (numChannels == 3):
                    toBeResampled[chan][sector * samplesPerSector + sample] = (dataSector['samplesAccel'][sample][chan])
                    # print(chan, dataSector['samplesAccel'][sample][chan], toBeResampled[chan][sample])
                elif (numChannels > 3):
                    if (chan < 3):
                        toBeResampled[chan][sector * sectorSize + sample] = (dataSector['samplesAccel'][sample][chan])
                    elif (chan < 6):
                        toBeResampled[chan][sector * sectorSize + sample] = (dataSector['samplesGyro'][sample][chan - 3])
                    elif (chan < 9):
                        toBeResampled[chan][sector * sectorSize + sample] = (dataSector['samplesMag'][sample][chan - 6])

    print("num samples", numSamples)

    dataSet: DataSet = Resampler.DataSet(logger['first']['timestamp'], logger['last']['timestamp'],
                                         numSamples, numChannels, toBeResampled)

    # Resample in here
    values = Resampler.resample(rzStart, rzStop, rzFreq, dataSet, resampleTask)

    # Write out this contiguous block to the file, for the nChannels on this logger
    print("Writing channel data for file", filePath)
    f = open(filePath, "rb+")
    f.seek(loggerOutputOffset)
    f.write(values)
    f.flush()
    f.close()

    print("Completed", filename)
    return 0