#!/usr/bin/env python

from datetime import datetime
from Tkinter import *
import tkFont
from tkFileDialog import *
from SimpleDialog import *
from ConfigParser import *
import tkMessageBox
import os
import toolpath
import gcode

IN_AXIS = os.environ.has_key("AXIS_PROGRESS_BAR")

class Application(Frame):
    def __init__(self, IniFile, master=None):
        Frame.__init__(self, master, width=700, height=400, bd=1)
        self.grid()
        self.ini_file = IniFile
        self.createMenu()
        self.createWidgets()
        self.LoadIniData()
        self.UpdateAllVars()
        self.tp = toolpath.Toolpath()
        self.tp.LoadIniData(self.ini_file)
        self.gcode = gcode.Gcode(self)

    def LoadIniData(self):
        FileName = self.ini_file
        self.cp=ConfigParser()
        try:
            fp = open(FileName,'r')
            self.cp.readfp(fp)
            fp.close()
        except IOError:
            raise Exception,'NoFileError : ' % (FileName)
        return
        
    def ReloadConfig(self):
        self.LoadIniData()
        self.UpdateAllVars()

    def SaveConfig(self):
        try:
            self.cp.set('RawData', 'input_dir', self.InputDirSV.get())
            self.cp.set('RawData', 'raw_input_file', self.InputNameSV.get())

            self.cp.set('Gcode', 'ncfile_dir', self.NCFileDirSV.get())
            self.cp.set('Gcode', 'move_feed_rate', self.MoverateSV.get())
            self.cp.set('Gcode', 'cut_feed_rate', self.CutrateSV.get())

            self.cp.set('TSP', 'start_temp', self.TSPTempSV.get())
            self.cp.set('TSP', 'alpha', self.TSPAlphaSV.get())
            self.cp.set('TSP', 'iterations', self.TSPIterationsSV.get())

            fn=open(self.ini_file,'w')
            self.cp.write(fn)
            fn.close()
        except:
            tkMessageBox.showinfo('Error', 'broke in save config '+ self.ini_file) 

    def InputFileDirectory(self):
        DirName = self.GetDirectory(self.cp.get("RawData", "input_dir"))
        if len(DirName)>0:
            self.cp.set("RawData", "input_dir", DirName)
            self.InputDirSV.set(self.cp.get('RawData', 'input_dir'))

    def NcFileDirectory(self):
        DirName = self.GetDirectory(self.cp.get('Gcode', 'ncfile_dir'))
        if len(DirName)>0:
            self.cp.set('Gcode', 'ncfile_dir', DirName)
            self.NCFileDirSV.set(self.cp.get('Gcode', 'ncfile_dir'))

    def GetDirectory(self, name):
        if len(name) == 0:
            name = '.'
        DirName = askdirectory(initialdir=name,title='Please select a directory')
        if len(DirName) > 0:
            return DirName 
       
    def createMenu(self):
        #Create the Menu base
        self.menu = Menu(self)
        self.master.config(menu=self.menu)
        # Add File Menu
        self.FileMenu = Menu(self.menu)
        self.menu.add_cascade(label='File', menu=self.FileMenu)
        self.FileMenu.add_command(label='Input Dir', command=self.InputFileDirectory)
        self.FileMenu.add_command(label='NC Dir   ', command=self.NcFileDirectory)
        self.FileMenu.add_command(label='Reload', command=self.ReloadConfig)
        self.FileMenu.add_command(label='Save', command=self.SaveConfig)

        self.FileMenu.add_command(label='Quit', command=self.quit)

        # Add Help Menu
        self.HelpMenu = Menu(self.menu)
        self.menu.add_cascade(label='Help', menu=self.HelpMenu)
        self.HelpMenu.add_command(label='Help Info', command=self.HelpInfo)
        self.HelpMenu.add_command(label='About', command=self.HelpAbout)

    def UpdateAllVars(self):
        self.InputDirSV.set(self.cp.get('RawData', 'input_dir'))
        self.InputNameSV.set(self.cp.get('RawData', 'raw_input_file'))

        self.NCFileDirSV.set(self.cp.get('Gcode', 'ncfile_dir'))
        # self.NCFileNameSV.set(self.cp.get('Gcode', 'ncfile_file'))

        self.CutrateSV.set(self.cp.get('Gcode', 'cut_feed_rate'))
        self.MoverateSV.set(self.cp.get('Gcode', 'move_feed_rate'))

        self.TSPTempSV.set(self.cp.get('TSP', 'start_temp'))
        self.TSPAlphaSV.set(self.cp.get('TSP', 'alpha'))
        self.TSPIterationsSV.set(self.cp.get('TSP', 'iterations'))

    def createWidgets(self):
        row = 0
        self.sp1 = Label(self)
        self.sp1.grid(row=row)
        
        row += 1
        self.st1 = Label(self, text='Input dir:')
        self.st1.grid(row=row, column=0, sticky=E)

        self.InputDirSV = StringVar()
        self.st1 = Label(self, textvariable=self.InputDirSV)
        self.st1.grid(row=row, column=1, sticky=W)

        row += 1
        self.st2 = Label(self, text='NC file dir:')
        self.st2.grid(row=row, column=0, sticky=E)

        self.NCFileDirSV = StringVar()
        self.st2 = Label(self, textvariable=self.NCFileDirSV)
        self.st2.grid(row=row, column=1, sticky=W)

        self.st8=Label(self,text='Units')
        self.st8.grid(row=row,column=4)
        UnitOptions=[('Inch',1),('MM',2)]
        self.UnitVar=IntVar()
        self.UnitVar.set(1)
        for text, value in UnitOptions:
            Radiobutton(self, text=text,value=value,
                variable=self.UnitVar,indicatoron=0,width=6,)\
                .grid(row=value, column=5)

        row += 1
        self.st2 = Label(self, text='Input file')
        self.st2.grid(row=row, column=0, sticky=E)
        self.InputNameSV = StringVar()
        self.InputName = Entry(self, width=18, textvariable=self.InputNameSV)
        self.InputName.grid(row=row, column=1, sticky=W)

        row += 1
        self.st3 = Label(self, text='Temp')
        self.st3.grid(row=row, column=0, sticky=E)
        self.TSPTempSV = StringVar()
        self.TSPTemp = Entry(self, width=5, textvariable=self.TSPTempSV)
        self.TSPTemp.grid(row=row, column=1, sticky=W)

        self.st4 = Label(self, text='alpha')
        self.st4.grid(row=row, column=1, sticky=E)
        self.TSPAlphaSV = StringVar()
        self.TSPAlpha = Entry(self, width=5, textvariable=self.TSPAlphaSV)
        self.TSPAlpha.grid(row=row, column=2, sticky=W)

        row += 1
        self.st5 = Label(self, text='Reps')
        self.st5.grid(row=row, column=0, sticky=E)
        self.TSPIterationsSV = StringVar()
        self.TSPIterations = Entry(self, width=8, textvariable=self.TSPIterationsSV)
        self.TSPIterations.grid(row=row, column=1, sticky=W)

        row += 1
        self.st6 = Label(self, text='')
        self.st6.grid(row=row, column=1, sticky=E)

        row += 1
        self.st5 = Label(self, text='Cutrate')
        self.st5.grid(row=row, column=0, sticky=E)
        self.CutrateSV = StringVar()
        self.Cutrate = Entry(self, width=5, textvariable=self.CutrateSV)
        self.Cutrate.grid(row=row, column=1, sticky=W)
        
        self.st6 = Label(self, text='Moverate')
        self.st6.grid(row=row, column=1, sticky=E)
        self.MoverateSV = StringVar()
        self.Moverate = Entry(self, width=5, textvariable=self.MoverateSV)
        self.Moverate.grid(row=row, column=2, sticky=W)
        
        row += 1
        self.st7 = Label(self, text='')
        self.st7.grid(row=row, column=1, sticky=E)

        row += 1

        self.font = tkFont.Font(family="Helvetica", size=14)

        self.results_string = StringVar(value="RESULTS")
        self.spacer3 = Label(self, textvariable=self.results_string, font=self.font)
        self.spacer3.grid(row=row, column=0, columnspan=5)
        
        row += 1
               
        self.GenButton = Button(self, text='Gen G-Code',command=self.GenCode)
        self.GenButton.grid(row=row, column=0)
        
        self.quitButton = Button(self, text='Quit', command=self.quit)
        self.quitButton.grid(row=row, column=5, sticky=E)    

    def QuitFromAxis(self):
        sys.stdout.write("M2 (Face.py Aborted)")
        self.quit()

    def GenCode(self):
        NcDir = self.cp.get("Gcode", "ncfile_dir")
        if len(NcDir) == 0:
            NcDir = self.GetDirectory()
        self.cp.set("Gcode", "ncfile_dir", NcDir)

        from os.path import join as pjoin

        # set some variables that may have been set by the interface 
        #  - if they're in the ini file they will be overridden 
        #  by the interface
        self.tp.input_file = pjoin(self.InputDirSV.get(), self.InputNameSV.get())
        self.tp.LoadRawData() # loads up the input file

        # do this in case the user manually changes the ini_file
        self.tp.LoadIniData(self.ini_file)
        self.gcode.LoadIniData(self.ini_file)

        # other variables from the ini file that may be edited by the interface
        self.tp.start_temp = float(self.TSPTempSV.get())
        self.tp.alpha = float(self.TSPAlphaSV.get())
        self.tp.iterations = int(self.TSPIterationsSV.get())
        self.gcode.output_file = pjoin(self.NCFileDirSV.get(), self.cp.get("Gcode", "output_file"))
        self.gcode.move_feed_rate = self.MoverateSV.get()
        self.gcode.cut_feed_rate = self.CutrateSV.get()

        gcode_cuts = self.tp.toolpath()

        # this gets stuck on the top line of the gcode, and is displayed to user
        p = self.gcode.MakePhrase()
        title = '(' + p + ')' + '\n\n'
        self.gcode.append(title)
        self.gcode.add_header()

        for i in gcode_cuts:
            for j in gcode_cuts[i]['cut_tour']:
                line = gcode_cuts[i]['cuts'][j].coords
                self.gcode.write_polyline(line)
            line = gcode_cuts[i]['part'].coords
            self.gcode.write_polyline(line)

        self.gcode.add_footer()
        # send the gcode to disk. 
        self.gcode.write_gcode()

        # display the unique phrase to the user
        self.results_string.set('(' + p + ')')


    def Simple(self):
        tkMessageBox.showinfo('Feature', 'Sorry this Feature has\nnot been programmed yet.')

    def HelpInfo(self):
        SimpleDialog(self,
            text='Required fields are:\n'
            'Part Width & Length,\n'
            'Amount to Remove,\n'
            'and Feedrate\n'
            'Fractions can be entered in most fields',
            buttons=['Ok'],
            default=0,
            title='User Info').go()

    def HelpAbout(self):
        tkMessageBox.showinfo('Help About', 'SVN site:\n'
            'https://code.google.com/p/laser-code/\n')


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print 'pass a ini file to command line'
        sys.exit(1)
    print sys.argv[1]
    app = Application(sys.argv[1])
    app.master.title('G-Code Generator')
    app.mainloop()

