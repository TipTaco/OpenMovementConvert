# Author Adrian Shedley

import rapidCWA as rCWA
import time
import numpy as np
import rInterpolate
import matplotlib.pyplot as plt

# Code goes here

base = "F:/Adrian/1822_FMG_Cloudbreak/LoggerFiles"
files = ["/6011027_0000000001.cwa"]

dummy = {}
dummy['first'] = {}
dummy['first']['samplesPerSector'] = 80

startTime = time.time()

'''
for file in files:
    masterArray = rCWA.readToMem(base+file, dummy)  # rCWA.method1(base + file)
    #rCWA.writeToFile(masterArray, base+file, 0, sizeBytes=4)

finishTime = time.time()
deltaT = finishTime - startTime
print(deltaT)
'''

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

plt.plot(x, y[0])
plt.plot(np.arange(100, 900.001, 1.9), V[0])
plt.show()
