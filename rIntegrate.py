# Author Adrian Shedley
# Date 14 July 2020
# Rapid integrator for the CWA-to-BIN program

from scipy.integrate import cumtrapz
import numpy as np


def integrate_data(data, frequency=800.0, out_units='m/s'):
    dx = 1/frequency

    # Do an integration by summation of trapeziods. This must be done manually as the scipy library is too resource
    #   intensive.

    shape = data.shape
    running_sum = np.zeros(shape, dtype='float64')

    scale_factor = 9.81
    if scale_factor == 'mm/s':
        scale_factor *= 1000

    running_sum[:,:-1] = ((scale_factor * dx) / 2.0) * (data[:,:-1] + data[:,1:])
    #running_sum[:, 0] = 0

    #for i in range(1, shape[1]-1):
    #    running_sum[:,i] = (dx / 2.0) * (data[:, i] + data[:, i + 1])

    running_sum = np.cumsum(running_sum, axis=1)
    return running_sum