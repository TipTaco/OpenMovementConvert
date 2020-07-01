# Author Adrian Shedley
# Date : 20 May 2020
# Purpose of this file is to take in data and write that data to the Cantam BIN file as required.
# This file also contains the layout of a BIN file's Header, Channel headers and Data block.

# Catman BIN header file, NB: Short = 2 bytes, Int = 4 bytes, Long = 8 bytes

# - - Begin Header Block - -
# Short     FileID = the version of this catman file
# Int       Data_offset = the number of bytes until the Data block starts
# Short     L = Comment length in bytes
# L bytes   Comment
## Repeat these two lines 32 times for the RESERVED lines
# Short     L = length of reverved comment
# L Bytes   Reserved comment
#
# Short     N = number of channels
# Int       Special max channel limit (typically 0 and unused)
## Repeat this next line N (NumChannels) times
# Int       Offset for length of channel i
#
# Int       Special and unused line

# - - Begin Channel Header Block - -
## Repeat all of the following N (NumChannels) times
# Short     Channel location in catman database (0, 1, 2, ...)
# Int       Samples = Number of samples in this channel
# Short     Channel name length
# L Bytes   Channel name
# Short     Channel units name length
# L bytes   Channel Units
#  # BLOCK FOR FileID <= 5009 #
# Short     String Date length in bytes
# L Bytes   Date of measurement (String)
# Short     String time length in bytes
# L Bytes   Time of measurement (String)
# #END CASE#
# Short     String Channel Comment length in bytes
# L bytes   Channel comment
# Short     Format of channel eg 0 = numeric 1 = string  2 = binary object     (new since 5007)
# Short     Data width in Bytes  (for numeric format always = 8  for string >= 8)  (new since 5007)
# Double    (8 bytes) Date and time of measurement in NOW format (since 5010)
# Int       Size of the extended channel header in bytes
# 148 Bytes VB_DB_ChannelHeader -> special format discussed below with more channel information such as dt in ms and others, this is a contiguious block of data
# 1 Byte    LIN_MODE = Linearisation mode (0=none,1=Extern Hardware, 2=user scale, 3=Thermo J,.....) (new since 5009 = catman 3.1)
# 1 Byte    User scale type (0=Linearisation table, 1=Polynom, 2=f(x), 3=DMS Skalierung) (new since 5009 = catman 3.1)
# 1 Byte    NUM_LINS = Number of points for user scale linearisation table (nScalData) (new since 5009 = catman 3.1)
# Repeat netx line NumLins times
# 1 Byte    User linearisation scale entry
# Short     Thermo-Type (new since 5009 = catman 3.1)
# Short     String length of formula f(x)  = L (new since 5009 = catman 3.1)
# L bytes   Formula f(x)  (if L > 0 ) (new since 5009 = catman 3.1)
# Int       K = Size of struct DBSensorInfo (new since 5012 catman 5.0)  DBSensorInfo   Sensor type description and TID  (new since 5012 catman 5.0)
# K Bytes   Continguious block for the Sensor Info setup,

# - - Begin Data Block - -
# GOTO Data_offset position in file.
## Repeat NumChans (Number of channels) times
# l1 = ChannelLength(i) / 10000         The number of samples in this channel divided by 10000
# l2 = ChannelLength(i) MOD 10000       The number of samples in this channel modded by 10000
# If export format == 0 (Numeric)
#   For n = 1 to l1 -> data stored in one mega block


""" VB DB Chanheader as per the VBA file.
Private Type VB_DB_CHANHEADER
 T0 As Double                     'ACQ timestamp info (NOW format)
 dt As Double                      'ACQ delta t in ms
 SensorType As Integer        'IDS code of sensor type
 SupplyVoltage As Integer    'IDS code supply voltage
 FiltChar As Integer              'IDS code of filter characteristics
 FiltFreq As Integer              'IDS code of filter frequency
 TareVal As Single               'Current value in tare buffer
 ZeroVal As Single               'Current value in zero adjustment buffer
 MeasRange As Single         'IDS code of measuring range
 InChar(3) As Single             'Input characteristics (0=x1,1=y1,2=x2,3=y2)
 SerNo As String * 32           'Amplifier serial number
 PhysUnit As String * 8         'Physical unit (if user scaling in effect, this is the user unit!)
 NativeUnit As String * 8        'Native unit
 Slot As Integer                    'Hardware slot number
 SubSlot As Integer               'Sub-channel, 0 if single channel slot
 AmpType As Integer             'IDS code of amplifier type
 APType As Integer               'IDS code of AP connector type (MGCplus only)
 kFactor As Single                'Gage factor used in strain gage measurements
 bFactor As Single                'Bridge factor used in strain gage measurements
 MeasSig As Integer              'IDS code of measurement signal (e.g. GROSS, NET) (MGCplus only)
 AmpInput As Integer             'IDS code of amplifier input (ZERO,CAL,MEAS)
 HPFilt As Integer                  'IDS code of highpass filter
 OLImportInfo As Byte           'Special information used in online export file headers
 ScaleType As Byte              '0=Engineering units, 1=Electrical
 SoftwareTareVal As Single   'Software tare (zero) for channels carrying a user scale
 WriteProtected As Byte       ' If true, write access is denied
 NominalRange As Single      'CAV value
 CLCFactor As Single           'Cable length compensation factor (CANHEAD only)
 ExportFormat As Byte          '0=8-Byte Double, 1=4-Byte Single, 2=2-Byte Integer  FOR CATMAN BINARY EXPORT ONLY!
 Reserve As String * 10
End Type """

""" SensorInfo as block
Private Type DBSensorInfo
 InUse As Integer
 Description As String * 50
 TID As String * 16
End Type
"""

from struct import *
import cwa_metadata as CWA

class Channel():
    def __init__(self, logger, name, comment, deviceId, sessionId, numSamples, sampleRate, startTime, stopTime):
        # Nice to have variables
        self.logger = logger
        # used variables
        self.name = name
        self.comment = comment
        self.deviceId = deviceId
        self.sessionId = sessionId
        self.numSamples = numSamples
        self.startTime = startTime
        self.stopTime = stopTime
        self.sampleRate = sampleRate

    def display(self):
        return "Name: " + self.name + ", (" + self.comment + ") with " + str(self.numSamples) + " samples at " + str(self.sampleRate) + "Hz"

    def start_stop(self):
        return "Start " + CWA.timestamp_string(self.startTime) + "; Stopped " + CWA.timestamp_string(self.stopTime)


def pack_string(string):
    outbytes = bytearray()
    s = bytes(string, 'utf8')
    outbytes += pack("H", len(s))
    outbytes += pack(str(len(s)) + "s", s)
    return outbytes

# A function to take the data block created by the CWA convert and write the equivelant to a .BIN file
def generate_BIN(testName, testComment, channelInfos):
    header = bytearray()

    # The number of channels as per the first block
    numChannels = len(channelInfos)
    units = "g"

    # Internal head offset
    startChannelHeader = 0

    # - - Begin Header Block - - #
    header += pack("H", int(5012))                # Short     FileID = the version of this catman file
    header += pack("L", 934)                # Int       Data_offset = the number of bytes until the Data block starts

    header += pack_string(testComment)        # Short     L = Comment length in bytes
    # L bytes   Comment

    for i in range(0, 32):                  ## Repeat these two lines 32 times for the RESERVED lines
        header += pack_string(" ")               # Short     L = length of reverved comment then L Bytes   Reserved comment

    header += pack("H", numChannels)       # Short     N = number of channels
    header += pack("L", 0)        # Int       Special max channel limit (typically 0 and unused)

    startChannelHeader = len(header)
    for i in range(0, numChannels):        ## Repeat this next line N (NumChannels) times
        header += pack("L", 0)        # Int       Offset for length of channel i
    header += pack("L", 0)        # Int       Special and unused line

    # For each of the channels, build the channel header
    channelHeaders = bytearray()
    chanOffset = []

    # - - Begin Channel headers - - #
    for i in range(0, len(channelInfos)):
        ch = bytearray()

        channel = channelInfos[i]
        chanDevId = channel.deviceId
        chanName = channel.name
        chanRate = channel.sampleRate
        chanComment = channel.comment
        chanSamples = channel.numSamples

        # startTime in NOW format
        startTime = seconds_to_BIN_time(channel.startTime)

        ch += pack("H", i)    # Short     Channel location in catman database (0, 1, 2, ...)
        print(chanSamples)
        ch += pack("L", chanSamples)   # Int       Samples = Number of samples in this channel
        ch += pack_string(chanName)  # Short     Channel name length
        # L Bytes   Channel name
        ch += pack_string(units)    # Short     Channel units name length
        # L bytes   Channel Units

            #  # BLOCK FOR FileID <= 5009 #
            # Short     String Date length in bytes
            # L Bytes   Date of measurement (String)
            # Short     String time length in bytes
            # L Bytes   Time of measurement (String)
            # #END CASE#
        ch += pack_string(chanComment)   # Short     String Channel Comment length in bytes
        # L bytes   Channel comment
        ch += pack("H", 0)    # Short     Format of channel eg 0 = numeric 1 = string  2 = binary object     (new since 5007)
        ch += pack("H", 8)    # Short     Data width in Bytes  (for numeric format always = 8  for string >= 8)  (new since 5007)
        ch += pack("d", startTime)    # Double    (8 bytes) Date and time of measurement in NOW format (since 5010)
        ch += pack("L", 148)    # Int       Size of the extended channel header in bytes
        # 148 Bytes VB_DB_ChannelHeader -> special format discussed below with more channel information such as dt in ms and others, this is a contiguious block of data
        ch += pack('d', startTime) # T0 As Double                     'ACQ timestamp info (NOW format)
        ch += pack('d', 1000.0/float(chanRate)) # dt As Double                      'ACQ delta t in ms
        ch += pack("L", 0)  # SensorType As Integer        'IDS code of sensor type
        ch += pack("L", 0)  # SupplyVoltage As Integer    'IDS code supply voltage
        ch += pack("L", 0)  # FiltChar As Integer              'IDS code of filter characteristics
        ch += pack("L", 0)  # FiltFreq As Integer              'IDS code of filter frequency
        ch += pack("f", 0)  # TareVal As Single               'Current value in tare buffer
        ch += pack("f", 0)  # ZeroVal As Single               'Current value in zero adjustment buffer
        ch += pack("f", 0)  # MeasRange As Single         'IDS code of measuring range
        ch += pack("f", 0)  # InChar(3) As Single             'Input characteristics (0=x1,1=y1,2=x2,3=y2)
        ch += pack("32s", "".encode("UTF-8"))  # SerNo As String * 32           'Amplifier serial number
        ch += pack("8s", "".encode("UTF-8"))  # PhysUnit As String * 8         'Physical unit (if user scaling in effect, this is the user unit!)
        ch += pack("8s", "".encode("UTF-8"))  #        NativeUnit As String * 8        'Native unit
        ch += pack("L", 0)  # Slot As Integer                    'Hardware slot number
        ch += pack("L", i)  # SubSlot As Integer               'Sub-channel, 0 if single channel slot
        ch += pack("L", 0)  # AmpType As Integer             'IDS code of amplifier type
        ch += pack("L", 0)  # APType As Integer               'IDS code of AP connector type (MGCplus only)
        ch += pack("f", 0)  # kFactor As Single                'Gage factor used in strain gage measurements
        ch += pack("f", 0)  # bFactor As Single                'Bridge factor used in strain gage measurements
        ch += pack("L", 0)  # MeasSig As Integer              'IDS code of measurement signal (e.g. GROSS, NET) (MGCplus only)
        ch += pack("L", 0)  # AmpInput As Integer             'IDS code of amplifier input (ZERO,CAL,MEAS)
        ch += pack("L", 0)  # HPFilt As Integer                  'IDS code of highpass filter
        ch += pack("B", 0)  # OLImportInfo As Byte           'Special information used in online export file headers
        ch += pack("B", 0)  # ScaleType As Byte              '0=Engineering units, 1=Electrical
        ch += pack("f", 0)  # SoftwareTareVal As Single   'Software tare (zero) for channels carrying a user scale
        ch += pack("B", 0)  # WriteProtected As Byte       ' If true, write access is denied
        ch += pack("f", 0)  # NominalRange As Single      'CAV value
        ch += pack("f", 0)  # CLCFactor As Single           'Cable length compensation factor (CANHEAD only)
        ch += pack("B", 0)  # ExportFormat As Byte          '0=8-Byte Double, 1=4-Byte Single, 2=2-Byte Integer  FOR CATMAN BINARY EXPORT ONLY!
        #ch += pack("10s", "".encode("UTF-8"))  # Reserve As String * 10

        ch += pack("B", 0)  #    # 1 Byte    LIN_MODE = Linearisation mode (0=none,1=Extern Hardware, 2=user scale, 3=Thermo J,.....) (new since 5009 = catman 3.1)
        ch += pack("B", 0)  #    # 1 Byte    User scale type (0=Linearisation table, 1=Polynom, 2=f(x), 3=DMS Skalierung) (new since 5009 = catman 3.1)
        ch += pack("B", 0)  #    # 1 Byte    NUM_LINS = Number of points for user scale linearisation table (nScalData) (new since 5009 = catman 3.1)
        for i in range(0, 0):    # Repeat netx line NumLins times
            ch += pack("B", 0)  #    # 1 Byte    User linearisation scale entry
        ch += pack("H", 0)  #   # Short     Thermo-Type (new since 5009 = catman 3.1)
        ch += pack("H", 0)  #    # Short     String length of formula f(x)  = L (new since 5009 = catman 3.1)
        #ch += pack("s", 0)  #    # L bytes   Formula f(x)  (if L > 0 ) (new since 5009 = catman 3.1)

        ch += pack("L", 70)   # Int       K = Size of struct DBSensorInfo (new since 5012 catman 5.0)  DBSensorInfo   Sensor type description and TID  (new since 5012 catman 5.0)
        # K Bytes   Continguious block for the Sensor Info setup,
        ch += pack("L", 0)     # InUse As Integer
        ch += pack("50s", "[description]".encode("UTF-8"))    # Description As String * 50
        ch += pack("16s", str(chanDevId).encode("UTF-8"))   # TID As String * 16

        # Append this channel header to all the channel headers
        print('Channel', i, 'has header of size', len(ch))
        chanOffset.append(len(ch))
        channelHeaders += ch

    # Update the reference to the location of the actual sample data in the header
    fullheaderLength = len(header) + len(channelHeaders)
    header[2:6] = pack("L", fullheaderLength)

    # Update the reference to the channel header in the header
    for i in range(numChannels):
        if (i > 1):
            header[startChannelHeader + 4 * i: startChannelHeader + 4 * (i + 1)] = pack("L", len(header) + chanOffset[i-1])  # Int       Offset for length of channel i
        else:
            header[startChannelHeader + 4*i : startChannelHeader+ 4 * (i+1)] = pack("L", len(header))  # Int       Offset for length of channel i

    return (header, channelHeaders)

# A function to take the data block created by the CWA convert and write the equivelant to a .BIN file
def bin_write_header(data):
    header = bytearray()
    print(data['file']['name'])

    # The number of channels as per the first block
    numChannels = int(data['first']['channels'])
    numSamples = int(data['file']['numSamples'])
    # Cleaned name for file
    inputName = (data['file']['name'])[:-4]

    chanTags = ['x', 'y', 'z']
    #if (numChannels > 3): chanTags = ['Ax', 'Ay', 'Az', 'Gx', 'Gy', "Gz"]
    units = "g"

    startChannelHeader = 0

    # - - Begin Header Block - -
    header += pack("H", int(5012))                # Short     FileID = the version of this catman file
    header += pack("L", 934)                # Int       Data_offset = the number of bytes until the Data block starts

    header += pack_string("Comment: " + inputName)        # Short     L = Comment length in bytes
    # L bytes   Comment

    for i in range(0, 32):                  ## Repeat these two lines 32 times for the RESERVED lines
        header += pack_string(" ")               # Short     L = length of reverved comment
        # L Bytes   Reserved comment

    header += pack("H", numChannels)       # Short     N = number of channels
    header += pack("L", 0)        # Int       Special max channel limit (typically 0 and unused)

    startChannelHeader = len(header)
    for i in range(0, numChannels):        ## Repeat this next line N (NumChannels) times
        header += pack("L", 0)        # Int       Offset for length of channel i
            #
    header += pack("L", 0)        # Int       Special and unused line

    # Debug Outputs
    #print (header)
    #print ("header len", len(header))
    #print(unpack("L", header[2:6]))

    # startTime in NOW format
    startTime = seconds_to_BIN_time(float(data['first']['timestamp']))

    # For each of the channels, build the channel header
    channelHeaders = bytearray()

    for i in range(0, numChannels):
        ch = bytearray()
        chanName = str(inputName + "_" + chanTags[i])

        print(chanName, len(chanName))

        ch += pack("H", i+10)    # Short     Channel location in catman database (0, 1, 2, ...)
        ch += pack("L", numSamples)   # Int       Samples = Number of samples in this channel
        ch += pack_string(chanName)  # Short     Channel name length
        # L Bytes   Channel name
        ch += pack_string(units)    # Short     Channel units name length
        # L bytes   Channel Units

            #  # BLOCK FOR FileID <= 5009 #
            # Short     String Date length in bytes
            # L Bytes   Date of measurement (String)
            # Short     String time length in bytes
            # L Bytes   Time of measurement (String)
            # #END CASE#
        ch += pack_string(chanName)   # Short     String Channel Comment length in bytes
        # L bytes   Channel comment
        ch += pack("H", 0)    # Short     Format of channel eg 0 = numeric 1 = string  2 = binary object     (new since 5007)
        ch += pack("H", 8)    # Short     Data width in Bytes  (for numeric format always = 8  for string >= 8)  (new since 5007)
        ch += pack("d", startTime)    # Double    (8 bytes) Date and time of measurement in NOW format (since 5010)
        ch += pack("L", 148)    # Int       Size of the extended channel header in bytes
        print('Starting length', len(ch))
        # 148 Bytes VB_DB_ChannelHeader -> special format discussed below with more channel information such as dt in ms and others, this is a contiguious block of data
        ch += pack('d', startTime) # T0 As Double                     'ACQ timestamp info (NOW format)
        ch += pack('d', 1000.0/float(data['header']['sampleRate'])) # dt As Double                      'ACQ delta t in ms
        ch += pack("L", 0)  # SensorType As Integer        'IDS code of sensor type
        ch += pack("L", 0)  # SupplyVoltage As Integer    'IDS code supply voltage
        ch += pack("L", 0)  # FiltChar As Integer              'IDS code of filter characteristics
        ch += pack("L", 0)  # FiltFreq As Integer              'IDS code of filter frequency
        ch += pack("f", 0)  # TareVal As Single               'Current value in tare buffer
        ch += pack("f", 0)  # ZeroVal As Single               'Current value in zero adjustment buffer
        ch += pack("f", 0)  # MeasRange As Single         'IDS code of measuring range
        ch += pack("f", 0)  # InChar(3) As Single             'Input characteristics (0=x1,1=y1,2=x2,3=y2)
        ch += pack("32s", "".encode("UTF-8"))  # SerNo As String * 32           'Amplifier serial number
        ch += pack("8s", "".encode("UTF-8"))  # PhysUnit As String * 8         'Physical unit (if user scaling in effect, this is the user unit!)
        ch += pack("8s", "".encode("UTF-8"))  #        NativeUnit As String * 8        'Native unit
        ch += pack("L", 0)  # Slot As Integer                    'Hardware slot number
        ch += pack("L", i)  # SubSlot As Integer               'Sub-channel, 0 if single channel slot
        ch += pack("L", 0)  # AmpType As Integer             'IDS code of amplifier type
        ch += pack("L", 0)  # APType As Integer               'IDS code of AP connector type (MGCplus only)
        ch += pack("f", 0)  # kFactor As Single                'Gage factor used in strain gage measurements
        ch += pack("f", 0)  # bFactor As Single                'Bridge factor used in strain gage measurements
        ch += pack("L", 0)  # MeasSig As Integer              'IDS code of measurement signal (e.g. GROSS, NET) (MGCplus only)
        ch += pack("L", 0)  # AmpInput As Integer             'IDS code of amplifier input (ZERO,CAL,MEAS)
        ch += pack("L", 0)  # HPFilt As Integer                  'IDS code of highpass filter
        ch += pack("B", 0)  # OLImportInfo As Byte           'Special information used in online export file headers
        ch += pack("B", 0)  # ScaleType As Byte              '0=Engineering units, 1=Electrical
        ch += pack("f", 0)  # SoftwareTareVal As Single   'Software tare (zero) for channels carrying a user scale
        ch += pack("B", 0)  # WriteProtected As Byte       ' If true, write access is denied
        ch += pack("f", 0)  # NominalRange As Single      'CAV value
        ch += pack("f", 0)  # CLCFactor As Single           'Cable length compensation factor (CANHEAD only)
        ch += pack("B", 0)  # ExportFormat As Byte          '0=8-Byte Double, 1=4-Byte Single, 2=2-Byte Integer  FOR CATMAN BINARY EXPORT ONLY!
        #ch += pack("10s", "".encode("UTF-8"))  # Reserve As String * 10
        print('ending len', len(ch))

        ch += pack("B", 0)  #    # 1 Byte    LIN_MODE = Linearisation mode (0=none,1=Extern Hardware, 2=user scale, 3=Thermo J,.....) (new since 5009 = catman 3.1)
        ch += pack("B", 0)  #    # 1 Byte    User scale type (0=Linearisation table, 1=Polynom, 2=f(x), 3=DMS Skalierung) (new since 5009 = catman 3.1)
        ch += pack("B", 0)  #    # 1 Byte    NUM_LINS = Number of points for user scale linearisation table (nScalData) (new since 5009 = catman 3.1)
        for i in range(0, 0):    # Repeat netx line NumLins times
            ch += pack("B", 0)  #    # 1 Byte    User linearisation scale entry
        ch += pack("H", 0)  #   # Short     Thermo-Type (new since 5009 = catman 3.1)
        ch += pack("H", 0)  #    # Short     String length of formula f(x)  = L (new since 5009 = catman 3.1)
        #ch += pack("s", 0)  #    # L bytes   Formula f(x)  (if L > 0 ) (new since 5009 = catman 3.1)

        ch += pack("L", 70)   # Int       K = Size of struct DBSensorInfo (new since 5012 catman 5.0)  DBSensorInfo   Sensor type description and TID  (new since 5012 catman 5.0)
        # K Bytes   Continguious block for the Sensor Info setup,
        ch += pack("L", 0)     # InUse As Integer
        ch += pack("50s", "[description]".encode("UTF-8"))    # Description As String * 50
        ch += pack("16s", "[TID]".encode("UTF-8"))   # TID As String * 16

        # Append this channel header to all the channel headers
        print('Channel', i, 'has header of size', len(ch))
        channelHeaders += ch

    fullheaderLength = len(header) + len(channelHeaders)
    print(fullheaderLength)
    header[2:6] = pack("L", fullheaderLength)

    print("Start channel offset at:", startChannelHeader)

    for i in range(numChannels):
        header[startChannelHeader + 4*i : startChannelHeader+ 4 * (i+1)] = pack("L", len(header) + i * len(ch))  # Int       Offset for length of channel i
        print(header[startChannelHeader + 8*i : startChannelHeader+ 8 * (i+1)])

    print("header dataStart updated to:", unpack("L", header[2:6]))

    # next is the data part, need to create a big empty block of data for the entries to be overwritten into
    #values = bytearray(8*numChannels*numSamples)

    # Attmept to write the first data block to the data page

    numSectors = int(data['file']['numSectors'])
    samplesPerSector = data['file']['samplesPerSector']

    #for sector in range(numSectors)
    #for i in range(numChannels):
    #   for sample in range(samplesPerSector):
    #        print("packing", pack('d', data['first']['samplesAccel'][sample][i]), "into", i*8*numSamples + sample*8, ":", i*8*numSamples + sample*8 + 8)
    #        values[i*8*numSamples + sample*8: i*8*numSamples + sample*8 + 8] = pack('d', float(data['first']['samplesAccel'][sample][i]))

    #f = open(binFilePath + ".BIN", "wb")
    #f.write(header)
    #f.write(channelHeaders)
    #f.write(values)
    #f.close()

   # f = open(binFilePath + ".TST", "w")
    #f.write("CATMAN TEST FILE\n")
    #f.write("Numerical precision=8 Byte Float\n")
    #f.write("DATAFILE=" + binFilePath + ".BIN")
    #f.close()

    return (header, channelHeaders)

def seconds_to_BIN_time(seconds: float):
    """Input decimal seconds since the UNIX epoch 1970-Jan-01 00:00:00
        Return 64bit floating point time representing the number of days as the whole number, and fractional days
         since Dec 20 1899 23:59:59 """

    newOLE2_time = seconds / (24 * 60 * 60) # input seconds converted to whole days since unix epoch

    unixEpochInOLE2 = 70 * 365.0 + 19 # offset between OLE time format and unix epoch time format (1900 to 1970)

    outputTime = float(newOLE2_time + unixEpochInOLE2)

    return outputTime


    # 4676266870090211826 is 1584104203.000 in unixtime






