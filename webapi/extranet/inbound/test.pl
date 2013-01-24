#!/usr/bin/perl

use lib "/httpd/modules";
use XML::Simple;

$xml = qq~<INCOMPLETEITEMS>
<INCOMPLETE ID="1" ACK="Y"/>
<INCOMPLETE ID="2" ACK="Y"/>
<INCOMPLETE ID="3" ACK="Y"/>
</INCOMPLETEITEMS>
~;

my @ACKS = ();
my ($rs) = XML::Simple::XMLin($xml,ForceArray=>1);
foreach my $incref (@{$rs->{'INCOMPLETE'}}) {
	if ($incref->{'ACK'} eq 'Y') {
		push @ACKS, $incref->{'ID'};
		}
	}
use Data::Dumper;
print Dumper($rs,@ACKS);

