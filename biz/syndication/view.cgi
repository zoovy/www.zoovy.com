#!/usr/bin/perl

## 
## view syndication files, now stored in PRIVATE FILES
##
## input: dst  => destination marketplace
##			 profile => profile
##			 guid => GUID of file
## output: file contents

use strict;

use Data::Dumper;
use lib "/httpd/modules";
require LUSER;
require SYNDICATION;

my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }


my %S = ();
## from PRIVATE FILES
if ($ZOOVY::cgiv->{'GUID'}) {
	$S{'GUID'} = $ZOOVY::cgiv->{'GUID'};
	}
## from SYNDICATION
if ($ZOOVY::cgiv->{'DST'}) {
	$S{'DST'} = $ZOOVY::cgiv->{'DST'};
	}
if ($ZOOVY::cgiv->{'PROFILE'}) {
	$S{'PROFILE'} = $ZOOVY::cgiv->{'PROFILE'};
	}


## get fileref from PRIVATE_FILES table
##
my $fileref = undef;
## from /biz/setup/private/
if ($S{'GUID'} ne '') {
	print STDERR "GUID: $S{'GUID'}\n";
	$fileref = SYNDICATION::file_from_guid($USERNAME,$S{'GUID'});
	}
## from /biz/syndication/...
elsif ($S{'DST'} ne '' && $S{'PROFILE'} ne '') {
	print STDERR "DST: $S{'DST'}\n";
	my $so = SYNDICATION->new($USERNAME,$S{'PROFILE'},$S{'DST'});
	$fileref = $so->file_from_so();
	}

## ERROR
if (not defined $fileref) {
	$GTOOLS::TAG{'<!-- MESSAGE -->'} = "Could not load file: $ZOOVY::cgiv->{'GUID'}";
	$template_file = 'output-error.shtml';	
	&GTOOLS::output(
		header=>1,
		tables=>1,
		file=>$template_file,
		);
	}

else {
	my $BUFFER = '';
	my $path = &ZOOVY::resolve_userpath($USERNAME).'/PRIVATE';

	open(FILE,$path."/".$fileref->{'FILENAME'});
	while(<FILE>) {
		$BUFFER .= $_;
		}
	close(FILE);

	print "Content-type: text/plain\n\n$BUFFER";
	}

exit;
