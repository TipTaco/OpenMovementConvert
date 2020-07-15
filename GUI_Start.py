# Author Adrian Shedley
# date 28 May 2020

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

import ConvertMain
import cwa_metadata as CWA

import os.path
import threading
from multiprocessing import freeze_support

PROCESS: str = 'CWA_to_BIN'
VERSION: str = 'v1.01'


class PrefForm():
    def __init__(self):
        self.root = tk.Tk()
        title = PROCESS + " " + VERSION
        self.root.title(title + ' - Conversion Preferences form')

        self.filePaths = []
        self.saveName: str = ""

        self.resample = tk.BooleanVar(value=False)
        self.resample_freq = tk.DoubleVar(value=800.0)

        self.lowpass = tk.BooleanVar(value=False)
        self.lowpass_freq = tk.DoubleVar(value=100.0)

        self.integrate = tk.BooleanVar(value=False)
        self.highpass1_freq = tk.DoubleVar(value=0.0)
        self.integrate_unit: str = "mm/s"
        self.highpass2_freq = tk.DoubleVar(value=0.0)

        self.multithread: bool = False
        self.numThreads: int = 4
        self.byteWidth: int = 8

        # The main frame for the GUI
        self.master_frame = tk.Frame(self.root, bg='red')
        self.master_frame.pack(anchor=tk.NW, fill=tk.BOTH, expand=True, side=tk.TOP, pady=1, padx=1)
        tk.Grid.columnconfigure(self.root, 0, weight=1)
        for y in range(1,8):
            tk.Grid.rowconfigure(self.master_frame, y, weight=1)

        # GUI rewrite
        self.title_frame = tk.Frame(self.master_frame)
        self.title_frame.grid(row=0, column=0, columnspan=1, sticky='nwew', padx=1, pady=1)

        self.in_file_frame = tk.Frame(self.master_frame)
        self.in_file_frame.grid(row=1, column=0, columnspan=1, sticky='nwew', padx=1, pady=1)

        self.resample_frame = tk.Frame(self.master_frame)
        self.resample_frame.grid(row=2, column=0, columnspan=1, sticky='nwew', padx=1, pady=1)

        self.test_resample_frame = tk.Frame(self.master_frame)
        self.test_resample_frame.grid(row=3, column=0, columnspan=1, sticky='nwew', padx=1, pady=1)

        self.integrate_frame = tk.Frame(self.master_frame)
        self.integrate_frame.grid(row=4, column=0, columnspan=1, sticky='nwew', padx=1, pady=1)

        self.out_format_frame = tk.Frame(self.master_frame)
        self.out_format_frame.grid(row=5, column=0, columnspan=1, sticky='nwew', padx=1, pady=1)

        self.out_file_frame = tk.Frame(self.master_frame)
        self.out_file_frame.grid(row=6, column=0, columnspan=1, sticky='nwew', padx=1, pady=1)

        self.button_frame = tk.Frame(self.master_frame)
        self.button_frame.grid(row=7, column=0, columnspan=1, sticky='nwew', padx=1, pady=1)


        # Now add the actual GUI content
        # Instructions box
        self.instruction = tk.Label(self.title_frame, justify=tk.LEFT, text="Usage instructions: \n 1) Select logger files (.cwa)" +
                                    "\n 2) (Optional) Choose to resample at a frequency \n 3) Select processing options" +
                                    "\n 4) Select output file name and location \n 5) Press convert")
        self.instruction.pack(anchor=tk.W, pady=5, padx=5)

        # Input file selection
        self.in_sep = ttk.Separator(self.in_file_frame)
        self.in_sep.pack(side=tk.TOP, fill=tk.X, expand=True)
        self.inLabel = tk.Label(self.in_file_frame, width = 10, justify=tk.LEFT, text="Input Files")
        self.inLabel.pack(side=tk.LEFT, pady=5, padx=5)
        self.inDisplay = tk.Entry(self.in_file_frame, state=tk.DISABLED, text="Select files...", borderwidth=2, width=50)
        self.inDisplay.pack(side=tk.LEFT, pady=5, padx=5, fill=tk.X, expand=True)
        self.inButton = tk.Button(self.in_file_frame, width = 16, text="Browse", command=self.inBrowse, height = 1, borderwidth=2)
        self.inButton.pack(side=tk.LEFT, padx=5, pady=5)

        # Resample or Decimation Selector
        state = tk.NORMAL if self.resample.get() else tk.DISABLED
        self.resample_mode = tk.IntVar(value=1)
        self.frequencyText = tk.StringVar(value="---")

        self.resample_sep = ttk.Separator(self.resample_frame)
        self.resample_sep.pack(side=tk.TOP, fill=tk.X, expand=True)

        self.resampleText = tk.Label(self.resample_frame, justify=tk.LEFT, fg='blue', text="Resampler / Downsampler: \n" +
                                                                    "  Resampling or downsampling with filtering applied at FREQUENCY / 2 to avoid aliasing")
        self.resampleText.pack(anchor=tk.NW, side = tk.TOP, pady = 5, padx =5)

        # subframes fro resampling
        self.resample_frame1 = tk.Frame(self.resample_frame)
        self.resample_frame1.pack(anchor=tk.NW, side=tk.LEFT)
        self.resample_frame2 = tk.Frame(self.resample_frame)
        self.resample_frame2.pack(anchor=tk.SE, side=tk.BOTTOM)

        resample_modes = [("Disabled", 1), ("Resample", 2), ("Decimate", 3)]
        for mode in resample_modes:
            tk.Radiobutton(self.resample_frame1, indicatoron=0, text=mode[0], width=20, command=self.change_resample_selection,
                           padx=4, pady=4, variable=self.resample_mode, value=mode[1])\
                .pack(anchor=tk.NW, padx=10, pady=4)

        self.resample_f_label = tk.Label(self.resample_frame2, text='Resample Frequency (Hz)', width=25, anchor='e')
        self.resample_f_label.grid(row=0, column=0, pady=2)
        self.resample_f_select = tk.Entry(self.resample_frame2, borderwidth=2, width=10, textvariable=self.resample_freq, justify=tk.RIGHT)
        self.resample_f_select.grid(row=0, column=1, sticky='w')

        self.filter_enable = tk.Checkbutton(self.resample_frame2, text='Lowpass Filter (Hz)', justify=tk.RIGHT, variable=self.lowpass, width=22, anchor='e', command=self.update_resample_filter)
        self.filter_enable.grid(row=1, column=0, pady=2)
        self.filter_f_select = tk.Entry(self.resample_frame2, borderwidth=2, width=10, textvariable=self.lowpass_freq, justify=tk.RIGHT)
        self.filter_f_select.grid(row=1, column=1, sticky='w')

        # Trim selection options
        self.startT = tk.DoubleVar(value=0)
        self.stopT = tk.DoubleVar(value=0)
        self.trimStartLabel = tk.Label(self.resample_frame2, text="Trim Start (decimal minutes)  ", width = 25, anchor='e', justify=tk.RIGHT)
        self.trimStartLabel.grid(row=3, column=0, pady = 2)  # pack(anchor=tk.NW, padx=5, pady=5, side=tk.LEFT)
        self.trimStartInput = tk.Entry(self.resample_frame2, text="decimal minutes", width = 10, borderwidth=2, textvariable=self.startT, justify=tk.RIGHT)
        self.trimStartInput.insert(0, "0")
        self.trimStartInput.config(state=state)
        self.trimStartInput.grid(row=3, column=1, sticky='w')  # .pack(padx=5, pady=5, side=tk.LEFT)

        self.trimEndLabel = tk.Label(self.resample_frame2, text="Trim Finish (decimal minutes)", width = 25, anchor='e', justify=tk.RIGHT)
        self.trimEndLabel.grid(row=4, column=0, pady = 2)  # .pack(anchor=tk.NW, padx=5, pady=5, side=tk.LEFT)
        self.trimEndInput = tk.Entry(self.resample_frame2, text="decimal minutes", width = 10, borderwidth=2, textvariable=self.stopT, justify=tk.RIGHT)
        self.trimEndInput.insert(0, "0")
        self.trimEndInput.config(state=state)
        self.trimEndInput.grid(row=4, column=1, sticky='w')  # .pack(padx=5, pady=5, side=tk.LEFT)

        # show sample output for time
        self.trimButton = tk.Button(self.resample_frame2, text="Compute trim", width=20, height=3, state = state, command=self.testResampleRange)
        self.trimButton.grid(row=5, column=0, sticky='nsew', padx=5, pady=5)  # .pack(anchor=tk.NW, padx=5, pady=5, side=tk.LEFT)
        self.trimText = tk.Label(self.resample_frame2, text="Start Time:     N/A\nFinish Time:   N/A\nSamples:        N/A", width=30, anchor='w')
        self.trimText.grid(row=5, column=1, sticky='w')  # .pack(anchor=tk.NW, padx=5, pady=5, side=tk.LEFT)

        # By default disabled the resample frames
        self.set_frame_state(self.resample_frame2, 'disabled')
        self.set_frame_state(self.resample_frame2, 'disabled')

        # Instead place the byte width selector here
        self.output_format_sep = ttk.Separator(self.out_format_frame)
        self.output_format_sep.pack(side=tk.TOP, fill=tk.X, expand=True)
        self.outputDesc = tk.Label(self.out_format_frame, text="Catman Output File (.BIN) format: \n" +
                                                 "  Recommended: \n" +
                                                 "    8 Byte Spacing (Full size)     1GB input = 4GB output\n" +
                                                 "    4 Byte Spacing (Half Size)     1GB input = 2GB output\n" +
                                                 "  Not Recommended: \n" +
                                                 "    2 Byte Spacing (Quater Size)   1GB input = 1GB output (May take 20% longer to generate)",
                                   fg="blue", justify=tk.LEFT)
        self.outputDesc.pack(side=tk.TOP, anchor=tk.NW, padx= 10, pady=5)
        # Dropdown to select the number of bytes to put in the output file
        self.bytesVar = tk.StringVar(self.root)
        self.bytesVar.set("8 Byte")
        self.byteDropDown = tk.OptionMenu(self.out_format_frame, self.bytesVar, "8 Byte", "4 Byte", "2 Byte", command=self.byteSelect)
        self.byteDropDown.pack(side=tk.TOP, anchor=tk.N, padx= 10, pady=5)

        # Now get file output from user
        self.out_file_sep = ttk.Separator(self.out_file_frame)
        self.out_file_sep.pack(side=tk.TOP, fill=tk.X, expand=True)
        self.outLabel = tk.Label(self.out_file_frame, justify=tk.LEFT, width = 10, text="Output File")
        self.outLabel.pack(side=tk.LEFT, pady=5, padx=5)
        self.outDisplay = tk.Entry(self.out_file_frame, state=tk.DISABLED, text="Select file...", borderwidth=2)
        self.outDisplay.pack(side=tk.LEFT, pady=5, padx=5, fill=tk.X, expand=True)
        self.outButton = tk.Button(self.out_file_frame, text="Select", width = 16, height = 1, command=self.outBrowse,  borderwidth=2)
        self.outButton.pack(side=tk.LEFT, padx=5, pady=5)

        # Exit and conform buttons
        self.button_sep = ttk.Separator(self.button_frame)
        self.button_sep.pack(side=tk.TOP, fill=tk.X, expand=True)
        self.button_exit = tk.Button(self.button_frame, text="Quit", command=self.quit, width=25)
        self.button_confirm = tk.Button(self.button_frame, text="Convert", command=self.confirm, width=25)
        self.button_exit.pack(padx=5, pady=10, side=tk.LEFT, fill=tk.X, expand=True)
        self.button_confirm.pack(padx=5, pady=10, side=tk.RIGHT, fill=tk.X, expand=True)

        #self.statusText = tk.Label(self.button_frame, text="Ready", justify=tk.LEFT)
        #self.statusText.pack(anchor=tk.NW, fill=tk.X, expand=True)

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

        self.change_resample_selection()

    def outBrowse(self):
        '''Let the user browse and Save-as the output file .bin and .tst location and name'''
        file = filedialog.asksaveasfilename(title="Save .TST file", filetypes=[("TST files", ".tst")])
        self.saveName = file
        self.outDisplay.config(state=tk.NORMAL)
        self.outDisplay.delete(0, "end")
        self.outDisplay.insert(0, self.saveName)
        self.outDisplay.config(state=tk.DISABLED)

    def change_resample_selection(self):
        '''Toggle on or off the resample or decimate option. This updates the trim buttons as well'''

        # MODE
        # 1 = No Resample
        # 2 = Resample to original intented logger frequency + optional filtering
        # 3 = Decimate to rate less than original logger + forced <fs/2 filtering
        mode = self.resample_mode.get()
        self.resample = False if mode == 1 else True

        state = tk.NORMAL if self.resample else tk.DISABLED

        self.set_frame_state(self.resample_frame2, state)
        self.set_frame_state(self.resample_frame2, state)

        if mode == 2:
            rate_text = self.get_logger_rates()
            self.resample_freq.set(rate_text)
            self.resample_f_select.configure(state='disabled')
            self.lowpass.set(False)
        elif mode == 3:
            rate_text = self.get_logger_rates()
            self.resample_freq.set(rate_text)
            if isinstance(rate_text, float):
                self.lowpass_freq.set(rate_text/2.0)
            self.resample_f_select.configure(state='normal')
            self.lowpass.set(True)
            self.filter_enable.configure(state='disabled')

        self.update_resample_filter()


    def set_frame_state(self, frame, state):
        for child in frame.winfo_children():
            child.configure(state=state)

    def get_logger_rates(self):
        # Do a dummy run of the .cwa read and extract only the average logging frequency
        (_, _, _, rate) = ConvertMain.compute_multi_channel(self.filePaths, self.saveName, resample=self.resample, getFreq=True)
        loggerDispFreq = "---"

        if float(rate['max']) - float(rate['min']) > 70.0:
            loggerDispFreq = "ERROR, Diff. Rates!"
        elif not self.resample:
            loggerDispFreq = "---"
        elif float(rate['average']) == 0.0:
            loggerDispFreq = "No loggers Selected!"
        else:
            loggerDispFreq = (round(float(rate['average']) / 100.0, 0) * 100)
            self.max_logger_rate = loggerDispFreq

        return loggerDispFreq

    def update_resample_filter(self):
        mode = self.resample_mode.get()
        if mode == 2:
            toggle_state = self.lowpass.get()
            self.filter_f_select.configure(state='disabled' if not toggle_state else 'normal')

    def testResampleRange(self):
        '''Apply the user trimmed time to the dummy run of loading .cwa files. The min and max start times are
            returned after being trimmed in AWST timezone'''

        if len(self.filePaths) == 0:
            print("No files selected")
            return

        try:
            resample_freq = self.resample_freq.get()
            trimStart = self.startT.get() * 60.0
            trimEnd = self.stopT.get() * 60.0
        except tk.TclError as e:
            print(e)
            return

        if trimStart < 0 or trimEnd < 0:
            print("Trim cannot be negative")
            return

        if resample_freq <= 1:
            print("Resample frequency too low. Must be >1 Hz")
            return
        elif resample_freq > self.max_logger_rate:
            print("Resample frequency too high. Must be no more than", self.max_logger_rate)
            return

        # Dummy run the loading of the logger files. It will return the timestamp of the start and stop times as well
        # as the number of samples that will be generated in the output files.
        (startTime, endTime, numSamples, _) = ConvertMain.compute_multi_channel(
            self.filePaths, self.saveName, resample=self.resample,
            resample_freq=resample_freq, demoRun=True, trimStart=trimStart, trimEnd=trimEnd)
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

        # Checks for input file number only, not actually goodness of files.
        if len(self.filePaths) == 0:
            #self.statusText.config(text="No valid input files")
            print("Error, No file Selected")
            return

        # Get the user to specify at least one output file
        if self.saveName == "":
            #self.statusText.config(text="No valid output file")
            print("Error, No file Selected")
            return

        try:
            trimStart = self.startT.get() * 60.0
            trimEnd = self.stopT.get() * 60.0

            resample = self.resample
            resample_freq = self.resample_freq.get()

            lowpass = self.lowpass
            lowpass_freq = self.lowpass_freq.get()

            integrate = self.integrate.get()
            high1 = self.highpass1_freq.get()
            high2 = self.highpass2_freq.get()
        except tk.TclError as e:
            print(e)
            return

        if resample and (trimStart < 0 or trimEnd < 0):
            print("Trim cannot be negative")
            return

        if resample and resample_freq <= 1:
            print("Resample frequency too low. Must be >1 Hz")
            return
        elif resample and resample_freq > self.max_logger_rate:
            print("Resample frequency too high. Must be no more than", self.max_logger_rate)
            return

        if resample and lowpass and lowpass_freq <= 1:
            print("Lowpass frequency too low. Must be >1 Hz")
            return
        elif resample and lowpass_freq > resample_freq/2.00:
            print("Lowpass frequency too high. Must be no more than", resample_freq/2.0)
            return

        if integrate and (high1 <= 0 or high2 <= 0):
            print("Highpass filters cannot be <= 0 Hz")
            return

        # Spawn a new thread and pass all the parameters to it. This must be cleaned up at some point !
        self.thread1 = threading.Thread(target=ConvertMain.compute_multi_channel,
                                        args=(self.filePaths, self.saveName,
                                              resample, resample_freq, lowpass, lowpass_freq,
                                              integrate, high1, high2,
                                              trimStart, trimEnd, False, self.byteWidth, False))
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
