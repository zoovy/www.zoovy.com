#!/usr/bin/perl -w

use strict;
use lib "/httpd/modules";
use CGI;
require ZOOVY;
require DBINFO;
use strict;

sub hostname {
	$/ = undef;
	open F, "</proc/sys/kernel/hostname";
	my $hostname = <F>;
	close F;
	$/ = "\n";
	$hostname =~ s/\W+//g;
	return($hostname);
	}

##
##
## Types of advice are:
## HAVEANICEDAY
## RECOMMENDED
## MANDATORY	- 
## GOAWAY		- displays error, then hit exit and ends program.
##	
##


my $q=CGI->new;

print "Content-type: text/plain\n\n";

my $x = rand(time()) % 3;

my $CLIENT = uc($q->param("CLIENT"));
my $VERSION = $q->param("VERSION");
if (not defined $VERSION) { $VERSION = ''; }
my ($MAJOR, $MINOR) = split(/\./,$VERSION);
my ($SYNC) = uc($q->param('SYNC'));
$MAJOR += 0;
$MINOR += 0;
my $USERNAME = lc($q->param("USERNAME"));

my $dbh = &DBINFO::db_zoovy_connect();

my $qtUSERNAME = $dbh->quote($USERNAME);
my $qtCLIENT = $dbh->quote($CLIENT.'='.$VERSION);
my $qtHOST = $dbh->quote(&hostname());
my $qtLOCALIP = "'unknown'";
if ($q->param('LOCALIP')) {
	$qtLOCALIP = $dbh->quote($q->param('LOCALIP'));
	}
my $PASSWORD = $q->param('PASSWORD');

my $qtSYNC = $dbh->quote($SYNC);
my $pstmt = "insert into SYNC_LOG (USERNAME,CREATED,CLIENT,HOST,REMOTEIP,SYNCTYPE) values($qtUSERNAME,now(),$qtCLIENT,$qtHOST,$qtLOCALIP,$qtSYNC)";
$dbh->do($pstmt);

&DBINFO::db_zoovy_close();
print STDERR "USERNAME: $USERNAME\nCLIENT: $CLIENT\nVERSION: $VERSION\n";

if ($PASSWORD ne '') {
	if (not &ZOOVY::verifypassword($USERNAME,$PASSWORD,1)) {
		$CLIENT = '';
		print "ADVICE=MANDATORY\n";
		print "MESSAGE=Sorry, the password $PASSWORD is not valid for username $USERNAME\n";
		}
	else {
		require Digest::MD5;
		my $t = time()+7200;
		my $KEY = "$t\@$USERNAME\@asdfasdf";
		print "TS=".time()."\n";
		print "AUTH_KEY=1\|$t\|".Digest::MD5::md5_base64($KEY)."\n";
		print "AUTH_EXPIRES=$t\n";
		}
	}

if ($CLIENT eq "ZOOVYMERCH-WIN32") {
	print "ADVICE=MANDATORY\n";
	print "MESSAGE=Product Manager is no longer supported.\n";
	}  
elsif ($CLIENT eq "ZOOVYORDER-WIN32") {

	print STDERR "VERSION: [$VERSION]\n";
	print "CLIENT=$CLIENT\n";
	print "URL=http://www.zoovy.com/biz/download\n";

	if ($USERNAME) {
		my $FLAGS = ','.ZOOVY::RETURN_CUSTOMER_FLAGS($USERNAME).',';
		if ($FLAGS =~ /,L2,/) { $FLAGS .= ',ZOM,'; }
		if ($FLAGS =~ /,BASIC,/) { $FLAGS .= ',L1,L2,L3,QBOOK,'; }

		print "FLAGS=$FLAGS\n";

#	if (($USERNAME ne 'hotnsexymama') && ($USERNAME ne 'adam')) {	
#		print "ADVICE=MANDATORY\n";
#		print "MESSAGE=service temporarily unavailable\n";
#		exit;
#		}

		print "MAJOR=$MAJOR\n";
		print "MINOR=$MINOR\n";

		if ($FLAGS =~ /DISABLE/) {
			print "ADVICE=RECOMMENDED\n";
			print "MESSAGE=Please login to the Zoovy.com website and verify your payment information as soon as possible.\n";
			exit;
			}
		elsif ($FLAGS =~ /CANCEL/) {
			print "ADVICE=MANDATORY\n";
			print "MESSAGE=Your can't use this software - your account seems to be cancelled!\n";
			exit;
			}
		elsif ($MAJOR < 5) {
			print "ADVICE=MANDATORY\n";
			print "MESSAGE=Order Manager versions below 5 are no longer supported. Please download the latest version.\n";
			exit;
			}
		elsif ($MINOR < 117) {
			print "ADVICE=MANDATORY\n";
			print "MESSAGE=Order Manager versions below 5.90 are no longer supported. Please download the latest version.\n";
			exit;
			}
		elsif ($MINOR < 156) {
			print "ADVICE=MANDATORY\n";
			print "MESSAGE=Please upgrade to version 6.038 at your next available opportunity. This version has expired\n";
			exit;
			}
#		elsif ($MINOR == 156) {
#			print "ADVICE=RECOMMENDED\n";
#			print "MESSAGE=Please upgrade to version 6.038 at your next available opportunity. This version will cease to operate on Jan 31st, 2007\n";
#			exit;
#			}
		elsif (1==1) {
			print "ADVICE=MANDATORY\n";
			print "MESSAGE=The version of the software you are using expired on January 31st, 2007. Please upgrade to the latest release.\n\n";
			}
#		elsif ($MINOR < 90) {
#			print "ADVICE=RECOMMENDED\n";
#			print "MESSAGE=For the best reliability, We recommend you download and install the latest version of Order Manager (5.90).\n";
#			exit;
#			}
		elsif ($FLAGS !~ /,ZOM/) {
			print "ADVICE=MANDATORY\n";
			print "MESSAGE=Your account type can't use this software - please visit http://www.zoovy.com/biz/configurator?VERB=VIEW&PACKAGE=ZPM to learn more.\n";
			}
		else {
			print "ADVICE=HAVEANICEDAY\n";
			print "MESSAGE=go gadget go!\n\n";
			}
		}

	
	if (0) {
		print "ADVICE=GOAWAY\n";
		print "MESSAGE=Syncing is currently unavailable.\n\n";
		exit;
		}

##	my @stop_cust = ( 
##		'abbys' ,'acceleracing'	,'affordablebeanies' ,'amulets' ,'bluegoose' ,'cobrastitch' ,'crescentclock' ,'heavensent'
##		,'hess' ,'homeandgarden' ,'ivysprettygifts' ,'jbswags' ,'jillypickadillygifts' ,'kahl' ,'netgod' ,'nofrillsmags'
##		,'pcstorm' ,'qualitycollectibles' ,'robersonpenworks' ,'schdistributing' ,'shoebacca' ,'usfreight'
##		);

#	foreach (@stop_cust) {
#		next unless(lc($USERNAME) eq $_);
#
#		print "ADVICE=GOAWAY\n";
#		print "MESSAGE=Your Order Manager client has been temporarily disabled. Please check your email for further details.\n\n";
#		exit;
#		}

	} # end of else
 else {
  print "CLIENT=UNKNOWN-WTF\nLATEST_VERSION=666\n";
}
