# Author Adrian Shedley
# Date 3 July 2020
# Code modified from the scipy standard library's interp1d method in order to cut down on memory usage
#   This library would use 4-6x as much memory as the arrays that it was using

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
        outputDelta = equispacing
        outputSamples = int((endInterp-startInterp)/equispacing) + 1

        # Force-cast y to a floating-point type, if it's not yet one
        #if not issubclass(y.dtype.type, np.inexact):
        #    y = y.astype(np.float_)

        if kind != 'linear':
            raise ValueError("The interpolation type must be linear")

        print("Input stats:", startVal, endVal, inputDelta, y.shape)
        print("Output stats:", startInterp, endInterp, outputDelta, outputSamples)

        linspac = np.linspace(startInterp, endInterp, outputSamples)

        lo = ((linspac - startVal) / inputDelta).astype(np.uint32)
        lo[lo>=y.shape[1]] = y.shape[1] - 2
        # print("lo", lo)

        # print("linspac", linspac)
        B = linspac - (startVal + lo * inputDelta)

        del linspac
        # print("B", B)

        V = y[:,lo] + (B/inputDelta) * (y[:,lo] - y[:,lo + 1])
        # print("V", V)
        del lo
        del B

        return V