#!/usr/bin/perl

use strict;
use LWP::Simple;
use YAML::Syck;
use Data::Dumper;

my ($yaml) = LWP::Simple::get("http://webapi.zoovy.com/webapi/dns/dump.cgi");
if ($yaml eq '') {
	## hmmm.. wonder if we could notify nagios here!
	die("Could not obtain YAML from zoovy servers.");
	}
my $domains = YAML::Syck::Load($yaml);
if (scalar(@{$domains})<1000) {
	die("Not enough domains in file.. something is wrong. exiting.");
	}

my $file = "/tmp/virtual.".time();
open(Fv, ">$file") || die "$!\n";
foreach my $dref (@{$domains}) {
	next if ($dref->{'DOMAIN'} eq '');	## skip the blank domain?! wtf. error.
	# print Dumper($dref);
	print "$dref->{'DOMAIN'}\n";
	print Fv "# $dref->{'USERNAME'} $dref->{'DOMAIN'}\n";
	print Fv "newsletter.$dref->{'DOMAIN'} OK\n";
	print Fv "\@newsletter.$dref->{'DOMAIN'} autofile@\mail.zoovy.com\n";
	}
close Fv;

rename("$file","/etc/postfix/virtual");
chmod(0644,"/etc/postfix/virtual");

system "/usr/sbin/postmap /etc/postfix/virtual";


