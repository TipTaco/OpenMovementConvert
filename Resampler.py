# Author Adrian Shedley
# Creation date 26 May 2020
# date last Modified 26 May 2020
# Created for Engineering Dynamics Consultants
# Copyright 2020
#
# Purpose: Resample a set of given data points between two given times at a given rate

from struct import *
import Multithread

class DataSet:
    """ A dataset is for n channels from the same logger to be resampled all at once. """
    def __init__(self, startTime, stopTime, numSamples, numChannels, data):
        self.startTime = startTime
        self.stopTime = stopTime
        self.numSamples = numSamples
        self.numChannels = numChannels
        self.data = data  # Format list of lists


def resample(targetStart, targetStop, targetFreq, dataSet: DataSet, resampleTask:Multithread.Task):
    """ Resample a dataset either up or down to match the desired set"""

    # Variables named with an 'o' at the start are the original dataset parameters
    # variables named with a 't' at the start are the target parameters
    oStartTime = int(dataSet.startTime * 1e9)
    oStopTime = int(dataSet.stopTime * 1e9)
    oDuration = int(oStopTime - oStartTime)  # Time in whole nanosectons
    oSamples = dataSet.numSamples
    oFreq = dataSet.numSamples / (dataSet.stopTime - dataSet.startTime)
    oDt = int((1.0 / oFreq) * 1e9)   # Delta time in nanoseconds

    tStartTime = int(targetStart * 1e9)
    tStopTime = int(targetStop * 1e9)
    tFreq = targetFreq
    tSamples = int((tStopTime - tStartTime) * tFreq / 1e9)
    print(tStopTime, tStartTime, tFreq, tSamples)
    tDt = int((1.0 / tFreq) * 1e9)  # Target delta time in nanoseconds

    #print(dataSet.data)
    resampledLogger = bytearray(dataSet.numChannels * 8 * tSamples)

    #resampledLogger = bytearray(8 * tSamples) * dataSet.numChannels

    # Write the resamples output to an array of correct size
    sampleTime = tStartTime
    chanOffset = tSamples * 8

    print('Resample extremes', oStartTime, oStopTime, oSamples)
    print("Resample request", tStartTime, tStopTime, tSamples)

    for newSample in range(0, tSamples):
        newSampleTime = tStartTime + newSample * tDt
        #print(newSampleTime)

        oldSampleNumber = (newSampleTime - oStartTime) / oDt
        #print("newsample", newSample, "maps to old sample number", oldSampleNumber)

        lower = int(oldSampleNumber)
        upper = lower + 1
        alpha = oldSampleNumber - lower

        if (newSample % (tSamples // 25) == 0):
            print("Resample", round(100.0 * newSample / tSamples, 1), "% complete")
            #Multithread.update_ID(resampleTask.taskID, round(100.0 * newSample / tSamples))

        for channel in range(dataSet.numChannels):
            if (newSample == tSamples - 2):
                print(lower, upper)
            lowerV = dataSet.data[channel][lower]
            upperV = dataSet.data[channel][upper]
            deltaV = upperV - lowerV

            newV = lowerV + (alpha) * deltaV
            #print("imput val", newSample, "lower", lower, "lowerV", lowerV, "upper", upper, "upperV", upperV, "newV", newV)
            # print(channel, channel * chanOffset + newSample * 8, channel * chanOffset + newSample * 8 + 8)
            resampledLogger[(channel * chanOffset) + (newSample * 8) : (channel * chanOffset) + (newSample + 1) * 8] = pack('d', newV)

    print(len(resampledLogger))
    return resampledLogger

def get_range(min_max_start, min_max_stop, freq, trimStart, trimEnd):
    """Returns the tuple of values
            (resampleStart, resampleStop, numSamples)"""

    marginSeconds = 0.25 # (1.0 / freq) * 0.1

    # Calculate the trim on either end of the smallest range of samples for all loggers
    realStart = min_max_start["max"] + max(trimStart, 0)
    realStop = min_max_stop["min"] - marginSeconds - max(trimEnd, 0)

    duration = realStop - realStart
    if duration <= 0: print("Error: resample interval less than 0")

    # Whole integer number of samples
    numSamples = int(duration * freq) + 1

    # New stop time, a whole number of samples after startTime
    # Add half a wave so that the resample algo will get the same number of samples.
    realStop = realStart + (1.0 / freq) * numSamples + (1.0/freq) * 0.50

    return (realStart, realStop, numSamples)











