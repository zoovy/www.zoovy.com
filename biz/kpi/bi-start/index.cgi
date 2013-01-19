#!/usr/bin/perl

use lib "/httpd/modules";
require GTOOLS;
require WEBDOC;

my ($w) = WEBDOC->new('51602',public=>1);
$GTOOLS::TAG{'<!-- WEBDOC -->'} = $w->wiki2html();

&GTOOLS::output(header=>1,file=>'index.shtml');