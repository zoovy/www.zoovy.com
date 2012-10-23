#!/usr/bin/perl

use strict;

print "Content-type: image/gif\n\n";
print pack("H84", "4749463839610100010080FF00C0C0C000000021F90401000000002C000000000100010000010132003B");

my $USERNAME = $ENV{'REQUEST_URI'};
if ($USERNAME =~ /\/([a-zA-Z0-9]+)\.gif$/) { $USERNAME = $1; } else { $USERNAME = ''; }

my $CPG = $ENV{'REQUEST_URI'};
if ($CPG =~ /\/CPG\=(.*?)\//) { $CPG = $1; } else { $CPG = 0; }
if ($CPG =~ /\@CAMPAIGN\:([\d]+)/) { $CPG = $1; }
	
my $CPN = $ENV{'REQUEST_URI'};
if ($CPN =~ /\/CPN\=([\d]+)\//) { $CPN = $1; } else { $CPN = 0; }

#if (1) {
#	# my $CMD = "/root/process.pl $id 1>> /tmp/process-$id.txt 2>> /tmp/process-$id.txt";
#	
#	$CPN = int($CPN);
#	$CPG = int($CPG);
#	my $CMD = qq~/usr/bin/perl -e 'use lib "/httpd/modules"; use CUSTOMER::RECIPIENT; CUSTOMER::RECIPIENT::coupon_action("$USERNAME",CPG=>$CPG,CPNID=>$CPN);'; ~;
#	open F, ">>/tmp/cpn-action";
#	print F $CMD;
#	close F;
#
#	$ENV{'SHELL'} = '/bin/bash';
#	open H, "|/usr/bin/at -q b now";
#	print H $CMD."\n";
#	close H;
#
#	$ENV{'SHELL'} = 'fofofof';
#
#	}


print STDERR "WEBBUG USER[$USERNAME] CPG[$CPG] CPN[$CPN]\n";

if (1) {

	use lib "/httpd/modules";
	require DBINFO;

	require CUSTOMER::RECIPIENT;
	&CUSTOMER::RECIPIENT::coupon_action($USERNAME,'OPENED',CPG=>$CPG,CPNID=>$CPN);
	}

