# Author Adrian Shedley

import time
import tkinter as tk
from tkinter import ttk

import numpy as np
from scipy import signal

import rIntegrate
import rInterpolate
import rFilter

from matplotlib import pyplot as plt
import scipy.fftpack

# Code goes here

base = "F:/Adrian/1822_FMG_Cloudbreak/LoggerFiles"
files = ["/6011027_0000000001.cwa"]

dummy = {}
dummy['first'] = {}
dummy['first']['samplesPerSector'] = 80

startTime = time.time()

N = 1000
f = 800.0
T = 1/f

x = np.linspace(0.0, N*T, N)
y = x[x < 100].reshape(1, N)


yf = rFilter.highpass_filter(y, order=4, in_freq=800.0, cutoff_freq=10.0)
Y = rIntegrate.integrate_data(yf, frequency=800.0)
YF = rFilter.highpass_filter(Y, order=4, in_freq=800.0, cutoff_freq=10.000)

plt.figure(3)
plt.plot(x, y[0])
plt.plot(x, yf[0])
#plt.show()

plt.figure(4)
plt.plot(x, Y[0])
plt.plot(x, YF[0])
#plt.show()

y = np.sin(50.0 * 2 * np.pi * (np.sqrt(x))).reshape(1, N)


print(x.shape)
print(y.shape)

x_fft = np.linspace(0.0, 1.0/(2.0*T), N//2)

filtered = rFilter.lowpass_filter(y, order=8, in_freq=800.0, cutoff_freq=100.0)
filtered_high = rFilter.highpass_filter(y, order=9, in_freq=800.0, cutoff_freq=1.0)

y_fft = scipy.fftpack.fft(y[0])
filtered_fft = scipy.fftpack.fft(filtered[0])
filtered_high_fft = scipy.fftpack.fft(filtered_high[0])

plt.figure(1)
ax1 = plt.subplot(211)
ax1.plot(x, y[0])
ax1.plot(x, filtered[0])
ax1.plot(x, filtered_high[0])
ax1.set_title('Signals')
ax2 = plt.subplot(212)
ax2.plot(x_fft, 20 * np.log10(2.0/N * np.abs(y_fft[:N//2])))
ax2.plot(x_fft, 20 * np.log10(2.0/N * np.abs(filtered_fft[:N//2])))
ax2.plot(x_fft, 20 * np.log10(2.0/N * np.abs(filtered_high_fft[:N//2])))
ax2.set_title('FFT')
#plt.show()


highpass_freq = 1.0
cutoff_freq = highpass_freq/(f/2.0)
print(cutoff_freq)
sos = signal.butter(8, cutoff_freq, btype='highpass', analog=False, output='sos')
#sos = signal.cheby2(9, 40, cutoff_freq, btype='highpass', analog=False, output='sos')

w, h = signal.sosfreqz(sos, worN=4096*8)

plt.figure(5)
plt.title("Filter freq response")
plt.plot(w, 20 * np.log10(abs(h)), 'b')
plt.ylabel('Amplitude [dB]', color='b')
plt.xlabel('Frequency [rad/sample]')
plt.show()


# Freq response part
'''nf = 100.0
lowp = (nf / (f/2)) * 0.98

b = firwin(8, lowp, window='hamming' , pass_zero='lowpass')
w, h = scipy.signal.freqz(b)

plt.figure(2)
plt.title("Filter freq response")
plt.plot(w, 20 * np.log10(abs(h)), 'b')
plt.ylabel('Amplitude [dB]', color='b')
plt.xlabel('Frequency [rad/sample]')
plt.show()'''

'''# Tk scrollbar example
parent = tk.Tk()

canvas = tk.Canvas(parent)
scroll_y = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)

frame = tk.Frame(canvas)
# group of widgets


for i in range(20):
    tk.Label(frame, text='label %i' % i).pack(side=tk.TOP)
    ttk.Progressbar(frame).pack(side = tk.LEFT)

# put the frame in the canvas
canvas.create_window(0, 0, anchor='nw', window=frame)
# make sure everything is displayed before configuring the scrollregion
canvas.update_idletasks()

canvas.configure(scrollregion=canvas.bbox('all'),
                 yscrollcommand=scroll_y.set)

canvas.pack(fill='both', expand=True, side='left')
scroll_y.pack(fill='y', side='right')

parent.mainloop()'''



'''
for file in files:
    masterArray = rCWA.readToMem(base+file, dummy)  # rCWA.method1(base + file)
    #rCWA.writeToFile(masterArray, base+file, 0, sizeBytes=4)

finishTime = time.time()
deltaT = finishTime - startTime
print(deltaT)


x = np.array([(1.0, 4.0, 6.5, ), (2.0, -1.0, 20.0), (4.0, -4.0, 4.0), (7.0, -6.0, 20.0), (-100.0, -100.0, 200.0)], dtype=[('X', '<i2'), ('Y', '<i2'), ('Z', '<i2')])
print(x)
print(x['X'])
print(x.shape)

y= x.view(np.int16).reshape(x.shape + (-1,)).transpose()
print(y)
print(y.shape)
print(y[0])

x = np.arange(0, 1000, 1)
y = np.arctan(np.sin(x/10)+1).reshape((1, len(x)))



V = rInterpolate.interp1d(y, 0, 1000, 100, 900, 1.9)

print(y[0].max())
print(V[0].max())
'''

