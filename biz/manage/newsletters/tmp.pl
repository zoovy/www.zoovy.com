#!/usr/bin/perl

use lib "/httpd/modules/";
use CUSTOMER::NEWSLETTER;
use Data::Dumper;
use ZWEBSITE;

my $USERNAME = 'patti';
my (@array) = CUSTOMER::NEWSLETTER::fetch_newsletter_detail($USERNAME);

print Dumper(\@array);