# Author Adrian Shedley

import rapidCWA as rCWA


# Code goes here

base = "F:/Adrian/1822_FMG_Cloudbreak/LoggerFiles"
files = ["/6011027_0000000001.cwa"]

dummy = {}
dummy['first'] = {}
dummy['first']['samplesPerSector'] = 80

for file in files:
    masterArray = rCWA.readToMem(base+file, dummy)  # rCWA.method1(base + file)
    rCWA.writeToFile(masterArray, base+file, 0, sizeBytes=4)