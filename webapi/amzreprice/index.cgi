#!/usr/bin/perl

## 
## REST BASED URI
##

use strict;

print "Content-Type: text/plain\n\n";

use YAML::Syck;
use lib "/httpd/modules";
#require AMZREPRICE;

use CGI;
my %params = ();
my ($q) = new CGI;
foreach my $k ($q->param()) {
	$params{$k} = $q->param($k);
	}
my ($VERB) = $params{'VERB'};

if ($VERB eq 'GET-RESOURCE') {
	my ($USERNAME) = $params{'USERNAME'};
	my ($MID) = &ZOOVY::resolve_mid($USERNAME);
	if ($MID>0) {
		
		}
	}

if ($VERB eq 'LIST-STRATEGIES') {
#	my $result = AMZREPRICE::list_strategies('',%params);
#	print YAML::Syck::Dump($result);
	}