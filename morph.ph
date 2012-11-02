sub prep_polylines_for_morph {
  my($p1, $p2) = @_;

  make_polyline_clockwise($p1);
  make_polyline_clockwise($p2);

  print "start $p1->{'count'} :: $p2->{'count'}\n";

  # note the arrays are expected to be of same length.
  if ($p1->{'count'} < $p2->{'count'}) {
    $p1 = add_vertices($p1, $p2->{'count'} - $p1->{'count'});
  }
  if ($p1->{'count'} > $p2->{'count'}) {
    $p2 = add_vertices($p2, $p1->{'count'} - $p2->{'count'});
  }

  print "end $p1->{'count'} :: $p2->{'count'}\n";

  return($p1, $p2);
}

sub morph_polylines {
  my($p1, $p2, $percent) = @_;
  my($r,$i);

  print "start $p1->{'count'} :: $p2->{'count'}\n";
  # note the arrays are expected to be of same length.
  if ($p1->{'count'} < $p2->{'count'}) {
    $p1 = add_vertices($p1, $p2->{'count'} - $p1->{'count'});
  }
  if ($p1->{'count'} > $p2->{'count'}) {
    $p2 = add_vertices($p2, $p1->{'count'} - $p2->{'count'});
  }

  print "end $p1->{'count'} :: $p2->{'count'}\n";

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

sub add_vertices {
  my($p, $num) = @_;
  my($i);

  for($i=0;$i<$num;$i++) {
    my ($j, $mid_x, $mid_y, $mid_z) = get_max_distance($p);

    # print "THING:  $mid_x $mid_y $p->{'count'}\n";
    # print_results($p);
    # print "--\n";
    insert_element($p, $j, $mid_x, $mid_y, $mid_z);
    # print_results($p);
  }

  return($p);
}

# finds the two vertices with the greatest distance. Used by add-vertices
sub get_max_distance {
  my($p) = @_;
  my($i, $x1, $x2, $y1, $y2, $z1, $z2, $d);
  my($pos, $mid_x, $mid_y, $mid_z, $max_d);

  $x1 = $p->{0}->{'x'};
  $x2 = $p->{1}->{'x'};
  $y1 = $p->{0}->{'y'};
  $y2 = $p->{1}->{'y'};
  $pos = 0;

  my $max_d = get_distance($x1, $y1, $x2, $y2);

  for($i=0;$i<$p->{'count'} - 1;$i++) {
    $x1 = $p->{$i}->{'x'};
    $y1 = $p->{$i}->{'y'};
    $z1 = $p->{$i}->{'z'};
    $x2 = $p->{$i+1}->{'x'};
    $y2 = $p->{$i+1}->{'y'};
    $z2 = $p->{$i+1}->{'z'};

    $d = get_distance($x1, $y1, $x2, $y2);

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

sub insert_element {
  my($p, $i, $x, $y) = @_;
  my($j, $next_x, $next_y);

  for($j=$p->{'count'}; $j > $i; $j--) {
    # print "X $p->{$j-1}->{'x'} -> $p->{$j}->{'x'} :: $p->{$j-1}->{'y'} -> $p->{$j}->{'y'}\n";
    $p->{$j} = $p->{$j-1};
    undef($p->{$j-1});
  }

  $p->{'count'}++;

  $p->{$i}->{'x'} = $x;
  $p->{$i}->{'y'} = $y;
}

sub get_distance {
  my ($x1, $y1, $x2, $y2) = @_;

  my $xdistance=abs(($x1-$x2)*($x1-$x2));
  my $ydistance=abs(($y1-$y2)*($y1-$y2));

  my $cvalue=sqrt($xdistance+$ydistance); 

  return ($cvalue);
}

1;
