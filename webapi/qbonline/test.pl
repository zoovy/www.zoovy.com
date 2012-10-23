#!/usr/bin/perl

use lib "/httpd/modules";
use ZPAY::QBMS;

$webdbref = &ZWEBSITE::fetch_website_dbref('brian');

my $ref = &ZPAY::QBMS::blah('brian',$webdbref);

