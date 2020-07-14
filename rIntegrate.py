# Author Adrian Shedley
# Date 14 July 2020
# Rapid integrator for the CWA-to-BIN program

from scipy.integrate import cumtrapz


def integrate_data(data, frequency=800.0):
    dx = 1/frequency
    return cumtrapz(data, dx=dx)