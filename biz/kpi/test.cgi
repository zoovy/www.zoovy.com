#!/usr/bin/perl

use lib "/httpd/modules";
use GTOOLS;

GTOOLS::output(file=>'test.shtml',header=>1,jquery=>1);