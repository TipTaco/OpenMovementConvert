# Test environment to confirm the working status of the file converter for converting files.
# Author: Adrian Shedley with external code used from the open source OMGUI github for AX3
# Date Created: 20 May 2020
# Last Modified 1 July 2020 - Modifications to speed up conversion by 40x

import cwa_metadata as CWA   # cwa file type converter
import rapidCWA as rCWA  # Rapid cwa file loader
import bin_data as BIN  # bin file type converter

import os

from struct import *

import tkinter as tk
from tkinter import filedialog

import time

from multiprocessing import Pool
from multiprocessing import freeze_support

import ResampleController as ResCon
import Resampler as Resampler

import Multithread as Multithread
from datetime import datetime

# Global Vars
NUM_THREADS: int = 4
MULTITHREAD: bool = True
RESAMPLE: bool = True
RESAMPLE_FREQ: float = 800.0
OUTPUT_DATA_WIDTH: int = 4

def main():
    """ Main function decl. This will be the position in file that is run to start with.

        First a selection of openMovement .cwa files are selcted by the user,
        Then an output file name (.tst) is specified.
        The channels are then computed and concatenated. """

    # get the user to specify at least one .cwa file
    cwaInputPaths = open_multiple_files()
    if len(cwaInputPaths) == 0:
        print("Error, terminating, no files selected")
        return

    # temp
    for loggerFile in cwaInputPaths:
        datablock = CWA.cwa_info(loggerFile, extract=True)
        print(datablock)

    # Get the user to specify at least one output file
    binOutputPath = save_file_name()
    if binOutputPath == "":
        print("Error, terminating")
        return

    # Run the conversion, first on the header, then on the files
    compute_multi_channel(cwaInputPaths, binOutputPath)


def open_multiple_files():
    """ Open a user dialog to get multiple file inputs """
    # List of filenames
    filePaths = []

    # File open stuff
    root = tk.Tk()
    root.withdraw()

    # Ask the user to select one or more files with the right type
    files = filedialog.askopenfiles(filetypes=[("CWA files", ".cwa")])
    for file in files:
        filePaths.append(file.name)  # Take the name of the file, and save it
        file.close() # Close the file stream

    return filePaths

def save_file_name():
    # File open stuff
    root = tk.Tk()
    root.withdraw()

    # Ask the user to specify a save file name
    file = filedialog.asksaveasfilename(filetypes=[("TST files", ".tst")])
    return file

def compute_multi_channel(listLoggerFiles, outputFile, resample=RESAMPLE, resampleFreq=RESAMPLE_FREQ, multithread=MULTITHREAD, nThreads:int=int(NUM_THREADS), trimStart=0, trimEnd=0, demoRun = False, byteWidth=OUTPUT_DATA_WIDTH):
    """ Operates on many
    Each physical logger has three accelerometer axis and as such will command THREE channels
    """
    # Order the logger files in numerical Order
    freeze_support()
    listLoggerFiles.sort()

    # Each file is a different logger, get and add its three channels
    loggers = []
    channel_list = []

    # Some limit holders to determine out of place loggers (too short duration, diff sample rate etc)
    samples = {"max":0, "maxLogger":"", "min":1e100, "minLogger":"", "average":0.0, "numLoggers":0}
    rate = {"max":0, "maxLogger":"", "min":1e100, "minLogger":"", "average":0.0, "numLoggers":0}
    startTime = {"max":0, "maxLogger":"", "min":1e100, "minLogger":"", "average":0.0, "numLoggers":0}
    stopTime = {"max":0, "maxLogger":"", "min":1e100, "minLogger":"", "average":0.0, "numLoggers":0}
    channels = {"max": 0, "maxLogger": "", "min": 1e100, "minLogger": "", "average": 0.0, "numLoggers": 0}

    for loggerPath in listLoggerFiles:
        # Get the header, file info, and first and last sectors or each logger
        loggerData = CWA.cwa_info(loggerPath, extract=True)
        # Add the file path to the summary set
        loggerData['filePath'] = loggerPath
        # Add the loggerData to the list of loggers
        loggers.append(loggerData)

        # Unused currently, perform some min, max, mean calculations across all loggers
        update_dictionary(loggerPath, loggerData['file']['numSamples'], samples)
        update_dictionary(loggerPath, loggerData['file']['meanRate'], rate)
        update_dictionary(loggerPath, loggerData['first']['timestamp'], startTime)
        update_dictionary(loggerPath, loggerData['last']['timestamp'], stopTime)
        update_dictionary(loggerPath, loggerData['first']['channels'], channels)

        # The the stats of the loggers (min max, start, end)
        #print(loggerData)

    #summary = {"sampels":samples, "rate":rate, "channels":channels, "startTime":startTime, "stopTime":stopTime}

    # Perform checks and conditions to eliminate loggers who fall outside the appropriate range (Unused)
    if logger_out_of_range(10000, samples): print("Samples out of range", samples)
    if logger_out_of_range(20, rate): print("Samlping freq. out of range", rate)
    if logger_out_of_range(10000, startTime): print("start time out of range", startTime)
    if logger_out_of_range(10000, stopTime): print("End time out of range", stopTime)
    if logger_out_of_range(1, stopTime): print("End time out of range", channels)

    # Get resample ranges
    #print(startTime)
    #print(stopTime)
    (rzStart, rzStop, rzSamples) = Resampler.get_range(startTime, stopTime, resampleFreq, trimStart, trimEnd)

    if (demoRun):
        return (rzStart, rzStop, rzSamples)

    # Now generate the BIN header file for all the good (in range) loggers
    ##TODO eliminate bad or out of range loggers
    # Number of channels, 1 for each accel axis in each logger
    numChannels = len(listLoggerFiles) * int(channels['max'])
    numsamples = samples['min']

    # Write each of the channels into the channel list (for the BIN headers)
    axis = ['X', 'Y', 'Z']  # Update this if the logger has more than 3 channels to extract
    if channels['max'] == 6: axis = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
    if channels['max'] == 9: axis = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz", "Mx", "My", "Mz"]

    loggerOffsets = []
    loggerOffsets.append(0)

    for logger in loggers:
        # Logger stats
        loggerId = str(logger['header']['deviceId'])
        sessionId = str(logger['header']['sessionId'])
        sampleRate = str(logger['file']['meanRate'])
        numSamples = logger['file']['numSamples']
        startTime = logger['first']['timestamp']
        endTime = logger['last']['timestamp']
        numChannelsPerLogger = channels['max']

        if (resample):
            sampleRate = resampleFreq
            numSamples = rzSamples
            startTime = rzStart
            stopTime = rzStop

        # generate a Channel object for each channel
        for i in range(numChannelsPerLogger):
            channelName = loggerId + "_" + sessionId + "_" + axis[i]
            channel_object = BIN.Channel(loggerPath, channelName, "comment", loggerId, sessionId, numSamples, sampleRate, startTime, endTime)
            channel_list.append(channel_object)

        # When writing out the data file, need to know exact position of data (either scaled or not)
        loggerOffsets.append(loggerOffsets[-1] + numSamples * numChannelsPerLogger * byteWidth)
        #print("last offset", loggerOffsets[-1])

    # Manipulate file paths
    base = os.path.basename(outputFile)
    base = os.path.splitext(base)[0]
    dirname = os.path.dirname(outputFile)

    comment = "Resampling "
    if (resample):
        comment += "on at " + str(resampleFreq) + "Hz"
    else: comment += "off."
    (header, channelHeaders) = BIN.generate_BIN(base, comment, channel_list, byteWidth)

    print("Saving output file to", dirname + "/")

    # Write the file header and channel headers
    outputPath = dirname + "/" + base + ".bin"
    f = open(outputPath, "wb")
    f.write(header)
    f.write(channelHeaders)
    lastFilePos = f.tell()
    f.flush()
    f.close()

    # Multithreading disabled for now - Dropping in rapidCWA methods

    startTime = time.time()

    for i, logger in enumerate(loggers):
        fp = logger['filePath']
        print("")  # Blank Display Line
        masterArray = rCWA.readToMem(fp, loggerInfo=logger, cols=axis)
        # TODO add in resampling here
        offset = lastFilePos + loggerOffsets[i]
        rCWA.writeToFile(masterArray, filePath=outputPath, loggerInfo=logger, offsetBytes=offset, sizeBytes=byteWidth, cols=axis)

    deltaT = time.time() - startTime
    print("\n Completed in", round(deltaT, 2), "s")

    """
    # Make a processing pool
    pool = None
    if (multithread == True):
        pool = Pool(processes=nThreads)

    loggerJobs = []
    for i,logger in enumerate(loggers):
        taskConvertObj = Multithread.Task("Convert " + str(logger['header']['deviceId']), i, "CONVERT")
        Multithread.add_task(taskConvertObj)

        taskResampleObj = None
        if (resample):
            taskResampleObj = Multithread.Task("Resample " + str(logger['header']['deviceId']), i+len(loggers), "RESAMPLE")
            Multithread.add_task(taskResampleObj)

        # Build the loggerJobs to be sent to the resampler and converter
        loggerJobs.append([logger, outputPath, lastFilePos + loggerOffsets[i], rzStart, rzStop, rzSamples, resampleFreq, taskConvertObj, taskResampleObj])

    # Define processing method
    methodPointer = get_logger_data
    if (resample): methodPointer = ResCon.resample_logger_data

    if (multithread == True):
        values_out = pool.map(methodPointer, loggerJobs)
    else:  # perform serial
        for lg in loggerJobs:
            methodPointer(lg)

    if (multithread == True):
        pool.close()
    """

    if (resample):
        write_tst_resampled(dirname + "/" + base, channel_list)
    else:
        write_tst_convert(dirname + "/" + base, channel_list)

    print("\nSave Completed to", dirname + "/" + base)
    print("( These windows may now be closed )")


def update_dictionary(logger, stat, dict):

    count = dict['average'] * dict['numLoggers']
    numLoggers = dict['numLoggers'] + 1

    count += stat
    average = count / numLoggers
    dict['average'] = average
    dict['numLoggers'] = numLoggers

    if stat > dict['max']:
        dict['max'] = stat
        dict['maxLogger'] = logger
    if stat < dict['min']:
        dict['min'] = stat
        dict['minLogger'] = logger


""" A function to return if one of the values for all the loggers is out of bounds"""
def logger_out_of_range(absDiffLimit, dictionary):
    diff = max((dictionary['max'] - dictionary['average']), (dictionary['average'] - dictionary['min']))
    if diff > absDiffLimit:
        return True
    else:
        return False


def get_logger_data(inParam: []):
    logger = inParam[0]
    filePath = inParam[1]
    loggerOutputOffset = inParam[2]
    convertTask:Multithread.Task = inParam[7]

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
    values = bytearray(numSamples * 8 * numChannels)
    v2mem = memoryview(values)
    chunk = bytearray()

    for sector in range(numSectors):
        if sector % chunkSize == 0:
            chunk = file.read(sectorSize * chunkSize)  # Read x sectors from file

        chunkOffset = sectorSize * (sector % chunkSize)

        dataSector = CWA.cwa_data(chunk[chunkOffset : chunkOffset + sectorSize], extractData=True)

        if (sector % (numSectors // 25) == 0):
            print("Logger", logger['header']['deviceId'], "at", round(100.0 * sector/numSectors, 1), "%")
            #Multithread.update_ID(convertTask.taskID, round(100.0*sector/numSectors))

        sectorOffset = sector * samplesPerSector * 8

        toBeResampled = [[0] * samplesPerSector for i in range(numChannels)]

        # For each of the channels and each of the samples
        for chan in range(numChannels):
            for sample in range(samplesPerSector):
                startOffset = sectorOffset + chan * 8 * numSamples + sample * 8
                # Get data back from the file either accels, gyros or mag channels
                if (numChannels == 3):
                    v2mem[startOffset : startOffset + 8] = pack('d', dataSector['samplesAccel'][sample][chan])
                elif (numChannels > 3):
                    if (chan < 3):
                        v2mem[startOffset: startOffset + 8] = pack('d', dataSector['samplesAccel'][sample][chan])
                    elif (chan < 6):
                        v2mem[startOffset : startOffset + 8] = pack('d', dataSector['samplesGyro'][sample][chan-3])
                    elif (chan < 9):
                        v2mem[startOffset : startOffset + 8] = pack('d', dataSector['samplesMag'][sample][chan-6])



    # Write out this contiguous block to the file, for the nChannels on this logger
    print("Writing channel data for file", filePath)
    f = open(filePath, "rb+")
    f.seek(loggerOutputOffset)
    f.write(values)
    f.flush()
    f.close()

    print("Completed", filename)
    return 0


def write_tst_convert(filePath, channel_list):
    """Write out a test file for the raw conversion of data"""

    f = open(filePath + ".TST", "w")
    f.write("CATMAN TEST FILE\n")
    f.write("Comment = These channels were created and imported with the use of the CWA to BIN converter\n")
    f.write("Date Converted = " + datetime.today().strftime('%Y-%m-%d-%H:%M:%S') +"\n")

    for i,chan in enumerate(channel_list):
        f.write("Chan(" + str(i) + ") = " + chan.display() + "\n")
        f.write("Chan(" + str(i) + ") = " + chan.start_stop() + "\n")

    f.write("DATAFILE=" + str(filePath) + ".BIN")
    f.close()

def write_tst_resampled(filePath, channel_list):
    """ Write a test file for the resampled data, everything's start and stop and sample count is the same"""
    f = open(filePath + ".TST", "w")
    f.write("CATMAN TEST FILE\n")
    f.write("Number Samples per channel = " + str(channel_list[0].numSamples) + "\n")
    f.write("Sample Rate = " + str(round(channel_list[0].sampleRate,2)) + " Hz\n")
    f.write("Logging Start Time = " + CWA.timestamp_string(channel_list[0].startTime) + " UTC\n")
    f.write("Logging End Time = " + CWA.timestamp_string(channel_list[0].stopTime) + " UTC\n")

    for i,chan in enumerate(channel_list):
        f.write("Logger =" + chan.name + "\n")

    f.write("DATAFILE=" + str(filePath) + ".BIN")
    f.close()

def read_file_to_mem(filepath):
    f = open(filepath, "rb")
    fileBytes = f.read()
    f.close()
    return memoryview(fileBytes)


if __name__ == "__main__":
    main()
