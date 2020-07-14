# Author Adrian Shedley
# Date 14 July 2020
# This file will create and apply the filtering as required in a FIR format from scipy.

import numpy as np

import scipy as sp
from scipy.signal import firwin
from scipy.signal import oaconvolve


def fir_lowpass(order, cutoff_freq_percent=0.98):
    return firwin(order+1, cutoff_freq_percent, window='hamming', pass_zero='lowpass')


def lowpass_filter(data, order=80, in_freq=800.0, cutoff_freq=100.0):
    offset_freq = ((8/order) * cutoff_freq) / 2.0
    # Modify the cutoff such that the frequency content is mostly gone by the desired freq
    cutoff_freq -= offset_freq
    lowp_freq = (cutoff_freq / (in_freq/2)) * 0.98
    b = fir_lowpass(order, lowp_freq)
    return oaconvolve(data, b[np.newaxis, :], mode='same') # Faster convolve



