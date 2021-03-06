# Test environment to confirm the working status of the file converter for converting files.
# Author: Adrian Shedley with external code used from the open source OMGUI github for AX3
# Date Created: 20 May 2020
# Last Modified 1 July 2020 - Modifications to speed up conversion by 40x
# Last Modified 6 July 2020 - Performance tweaks as well as linear interpolation method added.
import numpy as np

import cwa_metadata as CWA   # cwa file type converter
import rFilter
import rIntegrate
import rapidCWA as rCWA  # Rapid cwa file loader
import rInterpolate as rInter  # Rapid interpolator
import bin_data as BIN  # bin file type converter

import os.path
import time
from multiprocessing import freeze_support

import Resampler as Resampler

from datetime import datetime

# Global Vars
NUM_THREADS: int = 4
MULTITHREAD: bool = True
RESAMPLE: bool = True
RESAMPLE_FREQ: float = 800.0
OUTPUT_DATA_WIDTH: int = 4


def compute_multi_channel(listLoggerFiles, outputFile,
                          resample=RESAMPLE, resample_freq=RESAMPLE_FREQ,
                          lowpass=False, lowpass_freq=100.0,
                          integrate=False, high1_freq=1.0, high2_freq=1.0,
                          trimStart=0, trimEnd=0,
                          demoRun = False, byteWidth=OUTPUT_DATA_WIDTH, getFreq=False):
    """ Operates on many loggers
    Each physical logger has three (or more) accelerometer channels and as such will command THREE channels in the output
    @:param
        listLoggerFiles - Required : the .cwa logger files to be converted
        outputFile      - Required : the output file path with no extension

        demoRun = if the function will calculate only the resample range and then exit
        getFreq = if the function will calculate only the average sampling frequency of loggers and exit
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

    #summary = {"sampels":samples, "rate":rate, "channels":channels, "startTime":startTime, "stopTime":stopTime}

    # Perform checks and conditions to eliminate loggers who fall outside the appropriate range (Unused)
    if logger_out_of_range(10000, samples): print("[WARN]: Logger has samples out of range", samples)
    if logger_out_of_range(20, rate): print("[WARN]: Logger has sampling freq. out of range", rate)
    if logger_out_of_range(10000, startTime): print("[WARN]: Logger has start time out of range", startTime)
    if logger_out_of_range(10000, stopTime): print("[WARN]: Logger has end time out of range (>10000)", stopTime)
    if logger_out_of_range(1, stopTime): print("[WARN]: Logger has end time out of range (<1)", channels)

    # Quick and nasty way to get the rate of all the loggers, Next version should abstract out this code
    if getFreq:
        return (0, 0, 0, rate)

    # Get resample ranges
    (rzStart, rzStop, rzSamples) = Resampler.get_range(startTime, stopTime, resample_freq, trimStart, trimEnd)

    # Return this function early if the GUI requires a trim time only
    if demoRun:
        return (rzStart, rzStop, rzSamples, rate)

    # # Finished with the GUI helper potion, do the actual conversion heavy lifting # #

    # Set up the names of the logger channels depending on the number of channels of the max logger
    #   Currently not supported mixing and matching of loggers with different numbers of channels
    axis = ['X', 'Y', 'Z']  # Update this if the logger has more than 3 channels to extract
    if channels['max'] == 6: axis = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
    if channels['max'] == 9: axis = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz", "Mx", "My", "Mz"]

    loggerOffsets = []
    loggerOffsets.append(0)

    # For each of the loggers (.cwa files), get the header details and place it into a header for the BIN format
    for logger in loggers:
        # Logger stats
        loggerId = str(logger['header']['deviceId'])
        sessionId = str(logger['header']['sessionId'])
        sampleRate = str(logger['file']['meanRate'])
        numSamples = logger['file']['numSamples']
        beginTime = logger['first']['timestamp']
        endTime = logger['last']['timestamp']
        numChannelsPerLogger = channels['max']

        if resample:
            sampleRate = resample_freq
            numSamples = rzSamples
            beginTime = rzStart
            endTime = rzStop

        if integrate:
            logger

        # generate a Channel object for each channel
        for i in range(numChannelsPerLogger):
            channelName = loggerId + "_" + sessionId + "_" + axis[i]
            channel_object = BIN.Channel(loggerPath, channelName, "[no comment]", loggerId, sessionId, numSamples, sampleRate, beginTime, endTime)
            channel_list.append(channel_object)

        # When writing out the data file, need to know exact position of data (either scaled or not)
        extras = 0 if byteWidth != 2 else 16
        loggerOffsets.append(loggerOffsets[-1] + numSamples * numChannelsPerLogger * byteWidth + extras)

    # Manipulate file paths
    base = os.path.basename(outputFile)
    base = os.path.splitext(base)[0]
    dirname = os.path.dirname(outputFile)

    # Write the comment that will appear at the top of the catman test entry. This is a fast indication of if the
    #   set of channels were resampled or not
    comment = "Resampled"
    if resample:
        comment += " @" + str(resample_freq) + "Hz."
        if lowpass:
            comment += " Lowpass@" + str(lowpass_freq) + "Hz"
    else: comment = "Not resampled."

    if integrate:
        comment += " Integrated with highpass @" + str(high1_freq) + " and " + str(high2_freq) + "."

    units = 'g' if not integrate else 'mm/s'
    (header, channelHeaders) = BIN.generate_BIN(base, comment, channel_list, byteWidth, units=units)

    print("Saving output file to", dirname + "/")

    # Write the file header and channel headers
    outputPath = dirname + "/" + base + ".bin"
    f = open(outputPath, "wb")
    f.write(header)
    f.write(channelHeaders)
    lastFilePos = f.tell()  # Save the last position in file to continue writing data channels to
    f.flush()
    f.close()

    # Multithreading disabled for now -
    #   Instead use linear rapidCWA methods that are faster in series than old methods in parallel
    startTimeT = time.time()

    # # Data Processing, one logger at a time # #
    for i, logger in enumerate(loggers):    # New and improved reading, resampling and output
        fp = logger['filePath']
        print("")  # Blank Display Line
        # Read the data only for this logger to RAM array. This used to either resample or convert direct
        masterArray = rCWA.readToMem(fp, loggerInfo=logger, cols=axis)
        print(" Loaded ", masterArray.shape[0], " channels.", masterArray.shape[1], "samples each.")

        original_freq = float(logger['file']['meanRate'])

        # If the resample option was selected, first resample the data before outputting it to the file
        if resample:
            startVal = float(logger['first']['timestamp'])
            endVal = float(logger['last']['timestamp'])
            # Update the array in overwrite mode to contain the new resampled data
            if lowpass:
                print("Lowpass filtering at", lowpass_freq)
                masterArray = rFilter.lowpass_filter(masterArray, in_freq=original_freq, cutoff_freq=lowpass_freq)
            masterArray = rInter.interp1d(masterArray, startVal, endVal, rzStart, rzStop, 1 / resample_freq)

        if integrate:
            input_freq = original_freq if not resample else resample_freq
            print("Integrating at", input_freq, "Hz")
            print("Begin highpass Filtering at", high1_freq, "Hz")
            masterArray = rFilter.highpass_filter(masterArray, order=8, in_freq=input_freq, cutoff_freq=high1_freq)
            print("Begin integration")
            masterArray = rIntegrate.integrate_data(masterArray, frequency=input_freq)
            print("Begin highpass filtering at", high2_freq, "Hz")
            masterArray = rFilter.highpass_filter(masterArray, order=8, in_freq=input_freq, cutoff_freq=high2_freq)

        # Output the data for this logger to file and save the last position in file
        output_samples = masterArray.shape[1] if not resample else rzSamples
        lastFilePos = rCWA.writeToFile(masterArray, filePath=outputPath, loggerInfo=logger, offsetBytes=lastFilePos,
                                       sizeBytes=byteWidth, samples=output_samples)
        if len(loggers) > 1: print("\n COMPLETED", (i+1), "OF", len(loggers), "FILES")

    # Relay to the user how long the execution for all files took.
    deltaT = time.time() - startTimeT
    print("\nCompleted in", round(deltaT, 2), "s")

    # Write out the .TST file for catman to read. This file is only a pointer to the .BIN and is for the user.
    if resample:
        write_tst_resampled(dirname + "/" + base, channel_list)
    else:
        write_tst_convert(dirname + "/" + base, channel_list)

    print("\nSaved to", dirname + "/" + base + ".TST")
    print(" These windows may now be closed. ")


def update_dictionary(logger, stat, dict):
    """Update the logger dictionary for the given statistic"""
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


def logger_out_of_range(absDiffLimit, dictionary):
    """ A function to return if one of the values for all the loggers is out of bounds"""
    diff = max((dictionary['max'] - dictionary['average']), (dictionary['average'] - dictionary['min']))
    if diff > absDiffLimit:
        return True
    else:
        return False


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
