import rhinoscriptsyntax as rs
import ConfigParser
import StringIO

notes = rs.Notes()

if notes: 
    buf = StringIO.StringIO(notes)
    config = ConfigParser.ConfigParser()
    config.readfp(buf)
    if config.has_option('LAYER_POWER', 'CUTS'):
        result = config.get('LAYER_POWER', 'CUTS')
        print result

else:
    rs.Command("!_Notes")
    print "no notes"

