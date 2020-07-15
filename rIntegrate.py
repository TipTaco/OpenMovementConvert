# Author Adrian Shedley
# Date 14 July 2020
# Rapid integrator for the CWA-to-BIN program. Performs faster than the equivalent scipy cumtrapz method

import numpy as np


def integrate_data(data, frequency=800.0, out_units='mm/s'):
    dx = 1/frequency

    # Create a array to hold the running_sum
    shape = data.shape
    running_sum = np.zeros(shape, dtype='float64')

    # Define the scale factor to either do m/s or mm/s from g
    # While this does not take in g directly, the value of measurement is some scalar value times g and will be removed
    #   when the file is written
    scale_factor = 9.81*1000
    if scale_factor == 'm/s':
        scale_factor /= 1000

    # Trapezoidal area calculation for each point
    running_sum[:,:-1] = ((scale_factor * dx) / 2.0) * (data[:,:-1] + data[:,1:])

    # Summation of the trapezoids to perform a pseudo integral. Axis=1 to go along each channel individually
    running_sum = np.cumsum(running_sum, axis=1)
    return running_sum
