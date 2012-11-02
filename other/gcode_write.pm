use strict;

package gcode_write;

sub new {
  my $invocant = shift;
  my $props = shift;
  my $global = shift;

  my $class = ref($invocant) || $invocant;
  my $self = { @_ };
  bless($self,$class)->init($props);
  $self->{'property'} = $props if (length($props) > 0);
  $self->{'property'} = $global if (length($global) > 0);

  return $self;
}

sub init {
  my $self = shift;


}

sub clear_gcode_data {
  my $self = shift;

  $self->{'gcoce_str'} = "";

}

sub write_gcode {
  my $self = shift;
  my $f = shift;
  my $timestamp = shift;

  $self->add_gcode_header();
  $self->cutting_tool_off;
  $self->add_gcode_footer();
  $self->cutting_tool_off;

  if(length($f) > 0) {
    open(F_OUT, ">$f") || die "cant write to $f\n";
  }
  else {
    open(F_OUT, ">&STDOUT");
  }

  my $total = 0;
  foreach my $line (split(/\n/,$self->{'gcode_str'})) {
    $total++;
  }

  my $unique_string = "(TIME :: $timestamp  LINES :: $total)";

  my $count = 1;
  my $first_time = 1;
  foreach my $line (split(/\n/,$self->{'gcode_str'})) {
    if ($line =~ /%/) {
      if ($first_time == 1) {
         printf F_OUT ("$unique_string\n");
      }
      else {
         printf F_OUT ("M2\n");
      }
      $first_time = 0;
    }
    else {
      printf F_OUT ("N%d $line\n", $count++);
    }
  }
  close(F_OUT);

  return($unique_string);
}

sub write_gcode_polyline {
  my $self = shift;
  my($p) = @_;
  my($i, $x, $y);
  my($cut_speed, $move_speed, $name);

  my $prop = $self->{'property'};


  # $global->{'default_cut_feed_rate'} = 40;
  # $global->{'default_move_feed_rate'} = 50;

  if($prop->{'use_gcode_cut_feed'} == 1) {
      $cut_speed = "\#<feedrate>";
  }
  elsif(length($prop->{$p->{'layer'}}->{'cut_feed_rate'}) > 0) {
    $cut_speed = $prop->{$p->{'layer'}}->{'cut_feed_rate'};
  }
  elsif(length($prop->{'default_cut_feed_rate'}) > 0) {
    $cut_speed = $prop->{'default_cut_feed_rate'};
  }
  else {
      $cut_speed = 10;
  }

  if(length($prop->{$p->{'layer'}}->{'move_feed_rate'}) > 0) {
    $move_speed = $prop->{$p->{'layer'}}->{'move_feed_rate'};
  }
  elsif(length($prop->{'default_move_feed_rate'}) > 0) {
    $move_speed = $prop->{'default_move_feed_rate'};
  }
  else {
      $move_speed = 10;
  }


  if(length($p->{'gcode_name'}) > 0) {
    $name = $p->{'gcode_name'};
  }

  if(length($prop->{$p->{'layer'}}->{'comment'}) > 0) {
    $self->{'gcode_str'} .=
      sprintf ("(%s)\n",$prop->{$p->{'layer'}}->{'comment'});
  }

  $x = $p->{0}->{'x'};
  $y = $p->{0}->{'y'};

  $self->_move_no_cut($x, $y, $move_speed, $name);

  $self->cutting_tool_on;
  for($i=1;$i<$p->{'count'};$i++) {
    $x = $p->{$i}->{'x'};
    $y = $p->{$i}->{'y'};
    $self->_move($x, $y, $cut_speed);
  }
  $self->cutting_tool_off;
  $self->{'gcode_str'} .=
    sprintf "\n";
}

sub cutting_tool_on {
  my $self = shift;

  if ($self->{'cutting_tool_toggle'} == 0) {
    $self->_gcode_oxygen_on;
    $self->_gcode_cutting_tool_on;
  }

  $self->{'cutting_tool_toggle'} = 1;
}

sub cutting_tool_off {
  my $self = shift;

  if ($self->{'cutting_tool_toggle'} == 1 ||
     length($self->{'cutting_tool_toggle'}) == 0) {
    $self->_gcode_oxygen_off;
    $self->_gcode_cutting_tool_off;
  }
  $self->{'cutting_tool_toggle'} = 0;
}

sub _move_no_cut {
  my $self = shift;
  my($x, $y, $speed, $name) = @_;

  $self->cutting_tool_off;

  if (length($name) > 0) {
      # $self->{'gcode_str'} .=
      # sprintf ("G00 X%0.4lf Y%0.4lf F%d (layer: %s)\n", $x, $y, $speed, $name);
    $self->{'gcode_str'} .=
      sprintf ("G00 X%0.4lf Y%0.4lf F%s (layer: %s)\n", $x, $y, $speed, $name);
  }
  else {
      # $self->{'gcode_str'} .=
      # sprintf ("G00 X%0.4lf Y%0.4lf F%d\n", $x, $y, $speed);
    $self->{'gcode_str'} .=
      sprintf ("G00 X%0.4lf Y%0.4lf F%s\n", $x, $y, $speed);
  }

  $self->{'gcode_str'} .=
    sprintf "\n";
}

sub _move {
  my $self = shift;
  my($x, $y, $speed, $name) = @_;

  if (length($name) > 0) {
      # $self->{'gcode_str'} .=
      # sprintf ("G01 X%0.4lf Y%0.4lf F%d (layer: %s)\n", $x, $y, $speed, $name);
      $self->{'gcode_str'} .=
	  sprintf ("G01 X%0.4lf Y%0.4lf F%s (layer: %s)\n",
		   $x, $y, $speed, $name);
  }
  else {
      # $self->{'gcode_str'} .=
      # sprintf ("G01 X%0.4lf Y%0.4lf F%d\n", $x, $y, $speed);
    $self->{'gcode_str'} .=
      sprintf ("G01 X%0.4lf Y%0.4lf F%s\n", $x, $y, $speed);
  }
}

sub _gcode_oxygen_on {
  my $self = shift;
  $self->{'gcode_str'} .=
    sprintf ("M64 P1 (GAS LINE ON)\n");

  $self->{'gcode_str'} .=
    sprintf ("M103 (creates a time stamp)\n");
}


sub _gcode_oxygen_off {
  my $self = shift;
  $self->{'gcode_str'} .=
    sprintf ("M65 P1 (GAS LINE OFF)\n");
}

sub _gcode_cutting_tool_on {
  my $self = shift;

  # printf ("thing: G4 P%s\n",
  # $self->{'property'}->{'gcode_dwell_time'});


  $self->{'gcode_str'} .=
    sprintf ("M64 P2 (LASER ON)\nG4 P%s\n",
    $self->{'property'}->{'gcode_dwell_time'});
}

sub _gcode_cutting_tool_off {
  my $self = shift;
  $self->{'gcode_str'} .=
    sprintf ("M65 P2 (LASER OFF)\n");
}

sub add_gcode_footer {
  my $self = shift;

  $self->cutting_tool_off;

  $self->{'gcode_str'} .=
      sprintf ("M65 P0 (VENTILATION OFF)\n");

  $self->{'gcode_str'} .=
      sprintf ("G1 X0.000 Y0.000 F%d (HOME AGAIN HOME AGAIN)\n",
	       $self->{'property'}->{'default_move_feed_rate'});

  $self->{'gcode_str'} .= "%\n";
}

sub add_gcode_header {
  my $self = shift;

  my $feedrate = $self->{'property'}->{'default_cut_feed_rate'};

  my $str;

  $str .= sprintf "%\n";
  if($self->{'property'}->{'use_gcode_cut_feed'} == 1) {
      $str .= sprintf "\#<feedrate>=$feedrate\n";
  }
  $str .= sprintf "G17 G20 G40 G49 S10\n";
  $str .= sprintf "G80 G90 \n";
  $str .= sprintf "G92 X0 Y0 (SET CURRENT POSITION TO ZERO)\n";
  $str .= sprintf "G64 P0.005\n";
  $str .= sprintf "M64 P0 (VENTILATION ON)\n";

  $self->{'gcode_str'} = $str . $self->{'gcode_str'};
}

1;
