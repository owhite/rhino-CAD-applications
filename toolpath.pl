#!/usr/bin/perl

require "getopts.pl";
require "morph.ph";
require "funcs.ph";

use strict;
use rhino_parse;
use gcode_write;
use polygon;
use File::Copy;


# ./toolpath.pl -u laptop -i tmp1.3dm -d tmp2.3dm -r -g thing.ngc
#    or
# ./toolpath.pl -c config.file 
# tour methods 
#    salesman
#    grid_tour
#    line_tour

&Getopts('i:d:g:P:C:tcv');

use vars qw($opt_i $opt_d $opt_g $opt_c $opt_v $opt_P $opt_t $opt_C $global);

my ($global);

my ($second, $minute, $hour) = localtime();

$global->{'total_salesman'} = 0;
$global->{'clock_time'} = "$hour:$minute:$second";
$global->{'verbose'} = 0;
$global->{'tour_executable'} = "/usr/bin/LKH.UNIX";
$global->{'default_move_feed_rate'} = 30;
$global->{'default_cut_feed_rate'} = 30;
$global->{'use_gcode_cut_feed'} = 1;
$global->{'tag'} = "";

my $parts_layer = "PARTS";
my $cuts_layer = "CUTS";
my $path_layer = "PATH";
my $cutpath_layer = "CUTPATH";

my (%config, $input_file, $gcode_file, $dump_file, $base_url);

# opt start...

$global->{'verbose'} = 1 if ($opt_v == 1);
$global->{'report_tag'} = 1 if ($opt_t == 1);

my $ini_file;
if ($opt_c == 1) {
    # this only works when called from axis
    foreach my $key (sort(keys %ENV)) {
	$ini_file = $ENV{$key} if ($key eq "INI_FILE_NAME");
    }

    die("cant find config file") if (length($ini_file) == 0 && $global->{'verbose'} != 0);
    exit() if (length($ini_file) == 0);
}

$ini_file = $opt_C if (length($opt_C) > 0);

if (length($ini_file) > 0) {
    
    print "Found config file: $ini_file\n" if ( $global->{'verbose'} != 0);

    # config file
    open(F_IN, "$ini_file") || die("cant open: $ini_file");
    while(<F_IN>) {
	s/\n//;
	# print $_ . "\n";
	if (/^[^\#]/ && /(.*)\s+=\s+(.*)/) {
	    # print "HERE: $1 : $2\n";
	    $config{$1} = $2;
	}
    }
    close(F_IN);
}


if(length($opt_i) > 0) {
    $input_file = $opt_i;
} 
elsif (length($config{'TOOLPATH_INPUT_FILE'}) > 0) {
    $input_file = $config{'TOOLPATH_INPUT_FILE'};
    if (length($config{'TOOLPATH_INPUT_DIR'}) > 0) {
	$input_file = $config{'TOOLPATH_INPUT_DIR'} . "/" . $input_file;
    }
}
else {
    die "must supply an input file with -i";
}


my $gcode_deposit_dir;


if (length($config{'TOOLPATH_GCODE_FILE'}) > 0) {
    $gcode_file = $config{'TOOLPATH_GCODE_FILE'};
    if (length($config{'PROGRAM_PREFIX'}) > 0) {
	$gcode_deposit_dir = $config{'PROGRAM_PREFIX'};
    }

}
elsif (length($opt_g) > 0) {
    $gcode_file = $opt_g;
}
else {}

if (length($config{'TOOLPATH_DUMP_FILE'}) > 0) {
    $dump_file = $config{'TOOLPATH_DUMP_FILE'};
    if (length($config{'TOOLPATH_INPUT_DIR'}) > 0) {
	$dump_file = $config{'TOOLPATH_INPUT_DIR'} . "/" . $dump_file;
    }

}
elsif (length($opt_d) > 0) {
    $dump_file = $opt_d;
}
else {}

$global->{'default_power_setting'} = 95;
if (length($opt_P) > 0) {
    $global->{'default_power_setting'} = $opt_P;
}

if (length($config{'GCODE_DWELL_TIME'}) > 0) {
    $global->{'gcode_dwell_time'} = $config{'GCODE_DWELL_TIME'};
}
else {
    $global->{'gcode_dwell_time'} = 0.2;
}


$global->{'t_str'} = "";

toolpath( $gcode_deposit_dir, $input_file, $gcode_file, $cuts_layer, $path_layer, $cutpath_layer, $dump_file);

print $global->{'t_str'} if ($global->{'verbose'} != 0);

# --------------------------------------------------

sub toolpath {

    ($gcode_deposit_dir,
     $input_file, 
     $gcode_file, 
     $cuts_layer, 
     $path_layer, 
     $cutpath_layer, 
     $dump_file) = @_;

    print "fetching: $input_file\n" if ($global->{'verbose'} != 0);

    my $start_time = time();

    my $colors;
    $colors->{"CUTS"} = "red";
    $colors->{"PARTS"} = "blue";
    $colors->{"PATH"} = "green";
    $colors->{"CUTPATH"} = "purple";

    my $polyline_struct = polygon->new();
    $polyline_struct->set(rs2poly($input_file, $colors));

    # dumb place for this code to exist, should happen in rs2poly
    $polyline_struct->set_all_bounds;

    my $dump = rhino_parse->new();
    $dump->add_layer($cuts_layer, "255 0 0");
    $dump->add_layer($parts_layer, "0 0 255");
    $dump->add_layer($path_layer, "0 255 0");
    $dump->add_layer($cutpath_layer, "125 38 205");

    my $user_supplied_path;
    my $gcode;
    if (length($gcode_file) > 0) {
	$gcode = gcode_write->new(1,$global);
    }

    my $points;

    my $count = 0;
    my $parts = polygon->new();
    foreach my $p ($polyline_struct->polylines_by_layer($parts_layer)) {
	$parts->add($polyline_struct->{$p});
	$points->{$count}->{'x'} = $polyline_struct->{$p}->{0}->{'x'};
	$points->{$count}->{'y'} = $polyline_struct->{$p}->{0}->{'y'};
	$count++;
    }
    $points->{'count'} = $count;

    # check the layout, see if there is a line connecting the parts
    my($user_supplied_path) = $polyline_struct->get_vertices_by_layer($path_layer);

    my @tour = create_tour(points => $points,
			   part_path => $user_supplied_path,
			   parts => $parts,
			   origin_x => 0,
			   origin_y => 0);

    # done establishing the parts that will be cut, now
    # work on the cuts for each part...

    my $cuts = polygon->new();
    foreach my $p ($polyline_struct->polylines_by_layer($cuts_layer)) {
	$cuts->add($polyline_struct->{$p});
    }

    # no idea of what this does
    if ($cuts->polyline_is_clockwise2d($points)) {
	my @l = @tour;
	@tour = (shift(@l), reverse(@l));
    }

    # check the layout, see if there are lines connecting cuts
    my $cutpath = polygon->new();
    foreach my $p ($polyline_struct->polylines_by_layer($cutpath_layer)) {
	$cutpath->add($polyline_struct->{$p});
    }

    if ($parts->{'count'} != 0) {

	cut_parts($dump, $parts, $cuts, $cutpath, \@tour, $gcode, $polyline_struct);

	write_part_tour($dump, $points, @tour) if (length($dump_file) > 0);

	if (defined($gcode)) {
	    my $tmp = "/tmp/" . $gcode_file;
	    $global->{'tag'} = $gcode->write_gcode($tmp, $global->{'clock_time'});

	    my $f = $gcode_deposit_dir . "/" . $gcode_file;
	    move($tmp, $f);
	}
    } 
    else {
	$global->{'t_str'} .= "ERROR: got no parts to cut on layer: $parts_layer" 
    }

    my $response;


    print "dumping $gcode_file to: $gcode_deposit_dir\n" if ($global->{'verbose'} != 0);

    $global->{'t_str'} .= "look for this tag:: " if ($global->{'verbose'} != 0);
    $global->{'t_str'} .= "$global->{'tag'}\n" if ($global->{'verbose'} != 0);

    $global->{'t_str'} .= "DONE\n" if ($global->{'verbose'} != 0);


    print "TAG :: $global->{'tag'}\n" if ($global->{'report_tag'} != 0);

}

sub cut_parts {
    my($dump, $parts, $cuts, $cutpath, $tour, $gcode, $polyline_struct) = @_;

    my $done;
    # we have established a tour for all parts
    # pull each one and define the cuts
    foreach my $part (@$tour) {

	$global->{'t_str'} .= " part: $part\n" if ($global->{'verbose'} != 0);
	
	# see if there is a path inside the part to cut parts
	my $user_supplied_path;
	foreach my $c (polylines_overlap_polyline($cutpath, 
						  $parts->{$part}, 
						  $polyline_struct)) {
	    $user_supplied_path = $cutpath->{$c};

	    # there better be just one! 
	    last;
	}

	my $cut_set = polygon->new();
	my $points;

	my $count = 0;
	foreach my $c (polylines_overlap_polyline($cuts, 
						  $parts->{$part}, 
						  $polyline_struct)) {
	    if ($done->{$c} != 1) {
		$points->{$count}->{'x'} = $cuts->{$c}->{0}->{'x'};
		$points->{$count}->{'y'} = $cuts->{$c}->{0}->{'y'};
		$points->{$count}->{'part_number'} = $c;

		$cut_set->add($cuts->{$c});

		$count++;

	    } else {
		# for some reason cuts get found more than once.
	    }
	    $done->{$c} = 1;
	}
	$points->{'count'} = $count;

	my $x = $parts->{$part}->{$parts->{$part}->{'count'}-1}->{'x'};
	my $y = $parts->{$part}->{$parts->{$part}->{'count'}-1}->{'y'};

	if ($points->{'count'} > 0) {
	    $global->{'t_str'} .= "  Creating part path... $count cuts\n" if ($global->{'verbose'} != 0);

	    my @l = create_tour(points => $points,
				part_path => $user_supplied_path,
				parts => $cut_set,
				origin_x => $x,
				origin_y => $y);

	    $global->{'t_str'} .= "  ...done\n" if ($global->{'verbose'} != 0);
	    
	    foreach my $p (@l) {
		my $ptr = $cuts->{$points->{$p}->{'part_number'}};
		$dump->add_polygon($ptr, "CUTS") if (length($dump_file) > 0); 
		$gcode->write_gcode_polyline($ptr) if (defined($gcode));
	    }

	    write_part_tour($dump, $points, @l) if (length($dump_file) > 0);

	} 
	else {
	    $global->{'t_str'} .= "  no cuts in part: $part\n" if ($global->{'verbose'} != 0);
	}

	$dump->add_polygon($parts->{$part}, "PARTS") if (length($dump_file) > 0); 
	$gcode->write_gcode_polyline($parts->{$part}) if (defined($gcode));
    }

    return($done);
}

sub _get_distance {
    my ($x1, $y1, $x2, $y2) = @_;

    my $xdistance=abs(($x1-$x2)*($x1-$x2));
    my $ydistance=abs(($y1-$y2)*($y1-$y2));

    return (sqrt($xdistance+$ydistance));
}

sub write_part_tour {
    my($dump, $pts, @l) = @_;

    my $count = 0;
    my $path;
    foreach my $part (@l) {

	$path->{$count}->{'x'} = $pts->{$part}->{'x'};
	$path->{$count}->{'y'} = $pts->{$part}->{'y'};
	$path->{$count}->{'z'} = 0;

	$count++;

    }
    $path->{'count'} = $count;

    $dump->add_polygon($path, "PATH");
}


sub polylines_overlap_polyline {
    my($polylines, $part, $polyline_struct) = @_;
    my (@l);

    for (my $j=0; $j < $polylines->{'count'}; $j++) {

	my $ptr = $polylines->{$j};

	if ($polyline_struct->polyline_overlaps($ptr, $part)) {
	    push(@l, $j);
	}

    }

    return(@l);
}

sub name_gcodefile {
    my($n, $count) = @_;
    
    if ($n =~ /(\..*)/) {
	my $ext = $1;
	$n =~ s/\..*//;
	$n = $n . "_" . $count . $ext;
    } else {
	die ("was expecting some type of extension in gcode file name (e.g., \".ngc\")");
    }

    return($n);
}

sub rs2poly {
    my($file) = shift;
    my($colors) = shift;

    my ($p_struct, $done, $count);
    $count = 0;
    open(F_IN, $file) || die "cant open: $file";
    while (<F_IN>) {
	s/\n//;
	my($UID, $layer, $i, $x, $y) = split(/\s/,$_);

	$count++ if ($done->{$UID} != 1);
	$done->{$UID} = 1;

	$p_struct->{$count-1}->{$i}->{'x'} = $x;
	$p_struct->{$count-1}->{$i}->{'y'} = $y;
	$p_struct->{$count-1}->{'count'} = $i + 1;

	if(length($colors->{$layer}) > 0) {
	    $p_struct->{$count-1}->{'color'} = $colors->{$layer};
	}
	else {
	    $p_struct->{$count-1}->{'color'} = "black";
	}

	$p_struct->{$count-1}->{'layer'} = $layer;

	$p_struct->{'count'} = $count;

    }

    return($p_struct);
}


sub create_tour {
    my $opts;
    while (@_ && !ref $_[0]) {   
	my $key     = shift;
	$opts->{$key} = shift;
    }

    my $points = $opts->{points};
    $global->{'t_str'} .= "ERROR no points sent to create_tour\n" unless $points;

    my $tour_method;
    if ($opts->{part_path}) {
	$tour_method = "line_tour";
    }
    else{
	$tour_method = "salesman";
    }


    my @l;

    if ($tour_method eq "salesman") {
	@l = create_salesman_tour($points);
    } elsif ($tour_method eq "line_tour") {
	@l = tour_parts_by_line($opts);
    } else {
	@l = create_dumb_tour($points);
    }
    
    if (length($opts->{origin_x}) > 0 && length($opts->{origin_y}) > 0) {
	@l = rotate_loop($opts->{origin_x}, $opts->{origin_y}, $points, @l);
    }

    return(@l);
}

sub rotate_loop {
    my($x, $y, $points, @list) = @_;
    my ($i, $item, $d1, $d2, $count);

    my $d2 = _get_distance($x,$y,$points->{0}->{'x'},$points->{0}->{'y'});

    $item = 0;

    $count = 0;
    foreach $i (@list) {
	$d1 = _get_distance($x,$y,
			    $points->{$i}->{'x'},
			    $points->{$i}->{'y'});

	if ($d1 < $d2) {
	    $item = $count;
	    $d2 = $d1;
	}
	$count++;
    }
    
    my @l;
    for($i=$item; $i<$points->{'count'}; $i++) {
	push(@l, $list[$i]);
    }
    for($i=0; $i<$item; $i++) {
	push(@l, $list[$i]);
    }

    return(@l);
}

sub tour_parts_by_line {
    my $opts = shift;

    my $path = $opts->{part_path};
    my $parts = $opts->{parts};
    my $self = $opts->{parts};

    my ($line, $done, @list);
    for (my $i=0;$i<$path->{'count'}-1;$i++) {

	$line->{0}->{'x'} = $path->{$i}->{'x'};
	$line->{0}->{'y'} = $path->{$i}->{'y'};
	$line->{1}->{'x'} = $path->{$i + 1}->{'x'};
	$line->{1}->{'y'} = $path->{$i + 1}->{'y'};
	$line->{'count'} = 2;

	my $x = $line->{0}->{'x'};
	my $y = $line->{0}->{'y'};

	my @tmp;
	for(my $j=0;$j<$parts->{'count'};$j++) {
	    if ($done->{$j} != 1) {
		my $ptr = $parts->{$j};
		my $box = _get_bounding_box($ptr);
		my $r = $self->polyline_crosses($line, $box);
		if ($r) {
		    my $dist = _get_nearest_dist($x, $y, $r);
		    push(@tmp, $dist . " " . $j);
		    $done->{$j} = 1;
		}
	    }
	}

	foreach my $e (sort by_number (@tmp)) {
	    $e =~ s/.* //;
	    push(@list, $e);
	}
    }

    return(@list);
}

sub _get_nearest_dist {
    my($x, $y, $ptr) = @_;

    my ($i, $d_sq);
    my $rot   = 0;
    my $dmin_sq = sqrt(($ptr->{0}->{'x'}-$x)**2 + ($ptr->{0}->{'y'}-$y)**2);

    for(my $i=0; $i < $ptr->{'count'}; $i++) {

	$d_sq = sqrt(($ptr->{$i}->{'x'}-$x)**2 + ($ptr->{$i}->{'y'}-$y)**2);

	$dmin_sq = min($dmin_sq, $d_sq);
    }

    return($dmin_sq);
}

sub _get_bounding_box {
    my $p = shift;
    my $b;

    $b->{0}->{'x'} = $p->{'min_x'};
    $b->{0}->{'y'} = $p->{'min_y'};

    $b->{1}->{'x'} = $p->{'max_x'};
    $b->{1}->{'y'} = $p->{'min_y'};

    $b->{2}->{'x'} = $p->{'max_x'};
    $b->{2}->{'y'} = $p->{'max_y'};

    $b->{3}->{'x'} = $p->{'min_x'};
    $b->{3}->{'y'} = $p->{'max_y'};

    $b->{4}->{'x'} = $p->{'min_x'};
    $b->{4}->{'y'} = $p->{'min_y'};

    $b->{'count'} = 5;
    return($b);
}


sub dump_polyline_struct {
    my ($s) = shift;
    for(my $j=0; $j < $s->{'count'}; $j++) {
	$global->{'t_str'} .= "LINE: $j\n"  if ($global->{'verbose'} != 0);
	dump_vector($s->{$j});
    }
}


sub dump_vector {
    my ($p) = shift;
    for(my $j=0; $j < $p->{'count'}; $j++) {
	$global->{'t_str'} .= "$j :: $p->{$j}->{'x'} :: $p->{$j}->{'y'}\n" if ($global->{'verbose'} != 0);
    }
}

sub create_dumb_tour {
    my($points) = @_;

    # deal with situations with small number of datapoints
    if ($points->{'count'} == 1) {
	return(0);
    }

    if ($points->{'count'} == 0) {
	$global->{'t_str'} .= "ERROR call to create tour with polyline containing no points\n";
	exit(1);
    }

    my @l;
    my $i;
    for($i=0;$i<$points->{'count'};$i++) {
	push (@l, $points->{$i}->{'x'} . " " . $i);
    }

    my(@l2);
    foreach $i (sort by_number (@l)) {
	$i =~ s/.* //;
	push(@l2, $i);
    }

    return(@l2);
}

# This traveling salesman solution (LKH.UNIX) thanks to Keld Helsgaun.
#    http://www.akira.ruc.dk/~keld/
sub create_salesman_tour {
    my($points) = @_;

    # deal with situations with small number of datapoints
    if ($points->{'count'} == 1) {
	return(0);
    }

    my $start_time = time();

    my $param_file = "/tmp/tmp_param_file";
    my $input_file = "/tmp/tmp_input_file";
    my $output_file = "/tmp/tmp_output_file";

    open(PAR_FILE,">$param_file") || die("cant write file: $param_file");
    print PAR_FILE "PROBLEM_FILE = $input_file\n";
    print PAR_FILE "TOUR_FILE = $output_file\n";
    close(PAR_FILE);

    if ($points->{'count'} == 0) {
	$global->{'t_str'} .=  "ERROR call to create tour with polyline containing no points\n";
    }
    if ($points->{'count'} == 2) {
	return(0,1);
    }

    open(F_OUT, ">$input_file") || die("cant write: $input_file");
    print F_OUT "NAME : inputfile\n";
    print F_OUT "TYPE : TSP\n";
    print F_OUT "COMMENT : COMMENT\n";
    print F_OUT "DIMENSION : $points->{'count'}\n";
    print F_OUT "EDGE_WEIGHT_TYPE : EUC_2D\n";
    print F_OUT "NODE_COORD_SECTION\n";

    my ($t1, $t2);
    if ($points->{'count'} > 120) {
	$global->{'t_str'} .= "ERROR Be advised: the toolpath is processing $points->{'count'} points. Lists with\n";
	$global->{'t_str'} .= "ERROR  that many vertices require a bit of a wait.\n";
	$t1 = time();
    }
    
    my $i;
    for($i=0;$i<$points->{'count'};$i++) {
	printf F_OUT ("%d %lf %lf\n",
		      $i+1,
		      $points->{$i}->{'x'},
		      $points->{$i}->{'y'});
    }

    print F_OUT "EOF\n";
    close(F_OUT);

    my $cmd = "echo $param_file | $global->{'tour_executable'} > /dev/null";
    system($cmd);

    my(@l);
    my $start = 0;
    open(F_IN, "$output_file") || die("cant open: $output_file");
    while(<F_IN>) {

	s/\n//;

	$start = 0 if(/-1/);
	if ($start == 1) {
	    my $n = int($_-1);
	    push(@l,$n); 
	}
	$start = 1 if(/TOUR_SECTION/);
    }

    close(F_IN);

    if (length($t1) > 0) {
	$t2 = time();
	$global->{'t_str'} .= ("WARNING:  %d seconds TSP time\n", $t2 - $t1);
    }

    unlink($param_file);
    unlink($input_file);
    unlink($output_file);

    my $end = time();

    $global->{'total_salesman'} += ($end - $start_time);

    return(@l);
}

