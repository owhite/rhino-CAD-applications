#!/usr/bin/perl

require "getopts.pl";

use strict;

&Getopts('i:f:F:vp:w');

use vars qw($opt_f $opt_v $opt_F $opt_i $opt_p $opt_w);

my ($global);
$global->{'black'} = 0;

my $points = create_points(60);
my @l = create_tour($points);

my($i);
foreach $i (@l) {
  printf ("%d %d\n",
	  $points->{$i}->{'x'},
	  $points->{$i}->{'y'});
}

sub create_tour {
  my($points) = @_;

  my $param_file = "param_file";
  my $input_file = "input_file";
  my $output_file = "output_file";

  open(PAR_FILE,">$param_file") || die("cant write file: $param_file");
  print PAR_FILE "PROBLEM_FILE = $input_file\n";
  print PAR_FILE "TOUR_FILE = $output_file\n";
  close(PAR_FILE);

  open(F_OUT, ">$input_file") || die("cant write: $input_file");
  print F_OUT "NAME : inputfile\n";
  print F_OUT "TYPE : TSP\n";
  print F_OUT "COMMENT : COMMENT\n";
  print F_OUT "DIMENSION : $points->{'count'}\n";
  print F_OUT "EDGE_WEIGHT_TYPE : EUC_2D\n";
  print F_OUT "NODE_COORD_SECTION\n";

  my ($t1, $t2);
  if ($points->{'count'} > 150) {
    print STDERR "Be advised: the toolpath is processing $points->{'count'} points. Lists with\n";
    print STDERR "  that many vertices require a bit of a wait.\n";
    $t1 = time();
  }
  
  my $i;
  for($i=0;$i<$points->{'count'};$i++) {
    printf F_OUT ("%d %d %d\n",
		  $i+1,
		  $points->{$i}->{'x'},
		  $points->{$i}->{'y'});
  }

  print F_OUT "EOF\n";
  close(F_OUT);

  my $cmd = "echo $param_file | LKH.UNIX > /dev/null";
  system($cmd);

  my(@l);
  my $start = 0;
  open(F_IN, "$output_file") || die("cant open: $output_file");
  while(<F_IN>) {
    s/\n//;
    $start = 0 if(/-1/);
    if ($start == 1) {
      my $n = int($_-1);
      # print "FILE $_ :: $points->{$n}->{'x'} :: $points->{$n}->{'y'}\n";
      push(@l,$n); 
    }
    $start = 1 if(/TOUR_SECTION/);
  }

  if (length($t1) > 0) {
    $t2 = time();
    printf STDERR ("  %d seconds TSP time\n", $t2 - $t1);
  }

  return(@l);
}

sub create_points {
  my($num) = @_;
  my($i);

  for($i=0;$i<$num;$i++) {
    $points->{$i}->{'x'} = int(rand(100));
    $points->{$i}->{'y'} = int(rand(100));
  }
  $points->{'count'} = $i;

  return($points);
}
