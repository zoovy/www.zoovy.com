#!/usr/bin/perl

print "Content-type: application/excel\n\n";
open F, "<test.xml";
while (<F>) { print $_; }
close F;