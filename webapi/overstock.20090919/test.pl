#!/usr/bin/perl

use lib "/httpd/servers/overstock/modules";
use OVERSTOCK;

$USERNAME = 'brian';
	my ($r,$rmsg) = &OVERSTOCK::apiRequest($USERNAME,'GetUser',\%params);
print $rmsg."\n";