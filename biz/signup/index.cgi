#!/usr/bin/perl

print "Content-type: text/html\n\n";
open F, "<index.shtml"; $/ = undef;
print <F>;
close F; $/ = "\n";