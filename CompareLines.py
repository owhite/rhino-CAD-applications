import rhinoscriptsyntax as rs
import ConfigParser
import StringIO

notes = rs.Notes()

if notes: 
    buf = StringIO.StringIO(notes)
    config = ConfigParser.ConfigParser()
    config.readfp(buf)
    print config.get('LAYERS', 'Layer1')
