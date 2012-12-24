[Variables]
raw_input_file = rhino2nc_dump.txt
output_file = thing.txt

[Layers]
parts_name   = PARTS
cuts_name    = CUTS
path_name    = PART_PATH
cutpath_name = CUTS_PATH

parts_color   = 0,0,255
cuts_color    = 255,0,0
path_color    = 0,0,0
cutpath_color = 0,255,0

[Gcode]
use_cut_variable = True
move_feed_rate = 30
cut_feed_rate = 15
power_setting = 65
dwell_time = 0.2
output_file = thing.nc

[Debug]
debug = True
debug_file_name = thing.png

[TSP]
start_temp = 10.0
alpha = .6
iterations = 200000