sub by_number {
    $a <=> $b;
}

sub deep_copy {
  my $this = shift;
  if (not ref $this) {
    $this;
  } elsif (ref $this eq "ARRAY") {
    [map deep_copy($_), @$this];
  } elsif (ref $this eq "HASH") {
    +{map { $_ => deep_copy($this->{$_}) } keys %$this};
  } else { die "what type is $_?" }
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