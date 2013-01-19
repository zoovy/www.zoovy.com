#!/usr/bin/perl

use lib "/httpd/modules";
use INVENTORY;

$USERNAME = 'nerdgear';
($invref,$reserveref) = &INVENTORY::fetch_qty($USERNAME,undef);

use Data::Dumper;

print Dumper($invref,$reserveref);
