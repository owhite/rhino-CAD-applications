import ConfigParser as cp
import rhinoscriptsyntax as rs
import clr
import re

clr.AddReference("Eto")
clr.AddReference("Rhino.UI")
from Rhino.UI import *
from Eto.Forms import Form, Dialog, Label, TextBox, StackLayout, StackLayoutItem, Orientation, Button, HorizontalAlignment, MessageBox, TableLayout, TableRow, TableCell, DropDown, CheckBox, RadioButton
from Eto.Drawing import *

class Layout:
    def __init__(self):
      problem = False

      self.config = cp.ConfigParser()

      # If the document doesnt have configuration data, throw some complains
      if not rs.IsDocumentData():
        problem = True
      if len(rs.GetDocumentData(section='gcode', entry = 'material')) == 0:
        problem = True

      if problem:
        result = rs.MessageBox ("No CNC information in document, load some?", buttons=1, title="CNC Information Missing")
        if result != 1:
          print "not loading .ini information, bailing"
          return
        else:
          self.LoadIniFile()
      else:
        for section in rs.GetDocumentData(section=None, entry=None):
          if not self.config.has_section(section):
            self.config.add_section(section)
          for entry in rs.GetDocumentData(section=section):
            self.config.set(section, entry, rs.GetDocumentData(section=section, entry=entry))

      if len(self.config.get('gcode', 'material')) == 0:
        # we still have a problem
        print "bad .ini file??"
        self.status = False
        return

      # Looks like we have document data, load it up
      for section in rs.GetDocumentData(section=None, entry=None):
        if not self.config.has_section(section):
          self.config.add_section(section)
        for entry in rs.GetDocumentData(section=section):
          self.config.set(section, entry, rs.GetDocumentData(section=section, entry=entry))

      # These are some of the parameters that get loaded into the form
      self.param_items = ('cut_dwell_time', 'cut_feed_rate', 'cut_power_level', 'engrave_feed_rate', 'engrave_power_level', 'engrave_dwell_time')

    def LoadIniFile(self):
        # Find an ini file
        filename = rs.OpenFileName("Open", "Config file (*.ini)|*.ini||")
        if not filename:
            return 0
            print "user didnt select ini file"
        else:
            # loads it into the config structure
            self.config.read(filename)
            # and stuff data into document
            for s in self.config.sections():
                for row in self.config.items(s):
                    (key, entry) = row
                    rs.SetDocumentData(s, key, entry)

    def MakeForm(self):
      self.dlg = Dialog[bool](Title = "Edit parameters", Padding = 10)
      label = Label(Text = "Enter a value:")

      layout = TableLayout()
      Spacing = Size(5, 5)

      # Output file section
      self.outputFile = TextBox()
      self.outputFile.Text = rs.GetDocumentData(section='gcode', entry='output_file')
      Row = (TableRow(Label (Text = "Output File:" ), self.outputFile))
      layout.Rows.Add(Row)

      type = self.config.get('gcode', 'material')

      # This should be more generalized for a day when there are other materials. 
      self.dd = DropDown()
      self.dd.Items.Add('steel')
      self.dd.Items.Add('wood')

      if (type == 'steel'): 
        self.dd.SelectedIndex = 0
      if (type == 'wood'): 
        self.dd.SelectedIndex = 1

      # this is amazing how you supply a callback to Eto.form objects
      self.dd.SelectedIndexChanged  += self.dd_list_clicked

      # Section where all material parameters are loaded
      Row = (TableRow(Label (Text = "Material Type:" ), self.dd))
      layout.Rows.Add(Row)

      self.data_label = Label(Text = "Data:")
      Row = (TableRow(self.data_label))
      layout.Rows.Add(Row)

      self.paramTBs = {}
      for item in self.param_items:
        tb = TextBox()
        self.paramTBs[item] = tb
        tb.Text = self.config.get(type, item)
        self.config.get(type, item)
        x = re.sub(r'_',' ',item)
        Row = (TableRow(Label (Text = "  " + x + ":"), tb))
        layout.Rows.Add(Row)

      # Cut Part Checkbox
      self.cutpartsCB = CheckBox( Text = "Select = yes" )
      self.cutpartsCB.Checked = False
      if self.config.get('gcode', 'cut_part_flag') == "True":
        self.cutpartsCB.Checked = True
      Row = (TableRow(Label (Text = "Cut part:" ), self.cutpartsCB))
      layout.Rows.Add(Row)

      # Showpaths Checkbox
      self.showpathsCB = CheckBox( Text = "Select = yes" )
      self.showpathsCB.Checked = False
      if self.config.get('gcode', 'showpaths') == "True":
        self.showpathsCB.Checked = True
      Row = (TableRow(Label (Text = "Show paths:" ), self.showpathsCB))
      layout.Rows.Add(Row)

      # Closing out with apply and cancel buttons
      apply = Button(Text = "Apply")
      apply.Click += self.apply_click
      Row = (TableRow(Label(Text = "                                      "))) # blank line
      layout.Rows.Add(Row)
      cancel = Button(Text = "Cancel")
      cancel.Click += self.cancel_click
      Row = (TableRow(apply, cancel))
      layout.Rows.Add(Row)

      # Dialogue box stuff
      content = StackLayout(Spacing = 5)
      content.Items.Add(layout)

      self.dlg.DefaultButton = apply
      self.dlg.AbortButton = cancel
      self.dlg.Content = content;
      self.result = self.dlg.ShowModal(RhinoEtoApp.MainWindow)

    # User adjusted the drop down list 
    #  a callback
    def dd_list_clicked(self, sender, e):
      type = str(self.dd.SelectedValue)

      self.data_label.Text = type + " data:"
      for item in self.param_items:
        val = self.config.get(type, item)
        tb = self.paramTBs[item]
        tb.Text = self.config.get(type, item)

    # User poked at apply button
    #  a callback
    def apply_click(self, sender, e):
      self.dlg.Close(True) # true is return value

    # User poked the cancel button
    #  a callback
    def cancel_click(self, sender, e):
      self.dlg.Close(False)

    # Write all the changes into the self.config
    #  and then update the document data. 
    def DumpFormContents(self):
      self.config.set('gcode', 'output_file', self.outputFile.Text)
      self.config.set('gcode', 'showpaths', "False")
      if self.showpathsCB.Checked:
        self.config.set('gcode', 'showpaths', "True")

      self.config.set('gcode', 'cut_part_flag', "False")
      if self.cutpartsCB.Checked:
        self.config.set('gcode', 'cut_part_flag', "True")

      type = str(self.dd.SelectedValue)

      self.config.set('gcode', 'material', type)

      for item in self.param_items:
        tb = self.paramTBs[item]
        self.config.set(type, item, tb.Text)

      self.WriteDocumentData()

    # Everything is loaded into self.config, write that into the document
    #   separate function because it might get called by other functions
    #   at some point
    def WriteDocumentData(self):
      for s in self.config.sections():
        for row in self.config.items(s):
          (key, entry) = row
          rs.SetDocumentData(s, key, entry)


if __name__ == '__main__':
  l = Layout()
  l.MakeForm()

  if l.result: l.DumpFormContents()
