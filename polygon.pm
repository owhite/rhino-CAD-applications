package polygon;

use strict;
use Carp;
use Storable;
use Math::Vec qw(NewVec);
use Math::Trig;
use Math::Matrix;
use POSIX        qw/floor/;

use vars qw( $precision );
$precision = 7;

# in some cases if there are calls to Math::Geometry::Planar;
#  the problem is that the module only works in two dimensions
#  and the structure of polylines that go into the module
#  doesnt allow the user to store things I need, like layer.
#
#   http://search.cpan.org/~dvdpol/Math-Geometry-Planar-1.14/Planar.pm

# use Math::Geometry::Planar;

sub new {
  my $invocant = shift;
  my $struct = shift;
  my $class = ref($invocant) || $invocant;
  my $self = { @_ };

  bless($self,$class)->init();

  return $self;
}

sub init {
  my $self = shift;

  $self->{'count'} = 0;

}

sub set {
  my $self = shift;
  my $struct = shift;

  #erase...
  my $i;
  for($i = 0; $i < $self->{'count'}; $i++) {
    undef($self->{$i});
  }

  my $i;
  for($i = 0; $i < $struct->{'count'}; $i++) {
      $self->{$i} = _deep_copy($struct->{$i});
  }

  $self->{'count'} = $i;

}


sub add {
  my $self = shift;
  my $ptr = shift;

  my $count = $self->{'count'};
  $self->{$count} = _deep_copy($ptr);
  $self->{'count'}++;
}

sub flatten_triangle {
  my($self) = shift;
  my($p) = shift;

  my $debug = 0;
  print_results($p) if ($debug == 1);

  # scalene triangle area
  #  http://www.ajdesigner.com/phptriangle/scalene_triangle_area_k.php
  #  this uses the naming conventions of that picture
  # $p->{1} will be the origin, the line formed by 
  #  $p->{1} and $p->{2} will be the base

  my ($a, $b, $c);
  $a = _get_d_from_points($p->{1}, $p->{2});
  $b = _get_d_from_points($p->{0}, $p->{1}); # this is treated as the base
  $c = _get_d_from_points($p->{0}, $p->{2});

  print "sides: $a :: $b :: $c\n" if ($debug == 1);
  if ($a == 0 || $b == 0 || $c == 0) {
    print "something is wrong with sides of polygon\n";    
  }

  my $q;

  # these things are always true
  $q->{'count'} = 3;
  $q->{0}->{'z'} = 0;
  $q->{1}->{'z'} = 0;
  $q->{2}->{'z'} = 0;
  $q->{'point_to_z'} = $p->{'point_to_z'};

  $q->{0}->{'x'} = 0;
  $q->{0}->{'y'} = 0;

  $q->{1}->{'x'} = $b;
  $q->{1}->{'y'} = 0;

  # calculate area for a scalene triangle

  my $area = _get_triangle_area($a, $b, $c);

  # calculate height for a scalene triangle
  my $h = (2 * $area) / $b;

  $q->{2}->{'y'} = $h;

  # $h is the height of a right triangle, with hypotenuse length $a
  #  Props to Pythagoras:

  $q->{2}->{'x'} = sqrt(($c*$c) - ($h*$h));

  my $orientation = _get_normal2($q);

  print "Orientation : $orientation :: $q->{'point_to_z'}\n"  if ($debug == 1);
  print_results($q) if ($debug == 1);

  if ($orientation != $q->{'point_to_z'}) {
    print " orientation got wierd\n" if ($debug == 1);
    $q->{1}->{'x'} *= -1;
    $q->{2}->{'x'} *= -1;
    print_results($q) if ($debug == 1);
  }

  return($q);
}



# this function takes a profile, which basically serves 
#  as a function. given the height of polyline this function 
#  will modify the x values of the input polyline. 
#  new versions could be made for functions that work for y and z values.
sub map_x_to_poly {
  my $p = shift;
  my ($poly, $profile) = @_;

  # what was the scale between poly and profile?
  my $scale = ($poly->{'max_y'} - $poly->{'min_y'}) / ($profile->{'max_y'} - $profile->{'min_y'});

  # conversion factor for the p2 in x
  my $dist_x = ($profile->{'max_x'} - $profile->{'min_x'}) * $scale;

  my ($line, $i);
  for ($i=0;$i<$poly->{'count'};$i++) {
    # this is the relative height up $poly
    my $h = ($poly->{$i}->{'y'} - $poly->{'min_y'}) / 
      ($poly->{'max_y'} - $poly->{'min_y'});


    # which corresponds to the this height on $profile
    $h = $profile->{'min_y'} + (($profile->{'max_y'} - $profile->{'min_y'}) * $h);
    # whats the x file for this height on profile?
    my (@l) = $p->get_xz_positions($h, $profile);
    my $x = $l[0]->[0];

    # that's nice, scale between zero and one
    $x = ($x - $profile->{'min_x'}) /
      ($profile->{'max_x'} - $profile->{'min_x'});

    # now use this value to create a new x
    $line->{$i}->{'x'} = $poly->{$i}->{'x'} + ($x * $dist_x);
    $line->{$i}->{'y'} = $poly->{$i}->{'y'};
    $line->{$i}->{'z'} = $poly->{$i}->{'z'};
  }

  $line->{'count'} = $i;

  $p->set_polyline_bounds($line);

  return($line);
}

sub scale_polyline_to_polyline {
  my($self) = shift;
  my($from_part, $to_part) = @_;

  my $d1 = $self->get_distance($from_part->{0}->{'x'},
			 $from_part->{0}->{'y'}, 0,
			 $from_part->{$from_part->{'count'}-1}->{'x'},
			 $from_part->{$from_part->{'count'}-1}->{'y'},0);

  my $d2 = $self->get_distance($to_part->{0}->{'x'},
			$to_part->{0}->{'y'}, 0,
			$to_part->{$to_part->{'count'}-1}->{'x'},
			$to_part->{$to_part->{'count'}-1}->{'y'},0);
  my $div = $d2 / $d1;

  $self->polyline_scale($from_part, 
		     $from_part->{0}->{'x'}, 
		     $from_part->{0}->{'y'}, 
		     0, $div, $div, $div);

  $self->align_part($from_part, 
		 $to_part->{0}->{'x'},
		 $to_part->{0}->{'y'},
		 $to_part->{$to_part->{'count'}-1}->{'x'},
		 $to_part->{$to_part->{'count'}-1}->{'y'});

}

sub array_along_curve {
  my ($self) = shift;
  my ($part, $line, $total_parts, $percent) = @_;

  my $part_distance = $self->get_distance($part->{0}->{'x'},
				   $part->{0}->{'y'},
				   0,
				   $part->{$part->{'count'}-1}->{'x'},
				   $part->{$part->{'count'}-1}->{'y'},
				  0);
  $part_distance *= $total_parts;
  my $length = $self->get_length_along_line($line);
  $self->scale_part($part, $part_distance, $length);
  my $part_distance = $self->get_distance($part->{0}->{'x'},
				   $part->{0}->{'y'},
				   0,
				   $part->{$part->{'count'}-1}->{'x'},
				   $part->{$part->{'count'}-1}->{'y'},
				  0);

  my ($first_part, $last_part);
  $last_part = _deep_copy($part);
  if (length($percent) > 0) {
    $self->scale_part($last_part, $part_distance, $part_distance * $percent);
  }

  my $d = 0;
  my @l;
  my $composite;
  $composite->{'count'} = 0;
  my $first_time = 1;
  while ($part_distance < $length - $d) {
  
    if ($first_time == 1) {
      ($d, $last_part) = $self->align_segment_climb_up_line($line, $d, $last_part);
      $self->append_polyline($last_part, $composite);
    }
    else {
      ($d, $part) = $self->align_segment_climb_up_line($line, $d, $part);
      $self->append_polyline($part, $composite);
    }
    $first_time = 0;
  }

  my ($x1, $y1, $z1) = $self->point_by_travel_distance($line,$d);
  my $length = $self->get_distance($x1, $y1, $z1,
			    $line->{$line->{'count'}-1}->{'x'}, 
			    $line->{$line->{'count'}-1}->{'y'}, 
			    $line->{$line->{'count'}-1}->{'z'});

  $self->scale_part($part, $part_distance, $length);
  $self->align_part($part, $x1, $y1, 
		 $line->{$line->{'count'}-1}->{'x'}, 
		 $line->{$line->{'count'}-1}->{'y'});

  $self->append_polyline($part, $composite);
  $self->set_polyline_bounds($composite);

  return($composite);
}

# this only works on the 2d-plane.
sub align_segment_climb_up_line {
  my ($self) = shift;
  my $line = shift;
  my $dist = shift;
  my $part = shift;
  my @l = @_;

  my $q_dist = $self->get_distance($part->{0}->{'x'}, 
			     $part->{0}->{'y'},
			     0,
			     $part->{$part->{'count'}-1}->{'x'}, 
			     $part->{$part->{'count'}-1}->{'y'},
			     0);

  my ($l1, $l2) = $self->split_line_by_travel_distance($line,$dist);

  my ($q1, $q2) = $self->split_line_by_crow_flight($l2,$q_dist);
  
  my $x1 = (-1 * $part->{0}->{'x'});
  my $y1 = (-1 * $part->{0}->{'y'});

  my @transform_list = $self->align_part($part, 
				      $q1->{0}->{'x'}, $q1->{0}->{'y'}, 
				      $q2->{0}->{'x'}, $q2->{0}->{'y'});

  foreach my $thing (@l) {
    $self->move_polyline($thing, $x1, $y1);
    $self->move_polyline($thing, $q1->{0}->{'x'}, $q1->{0}->{'y'});
    $self->polyline_rotate($thing, @transform_list);
  }

  my $travel_dist = $self->get_length_along_line($l1);
  $travel_dist += $self->get_length_along_line($q1);

  return($travel_dist, $part, @l);
}

sub scale_part {
  my ($self) = shift;
  my($part, $l1, $l2) = @_;

  my $div = $l2 / $l1;

  $self->polyline_scale($part, $part->{0}->{'x'}, $part->{0}->{'y'}, 0, $div, $div, $div);
}


# this only works on the 2d-plane.
# pass this a line, a distance to travel up the line, a part, and other optional
#   lines. first travel up the line by distance, and then use the start coord
#   and end coords of the part to align the part to that position. if there
#   additional lines were passed, those are moved and oriented in the same
#   way as the part.
sub align_and_add_segment {
  my ($self) = shift;
  my $line = shift;
  my $dist = shift;
  my $part = shift;
  my @l = @_;

  my $q_dist = $self->get_distance($part->{0}->{'x'}, 
			     $part->{0}->{'y'},
			     0,
			     $part->{$part->{'count'}-1}->{'x'}, 
			     $part->{$part->{'count'}-1}->{'y'},
			     0);

  my ($l1, $l2) = $self->split_line_by_travel_distance($line,$dist);
  my ($q1, $q2) = $self->split_line_by_crow_flight($l2,$q_dist);
  
  my $x1 = (-1 * $part->{0}->{'x'});
  my $y1 = (-1 * $part->{0}->{'y'});

  my @transform_list = $self->align_part($part, 
				      $q1->{0}->{'x'}, $q1->{0}->{'y'}, 
				      $q2->{0}->{'x'}, $q2->{0}->{'y'});

  # you may want to change this for other applications. the part gets added into the 
  #   the initial line by doing this...
  $self->append_polyline($part, $l1, "overlap");
  $self->append_polyline($q2, $l1, "overlap");

  foreach my $thing (@l) {
    $self->move_polyline($thing, $x1, $y1);
    $self->move_polyline($thing, $q1->{0}->{'x'}, $q1->{0}->{'y'});
    $self->polyline_rotate($thing, @transform_list);
  }

  my $travel_dist = $self->get_length_along_line($l1);
  $travel_dist += $self->get_length_along_line($q1);

  return($travel_dist, $l1, @l);
}

sub point_by_travel_distance {
  my($self) = shift;
  my($line, $d) = @_;

  my($l1, $l2) = $self->split_line_by_travel_distance($line, $d);

  return($l2->{0}->{'x'}, $l2->{0}->{'y'}, $l2->{0}->{'z'});
}

sub get_length_along_line {
  my($self) = shift;
  my($line) = @_;
  my $i;

  my $d;
  for($i=0;$i<$line->{'count'}-1;$i++) {
    $d += $self->get_distance($line->{$i}->{'x'},
			$line->{$i}->{'y'},
			$line->{$i}->{'z'},
			$line->{$i+1}->{'x'},
			$line->{$i+1}->{'y'},
			$line->{$i+1}->{'z'});
  }

  return($d);
}


sub point_by_crow_flight {
  my($self) = shift;
  my($line, $d) = @_;
  my($l1, $l2) = $self->split_line_by_crow_flight($line, $d);
  return($l2->{'x'}, $l2->{'y'}, $l2->{'z'});
}

sub split_line_by_crow_flight {
  my($self) = shift;
  my($line, $d1) = @_;
  my($i, $d2);

  my($x1, $y1, $z1, $x2, $y2, $z2);
  my($l1, $l2);
  my $pos = 0; # reflects the distance traveled
  $l1->{'count'} = 0;
  $l2->{'count'} = 0;
  my $count;
  for($i=0;$i<$line->{'count'};$i++) {

    $x1 = $line->{$i}->{'x'};
    $y1 = $line->{$i}->{'y'};
    $z1 = $line->{$i}->{'z'};
    $x2 = $line->{$i+1}->{'x'};
    $y2 = $line->{$i+1}->{'y'};
    $z2 = $line->{$i+1}->{'z'};

    my ($diff) = $d1 - $pos;
    my $inc;
    if ($i != $line->{'count'}-1) {
      my $dist1 = $self->get_distance($line->{0}->{'x'},
			     $line->{0}->{'y'},
			     $line->{0}->{'z'},
			     $x1, $y1, $z1);
      my $dist2 = $self->get_distance($line->{0}->{'x'},
			     $line->{0}->{'y'},
			     $line->{0}->{'z'},
			     $x2, $y2, $z2);
      $inc = $dist2 - $dist1;
    }
    else {
      $inc = 0;
    }

    if ($d1 > $pos && $d1 >= ($pos + $inc)) { 
      $l1->{$i}->{'x'} = $x1;
      $l1->{$i}->{'y'} = $y1;
      $l1->{$i}->{'z'} = $z1;
      $l1->{'count'} = $i+1;
    }
    elsif ($d1 >= $pos && $d1 < ($pos + $inc)) { # we crossed the line
      $l1->{$i}->{'x'} = $x1;
      $l1->{$i}->{'y'} = $y1;
      $l1->{$i}->{'z'} = $z1;

      my($x, $y, $z) = $self->get_point_on_line($x1, $y1, $z1, $x2, $y2, $z2, $diff);

      $l1->{$i+1}->{'x'} = $x;
      $l1->{$i+1}->{'y'} = $y;
      $l1->{$i+1}->{'z'} = $z;
      $l1->{'count'} = $i+2;

      $l2->{0}->{'x'} = $x;
      $l2->{0}->{'y'} = $y;
      $l2->{0}->{'z'} = $z;
      $count = 1;
    }
    elsif ($pos > $d1) {
      $l2->{$count}->{'x'} = $line->{$i}->{'x'};
      $l2->{$count}->{'y'} = $line->{$i}->{'y'};
      $l2->{$count}->{'z'} = $line->{$i}->{'z'};
      $count++;
      $l2->{'count'} = $count;
    }
    else {
      die "unknown condition";
    }
    $pos += $inc;
  }

  return($l1, $l2);
}

sub split_line_by_travel_distance {
  my($self) = shift;
  my($line, $d1) = @_;
  my($i, $d2);

  my($x1, $y1, $z1, $x2, $y2, $z2);
  my($l1, $l2);
  my $pos = 0; # reflects the distance traveled
  $l1->{'count'} = 0;
  $l2->{'count'} = 0;
  my $count;
  for($i=0;$i<$line->{'count'};$i++) {

    $x1 = $line->{$i}->{'x'};
    $y1 = $line->{$i}->{'y'};
    $z1 = $line->{$i}->{'z'};
    $x2 = $line->{$i+1}->{'x'};
    $y2 = $line->{$i+1}->{'y'};
    $z2 = $line->{$i+1}->{'z'};

    my ($diff) = $d1 - $pos;
    my $inc;
    if ($i != $line->{'count'}-1) {
      $inc = $self->get_distance($x1, $y1, $z1, $x2, $y2, $z2);
    }
    else {
      $inc = 0;
    }

    if ($d1 > $pos && $d1 >= ($pos + $inc)) { 
      $l1->{$i}->{'x'} = $x1;
      $l1->{$i}->{'y'} = $y1;
      $l1->{$i}->{'z'} = $z1;
      $l1->{'count'} = $i+1;
    }
    elsif ($d1 >= $pos && $d1 < ($pos + $inc)) { # we crossed the line
      $l1->{$i}->{'x'} = $x1;
      $l1->{$i}->{'y'} = $y1;
      $l1->{$i}->{'z'} = $z1;

      my($x, $y, $z) = $self->get_point_on_line($x1, $y1, $z1, $x2, $y2, $z2, $diff);

      $l1->{$i+1}->{'x'} = $x;
      $l1->{$i+1}->{'y'} = $y;
      $l1->{$i+1}->{'z'} = $z;
      $l1->{'count'} = $i+2;

      $l2->{0}->{'x'} = $x;
      $l2->{0}->{'y'} = $y;
      $l2->{0}->{'z'} = $z;
      $count = 1;
    }
    elsif ($pos > $d1) {
      $l2->{$count}->{'x'} = $line->{$i}->{'x'};
      $l2->{$count}->{'y'} = $line->{$i}->{'y'};
      $l2->{$count}->{'z'} = $line->{$i}->{'z'};
      $count++;
      $l2->{'count'} = $count;
    }
    else {
      die "unknown condition";
    }
    $pos += $inc;
  }

  return($l1, $l2);
}

sub get_point_on_line {
  my($self) = shift;
  my($x1, $y1, $z1, $x2, $y2, $z2, $d) = @_;
  my($x_save, $y_save, $z_save);
  my($rm);

  $x_save = $x1;
  $y_save = $y1;
  $z_save = $z1;

  # move things to a zeroed-out center. 
  $x1 -= $x_save;
  $y1 -= $y_save;
  $z1 -= $z_save;
  $x2 -= $x_save;
  $y2 -= $y_save;
  $z2 -= $z_save;

  my $angle = atan(($z2-$z1)/($x2-$x1));

  $rm = new Math::Matrix ([cos($angle),0,sin($angle),0],
			  [0,1,0,0],
			  [(sin($angle)*-1),0,cos($angle),0],
			  [0,0,0,1]);

  my $m = new Math::Matrix ([0,0,0,$x2],
			    [0,0,0,$y2],
			    [0,0,0,$z2],
			    [0,0,0,1]);

  my $a = $rm->multiply($m)->slice(3);

  $x2 = $a->[0]->[0];
  $y2 = $a->[1]->[0];
  $z2 = $a->[2]->[0];

  $angle *= -1;

  my ($x, $y) = $self->segment_circle_intersection($x1, $y1, $x2, $y2, $d);

  $rm = new Math::Matrix ([cos($angle),0,sin($angle),0],
			  [0,1,0,0],
			  [(sin($angle)*-1),0,cos($angle),0],
			  [0,0,0,1]);

  my $m = new Math::Matrix ([0,0,0,$x],
			    [0,0,0,$y],
			    [0,0,0,$z2],
			    [0,0,0,1]);
  
  my $a = $rm->multiply($m)->slice(3);

  return($a->[0]->[0] + $x_save, 
	 $a->[1]->[0] + $y_save, 
	 $a->[2]->[0] + $z_save);
}

sub segment_circle_intersection {
  my($self) = shift;
  my($x1, $y1, $x2, $y2, $r) = @_;
  my($x_save, $y_save);

  $x_save = $x1;
  $y_save = $y1;

  # move things to a zeroed-out center. not sure it was necessary but made it easier
  #  to conceptualize
  $x1 -= $x_save;
  $y1 -= $y_save;
  $x2 -= $x_save;
  $y2 -= $y_save;

  my ($m, $b) = $self->get_slope_intercept($x1, $y1, $x2, $y2);

  my ($xchoice1, $xchoice2) = $self->solve_quadratic(1+($m*$m),
						     2*$m*$b,
						     ($b * $b) - ($r * $r));

  # substituting each x back in, generate possible y values for each x
  my $ychoice1 = ($m * $xchoice1) + $b;
  my $ychoice2 = ($m * $xchoice2) + $b;

  if ($x2 > 0) {
    $x1 = $xchoice1;
    $y1 = $ychoice1;
  }
  else {
    $x1 = $xchoice2;
    $y1 = $ychoice2;
  }

  # add back the old values to restore position
  return($x1 + $x_save, $y1 + $y_save);
}


sub solve_quadratic {
  my($self) = shift;
  my($a, $b, $c) = @_;
  my ($x1, $x2);

  $x1 = ((-1 * $b) + (sqrt(($b*$b) - 4*($a*$c)))) / (2 * $a);
  $x2 = ((-1 * $b) - (sqrt(($b*$b) - 4*($a*$c)))) / (2 * $a);

  return($x1, $x2);
}


sub get_slope_intercept {
  my($self) = shift;
  my($x1, $y1, $x2, $y2) = @_;

  my $slope = ($y2 - $y1) / ($x2 - $x1);
  my $b = $y1 - ($slope * $x1);

  return($slope, $b);
}


sub align_part {
  my ($self) = shift;
  my($part, $x1, $y1, $x2, $y2) = @_;

  $self->move_polyline($part, (-1 * $part->{0}->{'x'}), (-1 * $part->{0}->{'y'}));
  $self->move_polyline($part, $x1, $y1);

  my $line;

  $line->{0}->{'x'} = $x2;
  $line->{0}->{'y'} = $y2;
  $line->{1}->{'x'} = $x1;
  $line->{1}->{'y'} = $y1;
  $line->{2}->{'x'} = $part->{$part->{'count'}-1}->{'x'};
  $line->{2}->{'y'} = $part->{$part->{'count'}-1}->{'y'};

  my $angle = $self->angle_from_lines($line);
  $self->polyline_rotate($part, (-1 * $angle), 'z', $x1, $y1);

  return((-1 * $angle), 'z', $x1, $y1);
}


# pass this a polyline composed of three points 
#  which have been collapsed on a 2d (x-y) plane
# see: http://en.wikipedia.org/wiki/Dot_product

sub angle_from_lines {
  my($self) = shift;
  my($p) = shift;

  my $v1 = NewVec($p->{1}->{'x'} - $p->{0}->{'x'}, 
		  $p->{1}->{'y'} - $p->{0}->{'y'});

  my $v2 = NewVec($p->{1}->{'x'} - $p->{2}->{'x'}, 
		  $p->{1}->{'y'} - $p->{2}->{'y'});

  my $a = rad2deg(acos($v1->Dot($v2) / (($v1->Magnitude($v1)) * ($v2->Magnitude($v1)))));

  my ($x, $y, $z) = $v1->Cross($v2);

  $a = 360 - $a  if ($z < 0);

  return( $a );
}


# given a line, find the x and z coordinates for a user-
#   supplied y value.
sub get_xz_positions {
  my($self) = shift;
  my ($y, $line, $debug) = @_;
  # first find two points along line that flank $y
  my $i;
  my @l;
  my ($x1, $y1, $x2, $y2, $z1, $z2);
  my $hit = 0;
  my @answer;

  for($i=0;$i<$line->{'count'}-1;$i++) {

    $x1 = $line->{$i}->{'x'};
    $y1 = $line->{$i}->{'y'};
    $z1 = $line->{$i}->{'z'};
    $x2 = $line->{$i+1}->{'x'};
    $y2 = $line->{$i+1}->{'y'};
    $z2 = $line->{$i+1}->{'z'};

    if ($y1 > $y2) {
      ($x2, $x1) = ($x1, $x2);
      ($y2, $y1) = ($y1, $y2);
      ($z2, $z1) = ($z1, $z2);
    }

    if ($y1 < $y && $y2 > $y) {
      push(@l, [$x1, $y1, $z1, $x2, $y2, $z2]);
      $hit = 1;
    }

    push(@answer, [$x1,$z1]) if ($y1 == $y);
    push(@answer, [$x2,$z2]) if ($y2 == $y);
  }

  if ($y2 < $y && $line->{$line->{'count'}-1}->{'y'} > $y) {
    push(@l, [$x1, $y1, $z1, $line->{$line->{'count'}-1}->{'x'}, $line->{$line->{'count'}-1}->{'y'}, $line->{$line->{'count'}-1}->{'z'}]);

    $hit = 1;
  }

  if ($hit ==  1) {
    foreach my $e (@l) {
      ($x1, $y1, $z1, $x2, $y2, $z2) = ($e->[0], $e->[1], $e->[2], $e->[3], $e->[4], $e->[5]);
      my ($x, $z);
      if ($x1 != $x2) {
	my $slope = ($y2 - $y1) / ($x2 - $x1);
	my $b = $y1 - ($slope * $x1);
	$x = ($y - $b) / $slope;
      }
      else {
	$x = $x1;
      }

      my $slope = ($z2 - $z1) / ($y2 - $y1);
      my $b = $z1 - ($slope * $y1);
      my $z = ($slope * $y) + $b;

      push(@answer,[$x,$z]);
    }
  }
  else {
    # print "NO HIT\n";
  }
  return(@answer);
}

# given a line, find the y and z coordinates for a user-
#   supplied x value.
sub get_yz_positions {
  my($self) = shift;
  my ($x, $line, $debug) = @_;
  # first find two points along line that flank $y
  my $i;
  my @l;
  my ($x1, $y1, $x2, $y2, $z1, $z2);
  my $hit = 0;
  my @answer;

  for($i=0;$i<$line->{'count'}-1;$i++) {
    $x1 = $line->{$i}->{'x'};
    $y1 = $line->{$i}->{'y'};
    $z1 = $line->{$i}->{'z'};
    $x2 = $line->{$i+1}->{'x'};
    $y2 = $line->{$i+1}->{'y'};
    $z2 = $line->{$i+1}->{'z'};
    if ($x1 > $x2) {
      ($x2, $x1) = ($x1, $x2);
      ($y2, $y1) = ($y1, $y2);
      ($z2, $z1) = ($z1, $z2);
    }

    my @thing;
    if ($x1 < $x && $x2 > $x) {
      push(@l, [$x1, $y1, $z1, $x2, $y2, $z2]);
      $hit = 1;
    }
    push(@answer, [$y1, $z1]) if ($x1 == $x);
    push(@answer, [$y2, $z2]) if ($x2 == $x);
  }

  # see this code? Its in the get_xz_function() above, but its untested here
  # if ($y2 < $y && $line->{$line->{'count'}-1}->{'y'} > $y) {
    # push(@l, [$x1, $y1, $z1, $line->{$line->{'count'}-1}->{'x'}, $line->{$line->{'count'}-1}->{'y'}, $line->{$line->{'count'}-1}->{'z'}]);

    # $hit = 1;
  # }

  if ($hit ==  1) {
    foreach my $e (@l) {
      ($x1, $y1, $z1, $x2, $y2, $z2) = ($e->[0], $e->[1], $e->[2], $e->[3], $e->[4], $e->[5]);

      my $slope = ($y2 - $y1) / ($x2 - $x1);
      my $b = $y1 - ($slope * $x1);
      my $y = ($slope * $x) + $b;

      my $slope = ($z2 - $z1) / ($x2 - $x1);
      my $b = $z1 - ($slope * $x1);
      my $z = ($slope * $x) + $b;

      push(@answer,[$y,$z]);
    }
  }
  return(@answer);
}


sub _get_orientation {
  my ($p) = @_;
  
  # this should work but it doesnt. I was hoping to get the
  #  the directionality of a triangle. but I couldnt get a 
  #  a correct $x3, $y3, $z3 value
  # clockwise ness of a triangle
  # http://mathforum.org/library/drmath/view/55343.html

  my ($x3, $y3, $z3) = _get_normal($p);

  my $v = NewVec($x3,$y3,$z3);

  my ($mag) = $v->Magnitude();
  
  print "NORMAL1: $x3 :: $y3 :: $z3 :: Mag: $mag\n";
  printf("NORMAL2: %lf\n", _get_normal2($p));

  my $x0 = $p->{0}->{'x'};
  my $y0 = $p->{0}->{'y'};
  my $z0 = $p->{0}->{'z'};

  my $x1 = $p->{1}->{'x'};
  my $y1 = $p->{1}->{'y'};
  my $z1 = $p->{1}->{'z'};

  my $x2 = $p->{2}->{'x'};
  my $y2 = $p->{2}->{'y'};
  my $z2 = $p->{2}->{'z'};
  
  my $m = new Math::Matrix ([$x0,$y0,$z0,1],
			    [$x1,$y1,$z1,1],
			    [$x2,$y2,$z2,1],
			    [$x3,$y3,$z3,1]);

  my $d = $m->determinant;
  
  print "D: $d\n";
  my $r = 0;
  if ($d > 0) {
    $r = 1;
  }
  elsif ($d < 0) {
    $r = -1;
  }
  else {
    $r = 0;
  }

  return($r);
}

sub _get_normal {
  my ($p) = @_;
  
  my $x1 = $p->{0}->{'x'};
  my $y1 = $p->{0}->{'y'};
  my $z1 = $p->{0}->{'z'};

  my $x2 = $p->{1}->{'x'};
  my $y2 = $p->{1}->{'y'};
  my $z2 = $p->{1}->{'z'};

  my $x3 = $p->{2}->{'x'};
  my $y3 = $p->{2}->{'y'};
  my $z3 = $p->{2}->{'z'};
  
  my $v1 = NewVec($x1 - $x2,
		  $y1 - $y2,
		  $z1 - $z2);
  
  my $v2 = NewVec($x3 - $x2,
		  $y3 - $y2,
		  $z3 - $z2);
  

  my ($x, $y, $z) = $v1->Cross($v2);
  

  my $z2 = (($x2-$x1) * ($y1 - $y3)) - (($y2 - $y1) * ($x1 - $x3));

  return($x, $y, $z);
}

sub _get_normal2 {
  my ($p) = @_;
  
  my $x1 = $p->{0}->{'x'};
  my $y1 = $p->{0}->{'y'};
  my $z1 = $p->{0}->{'z'};

  my $x2 = $p->{1}->{'x'};
  my $y2 = $p->{1}->{'y'};
  my $z2 = $p->{1}->{'z'};

  my $x3 = $p->{2}->{'x'};
  my $y3 = $p->{2}->{'y'};
  my $z3 = $p->{2}->{'z'};
  
  my $z = (($x2-$x1) * ($y1 - $y3)) - (($y2 - $y1) * ($x1 - $x3));
  my $r = 0;
  if ($z > 0) {
    $r = 1;
  }
  elsif ($z < 0) {
    $r = -1;
  }
  else {
    $r = 0;
  }

  return($r);
}

# heron's formula
sub _get_triangle_area {
  my ($a, $b, $c) = @_;

  my $p = ($a + $b + $c) / 2;

  return(sqrt($p * ($p - $a) * ($p - $b) * ($p - $c)));
}

sub _get_d_from_points {
  my ($p1) = shift;
  my ($p2) = shift;
  my ($x1, $y1, $z1, $x2, $y2, $z2) = @_;

  $x1 = $p1->{'x'};
  $y1 = $p1->{'y'};
  $z1 = $p1->{'z'};
  $x2 = $p2->{'x'};
  $y2 = $p2->{'y'};
  $z2 = $p2->{'z'};
  my $xdistance=abs(($x1-$x2)*($x1-$x2));
  my $ydistance=abs(($y1-$y2)*($y1-$y2));
  my $zdistance=abs(($z1-$z2)*($z1-$z2));

  my $cvalue=sqrt($xdistance+$ydistance+$zdistance); 

  return ($cvalue);
}

sub polylines_by_layer {
  my $self = shift;
  my ($name) = shift;
  my @l;
  my ($i);

  for($i=0; $i < $self->{'count'}; $i++) {

    if ($self->{$i}->{'layer'} eq $name) {
      push(@l,$i);
    }  
  }

  return(@l);
}

sub polylines_by_layer_regex {
  my $self = shift;
  my ($name) = shift;
  my @l;
  my ($i);

  for($i=0; $i < $self->{'count'}; $i++) {

    if ($self->{$i}->{'layer'} =~ /$name/) {
      push(@l,$i);
    }  
  }

  return(@l);
}

# may want to change this so it returns a set of polylines, not just put
#  them into the dxf using build_dxf.
sub create_word {
  my($self) = shift;
  my($x, $y, $w, $font_file) = @_;
  my ($i, $struct, $ptr);
  
  my $letters = retrieve($font_file);

  my ($inc, $last_inc, $ptr);
  $inc = 0;
  foreach my $char (split(//, $w)) {

    if ($char eq " ") {
      $inc += $letters->{'7'}->{'char_width'} + 0.1;
    }
    else {
      for($i=0;$i<$letters->{$char}->{'count'};$i++) {
	$ptr = _deep_copy($letters->{$char}->{$i});
	$ptr = $self->move_polyline($ptr, $inc + $x, $y, 0);
	$self->build_dxf($ptr);
      }
      
      $inc += $letters->{$char}->{'char_width'} + 0.1;
    }
  }
}

sub get_vertices_by_layer {
  my $self = shift;
  my ($name) = @_;
  my $ptr;
  my ($i,$j,$first_time, $c);

  my $r = 0;
  $first_time = 1;
  for($i=0; $i < $self->{'count'}; $i++) {
    if ($self->{$i}->{'layer'} eq $name) {
      $c = 0;
      if ($first_time != 1) {
	print "encountering more than one vector called: $name\n";
	$ptr->{'count'} = 0;
      }

      if ($self->{$i}->{'layer'} eq $name) {

	$ptr = $self->{$i};
	$r = 1;
	$first_time = 0;
      }
    }  
  }

  # print "didnt find any vectors called $name\n" if ($r == 0);

  return($ptr);
}

# this catches any vertex that is inside the bound
sub polyline_is_inside {
  my ($self) = shift;
  my ($pl_test, $pl_bound) = @_;

  my $r = 0;

  if ($pl_bound->{'count'} == 0) {
    print STDERR "polyline_is_inside receiving bound polyline of no length\n";
  }
  if ($pl_test->{'count'} == 0) {
    print STDERR "polyline_is_inside receiving test polyline of no length\n";
  }

  my($i);
  for($i=0;$i<$pl_test->{'count'};$i++) {

    if ($self->isinside($pl_test->{$i}->{'x'}, 
			   $pl_test->{$i}->{'y'},
			   $pl_bound)) {
      $r = 1;
    }
    else {
      $r = 0;
      last;
    }
  }

  return($r);
}

# this catches polylines straddling the bound
sub polyline_overlaps {
  my ($self) = shift;
  my ($pl_test, $pl_bound) = @_;

  my $r = 0;

  if ($pl_bound->{'count'} == 0) {
    print STDERR "polyline_is_inside receiving bound polyline of no length\n";
  }
  if ($pl_test->{'count'} == 0) {
    print STDERR "polyline_is_inside receiving test polyline of no length\n";
  }

  my($i);
  for($i=0;$i<$pl_test->{'count'};$i++) {

    if ($self->isinside($pl_test->{$i}->{'x'}, 
			   $pl_test->{$i}->{'y'},
			   $pl_bound)) {
      $r = 1;
    }
  }

  return($r);
}

sub isinside {   
  my $self = shift;
  my $x = shift;
  my $y = shift;
  my $ptr = shift;

  return(0) if ($ptr->{'count'} < 3);
  my $inside  = 0;
  my ($px, $py) = ($ptr->{0}->{'x'}, $ptr->{0}->{'y'});

  my ($i);
  for($i=1;$i<$ptr->{'count'};$i++) {

    my ($nx, $ny) = ($ptr->{$i}->{'x'}, $ptr->{$i}->{'y'});
    if(    $py == $ny
	   || ($y <= $py && $y <= $ny)
	   || ($y >  $py && $y >  $ny)
	   || ($x >  $px && $x >  $nx)
      )
      {   
	($px, $py) = ($nx, $ny);
	next;
      }

    $inside = !$inside
      if $px==$nx || $x <= ($y-$py)*($nx-$px)/($ny-$py)+$px;

    ($px, $py) = ($nx, $ny);
  }

  return($inside);
}

# tests if a line crosses a polyline
sub polyline_crosses {
  my ($self) = shift;
  my ($line, $p) = @_;

  my $r;

  if (length($line->{0}->{'x'}) == 0 || 
      length($line->{0}->{'y'}) == 0 ||
      length($line->{1}->{'x'}) == 0 || 
      length($line->{1}->{'y'}) == 0) {
    print STDERR "polyline_crosses receiving line with no points\n";
  }
  if ($p->{'count'} == 0) {
    print STDERR "polyline_crosses receiving polyline of no length\n";
  }

  my($i, $l2);
  my $count = 0;
  for($i=0;$i<$p->{'count'}-1;$i++) {

    $l2->{0}->{'x'} = $p->{$i}->{'x'};
    $l2->{0}->{'y'} = $p->{$i}->{'y'};
    $l2->{1}->{'x'} = $p->{$i + 1}->{'x'};
    $l2->{1}->{'y'} = $p->{$i + 1}->{'y'};

    my $q = $self->segment_intersection($line, $l2);

    if ($q) {
      $r->{$count}->{'x'} = $q->{0}->{'x'};
      $r->{$count}->{'y'} = $q->{0}->{'y'};
      $count++;
    }

  }

  $r->{'count'} = $count if ($count != 0);

  return($r);
}

sub dump_vector {
  my ($self) = shift;
  my ($p) = shift;

  for(my $j=0; $j < $p->{'count'}; $j++) {
    print "$j :: $p->{$j}->{'x'} :: $p->{$j}->{'y'} :: $p->{$j}->{'z'}\n";
  }
}

################################################################################
#
# Intersection point of 2 lines - (almost) identical as for Segments
# each line is defined by 2 points
# 
# args : reference to an array with 4 points p1,p2,p3,p4
#
sub line_intersection {
  my $self = shift;
  my($p1, $p2) = @_;

  my($p3);
  my $delta = 10 ** (-$precision);

  if (length($p1->{0}->{'x'}) == 0 || 
      length($p1->{0}->{'y'}) == 0 ||
      length($p1->{1}->{'x'}) == 0 || 
      length($p1->{1}->{'y'}) == 0) {
    print STDERR "line_intersection receiving line1 with no points\n";
  }

  if (length($p2->{0}->{'x'}) == 0 || 
      length($p2->{0}->{'y'}) == 0 ||
      length($p2->{1}->{'x'}) == 0 || 
      length($p2->{1}->{'y'}) == 0) {
    print STDERR "line_intersection receiving line2 with no points\n";
  }

  my $n1 = Determinant(($p2->{0}->{'x'}-$p1->{0}->{'x'}),
		       ($p2->{0}->{'x'}-$p2->{1}->{'x'}),
		       ($p2->{0}->{'y'}-$p1->{0}->{'y'}),
		       ($p2->{0}->{'y'}-$p2->{1}->{'y'}));

  my $d  = Determinant(($p1->{1}->{'x'}-$p1->{0}->{'x'}),
		       ($p2->{0}->{'x'}-$p2->{1}->{'x'}),
		       ($p1->{1}->{'y'}-$p1->{0}->{'y'}),
		       ($p2->{0}->{'y'}-$p2->{1}->{'y'}));
  if (abs($d) < $delta) {
    return 0; # parallel
  }
  $p3->{0}->{'x'} = $p1->{0}->{'x'} + $n1/$d * ($p1->{1}->{'x'} - $p1->{0}->{'x'});
  $p3->{0}->{'y'} = $p1->{0}->{'y'} + $n1/$d * ($p1->{1}->{'y'} - $p1->{0}->{'y'});

  return($p3);
}

sub segment_intersection {
  my $self = shift;
  my($p1, $p2) = @_;

  my($p3);
  my $delta = 10 ** (-$precision);

  if (length($p1->{0}->{'x'}) == 0 || 
      length($p1->{0}->{'y'}) == 0 ||
      length($p1->{1}->{'x'}) == 0 || 
      length($p1->{1}->{'y'}) == 0) {
    print STDERR "line_intersection receiving line1 with no points\n";
  }

  if (length($p2->{0}->{'x'}) == 0 || 
      length($p2->{0}->{'y'}) == 0 ||
      length($p2->{1}->{'x'}) == 0 || 
      length($p2->{1}->{'y'}) == 0) {
    print STDERR "line_intersection receiving line2 with no points\n";
  }

  my $n1 = Determinant(($p2->{0}->{'x'}-$p1->{0}->{'x'}),
		       ($p2->{0}->{'x'}-$p2->{1}->{'x'}),
		       ($p2->{0}->{'y'}-$p1->{0}->{'y'}),
		       ($p2->{0}->{'y'}-$p2->{1}->{'y'}));

  my $n2 = Determinant(($p1->{1}->{'x'}-$p1->{0}->{'x'}),
                       ($p2->{0}->{'x'}-$p1->{0}->{'x'}),
		       ($p1->{1}->{'y'}-$p1->{0}->{'y'}),
		       ($p2->{0}->{'y'}-$p1->{0}->{'y'}));

  my $d  = Determinant(($p1->{1}->{'x'}-$p1->{0}->{'x'}),
		       ($p2->{0}->{'x'}-$p2->{1}->{'x'}),
		       ($p1->{1}->{'y'}-$p1->{0}->{'y'}),
		       ($p2->{0}->{'y'}-$p2->{1}->{'y'}));

  if (abs($d) < $delta) {
    return 0; # parallel
  }
  if (!(($n1/$d < 1) && ($n2/$d < 1) &&
        ($n1/$d > 0) && ($n2/$d > 0))) {
    return 0;
  }
  my($p3);
  $p3->{0}->{'x'} = $p1->{0}->{'x'} + $n1/$d * ($p1->{1}->{'x'} - $p1->{0}->{'x'});
  $p3->{0}->{'y'} = $p1->{0}->{'y'} + $n1/$d * ($p1->{1}->{'y'} - $p1->{0}->{'y'});

  return($p3);
}

################################################################################
#  
#  The determinant for the matrix  | x1 y1 |
#                                  | x2 y2 |
#
# args : x1,y1,x2,y2
#
sub Determinant {
  my ($x1,$y1,$x2,$y2) = @_;
  return ($x1*$y2 - $x2*$y1);
}

# see http://search.cpan.org/src/MARKOV/Math-Polygon-0.003/lib/Math/Polygon/Calc.pm
sub my_polyline_area {   
  my ($self) = shift;
  my $ptr = shift;
  my $area    = 0;
  my ($i);
  for($i=0;$i<$ptr->{'count'} - 1;$i++) {

      $area += ($ptr->{$i}->{'x'}*$ptr->{$i+1}->{'y'}) - ($ptr->{$i}->{'y'} * $ptr->{$i+1}->{'x'});
  }

  return(abs($area)/2);
}

sub polyline_grid {   
  my $self = shift;
  my %opts;
  while(@_ && !ref $_[0]) {   
    my $key     = shift;
    $opts{$key} = shift;
  }

  my $raster = exists $opts{raster} ? $opts{raster} : 1;
  return @_ if $raster == 0;

  my $p = $opts{points};
  print "no points sent to mirror" unless $p;

  my $i;
  if ($raster > 0.99999 && $raster < 1.00001) {
    for($i=0;$i<$p->{'count'} - 1;$i++) {
      $p->{$i}->{'x'} = floor($p->{$i}->{'x'} + 0.5);
      $p->{$i}->{'y'} = floor($p->{$i}->{'y'} + 0.5);
    }
    return();
  }
  for($i=0;$i<$p->{'count'} - 1;$i++) {
    $p->{$i}->{'x'} = $raster * floor($p->{$i}->{'x'}/$raster + 0.5);
    $p->{$i}->{'y'} = $raster * floor($p->{$i}->{'y'}/$raster + 0.5);
  }
}

sub make_2dpolyline_clockwise {
  my $self = shift;
  my $ptr = shift;


  $self->reverse_polyline($ptr) if (!($self->polyline_is_clockwise2d($ptr)));
}

# see http://search.cpan.org/src/MARKOV/Math-Polygon-0.003/lib/Math/Polygon/Calc.pm
#  note this only works on the X-Y plane
sub polyline_is_clockwise2d {   
  my $self = shift;
  my $q = shift;
  my $area    = 0;
  my ($i);

  my $ptr = _deep_copy($q);
  
  # also requires elements of the polyline are in +x and +y quadrant
  my $x = abs($ptr->{'min_x'});
  my $y = abs($ptr->{'min_y'});
  
  # they also cant be zero
  $x += 1;
  $y += 1;

  $self->move_polyline($ptr, $x, $y, 0);

  for($i=0;$i<$ptr->{'count'}-1;$i++) {

    my $a = ($ptr->{$i}->{'x'} * $ptr->{$i+1}->{'y'}) - ($ptr->{$i}->{'y'} * $ptr->{$i+1}->{'x'});

    $area += $a;
  }

  return($area < 0);
}

# find nearest point to the left-bottom of the bounding box
sub polyline_minxy {   
  my $self = shift;
  my $ptr = shift;

  my ($i);
  my ($xmin, $ymin) = ($ptr->{'min_x'}, $ptr->{'min_x'});
  my $rot   = 0;
  my $dmin_sq = ($ptr->{0}->{'x'}-$xmin)**2 + ($ptr->{0}->{'x'}-$ymin)**2;

  for($i=0;$i<$ptr->{'count'} - 1;$i++) {
    my $d_sq = ($ptr->{$i}->{'x'}-$xmin)**2 + ($ptr->{$i}->{'y'}-$ymin)**2;
    if($d_sq < $dmin_sq) {
      $dmin_sq = $d_sq;
      $rot     = $i;
    }
  }

  return($rot + 1);
}

sub reverse_polyline {
  my $self = shift;
  my $ptr = shift;
  my ($i, $j, $new);

  $new = _deep_copy($ptr);

  for($i=$new->{'count'}-1, $j = 0;$i != -1;$i--, $j++) {
    $ptr->{$j} = _deep_copy($new->{$i});
  }
}

sub isclosed  {   
  my $self = shift;
  my $p = shift;
  my $tolerance = shift;

  if (length($tolerance) == 0) {
    $tolerance = 0.0001;
  }

  my $l = $p->{'count'} - 1;
  if (abs($p->{0}->{'x'} - $p->{$l}->{'x'}) > $tolerance || 
      abs($p->{0}->{'y'} - $p->{$l}->{'y'}) > $tolerance) {
    return 0;
  }

  return(1);
}

sub mirror_along_line(@) {  
  my $self = shift;
  my $p = shift;
  my ($x1, $y1, $x2, $y2) = @_;

  for(my $i=0; $i < $p->{'count'}; $i++) {
    my ($x, $y) = $self->PerpendicularFoot($x1, $y1, $x2, $y2, $p->{$i}->{'x'}, $p->{$i}->{'y'});
    $p->{$i}->{'x'} = $x - ($p->{$i}->{'x'} - $x);
    $p->{$i}->{'y'} = $y - ($p->{$i}->{'y'} - $y);
  }

  return($p);
}

################################################################################
#
# Calculates the 'perpendicular foot' of a point on a line
#       p1p2 = line
#       p3   = point for which perpendicular foot is to be calculated
sub PerpendicularFoot {
  my($self) = shift;
  my($x1, $y1, $x2, $y2, $x3, $y3) = @_;
  my($l1, $l2);

  # vector penpenidular to line
  my ($v1, $v2);
  $v1 = $y2 - $y1;
  $v2 =  - ($x2 - $x1); 

  # p4 = v + p3 is a second point of the line perpendicular to p1p2 going through p3
  my ($x4, $y4);
  $x4 =  $x3 + $v1;
  $y4 =  $y3 + $v2;

  $l1->{0}->{'x'} = $x1;
  $l1->{0}->{'y'} = $y1;

  $l1->{1}->{'x'} = $x2;
  $l1->{1}->{'y'} = $y2;

  $l2->{0}->{'x'} = $x3;
  $l2->{0}->{'y'} = $y3;

  $l2->{1}->{'x'} = $x4;
  $l2->{1}->{'y'} = $y4;

  my $q = $self->line_intersection($l1, $l2);

  return($q->{0}->{'x'}, $q->{0}->{'y'});
}


# only works on x-y plane
#  x1, y1, x2, y2 define the plane
#  x and y is the point around which the thing turns.
sub mirror_along_line_old(@) {  
  my $self = shift;
  my $p = shift;
  my ($x, $y, $x1, $y1, $x2, $y2) = @_;
  my ($line);

  $self->move_polyline($p,($x * -1),($y * -1),0);

  $line->{0}->{'x'} = $x2;
  $line->{0}->{'y'} = $y2;
  $line->{1}->{'x'} = 0;
  $line->{1}->{'y'} = 0;
  $line->{2}->{'x'} = 0;
  $line->{2}->{'y'} = 1;

  my $angle = $self->angle_from_lines($line);
  $self->polyline_rotate($p, (-1 * $angle), 'z', 0, 0);

  for(my $j=0; $j < $p->{'count'}; $j++) {
    $p->{$j}->{'x'} *= -1;
    $p->{$j}->{'y'} = $p->{$j}->{'y'};
  }

  $self->polyline_rotate($p, $angle, 'z', 0, 0);
  $self->move_polyline($p,$x,$y,0);
  $self->set_polyline_bounds($p);
}

# http://search.cpan.org/~markov/Math-Polygon-0.003/lib/Math/Polygon.pod
sub polyline_mirror(@) {  
  my $self = shift;
  my $p = shift;
  my $dir = shift;
  my $ori_1 = shift;
  my $ori_2 = shift;

    if($dir eq 'x') {
	for(my $j=0; $j < $p->{'count'}; $j++) {
	  $p->{$j}->{'x'} = $ori_1 - $p->{$j}->{'x'};
	  $p->{$j}->{'y'} = $p->{$j}->{'y'};
	}
	return();
    }

    if($dir eq 'y') { 
	for(my $j=0; $j < $p->{'count'}; $j++) {
	  $p->{$j}->{'x'} = $p->{$j}->{'x'};
	  $p->{$j}->{'y'} = $ori_2 - $p->{$j}->{'y'};
	}
	return();
    }

  $self->set_polyline_bounds($p);
}

sub polyline_resize(@) {   
  my $self = shift;
  my %opts;
  while(@_ && !ref $_[0]) {   
    my $key     = shift;
    $opts{$key} = shift;
  }

  my $p = $opts{points};
  print "no points sent to resize" unless $p;

  my $sx = $opts{xscale} || $opts{scale} || 1.0;
  my $sy = $opts{yscale} || $opts{scale} || 1.0;
  return @_ if $sx==1.0 && $sy==1.0;

  my ($cx, $cy)   = defined $opts{center} ? @{$opts{center}} : (0,0);

  if (length($opts{center} > 0)) {
    for(my $j=0; $j < $p->{'count'}; $j++) {
      $p->{$j}->{'x'} = ($p->{$j}->{'x'}-$cx) * $sx;
      $p->{$j}->{'y'} = ($p->{$j}->{'y'}-$cy) * $sy 
    }
    return();
  }
    
  for(my $j=0; $j < $p->{'count'}; $j++) {
    $p->{$j}->{'x'} = $cx + ($p->{$j}->{'x'}-$cx) * $sx;
    $p->{$j}->{'y'} = $cy + ($p->{$j}->{'y'}-$cy) * $sy 
  }

  $self->set_polyline_bounds($p);
}

# pass this a polyline struct, an angle, and an axis (e.g. x, y, or z)
#  only does rotations around 0,0,0 axes.
sub polyline_rotate() {   
  my $self = shift;
  my $p = shift;
  my $angle = shift;
  my $axis = shift;
  my ($x, $y, $z) = @_;

  $self->move_polyline($p,($x * -1),($y * -1),($z * -1));

  my $rm;
  if ($axis eq 'x') {

    $rm = new Math::Matrix ([1,0,0,0],
			    [0,cos(deg2rad($angle)),(sin(deg2rad($angle))*-1),0],
			    [0,sin(deg2rad($angle)),cos(deg2rad($angle)),0],
			    [0,0,0,1]);
  }
  elsif ($axis eq 'y') {
    $rm = new Math::Matrix ([cos(deg2rad($angle)),0,sin(deg2rad($angle)),0],
			    [0,1,0,0],
			    [(sin(deg2rad($angle))*-1),0,cos(deg2rad($angle)),0],
			    [0,0,0,1]);

  }
  elsif ($axis eq 'z') {
    $rm = new Math::Matrix ([cos(deg2rad($angle)),(sin(deg2rad($angle))*-1),0,0],
			    [sin(deg2rad($angle)),cos(deg2rad($angle)),0,0],
			    [0,0,1,0],
			    [0,0,0,1]);
  }
  else {
    print "dont have an axis for polyline_rotate\n";
  }

  for(my $j=0; $j < $p->{'count'}; $j++) {

    my $m = new Math::Matrix ([0,0,0,$p->{$j}->{x}],
			      [0,0,0,$p->{$j}->{y}],
			      [0,0,0,$p->{$j}->{z}],
			      [0,0,0,1]);

    my $a = $rm->multiply($m)->slice(3);

    $p->{$j}->{'x'} = $a->[0]->[0];
    $p->{$j}->{'y'} = $a->[1]->[0];
    $p->{$j}->{'z'} = $a->[2]->[0];

  }

  undef($rm);

  $self->move_polyline($p,$x,$y,$z);

  $self->set_polyline_bounds($p)
}

# pass this a polyline struct, an angle, and an axis (e.g. x, y, or z)
#  only does rotations around 0,0,0 axes.
sub polyline_scale() {   
  my $self = shift;
  my $p = shift;
  my ($x, $y, $z, $sx, $sy, $sz) = @_;

  $self->move_polyline($p,($x * -1),($y * -1),($z * -1));

  my $scale = new Math::Matrix ([$sx,0,0,0],
				[0,$sy,0,0],
				[0,0,$sz,0],
				[0,0,0,1]);


  for(my $j=0; $j < $p->{'count'}; $j++) {

    my $m = new Math::Matrix ([1,0,0,$p->{$j}->{'x'}],
			      [0,1,0,$p->{$j}->{'y'}],
			      [0,0,1,$p->{$j}->{'z'}],
			      [0,0,0,1]);

    my $a = $scale->multiply($m)->slice(3);

    # print "$j :: $a->[0]->[0] :: $a->[1]->[0] :: $a->[2]->[0]\n";

    $p->{$j}->{'x'} = $a->[0]->[0];
    $p->{$j}->{'y'} = $a->[1]->[0];
    $p->{$j}->{'z'} = $a->[2]->[0];

  }

  undef($scale);

  $self->move_polyline($p,$x,$y,$z);

  $self->set_polyline_bounds($p)
}

sub print_results {
  my($p) = @_;
  my($i);

  for($i=0;$i<$p->{'count'};$i++) {
    printf("  %d :: %2.14lf :: %2.14lf :: %2.14lf\n", $i, $p->{$i}->{'x'}, $p->{$i}->{'y'}, $p->{$i}->{'z'});
  }
}

sub move_polyline {
  my $self = shift;
  my ($p, $x, $y, $z) = @_;
  my ($i,$j);

  my $min_x = $p->{0}->{'x'} + $x;
  my $max_x = $p->{0}->{'x'} + $x;
  my $min_y = $p->{0}->{'y'} + $y;
  my $max_y = $p->{0}->{'y'} + $y;
  my $min_z = $p->{0}->{'z'} + $z;
  my $max_z = $p->{0}->{'z'} + $z;

  for($j=0; $j < $p->{'count'}; $j++) {
    $p->{$j}->{'x'} = $p->{$j}->{'x'} + $x;
    $p->{$j}->{'y'} = $p->{$j}->{'y'} + $y;
    $p->{$j}->{'z'} = $p->{$j}->{'z'} + $z;
    $min_x = min($min_x, $p->{$j}->{'x'});
    $max_x = max($max_x, $p->{$j}->{'x'});
    $min_y = min($min_y, $p->{$j}->{'y'});
    $max_y = max($max_y, $p->{$j}->{'y'});
    $min_z = min($min_z, $p->{$j}->{'z'});
    $max_z = max($max_z, $p->{$j}->{'z'});
  }

  $p->{'min_x'} = $min_x;
  $p->{'max_x'} = $max_x;
  $p->{'min_y'} = $min_y;
  $p->{'max_y'} = $max_y;
  $p->{'min_z'} = $min_z;
  $p->{'max_z'} = $max_z;
  $p->{'width'} = $max_x - $min_x;
  $p->{'height'} = $max_y - $min_y;
  $p->{'depth'} = $max_z - $min_z;
  $p->{'center_x'} = $min_x + (($max_x - $min_x) / 2);
  $p->{'center_y'} = $min_y + (($max_y - $min_y) / 2);
  $p->{'center_z'} = $min_z + (($max_z - $min_z) / 2);
}

# converts my array that holds the polyline to the form
#  that Math::Geometry::Planar wants.
sub array2MGP {
  my($a) = @_;

  my($i, @q);
  for($i=0;$i<$a->{'count'};$i++) {
    push(@q, [$a->{$i}->{'x'},$a->{$i}->{'y'}]);
  }

  return(\@q);

}

# pass this my array, this inserts the x-y points in
# Math::Geometry::Planar->polyline into that array. user better make
# sure the lengths of arrays are correct.

sub MGP2array {
  my($old, $a) = @_;

  my $p = $a->points;

  my $n = scalar(@$p);

  if ($old->{'count'} != $n) {
    print STDERR "array2MGP not getting the right lengths arrays: $old->{'count'} :: $n\n";
  }

  my $count = 0;
  foreach my $e (@$p) {
    $old->{$count}->{'x'} = $e->[0];
    $old->{$count}->{'y'} = $e->[1];
    $count++;
  }

  return($old);
}

sub set_polyline_bounds {
  my $self = shift;
  my $p = shift;
  my ($i,$j);

  my $min_x = $p->{0}->{'x'};
  my $max_x = $p->{0}->{'x'};
  my $min_y = $p->{0}->{'y'};
  my $max_y = $p->{0}->{'y'};

  for($j=0; $j < $p->{'count'}; $j++) {
    $min_x = min($min_x, $p->{$j}->{'x'});
    $max_x = max($max_x, $p->{$j}->{'x'});
    $min_y = min($min_y, $p->{$j}->{'y'});
    $max_y = max($max_y, $p->{$j}->{'y'});
  }

  $p->{'min_x'} = $min_x;
  $p->{'min_y'} = $min_y;
  $p->{'max_x'} = $max_x;
  $p->{'max_y'} = $max_y;
  $p->{'width'} = $max_x - $min_x;
  $p->{'height'} = $max_y - $min_y;
  $p->{'center_x'} = $min_x + (($max_x - $min_x) / 2);
  $p->{'center_y'} = $min_y + (($max_y - $min_y) / 2);

}

sub set_all_bounds {
  my $self = shift;
  my ($i,$j);

  for($i=0; $i < $self->{'count'}; $i++) {

    my $p = $self->{$i};
    my $min_x = $p->{0}->{'x'};
    my $max_x = $p->{0}->{'x'};
    my $min_y = $p->{0}->{'y'};
    my $max_y = $p->{0}->{'y'};

    for($j=0; $j < $p->{'count'}; $j++) {
      $min_x = min($min_x, $p->{$j}->{'x'});
      $max_x = max($max_x, $p->{$j}->{'x'});
      $min_y = min($min_y, $p->{$j}->{'y'});
      $max_y = max($max_y, $p->{$j}->{'y'});
    }

    $self->{$i}->{'min_x'} = $min_x;
    $self->{$i}->{'min_y'} = $min_y;
    $self->{$i}->{'max_x'} = $max_x;
    $self->{$i}->{'max_y'} = $max_y;
    $self->{$i}->{'width'} = $max_x - $min_x;
    $self->{$i}->{'height'} = $max_y - $min_y;
    $self->{$i}->{'center_x'} = $min_x + (($max_x - $min_x) / 2);
    $self->{$i}->{'center_y'} = $min_y + (($max_y - $min_y) / 2);

  }
}

sub append_polyline {
  my $self = shift;
  my($add, $to_this, $type) = @_;
  my($j);
  my($skip) = 0;

  # if the end of part being added is identical to end of the part getting added to,
  #   then skip the first point. 

  $skip = 1 if ($type eq "overlap");

  my $c = $to_this->{'count'};
  for($j=0; $j < $add->{'count'}-$skip; $j++) {
    $to_this->{$c + $j} = _deep_copy($add->{$j+$skip});
  }
  $to_this->{'count'} = $j + $c;

  $self->set_polyline_bounds($to_this);
}

sub morph_polylines {
  my $self = shift;
  my($p1, $p2, $percent) = @_;
  my($r,$i);

  # should not be necessary.
  if ($p1->{'count'} != $p2->{'count'}) {
    die ("morphing doesnt work on polylines that dont have the same number of vertices $p1->{'count'} :: $p2->{'count'}");
  }

  for($i=0; $i < $p1->{'count'}; $i++) {
    $r->{$i}->{'x'} = $p1->{$i}->{'x'} + 
      (($p2->{$i}->{'x'} - $p1->{$i}->{'x'}) * $percent);

    $r->{$i}->{'y'} = $p1->{$i}->{'y'} + 
      (($p2->{$i}->{'y'} - $p1->{$i}->{'y'}) * $percent);

    $r->{$i}->{'z'} = $p1->{$i}->{'z'} + 
      (($p2->{$i}->{'z'} - $p1->{$i}->{'z'}) * $percent);

  }
  $r->{'count'} = $i;
  return($r);
}

# the hope is if you have two polylines and you want to morph them
#   or to loft between them, they have to have the same number
#   of vertices. this function takes a shot at getting an equal
#   number of vertices. it does it by finding the longest distance
#   between vertices and adding more.

sub attempt_increase_in_vertices {
  my $self = shift;
  my($p1, $p2) = @_;

  # I once used this, but it is not reliable for polylines in 3d space.
  # $self->make_2dpolyline_clockwise($p1);
  # $self->make_2dpolyline_clockwise($p2);

  # note the arrays are expected to be of same length.
  if ($p1->{'count'} < $p2->{'count'}) {
    $p1 = $self->add_vertices($p1, $p2->{'count'} - $p1->{'count'});
  }
  if ($p1->{'count'} > $p2->{'count'}) {
    $p2 = $self->add_vertices($p2, $p1->{'count'} - $p2->{'count'});
  }

  my $c1 = $self->isclosed($p1);
  my $c2 = $self->isclosed($p2);
  if ($c1 != $c2) {
    print "one morphed polylines is closed and the other is open\n";
    exit(1);
  }
  if ($c1 == 1 && $c2 == 1) {
    # $self->reorder_polyline($p1, $self->polyline_minxy($p1));
    # $self->reorder_polyline($p2, $self->polyline_minxy($p2));
  }
}

sub add_vertices {
  my $self = shift;
  my($p, $num) = @_;
  my($i);

  for($i=0;$i<$num;$i++) {
    my ($j, $mid_x, $mid_y, $mid_z) = $self->_get_max_distance($p);
    $self->insert_element($p, $j, $mid_x, $mid_y, $mid_z);
  }

  return($p);
}

# finds the two vertices with the greatest distance. Used by add-vertices
sub _get_max_distance {
  my($self) = shift;
  my($p) = @_;
  my($i, $x1, $x2, $y1, $y2, $z1, $z2, $d);
  my($pos, $mid_x, $mid_y, $mid_z, $max_d);

  $x1 = $p->{0}->{'x'};
  $x2 = $p->{1}->{'x'};

  $y1 = $p->{0}->{'y'};
  $y2 = $p->{1}->{'y'};

  $z1 = $p->{0}->{'z'};
  $z2 = $p->{1}->{'z'};
  $pos = 0;

  my $max_d = $self->get_distance($x1, $y1, $z1, $x2, $y2, $z2);

  for($i=0;$i<$p->{'count'} - 1;$i++) {
    $x1 = $p->{$i}->{'x'};
    $y1 = $p->{$i}->{'y'};
    $z1 = $p->{$i}->{'z'};
    $x2 = $p->{$i+1}->{'x'};
    $y2 = $p->{$i+1}->{'y'};
    $z2 = $p->{$i+1}->{'z'};

    $d = $self->get_distance($x1, $y1, $z1, $x2, $y2, $z2);

    if ($d > $max_d) {
      $max_d = $d;
      $mid_x = $x1 + (($x2 - $x1)/2);
      $mid_y = $y1 + (($y2 - $y1)/2);
      $mid_z = $z1 + (($z2 - $z1)/2);
      $pos = $i;
    }
  }

  $x1 = $p->{$pos}->{'x'};
  $y1 = $p->{$pos}->{'y'};
  $z1 = $p->{$pos}->{'z'};
  $x2 = $p->{$pos+1}->{'x'};
  $y2 = $p->{$pos+1}->{'y'};
  $z2 = $p->{$pos+1}->{'z'};

  $mid_x = $x1 + (($x2 - $x1)/2);
  $mid_y = $y1 + (($y2 - $y1)/2);
  $mid_z = $z1 + (($z2 - $z1)/2);

  return($pos + 1, $mid_x, $mid_y, $mid_z);
}

# finds distance between vertices.
sub get_distance {
  my ($self) = shift;
  my ($x1, $y1, $z1, $x2, $y2, $z2) = @_;

  my $xdistance=abs(($x1-$x2)*($x1-$x2));
  my $ydistance=abs(($y1-$y2)*($y1-$y2));
  my $zdistance=abs(($z1-$z2)*($z1-$z2));

  my $cvalue=sqrt($xdistance+$ydistance+$zdistance); 

  return ($cvalue);
}

sub insert_element {
  my $self = shift;
  my($p, $i, $x, $y, $z) = @_;
  my($j, $next_x, $next_y);

  for($j=$p->{'count'}; $j > $i; $j--) {
    $p->{$j} = $p->{$j-1};
    undef($p->{$j-1});
  }

  $p->{'count'}++;

  $p->{$i}->{'x'} = $x;
  $p->{$i}->{'y'} = $y;
  $p->{$i}->{'z'} = $z;
}

# http://www.mathematische-basteleien.de/eggcurves.htm
#  only places oval on x-y plane. 
sub oval {
  my $self = shift;
  my($a, $b, $d, $half) = @_;
  my ($oval, $count, $x, $y);
  
  $a = abs($a) ;
  my $div = 60;
  my $inc = ($a * 2) / $div;

  my $start1 = ($a * -1) + ($inc * 2);
  my $start2 = $a - ($inc * 3);

  $count = 0;
  my ($y_next);
  my (@l);
  for($x = ($a * -1); $x < $a; $count++) {
    if (($x < $start1) || ($x > $start2)) {
      $inc = (($a * 2) / $div) / 4;
    }
    else {
      $inc = ($a * 2) / $div;
    }

    push(@l, $x);

    $x += $inc;
    $count++;
  }

  # printf("Y: %lf %lf \n", $x - $a, $inc / 10 );

  if (($x - $a) < ($inc / 2)) {
    push(@l, $a);
  }


  $count = 0;
  foreach $x (@l) {
    my $i1 = ($a * $a * $b *$b);
    my $i2 = ($b * $b * $x * $x);
    my $i3 = ($a * $a);
    my $i4 = (2 * $d * $x);
    my $i5 = ($d * $d);

    my $y = ($i1 - $i2) / ($i3 + $i4 + $i5);

    if ($y < .000001) {
      $y = $y;
    } else {
      $y = sqrt($y);
    }

    $oval->{$count}->{'x'} = $x;
    $oval->{$count}->{'y'} = $y;
    $oval->{$count}->{'z'} = 0;
    $count++;
  }

  $oval->{'count'} = $count;

  return($oval);
}

# http://www.mathematische-basteleien.de/eggcurves.htm
#  only places oval on x-y plane. 
sub oval_old {
  my $self = shift;
  my($a, $b, $d, $half) = @_;
  my ($oval);
  
  my $inc = ($a * 2) / 60;

  my ($x, $p, @l, @l2);
  my $count = 0;
  my $old_y = 0;
  push(@l, ($a * -1));
  for($x = ($a * -1); $x < $a; $x+=$inc) {
    my $test_x = $x + $inc;
    $test_x = $a if ($test_x > $a);
    my $i1 = ($a * $a * $b *$b);
    my $i2 = ($b * $b * $test_x * $test_x);
    my $i3 = ($a * $a);
    my $i4 = (2 * $d * $test_x);
    my $i5 = ($d * $d);

    my $y = ($i1 - $i2) / ($i3 + $i4 + $i5);

    # print "$test_x :: $y :: $i1 :: $i2 :: $i3 :: $i4 :: $i5\n";

    if ($y < .000001) {
      $y = $y;
    }
    else {
      $y = sqrt($y);
    }

    # this adds points in situations where the y to y_old distance is really large
    my $diff1 = ($inc + ($inc/2));
    my $diff2 = abs($y - $old_y);
    if ($diff2 > $diff1){
      print "HERE\n";
      push(@l, $x + ($inc/4));
      push(@l, $x + (($inc*2)/4));
      push(@l, $x + (($inc*3)/4));
      push(@l, $test_x);
    }
    else {
      push(@l, $test_x);
    }
    $old_y = $y;
  }

  foreach $x (@l) {
    my $i1 = ($a * $a * $b *$b);
    my $i2 = ($b * $b * $x * $x);
    my $i3 = ($a * $a);
    my $i4 = (2 * $d * $x);
    my $i5 = ($d * $d);

    my $y = ($i1 - $i2) / ($i3 + $i4 + $i5);

    print "oval2: $x :: $y :: $i1 :: $i2 :: $i3 :: $i4 :: $i5\n";

    if ($y < .000001) {
      $y = $y;
    } else {
      $y = sqrt($y);
    }

    $oval->{$count}->{'x'} = $x;
    $oval->{$count}->{'y'} = $y;
    $oval->{$count}->{'z'} = 0;
    push(@l2, $x);
    $count++;
  }

  if ($half ne "half") {
    foreach $x (reverse(@l2)) {

      my $i1 = ($a * $a * $b *$b);
      my $i2 = ($b * $b * $x * $x);
      my $i3 = ($a * $a);
      my $i4 = (2 * $d * $x);
      my $i5 = ($d * $d);

      my $y = ($i1 - $i2) / ($i3 + $i4 + $i5);

      # print "$x :: $y :: $i1 :: $i2 :: $i3 :: $i4 :: $i5\n";

      if ($y < .000001) {
	$y = $y;
      } else {
	$y = sqrt($y);
      }

      $y *= -1;

      $oval->{$count}->{'x'} = $x;
      $oval->{$count}->{'y'} = $y;
      $oval->{$count}->{'z'} = 0;
      $count++;
    }
  }
  $oval->{'count'} = $count;

  return($oval);
}

sub circle {
  my $self = shift;
  my($x_start, $y_start, $dia, $start, $stop) = @_;
  my($x, $y, $line, @l);
  
  $dia = $dia / 2;

  if (length($stop) == 0) {
     $start = 0;
     $stop = 360;
  }

  my $inc = ($dia * 2) / 30;
  my $count = 0;
  my $angle;
  for($angle = $start; $angle < $stop; $angle+=10) {

    $y = sin(deg2rad($angle)) * $dia;
    $x = cos(deg2rad($angle)) * $dia;

    $line->{$count}->{'x'} = $x + $x_start;
    $line->{$count}->{'y'} = $y + $y_start;
    $line->{$count}->{'z'} = 0;
    $count++;
  }

  $y = sin(deg2rad($stop)) * $dia;
  $x = cos(deg2rad($stop)) * $dia;
  $line->{$count}->{'x'} = $x + $x_start;
  $line->{$count}->{'y'} = $y + $y_start;
  $line->{$count}->{'z'} = 0;
    $count++;

  $line->{'count'} = $count;

  return($line);
}


sub min {
  my($x,$y) = @_;
  my($r);

  if ($x < $y) {
    $r = $x;
  }
  else {
    $r = $y;
  }
  return($r);
}

sub max {
  my($x,$y) = @_;
  my($r);

  if ($x > $y) {
    $r = $x;
  }
  else {
    $r = $y; 
  }
  return($r);
}

sub _deep_copy {
  my $this = shift;

  if (not ref $this) {
    $this;
  } elsif (ref $this eq "ARRAY") {
    [map _deep_copy($_), @$this];
  } elsif (ref $this eq "HASH") {
    +{map { $_ => _deep_copy($this->{$_}) } keys %$this};
  } else { die "what type is $_?" }
}

1;
