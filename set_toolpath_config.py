#!/usr/bin/env python

import clr
clr.AddReference("Eto")
clr.AddReference("Rhino.UI")

from Rhino.UI import *
from Eto.Forms import Form, Dialog, Label, TextBox, StackLayout, StackLayoutItem, Orientation, Button, HorizontalAlignment, MessageBox
from Eto.Drawing import *
import os
import random
import ConfigParser


class interface:
    def __init__(self, name):
        (head, tail) = os.path.split(file_name)
        if len(head) == 0:
            self.config_file_path = os.getcwd()
        self.config_file = tail

        print "loading: %s" % file_name

        parser = ConfigParser.RawConfigParser()
        parser.read(file_name)

        self.config_parser = parser

        self.showpaths = parser.getboolean('layers', 'showpaths')
        self.move_feed_rate = parser.getint('gcode', 'move_feed_rate')
        self.cut_feed_rate = parser.getint('gcode', 'cut_feed_rate')
        self.dwell_time = parser.getfloat('gcode', 'dwell_time')

        from os.path import join as pjoin
        self.output_file = pjoin(parser.get('gcode', 'ncfile_dir'), 
                                 parser.get('gcode', 'output_file'))
        self.addControls()


    # Add each control to an accumulated list of controls
    def addControls(self):
        dlg = Dialog[bool](Title = "Some Dialog", Padding = Padding(10))

        label = Label(Text = "Enter a value:")

        textBox = TextBox()

        entry = StackLayout(Spacing = 5, Orientation = Orientation.Horizontal)
        entry.Items.Add(label)
        entry.Items.Add(textBox)

        apply = Button(Text = "Apply")
        def apply_click(sender, e): dlg.Close(True) # true is return value
        apply.Click += apply_click

        cancel = Button(Text = "Cancel")
        def cancel_click(sender, e): dlg.Close(False)
        cancel.Click += cancel_click

        buttons = StackLayout(Spacing = 5, Orientation = Orientation.Horizontal)
        buttons.Items.Add(cancel)
        buttons.Items.Add(apply)

        content = StackLayout(Spacing = 5) # default orientation is vertical
        content.Items.Add(entry)
        content.Items.Add(StackLayoutItem(buttons, HorizontalAlignment.Right))

        dlg.DefaultButton = apply
        dlg.AbortButton = cancel
        dlg.Content = content;

if __name__ == '__main__':
    t = interface('polyline_dump.ini')

