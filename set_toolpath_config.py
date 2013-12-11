#!/usr/bin/env python

import rhinoscriptsyntax as rs
import Rhino
import Meier_UI_Utility
import os
import random
import System.Windows.Forms.DialogResult
import ConfigParser

class thing:
    def __init__(self, name):
        self.LoadFile(name)
        # Make a new form (dialog)
        self.form = Meier_UI_Utility.UIForm("TSP parameters") 
        # Accumulate controls for the form
        self.addControls()
        # Layout the controls on the form
        self.form.layoutControls() 
        # rs.MessageBox("problem finding file")
    

    # Add each control to an accumulated list of controls
    def addControls(self):
        # The controls get added to the panel of the form
        p = self.form.panel
        buttonWidth = 100
        p.addLabel("", "", None, False) # helps with weird whitespace around pic
        p.addPictureBox("Robot", "./robot.jpg", True)


        p.addLabel("", "Power: ", None, False)
        p.addTrackBar("TB1", 1, 100, 1, 2, 1, self.power, 150, False, self.trackBar1_OnValueChange)
        p.addLabel("trackbar1", "%d" % self.power, None, True)

        p.addLabel("", "Cut: ", None, False)
        p.addTrackBar("TB2", 10, 50, 1, 2, 1, self.cut_feed_rate, 150, False, self.trackBar2_OnValueChange)
        p.addLabel("trackbar2", "%d" % self.cut_feed_rate, None, True)

        p.addLabel("", "Move: ", None, False)
        p.addTrackBar("TB3", 10, 50, 1, 2, 1, self.move_feed_rate, 150, False, self.trackBar3_OnValueChange)
        p.addLabel("trackbar3", "%d" % self.move_feed_rate, None, True)

        p.addCheckBox("check1", "Show paths to cut", self.showpaths, True, self.check1_CheckStateChanged)
        p.addSeparator("sep1", 300, True)
        p.addButton("button1", self.config_file, buttonWidth, False, self.button1_OnButtonPress)
        p.addButton("", "OK", buttonWidth, False, self.OK_button)

    # Called when the box is checked or unchecked
    def check1_CheckStateChanged(self, sender, e):
        try:
            self.showpaths = not self.showpaths
            print self.showpaths
            c.Enabled = sender.Checked
        except:
            pass
    
    # Called when a selection is made from the combobox
    def combo1_SelectedIndexChanged(self, sender, e):
        index = sender.SelectedIndex # 0 based index of choice
        item = sender.SelectedItem # Text of choice
        try:
            c = self.form.panel.Controls.Find("combo1Label", True)[0]
            c.Text = "Index="+str(index)+", Item="+item
        except:
            pass
    
    # Called when the button is pressed
    def button1_OnButtonPress(self, sender, e):
        print "original config_file location: ", self.config_file_path
        filename = rs.OpenFileName("Open", "Text Files (*.ini)|*.ini|All Files (*.*)|*.*||")
        if filename:
            (head, tail) = os.path.split(filename)
            self.LoadFile(filename)
            sender.Text = tail
    
    # Called when the value is changed
    def num1_OnValueChange(self, sender, e):
        value = sender.Value.ToString()
        try:
            c = self.form.panel.Controls.Find("num1Label", True)[0]
            c.Text = "Value="+str(value)
        except:
            pass
    
    # Called when the value changes
    def trackBar1_OnValueChange(self, sender, e):
        try:
            self.power = int(sender.Value)
            c = self.form.panel.Controls.Find("trackbar1", True)[0]
            c.Text = str(sender.Value)
        except:
            pass

    # Called when the value changes
    def trackBar2_OnValueChange(self, sender, e):
        try:
            self.cut_feed_rate = int(sender.Value)
            c = self.form.panel.Controls.Find("trackbar2", True)[0]
            c.Text = str(sender.Value)
        except:
            pass

    # Called when the value changes
    def trackBar3_OnValueChange(self, sender, e):
        try:
            self.move_feed_rate = int(sender.Value)
            c = self.form.panel.Controls.Find("trackbar3", True)[0]
            c.Text = str(sender.Value)
        except:
            pass

    def OK_button(self, sender, e):
        cf = self.config_parser
        cf.set('laser','power', str(self.power))
        cf.set('gcode','move_feed_rate', str(self.move_feed_rate))
        cf.set('gcode','cut_feed_rate', str(self.cut_feed_rate))
        cf.set('layers', 'showpaths', self.showpaths)

        with open(self.config_file, 'wb') as configfile:
            cf.write(configfile)


    def LoadFile(self,file_name):
        (head, tail) = os.path.split(file_name)
        if len(head) == 0:
            self.config_file_path = os.getcwd()
        print self.config_file_path
        self.config_file = tail

        parser = ConfigParser.RawConfigParser()
        parser.read(file_name)

        self.config_parser = parser

        self.parts_layer = parser.get('layers', 'parts_layer')
        self.cuts_layer = parser.get('layers', 'cuts_layer')
        self.path_layer = parser.get('layers', 'parts_path_layer')
        self.cutspath_layer = parser.get('layers', 'cuts_path_layer')
        self.showpaths = parser.getboolean('layers', 'showpaths')

        self.iterations = parser.getint('tsp', 'iterations')
        self.start_temp = parser.getfloat('tsp', 'start_temp')
        self.alpha = parser.getfloat('tsp', 'alpha')

        self.dictionary_file = parser.get('gcode', 'dictionary')
        self.move_feed_rate = parser.getint('gcode', 'move_feed_rate')
        self.cut_feed_rate = parser.getint('gcode', 'cut_feed_rate')
        self.dwell_time = parser.getfloat('gcode', 'dwell_time')
        self.use_cut_variable = parser.getboolean('gcode', 'use_cut_variable')
    
        from os.path import join as pjoin
        self.output_file = pjoin(parser.get('gcode', 'ncfile_dir'), 
                                 parser.get('gcode', 'output_file'))

        self.power = parser.getint('laser', 'power')


if __name__ == '__main__':

    t = thing('polyline_dump.ini')
    Rhino.UI.Dialogs.ShowSemiModal(t.form)
