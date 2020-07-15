# Author Adrian Shedley
# Date 14 July 2020
# This file will create and apply the filtering as required in a FIR format from scipy.

import numpy as np

# import scipy as sp
from scipy.signal import firwin, butter
from scipy.signal import filtfilt, sosfiltfilt


def _butter_lowpass(order, cutoff_freq):
    return butter(order, Wn=cutoff_freq, btype='lowpass', analog=False, output='ba')

def _butter_highpass(order, cutoff_freq):
    return butter(order, Wn=cutoff_freq, btype='highpass', analog=False, output='sos')


def lowpass_filter(data, order=8, in_freq=800.0, cutoff_freq=100.0):

    offset_freq = (0.1 * cutoff_freq) / 2.0

    # Modify the cutoff such that the frequency content is mostly gone by the desired freq
    cutoff_freq -= offset_freq
    lowp_freq = (cutoff_freq / (in_freq/2)) * 0.98
    b = _butter_lowpass(order, lowp_freq)

    # Perform the filtering using Scipy, expensive operation
    return filtfilt(b[0], b[1], data)


def highpass_filter(data, order=8, in_freq=800.0, cutoff_freq=100.0):
    highp_freq = (cutoff_freq / (in_freq/2))
    print("Highpass cutoff", highp_freq)
    sos = _butter_highpass(order, highp_freq)

    # Perform the filtering using Scipy, expensive operation
    return sosfiltfilt(sos, data)

