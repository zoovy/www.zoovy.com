#!/usr/bin/perl

if (not defined $::U) {
	$::U = $$.'-'.time();
	}
print "Content-type: text/plain\n\n";
print "$::U\n";
print "$$\n";
$::C++;
print "$::C\n";
exit;
