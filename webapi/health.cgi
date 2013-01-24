#!/usr/bin/perl

print "Content-type: text/plain\n\n";

my @ERRORS = ();
my $okay = 1;

## check for errors here 
##		database
##		diskspace
##		nfs mounts
##		blah blah

if ($okay) {
	print "OK\n";
	}
else {
	print "NOT OK!\n";
	print join("\n",@ERRORS)."\n";
	}
