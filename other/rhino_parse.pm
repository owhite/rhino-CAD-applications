package rhino_parse;

use strict;

sub new {
  my $invocant = shift;
  my $file = shift;
  my $props = shift;
  my $class = ref($invocant) || $invocant;
  my $self = { @_ };

  bless($self,$class)->init($file);

  return $self;
}

sub init {
  my $self = shift;
  my $file = shift;

  $self->{'count'} = 0;

  if(length($file) > 0) {
    $self->chow_file($file);
  }
}

sub add_layer {
  my $self = shift;
  my $name = shift;
  my $color = shift;

  my $c;

  if (length($self->{'layer_count'}) > 0) {
    $c = $self->{'layer_count'};
  }
  else {
    $c = 0;
    $self->{'layer_count'} = $c;
  }
  $self->{'layer'}->{$c}->{'name'} = $name;

  if (length($color) > 0) {
    $self->{'layer'}->{$c}->{'color'} = $color;
  }
  else {
    $self->{'layer'}->{$c}->{'color'} = "0 0 0";
  }
  $self->{'layer_count'}++;
}

sub add_triangle {
  my $self = shift;
  my $t = shift;
  my $name = shift;
  my ($p);

  if (length($name) == 0) {
    die("dont forget to send a layer for the polygon");
  }

  my ($i, $r);
  for($i=0;$i < $self->{'layer_count'}; $i++) {
    $r = 1 if ($name eq $self->{'layer'}->{$i}->{'name'});
  }
  die("the layer name: $name is not in the file struct") if ($r != 1);

  my $c = $self->{'count'};
  $p->{'layer'} = $name;

  $p->{0}->{'x'} = $t->{'A'}->[0];
  $p->{0}->{'y'} = $t->{'A'}->[1];
  $p->{0}->{'z'} = $t->{'A'}->[2];
  $p->{1}->{'x'} = $t->{'B'}->[0];
  $p->{1}->{'y'} = $t->{'B'}->[1];
  $p->{1}->{'z'} = $t->{'B'}->[2];
  $p->{2}->{'x'} = $t->{'C'}->[0];
  $p->{2}->{'y'} = $t->{'C'}->[1];
  $p->{2}->{'z'} = $t->{'C'}->[2];
  $p->{'count'} = 3;

  $self->{$c} = $p;

  $self->{'count'}++;
}

sub add_polygon {
  my $self = shift;
  my $p = shift;
  my $name = shift;

  if (length($name) == 0) {
    die("dont forget to send a layer for the polygon");
  }

  my ($i, $r);
  for($i=0;$i < $self->{'layer_count'}; $i++) {
    $r = 1 if ($name eq $self->{'layer'}->{$i}->{'name'});
  }
  die("the layer name: $name is not in the file struct") if ($r != 1);

  my $c = $self->{'count'};
  $p->{'layer'} = $name;

  $self->{$c} = $p;

  $self->{'count'}++;
}

sub dump_file {
  my $self = shift;
  my $file = shift;

  my $tmp_file = ".thing." . $$;  # a log file

  my $cmd = "nurb_writer $file $tmp_file";
  
  open(CMD, "|$cmd") || die "cant open $cmd";

  print CMD "\#S layercount objectcount\n";
  print CMD "S $self->{'layer_count'} $self->{'count'}\n";
  print CMD "\#L layernum layername\n";
  
  my ($i, %list);
  for ($i=0;$i < $self->{'layer_count'}; $i++) {
    print CMD "L $i $self->{'layer'}->{$i}->{'name'} $self->{'layer'}->{$i}->{'color'}\n";
    $list{$self->{'layer'}->{$i}->{'name'}} = $i;
  }

  print CMD "\#P objectnum layernum x y z\n";
  my ($i, $j);
  for ($i=0;$i < $self->{'count'}; $i++) {
    my $p = $self->{$i};
    for ($j=0;$j<$p->{'count'};$j++) {
      printf CMD ("P %d %d %lf %lf %lf\n",
	     $i,
	     $list{$p->{'layer'}},
	     $p->{$j}->{'x'},
	     $p->{$j}->{'y'},
	     $p->{$j}->{'z'});
    }
  }
  close(CMD);
  
  open(F_IN, $tmp_file) || die "cant open $tmp_file, that's a bad sign (dump_file())";
  my $r = -1;
  while(<F_IN>) {
    $r = 1 if (/model.Write.*succeeded/);
  }
  if ($r == 1) {
    unlink($tmp_file);
  }
  else {
    print "Something may have failed in:\n  $cmd\nSee: $tmp_file\n";
  }
  close(F_IN);

  return($r)
}

sub chow_file {
  my $self = shift;
  my ($f) = @_;
  my $layer_mode = 0;
  my $object_mode = 0;
  my $layer;
  my ($num, $l);

  my $struct;
  my $tmp_file = "/tmp/.tmp_rhino_parse";

  my $cmd = "nurb_reader $f > $tmp_file";
  
  system($cmd);

  open(F_IN, $tmp_file) || die "cant open: $tmp_file";
  while (<F_IN>) {
    s///;
    s/\n//;
    if ($layer_mode == 1) {
      if (/^\s*Layer ([0-9]+):/) {
	$num = $1;
	$self->{'layer_count'} = $num + 1;
      }
      if (/^\s*name =\s"(.*)"/) {
	$layer->{$num} = $1;
	$self->{'layer'}->{$num}->{'name'} = $1;
      }
      if (/^\s*display color rgb =\s(.*)/) {
	$self->{'layer'}->{$num}->{'color'} = $1;
      }
    }
    if ($object_mode == 1) {
      if (/^\s*Object ([0-9]+):/) {
	$num = $1;
      }
      if (/^\s*object layer index = ([0-9]+)/) {
	$self->{$num}->{'layer'} = $layer->{$1};
      }
      if (/^\s*point\[\s*([0-9]+)\] =\s\((.*)\)/) {
	my $j = $1;
	my $k = $2;
	$k =~ s/\s//g;
	my ($x, $y, $z) = split(/,/,$k);
	$self->{$num}->{$j}->{'x'} = $x;
	$self->{$num}->{$j}->{'y'} = $y;
	$self->{$num}->{$j}->{'z'} = $z;
	$self->{$num}->{'count'} = $j + 1;
	$self->{'count'} = $num + 1;
      }      
      if (/^\s*start\s=\s\((.*)\)/) { # start and end are for two point lines
	my $j = $1;
	my ($x, $y, $z) = split(/,/,$j);
	$self->{$num}->{0}->{'x'} = $x;
	$self->{$num}->{0}->{'y'} = $y;
	$self->{$num}->{0}->{'z'} = $z;
	$self->{'count'} = $num + 1;
      }      
      if (/^\s*end\s=\s\((.*)\)/) {
	my $j = $1;
	my ($x, $y, $z) = split(/,/,$j);
	$self->{$num}->{1}->{'x'} = $x;
	$self->{$num}->{1}->{'y'} = $y;
	$self->{$num}->{1}->{'z'} = $z;
	$self->{$num}->{'count'} = 2;
	$self->{'count'} = $num + 1;
      }      
      if (/^\s*CV\[\s*([0-9]+)\]\s\((.*)\)/) {
	my $j = $1;
	my $k = $2;
	$k =~ s/\s//g;
	my ($x, $y, $z) = split(/,/,$k);
	$self->{$num}->{$j}->{'x'} = $x;
	$self->{$num}->{$j}->{'y'} = $y;
	$self->{$num}->{$j}->{'z'} = $z;
	$self->{$num}->{'count'} = $j + 1;
	$self->{'count'} = $num + 1;
      }      
      
    }
    if (/^\s+Layer table:/) {
      $layer_mode = 1;
    }
    if (/^\s+Group table:/) {
      $layer_mode = 0;
    }
    if (/^\s+Object table:/) {
      $object_mode = 1;
    }
    if (/^\s+History record table:/) {
      $object_mode = 0;
    }
  }
  close(F_IN);

  $self->set_all_bounds;
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
    my $min_z = $p->{0}->{'z'};
    my $max_z = $p->{0}->{'z'};

    for($j=0; $j < $p->{'count'}; $j++) {
      $min_x = min($min_x, $p->{$j}->{'x'});
      $max_x = max($max_x, $p->{$j}->{'x'});
      $min_y = min($min_y, $p->{$j}->{'y'});
      $max_y = max($max_y, $p->{$j}->{'y'});
      $min_z = min($min_z, $p->{$j}->{'z'});
      $max_z = max($max_z, $p->{$j}->{'z'});
    }

    $self->{$i}->{'min_x'} = $min_x;
    $self->{$i}->{'min_y'} = $min_y;
    $self->{$i}->{'min_z'} = $min_z;
    $self->{$i}->{'max_x'} = $max_x;
    $self->{$i}->{'max_y'} = $max_y;
    $self->{$i}->{'max_z'} = $max_z;
    $self->{$i}->{'width'} = $max_x - $min_x;
    $self->{$i}->{'height'} = $max_y - $min_y;
    $self->{$i}->{'depth'} = $max_z - $min_z;
    $self->{$i}->{'center_x'} = $min_x + (($max_x - $min_x) / 2);
    $self->{$i}->{'center_y'} = $min_y + (($max_y - $min_y) / 2);
    $self->{$i}->{'center_z'} = $min_z + (($max_z - $min_z) / 2);

  }
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

1;
