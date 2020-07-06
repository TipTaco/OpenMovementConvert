# Author Adrian Shedley
# date 28 May 2020

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

import ConvertMain
import cwa_metadata as CWA

import os
import threading
from multiprocessing import freeze_support

PROCESS: str = 'CWA_to_BIN'
VERSION: str = 'v0.9'


class PrefForm():
    def __init__(self):
        self.root = tk.Tk()
        title = PROCESS + " " + VERSION
        self.root.title(title + ' - Conversion Preferences form')

        self.filePaths = []
        self.saveName: str = ""

        self.resample: bool = False
        self.resampleFreq: float = 800.0
        self.multithread: bool = False
        self.numThreads: int = 4
        self.byteWidth: int = 8
        self.loggerFrequency: float = 800.0

        # The main frame for the GUI
        self.masterFrame = tk.Frame(self.root)
        self.masterFrame.pack(anchor=tk.NW, fill=tk.BOTH, expand=True, side=tk.TOP, pady=1, padx=1)

        # Make top 't' and bottom 'b' content frames in the correct order
        # A rewrite would be nice here, but everything was done by hand and works as is for now
        self.topFrame = tk.Frame(self.masterFrame)
        self.topFrame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        self.b4 = tk.Frame(self.masterFrame)
        self.b4.pack(side=tk.BOTTOM, expand=True, fill=tk.X)
        self.b3 = tk.Frame(self.masterFrame)
        self.b3.pack(side=tk.BOTTOM, expand=True, fill=tk.X)
        self.bottomFrame = tk.Frame(self.masterFrame)
        self.bottomFrame.pack(fill=tk.X, side=tk.BOTTOM)

        # Each of these tX and bX blocks are a rung on the GUI and separated as such. A grid would work better for this
        self.t1 = tk.Frame(self.topFrame)
        self.t1.pack(anchor=tk.NW, side=tk.TOP)
        self.sep1 = ttk.Separator(self.topFrame)
        self.sep1.pack(side=tk.TOP, expand=True, fill=tk.X, padx=5, pady=5)

        self.t2 = tk.Frame(self.topFrame)
        self.t2.pack(anchor=tk.NW, side=tk.TOP, fill=tk.X)
        self.sep2 = ttk.Separator(self.topFrame)
        self.sep2.pack(side=tk.TOP, expand=True, fill=tk.X, padx=5, pady=5)

        self.t3 = tk.Frame(self.topFrame)
        self.t3.pack(anchor=tk.NW, side=tk.TOP, fill=tk.X)
        self.t4 = tk.Frame(self.topFrame)
        self.t4.pack(anchor=tk.NW, side=tk.TOP, fill=tk.X)
        self.t5 = tk.Frame(self.topFrame)
        self.t5.pack(anchor=tk.NW, side=tk.TOP, fill=tk.X)

        self.t5_1 = tk.Frame(self.topFrame)
        self.t5_1.pack(anchor=tk.NW, side=tk.TOP, fill=tk.X)
        self.sep6 = ttk.Separator(self.topFrame)
        self.sep6.pack(side=tk.TOP, expand=True, fill=tk.X, padx=5, pady=5)

        self.t6 = tk.Frame(self.topFrame)
        self.t6.pack(anchor=tk.NW, side=tk.TOP, expand=True, fill=tk.X)

        self.sepEnd = ttk.Separator(self.topFrame)
        self.sepEnd.pack(side=tk.TOP, expand=True, fill=tk.X, padx=5, pady=5)

        self.b1 = tk.Frame(self.bottomFrame)
        self.b1.pack(side=tk.TOP, expand=True, fill=tk.X)
        self.b2 = tk.Frame(self.bottomFrame)
        self.b2.pack(side=tk.BOTTOM)

        # Now add the actual GUI content
        # Instructions box
        self.instruction = tk.Label(self.t1, justify=tk.LEFT, text="Usage instructions: \n 1) Select logger files (.cwa)" +
                                    "\n 2) (Optional) Choose to resample at a frequency \n 3) Select processing options" +
                                    "\n 4) Select output file name and location \n 5) Press convert")
        self.instruction.pack(anchor=tk.W, pady=10, padx=10)

        #Input files selection one textbox one label
        self.inLabel = tk.Label(self.t2, width = 10, justify=tk.LEFT, text="Input Files")
        self.inLabel.pack(side=tk.LEFT, pady=5, padx=5)
        self.inDisplay = tk.Entry(self.t2, state=tk.DISABLED, text="Select files...", borderwidth=2)
        self.inDisplay.pack(side=tk.LEFT, pady=5, padx=5, fill=tk.X, expand=True)
        self.inButton = tk.Button(self.t2, width = 16, text="Browse", command=self.inBrowse, height = 1, borderwidth=2)
        self.inButton.pack(side=tk.LEFT, padx=5, pady=5)

        # Resample button and text and frequency selector
        state = tk.NORMAL if self.resample else tk.DISABLED
        self.frequencyText = tk.StringVar()
        self.frequencyText.set('---')
        self.resCheck = tk.Checkbutton(self.t3, width = 22, text="Resample", justify=tk.LEFT, command=self.getLoggerRate)
        self.resCheck.pack(anchor=tk.NW, side = tk.LEFT, pady = 5, padx =5)
        self.resFreq = tk.Label(self.t3, textvariable=self.frequencyText)
        self.resFreq.pack(anchor=tk.NW, side=tk.LEFT, pady=5, padx=5)
        #defaultFreq = tk.DoubleVar(value=self.resampleFreq)
        #self.resFreqInput = tk.Spinbox(self.t3, width = 10, from_=0.5, to_=10000.0, increment=1.0, borderwidth=2, textvariable=defaultFreq, state=state)
        #self.resFreqInput.pack(anchor=tk.NW, side=tk.LEFT, pady=5, padx=5)
        self.resHz = tk.Label(self.t3, text="Hz")
        self.resHz.pack(side=tk.LEFT)

        # Trim selection options
        startT = ""; stopT =""
        self.trimStartLabel = tk.Label(self.t4, text="Trim Start (decimal minutes)  ", width = 25, justify=tk.RIGHT)
        self.trimStartLabel.pack(anchor=tk.NW, padx=5, pady=5, side=tk.LEFT)
        self.trimStartInput = tk.Entry(self.t4, text="decimal minutes", width = 20, borderwidth=2, textvariable=startT)
        self.trimStartInput.insert(0, "0")
        self.trimStartInput.config(state=state)
        self.trimStartInput.pack(padx=5, pady=5, side=tk.LEFT)

        self.trimEndLabel = tk.Label(self.t5, text="Trim Finish (decimal minutes)", width = 25, justify=tk.RIGHT)
        self.trimEndLabel.pack(anchor=tk.NW, padx=5, pady=5, side=tk.LEFT)
        self.trimEndInput = tk.Entry(self.t5, text="decimal minutes", width = 20, borderwidth=2, textvariable=stopT)
        self.trimEndInput.insert(0, "0")
        self.trimEndInput.config(state=state)
        self.trimEndInput.pack(padx=5, pady=5, side=tk.LEFT)

        # show sample output for time
        self.trimButton = tk.Button(self.t5_1, text="Compute trim", width=24, height=3, state = state, command=self.testResampleRange)
        self.trimButton.pack(anchor=tk.NW, padx=5, pady=5, side=tk.LEFT)
        self.trimText = tk.Label(self.t5_1, text="Start Time:     N/A\nFinish Time:   N/A\nSamples:        N/A", justify=tk.LEFT)
        self.trimText.pack(anchor=tk.NW, padx=5, pady=5, side=tk.LEFT)

        # Parallelism options - DISABLED for now
        '''multi = self.multithread
        state = tk.NORMAL if self.multithread else tk.DISABLED
        self.paraWarn = tk.Label(self.t6, text="WARNING:\n  Only set the threads to number of processing cores or less." +
                                               "\n  Using more cores in combination with large input files may cause instablity. " +
                                               "\n   - Field Laptop = 2/4 Cores \n   - Workstation = 8 Cores", fg="red", justify=tk.LEFT)
        self.paraWarn.pack(side=tk.TOP, anchor=tk.NW, pady=10, padx=10)
        self.paraCheck = tk.Checkbutton(self.t6, width = 22, text = "Multithread", variable=multi, command=self.changeTogglePara)
        self.paraCheck.pack(anchor=tk.NW, side = tk.LEFT, pady = 5, padx =5)
        defaultCores = tk.IntVar(value=int(self.numThreads))
        self.paraCores = tk.Spinbox(self.t6, width = 10, from_=1, to_=64, increment=1, state=state, textvariable=defaultCores, borderwidth = 2)
        self.paraCores.pack(anchor=tk.NW, side=tk.LEFT, pady=5, padx=5)'''

        # Instead place the byte width selector here
        self.outputDesc = tk.Label(self.t6, text="Catman Ouput File (.BIN) format: \n" +
                                                 "  8 Byte Spacing (Full size)     4GB output = 1GB input\n" +
                                                 "  4 Byte Spacing (Half Size)     2GB output = 1GB input\n" +
                                                 "  2 Byte Spacing (Quater Size)   1GB output = 1GB input (May take 20% longer to generate)",
                                   fg="blue", justify=tk.LEFT)
        self.outputDesc.pack(side=tk.TOP, anchor=tk.NW, padx= 10, pady=5)
        # Dropdown to select the number of bytes to put in the output file
        self.bytesVar = tk.StringVar(self.root)
        self.bytesVar.set("8 Byte")
        self.byteDropDown = tk.OptionMenu(self.t6, self.bytesVar, "8 Byte", "4 Byte", "2 Byte", command=self.byteSelect)
        self.byteDropDown.pack(side=tk.TOP, anchor=tk.N, padx= 10, pady=5)

        # Now get file output from user
        self.outLabel = tk.Label(self.b1, justify=tk.LEFT, width = 10, text="Output File")
        self.outLabel.pack(side=tk.LEFT, pady=5, padx=5)
        self.outDisplay = tk.Entry(self.b1, state=tk.DISABLED, text="Select file...", borderwidth=2)
        self.outDisplay.pack(side=tk.LEFT, pady=5, padx=5, fill=tk.X, expand=True)
        self.outButton = tk.Button(self.b1, text="Select", width = 16, height = 1, command=self.outBrowse,  borderwidth=2)
        self.outButton.pack(side=tk.LEFT, padx=5, pady=5)

        # Exit and conform buttons
        self.button_exit = tk.Button(self.b2, text="Quit", command=self.quit, width=25)
        self.button_confirm = tk.Button(self.b2, text="Convert", command=self.confirm, width=25)
        self.button_exit.pack(padx=5, pady=10, side=tk.LEFT)
        self.button_confirm.pack(padx=5, pady=10, side=tk.LEFT)

        self.statusText = tk.Label(self.b3, text="Ready", justify=tk.LEFT)
        self.statusText.pack(anchor=tk.NW, fill=tk.X, expand=True)

        # Enter the main loop and display the GUI
        self.root.mainloop()

    def byteSelect(self, dummy):
        ''' Update the currently selected byte width using dropdown menu'''
        if "2" in self.bytesVar.get():
            self.byteWidth = 2
        elif "4" in self.bytesVar.get():
            self.byteWidth = 4
        else:
            self.byteWidth = 8


    def changeTogglePara(self):
        '''Unused: Update the current multithreading options'''
        self.multithread = not self.multithread

        state = tk.NORMAL if self.multithread else tk.DISABLED
        self.paraCores.config(state=state)
        self.numThreads = self.paraCores.get()


    def changeToggleRes(self):
        '''Toggle on or off the resample option. This updates the trip buttons as well'''
        self.resample = not self.resample

        state = tk.NORMAL if self.resample else tk.DISABLED
        #self.resFreqInput.config(state=state)
        self.trimStartInput.config(state=state)
        self.trimEndInput.config(state=state)
        self.trimButton.config(state=state)


    def inBrowse(self):
        '''Let the user browse for .cwa files as input to the program'''
        files = filedialog.askopenfilenames(title="Open .cwa files", filetypes=[("CWA files", ".cwa")])

        stringName = ""
        for file in files:
            self.filePaths.append(file)  # Take the name of the file, and save it
            shortPath = os.path.basename(file)
            stringName += shortPath + ",  "

        self.inDisplay.config(state=tk.NORMAL)
        self.inDisplay.delete(0, "end")
        self.inDisplay.insert(0, stringName)
        self.inDisplay.config(state=tk.DISABLED)


    def outBrowse(self):
        '''Let the user browse and Save-as the output file .bin and .tst location and name'''
        file = filedialog.asksaveasfilename(title="Save .TST file", filetypes=[("TST files", ".tst")])
        self.saveName = file
        self.outDisplay.config(state=tk.NORMAL)
        self.outDisplay.delete(0, "end")
        self.outDisplay.insert(0, self.saveName)
        self.outDisplay.config(state=tk.DISABLED)

    def getLoggerRate(self):
        self.changeToggleRes()

        # Do a dummy run of the .cwa read and extract only the average logging frequency
        (_, _, _, rate) = ConvertMain.compute_multi_channel(self.filePaths, self.saveName, resample=self.resample, getFreq=True)
        loggerDispFreq = "---"

        if float(rate['max']) - float(rate['min']) > 70.0:
            loggerDispFreq = "ERROR, All Loggers are not same rate!"
        elif not self.resample:
            loggerDispFreq = "---"
        elif float(rate['average']) == 0.0:
            loggerDispFreq = "No loggers Selected! ---"
        else:
            self.loggerFrequency = round(float(rate['average']) / 100.0, 0) * 100
            loggerDispFreq = str(self.loggerFrequency)

        self.frequencyText.set(loggerDispFreq)

    def testResampleRange(self):
        '''Apply the user trimmed time to the dummy run of loading .cwa files. The min and max start times are
            returned after being trimmed in AWST timezone'''
        trimStart = float(eval(self.trimStartInput.get())) * 60.0
        trimEnd = float(eval(self.trimEndInput.get())) * 60.0

        resampleFreq = self.loggerFrequency
        numThreads = 1 # DISABLED int(self.paraCores.get())

        # Dummy run the loading of the logger files. It will return the timestamp of the start and stop times as well
        # as the number of samples that will be generated in the output files.
        (startTime, endTime, numSamples, _) = ConvertMain.compute_multi_channel(self.filePaths, self.saveName, resample=self.resample,
                                                                             resampleFreq=resampleFreq, multithread=self.multithread,
                                                                             nThreads=numThreads, demoRun=True, trimStart=trimStart, trimEnd=trimEnd)
        # Special methods to fake the timezone display in the GUI. Later, this can be updated to accept the local
        #   timezone of the computer, but for now, Australian Western Standard Time is sufficient.
        start = CWA.timezone_timestamp_string(startTime)
        end = CWA.timezone_timestamp_string(endTime)

        output = "Start Time:     " + start + "\nFinish Time:   " + end + "\nSamples:        " + str(numSamples)
        self.trimText.config(text=output)

    def confirm(self):
        '''Function called when it is time to actually convert the files. This will create a new parallel thread and
        do all processing there with a new terminal window open. Once started, and after checks are passed, the
        confirm button may no be pressed again due to the nature of needing to reset variables as well as the immense
        resource drain placed on the machine.

        Two instances of this program should not be run simultaneously unless the machine is a workstation'''
        trimStart = float(eval(self.trimStartInput.get())) * 60.0
        trimEnd = float(eval(self.trimEndInput.get())) * 60.0

        # Checks for input file number only, not actually goodness of files.
        if len(self.filePaths) == 0:
            self.statusText.config(text="No valid input files")
            print("Error, No file Selected")
            return

        # Get the user to specify at least one output file
        if self.saveName == "":
            self.statusText.config(text="No valid output file")
            print("Error, No file Selected")
            return

        resampleFreq = self.loggerFrequency
        numThreads = 1 # int(self.paraCores.get())  DISABLED

        # Spawn a new thread and pass all the parameters to it. This must be cleaned up at some point !
        self.thread1 = threading.Thread(target=ConvertMain.compute_multi_channel, args=(self.filePaths, self.saveName, self.resample, resampleFreq,
                                          self.multithread, numThreads, trimStart, trimEnd, False, self.byteWidth, False))
        self.thread1.start()
        self.button_confirm.config(state=tk.DISABLED)

    def quit(self):
        '''Destroy the GUI and all spawned threads'''
        self.root.destroy()


def main():
    ''' Main function for th CWA to BIN file converter'''
    freeze_support()
    form = PrefForm()


if __name__ == "__main__":
    main()
