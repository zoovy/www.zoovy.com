#!/usr/bin/perl

use lib "/httpd/modules";
use GT;
use ZOOVY;

($USERNAME) = &ZOOVY::authenticate("/biz/reward/CSGTOC");

unless ($USERNAME) { exit; }

print "Content-type: text/html\n\n";

&GT::print_form("","index.shtml");