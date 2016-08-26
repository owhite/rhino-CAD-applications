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

        # config is the data structure that stores information for the most part
        # the program will load stuff from the document into config
        # if there's nothing in the document ask the user for a file to load into config
        # when user makes changes and selects buttons they get written into config
        # when the program closes config is dumped back into the document data. 
        self.config = cp.ConfigParser()

        # These are some of the parameters that get loaded into the form
        self.param_items = ('cut_dwell_time', 'cut_feed_rate', 'cut_power_level', 'engrave_feed_rate', 'engrave_power_level', 'engrave_dwell_time')

        # If the document doesnt have configuration data, throw some complaints
        if not rs.IsDocumentData():
            problem = True
        type = rs.GetDocumentData(section='gcode', entry = 'material')
        if len(type) == 0:
            problem = True
        else: # it's got data, try to load it
            for section in rs.GetDocumentData(section=None, entry=None):
                if not self.config.has_section(section):
                    self.config.add_section(section)
                for entry in rs.GetDocumentData(section=section):
                    self.config.set(section, entry, rs.GetDocumentData(section=section, entry=entry))

        # test if the config is happy
        if self.ConfigParamsAreBroke():
            problem = True

        if problem:
            # ask the user to find a config file
            result = rs.MessageBox ("No CNC information in document, load some?", buttons=1, title="CNC Information Missing")
            if result != 1:
                print "not loading .ini information, bailing"
                return
            else:
                # get data from disk
                self.LoadIniFile()

        # run another test
        if self.ConfigParamsAreBroke():
            # we still have a problem
            print "User supplied bad .ini file or document data has an issue"
            self.status = False

        return

    def ConfigParamsAreBroke(self):
        type = self.config.get('gcode', 'material')
        if len(type) == 0:
            return True
        else:
            # test if the config is happy
            for item in self.param_items:
                if len(self.config.get(type, item)) == 0:
                    return True

        if len(self.config.get('gcode', 'output_file')) == 0: return True
        if len(self.config.get('gcode', 'cut_part_flag')) == 0: return True
        if len(self.config.get('gcode', 'showpaths')) == 0: return True

        return False


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
        Row = (TableRow(Label (Text = "Output File:" ), self.outputFile))
        layout.Rows.Add(Row)

        type = self.config.get('gcode', 'material')

        # This should be more generalized for a day when there are other materials. 
        self.dd = DropDown()
        self.dd.Items.Add('steel')
        self.dd.Items.Add('wood')

        # this is amazing how you supply a callback to Eto.form objects
        self.dd.SelectedIndexChanged  += self.dd_list_clicked

        # Section where all material parameters are loaded
        Row = (TableRow(Label (Text = "Material Type:" ), self.dd))
        layout.Rows.Add(Row)

        self.data_label = Label(Text = "Data:")
        Row = (TableRow(self.data_label))
        layout.Rows.Add(Row)

        self.paramTBs = {}
        self.paramLabels = {}
        for item in self.param_items:
            tb = TextBox()
            self.paramTBs[item] = tb
            label = Label()
            self.paramLabels[item] = label
            Row = (TableRow(label, tb))
            layout.Rows.Add(Row)

        # Cut Part Checkbox
        self.cutpartsCB = CheckBox( Text = "Select = yes" )
        self.cutpartsCB.Checked = False
        Row = (TableRow(Label (Text = "Cut part:" ), self.cutpartsCB))
        layout.Rows.Add(Row)

        # Showpaths Checkbox
        self.showpathsCB = CheckBox( Text = "Select = yes" )
        self.showpathsCB.Checked = False
        Row = (TableRow(Label (Text = "Show paths:" ), self.showpathsCB))
        layout.Rows.Add(Row)

        Row = (TableRow(Label(Text = "                                      "))) # blank line
        layout.Rows.Add(Row)

        # Apply, reload and cancel buttons
        Row = (TableRow(Label(Text = "                                      "))) # blank line
        layout.Rows.Add(Row)
        apply = Button(Text = "Apply")
        apply.Click += self.apply_click
        cancel = Button(Text = "Cancel")
        cancel.Click += self.cancel_click
        reload = Button(Text = "Reload")
        reload.Click += self.reload_click
        Row = (TableRow(apply, reload, cancel))
        layout.Rows.Add(Row)

        self.UpdateForm()
        # Dialogue box stuff
        content = StackLayout(Spacing = 5)
        content.Items.Add(layout)

        self.dlg.DefaultButton = apply
        self.dlg.AbortButton = cancel
        self.dlg.Content = content;
        self.result = self.dlg.ShowModal(RhinoEtoApp.MainWindow)


    # handles loading all the config variables into form elements
    def UpdateForm(self):
        # Output file section
        self.outputFile.Text = self.config.get('gcode', 'output_file')

        type = self.config.get('gcode', 'material')

        # This should be more generalized for a day when there are other materials. 
        if (type == 'steel'): 
            self.dd.SelectedIndex = 0
        if (type == 'wood'): 
            self.dd.SelectedIndex = 1

        # Section where all material parameters are loaded
        for item in self.param_items:
            tb = self.paramTBs[item]
            tb.Text = self.config.get(type, item)
            x = re.sub(r'_',' ',item)
            label = self.paramLabels[item]
            label.Text = "  " + x + ":"

        # Cut Part Checkbox
        self.cutpartsCB.Checked = False
        if self.config.get('gcode', 'cut_part_flag') == "True":
            self.cutpartsCB.Checked = True

        # Showpaths Checkbox
        self.showpathsCB.Checked = False
        if self.config.get('gcode', 'showpaths') == "True":
            self.showpathsCB.Checked = True

    # User adjusted the drop down list 
    #  a callback
    def dd_list_clicked(self, sender, e):
        type = str(self.dd.SelectedValue)

        self.data_label.Text = type + " data:"
        for item in self.param_items:
            val = self.config.get(type, item)
            tb = self.paramTBs[item]
            tb.Text = self.config.get(type, item)

    # Callback - user poked at reload button
    def reload_click(self, sender, e):
        result = rs.MessageBox ("Delete and reload document data?", buttons=1, title="RELOAD")
        if result != 1:
            print "not loading .ini information, bailing"
            return
        else:
            rs.DeleteDocumentData()
            self.LoadIniFile()
            if self.ConfigParamsAreBroke():
                print "that file didnt work, better try again"
            else:
                self.UpdateForm()

    # Callback - user poked at apply button
    def apply_click(self, sender, e):
        self.dlg.Close(True) # true is return value

    # Callback - user poked the cancel button
    def cancel_click(self, sender, e):
        self.dlg.Close(False)

    # Write all the changes into the self.config
    def CaptureFormContents(self):
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

    if l.result: 
        l.CaptureFormContents()
        l.WriteDocumentData()
