#!/usr/bin/perl

use lib "/httpd/modules";
use Data::Dumper;
use ZCSV;

open F, "<foo"; $/ = undef; $BUFFER = <F>; close F;

print Dumper(&ZCSV::readHeaders($BUFFER,noheader=>1));

