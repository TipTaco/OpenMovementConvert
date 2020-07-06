# Author Adrian Shedley

import time
import tkinter as tk
from tkinter import ttk

import numpy as np
import rInterpolate

# Code goes here

base = "F:/Adrian/1822_FMG_Cloudbreak/LoggerFiles"
files = ["/6011027_0000000001.cwa"]

dummy = {}
dummy['first'] = {}
dummy['first']['samplesPerSector'] = 80

startTime = time.time()

# Tk scrollbar example
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

parent.mainloop()



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

