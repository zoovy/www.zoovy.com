#!/usr/bin/perl

my $a = 'https://webapi.zoovy.com/webapi/google/callback.cgi/v=1/u=theh2oguru/prt=0';

if ($a =~ /\/webapi\/google\/callback\.cgi\/v=1\/u\=([a-zA-Z0-9]+)\/prt=([\d]+)$/) {
	print "MATCH!\n";
	}