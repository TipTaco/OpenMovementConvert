# Author Adrian Shedley
# Date 3 July 2020
# Code modified from the scipy standard library's interp1d method in order to cut down on memory usage
#   This library would use 4-6x as much memory as the arrays that it was using
# Last modified 6 July 2020

import numpy as np

def interp1d(y, startVal, endVal, startInterp, endInterp, equispacing, kind='linear', fill_value=0):

        if y.ndim == 0:
            raise ValueError("the y array must have at least one dimension.")

        endInterp = endInterp if endInterp <= endVal else endVal
        startInterp = startInterp if startInterp >= startVal else startVal

        startVal = startVal
        endVal = endVal

        # The difference between samples on the input and output sequences
        inputDelta = (endVal-startVal) / y.shape[1]
        outputSamples = int((endInterp-startInterp)/equispacing) + 1

        if kind != 'linear':
            raise ValueError("The interpolation type must be linear")

        # print("Input stats:", startVal, endVal, inputDelta, y.shape)
        # print("Output stats:", startInterp, endInterp, outputDelta, outputSamples)

        print("Begin Resample")

        # We have an input time sampled data set starting at startVal seconds, ending at endVal seconds with inputDelta
        #       seconds between samples
        # We require an output time sampled data set that is a different frequency to the original set,
        #   start time startInterp seconds
        #   stop time: endInter seconds
        #   time between samples: outputDelta
        #   number of samples: outputSamples derived from (endInterp - startInterp) / outputDelta

        # Let N be number of samples and H be number of channels

        # Get a linear spacing array of the actual time in seconds for all output points required [start:end:delta]
        #   Shape = (N)
        outSeq = np.linspace(startInterp - startVal, endInterp - startVal, outputSamples) / inputDelta
        outSeq[outSeq >= y.shape[1]] = y.shape[1] - 2
        print("Resample output defined")

        # Get the whole integer index of the input sample for this linear interpolation
        #
        #   A *
        #         *C
        #               * B
        # We have points A and B from the input set, and require C.
        #   Shape = (N) as type INTEGER
        lo = outSeq.astype(np.int32)
        # Ensure that all values of the original input indexs are inbound.. this is a Hack and should be cleaned later

        # The B array is an array that is the difference between the point C and the point A in the time domain
        # It is the scale factor distance of C between A and B for all points in the new output
        #   Shape = (N)
        B = np.subtract(outSeq, lo)
        del outSeq

        print("Resample subvalues computed")

        # Interpolation calculation
        V = B * (y[:,(lo + 1)] - y[:,lo]) + y[:,lo]

        del lo
        del B

        print("Resample Complete")

        return V