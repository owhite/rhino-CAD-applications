#!/usr/bin/env python
version = '1.0'
# python toolpath.py

from Tkinter import *
from tkFileDialog import *
from math import *
from SimpleDialog import *
from ConfigParser import *
from decimal import *
import tkMessageBox
from subprocess import Popen, PIPE, STDOUT
import os

IN_AXIS = os.environ.has_key("AXIS_PROGRESS_BAR")

class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master, width=700, height=400, bd=1)
        self.grid()
        self.InputFile = 'nc_files/toolpath.ini'
        self.LoadIniData()
        self.createMenu()
        self.createWidgets()

    def createMenu(self):
        #Create the Menu base
        self.menu = Menu(self)
        #Add the Menu
        self.master.config(menu=self.menu)
        #Create our File menu
        self.FileMenu = Menu(self.menu)
        #Add our Menu to the Base Menu
        self.menu.add_cascade(label='File', menu=self.FileMenu)
        #Add items to the menu
        self.FileMenu.add_command(label='Quit', command=self.quit)
        
        self.EditMenu = Menu(self.menu)
        self.menu.add_cascade(label='Edit', menu=self.EditMenu)
        self.EditMenu.add_command(label='Copy', command=self.CopyClpBd)
        self.EditMenu.add_command(label='Select All', command=self.SelectAllText)
        self.EditMenu.add_command(label='Delete All', command=self.ClearTextBox)
        self.EditMenu.add_separator()
        self.EditMenu.add_command(label='NC Directory', command=self.NcFileDirectory)
        self.EditMenu.add_command(label='tmp Directory', command=self.TMPFileDirectory)
        
        self.HelpMenu = Menu(self.menu)
        self.menu.add_cascade(label='Help', menu=self.HelpMenu)
        self.HelpMenu.add_command(label='Help Info', command=self.HelpInfo)
        self.HelpMenu.add_command(label='About', command=self.HelpAbout)

    def createWidgets(self):
        
        self.sp1 = Label(self)
        self.sp1.grid(row=0)
        
        self.st1 = Label(self, text='File location -t')
        self.st1.grid(row=1, column=0, sticky=E)
        self.TargetDirVar = StringVar()
        self.TargetDir = Entry(self, width=30, textvariable=self.TargetDirVar)
        self.TargetDir.grid(row=1, column=1, sticky=W)
        self.TargetDir.focus_set()
        self.TargetDir.insert(0, self.cp.get('Directories', 'target_dir'));

        self.st2 = Label(self, text='Input file -i')
        self.st2.grid(row=2, column=0, sticky=E)
        self.TargetNameVar = StringVar()
        self.TargetName = Entry(self, width=18, textvariable=self.TargetNameVar)
        self.TargetName.grid(row=2, column=1, sticky=W)
        self.TargetName.insert(0, self.cp.get('Files', 'target'));

        self.st4 = Label(self, text='Execute ')
        self.st4.grid(row=3, column=0, sticky=E)
        self.ExecuteVar = StringVar()
        self.Execute = Entry(self, width=30, textvariable=self.ExecuteVar)
        self.Execute.grid(row=3, column=1, sticky=W)
        self.Execute.insert(0, self.cp.get('Executable', 'toolpathcode'));

        self.st3 = Label(self, text='Laser power -p')
        self.st3.grid(row=4, column=0, sticky=E)
        self.LaserPowerVar = StringVar()
        self.LaserPower = Entry(self, width=5, textvariable=self.LaserPowerVar)
        self.LaserPower.grid(row=4, column=1, sticky=W)
        self.LaserPower.insert(0, self.cp.get('Gcode', 'power'));

        self.st5 = Label(self, text='Feedrate -f')
        self.st5.grid(row=5, column=0, sticky=E)
        self.FeedrateVar = StringVar()
        self.Feedrate = Entry(self, width=5, textvariable=self.FeedrateVar)
        self.Feedrate.grid(row=5, column=1, sticky=W)
        self.Feedrate.insert(0, self.cp.get('Gcode', 'feedrate'));
        
        self.spacer3 = Label(self, text='')
        self.spacer3.grid(row=6, column=0, columnspan=4)
        self.g_code = Text(self,width=40,height=10,bd=3)
        self.g_code.grid(row=7, column=0, columnspan=5, sticky=E+W+N+S)
        self.tbscroll = Scrollbar(self,command = self.g_code.yview)
        self.tbscroll.grid(row=7, column=5, sticky=N+S+W)
        self.g_code.configure(yscrollcommand = self.tbscroll.set) 

        self.sp4 = Label(self)
        self.sp4.grid(row=8)
        
        self.st8=Label(self,text='Units')
        self.st8.grid(row=0,column=5)
        UnitOptions=[('Inch',1),('MM',2)]
        self.UnitVar=IntVar()
        for text, value in UnitOptions:
            Radiobutton(self, text=text,value=value,
                variable=self.UnitVar,indicatoron=0,width=6,)\
                .grid(row=value, column=5)
        self.UnitVar.set(1)
               
        self.GenButton = Button(self, text='Generate G-Code',command=self.GenCode)
        self.GenButton.grid(row=8, column=0)
        
        self.SaveButton = Button(self, text='Save config',command=self.SaveConfig)
        self.SaveButton.grid(row=8, column=1)

        if IN_AXIS:
            self.toAxis = Button(self, text='Write to AXIS and Quit',\
                command=self.WriteToAxis)
            self.toAxis.grid(row=8, column=3)
        
            self.quitButton = Button(self, text='Quit', command=self.QuitFromAxis)
            self.quitButton.grid(row=8, column=5, sticky=E)
        else:
            self.quitButton = Button(self, text='Quit', command=self.quit)
            self.quitButton.grid(row=8, column=5, sticky=E)    

    def QuitFromAxis(self):
        sys.stdout.write("M2 (Face.py Aborted)")
        self.quit()

    def WriteToAxis(self):
        sys.stdout.write(self.g_code.get(0.0, END))
        self.quit()

    def GenCode(self):
        NcDir = self.cp.get("Directories", "ncfiles")
        if len(NcDir) == 0:
            NcDir = self.GetDirectory()
        self.cp.set("Directories", "ncfiles", NcDir)

        TMPDir = self.cp.get("Directories", "tmp_dir")
        if len(TMPDir) == 0:
            TMPDir = self.GetDirectory()
        self.cp.set("Directories", "tmp_dir", TMPDir)

        process = str(self.ExecuteVar.get()) \
            + ' -f ' + str(self.FeedrateVar.get()) \
            + ' -i ' + str(self.TargetNameVar.get()) \
            + ' -t ' + str(self.TargetDirVar.get()) \
            + ' -p ' + str(self.LaserPowerVar.get()) \
            + ' -d ' + self.cp.get("Directories", "ncfiles") \
            + ' -g thing.ngc'

        self.g_code.delete(1.0,END)
        self.g_code.insert(END, "CMD: " + process)

        p = Popen(process, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
        output = p.stdout.read()

        self.g_code.insert(END, '\n')
        for line in output:
            self.g_code.insert(END, line)

        # for line in p.stderr:
            #self.g_code.insert(END, line)

    def FToD(self,s): # Float To Decimal
        """
        Returns a decimal with 4 place precision
        valid imputs are any fraction, whole number space fraction
        or decimal string. The input must be a string!
        """
        s=s.strip(' ') # remove any leading and trailing spaces
        D=Decimal # Save typing
        P=D('0.0001') # Set the precision wanted
        if ' ' in s: # if it is a whole number with a fraction
            w,f=s.split(' ',1)
            w=w.strip(' ') # make sure there are no extra spaces
            f=f.strip(' ')
            n,d=f.split('/',1)
            return D(D(n)/D(d)+D(w)).quantize(P)
        elif '/' in s: # if it is just a fraction
            n,d=s.split('/',1)
            return D(D(n)/D(d)).quantize(P)
        return D(s).quantize(P) # if it is a decimal number already

    def LoadIniData(self):
        FileName = self.InputFile
        self.cp=ConfigParser()
        try:
            self.cp.readfp(open(FileName,'r'))
            # f.close()
        except IOError:
            raise Exception,'NoFileError'
        return
        
    def GetDirectory(self, name):
        if len(name) == 0:
            name = '.'
        DirName = askdirectory(initialdir=name,title='Please select a directory')
        if len(DirName) > 0:
            return DirName 
       
    def CopyClpBd(self):
        self.g_code.clipboard_clear()
        self.g_code.clipboard_append(self.g_code.get(0.0, END))

    def SaveConfig(self):
        try:
            FileName = self.InputFile
            # nc dir and tmp_dir
            NcDir = self.cp.get("Directories", "ncfiles")
            if len(NcDir) == 0:
                NcDir = self.GetDirectory()
            self.cp.set("Directories", "ncfiles", NcDir)

            TMPDir = self.cp.get("Directories", "tmp_dir")
            if len(TMPDir) == 0:
                TMPDir = self.GetDirectory()
            self.cp.set("Directories", "tmp_dir", TMPDir)

            self.cp.set("Directories", "tmp_dir", TMPDir)
            self.cp.set("Directories", "ncfiles", NcDir)
            self.cp.set("Directories", "target_dir", self.TargetDirVar.get())
            self.cp.set("Gcode", "feedrate", self.FeedrateVar.get())
            self.cp.set("Gcode", "power", self.LaserPowerVar.get())
            self.cp.set("Files", "target", self.TargetNameVar.get())
            self.cp.set("Executable", "toolpathcode", self.ExecuteVar.get())
            self.fn=open(FileName,'w')
            self.cp.write(self.fn)
            self.fn.close()
        except:
            tkMessageBox.showinfo('Error', 'broke in save config')            

    def WriteToFile(self):
        try:
            NcDir = self.cp.get("Directories", "ncfiles")
            if len(NcDir)>0:
                NcDir = self.GetDirectory()
            self.NewFileName = asksaveasfile(initialdir=self.NcDir,mode='w', \
                master=self.master,title='Create NC File',defaultextension='.ngc')
            self.NewFileName.write(self.g_code.get(0.0, END))
            self.NewFileName.close()
        except:
            tkMessageBox.showinfo('Error', 'broke in write to file')            

    def NcFileDirectory(self):
        DirName = self.GetDirectory(self.cp.get("Directories", "ncfiles"))
        if len(DirName)>0:
            self.cp.set("Directories", "ncfiles", DirName)

    def TMPFileDirectory(self):
        DirName = self.GetDirectory(self.cp.get("Directories", "tmp_dir"))
        if len(DirName)>0:
            self.cp.set("Directories", "tmp_dir", DirName)

    def Simple(self):
        tkMessageBox.showinfo('Feature', 'Sorry this Feature has\nnot been programmed yet.')

    def ClearTextBox(self):
        self.g_code.delete(1.0,END)

    def SelectAllText(self):
        self.g_code.tag_add(SEL, '1.0', END)

    def SelectCopy(self):
        self.SelectAllText()
        self.CopyClpBd()

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
        tkMessageBox.showinfo('Help About', 'Programmed by\n'
            'Big John T (AKA John Thornton)\n'
            'Rick Calder\n'
            'Brad Hanken\n'
            'Version ' + version)

app = Application()
app.master.title('G-Code Generator')
app.mainloop()

