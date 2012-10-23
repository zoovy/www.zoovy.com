#!/usr/bin/perl

use strict;

use Data::Dumper;
#open F, ">/tmp/asdf-".time();
#print F Dumper(\%ENV);
#close F;


my %ERRORS = (
	'1' => 'Generic Error... shit happened!',
	'2' => 'WEBAPI Internal Application Failure',
	'3' => 'We regret to inform you that your requested action was denied because payment processing with Order Manager v10 is no longer compatible with the Zoovy servers.',
	'555' => 'Insufficient access flags, please contact Zoovy support',
	'556' => 'Seat not licensed',
	'989' => 'Internal MIME Base64 encoding error.',
	'990' => 'Internal MIME Base64 decoding error.',
	'995' => 'Internal Zlib decomrpession error. Could not decompress data.',
	'996' => 'Internal Gzip decompression error. Could not decompress data.',
	'997' => 'Internal Bzip2 decompression error. Could not decompress data.',
	'998' => 'Internal Error - cannot determine server name.',
	'999' => 'Internal Error - cannot connect to database!',
	'1000' => 'X-ZOOVY-USERNAME was not found in header.',
	'1001' => 'X-ZOOVY-SECURITY was not found in header.',
	'1002' => 'X-LENGTH was not found in header.',
	'1003' => 'X-ZOOVY-API was not found in header.',
	'1004' => 'X-ZOOVY-REQUEST was not found in header.',
	'1005' => 'X-TIME was not found in header.',
	'1006' => 'X-COMPRESS is missing or contains an invalid value, please pick one: NONE|BZIP2|GZIP.',
	'1024' => 'X-COMPAT Error Compatibility level too low, please upgrade to a newer version of your software.',
	'1025' => 'X-COMPAT Error Compatibility level passed exceeds maximum allowed value.',
	'2000' => 'Length of content does not match X-Length.',
	'2001' => 'X-ZOOVY-REQUEST appears to be blank.',
	'2002' => 'Deviation of X-TIME too large.',
	'2003' => 'Variable X-ZOOVY-API was received, but is blank.',
	'2004' => 'Invalid API called.',
	'2005' => 'Security Digests do not match - probably invalid password.',
	'2006' => 'Received legacy X-ZOOVY-PASSWORD variable, but it did not match password on file.',
	'2007' => 'Received unknown MODE: in XSECURITY try either PASSWORD or TOKEN',
	'2010' => 'User attempting to authenticate does not have administrative access',
	'2098' => 'X-CLIENT is required at this compatibility level',
	'2099' => 'Unknown X-CLIENT value - please contact zoovy support',
);




use lib "/httpd/modules";
require ZOOVY;
require WEBAPI;
require ORDER;
use Digest::MD5;
use Compress::Bzip2;
use Compress::Zlib;
use MIME::Base64;

my $dbh = &DBINFO::db_zoovy_connect();
my $MID = 0;
my $USERNAME = '';						# the X-ZOOVY-USERNAME variable 
my $LUSER = '';							# Login Username (e.g. the value after the *)
my $SERVER = &ZOOVY::servername();		
my $DATA = '';								# the actual DATA received from the post.
my $LENGTH = -1;							# the X-LENGTH variable
my $XREQUEST = '';						# the X-ZOOVY-REQUEST variable
my $XTIME = -1;							# the X-TIME variable
my $XAPI = '';								# the API name as it was passed X-ZOOVY-API
my $ACTUALMD5 = ''; 						# the computed MD5 value
my $XSECURITY = '';						# the X-ZOOVY-SECURITY variable
my $API = ''; 								# the actual API (before the params)
my @APIPARAMS = ();						# the parameters (delimited by /)
my $EC = 0;									# Error Code 
my $XCOMPRESS	= '';						# the type of compress specified by X-COMPRESS

$::XCLIENTCODE = 'WTF';					# the code portion of the X-CLIENT variable (e.g. ZOM/ZWM)
$::XCOMPAT = 0;							# the compatability mode
$::XERRORS = 0;							# the X-ERRORS variable

if ($::XERRORS) {
	
	}

##
## $::XCOMPAT = 100 -- initial release
##	$::XCOMPAT = 101 -- 12/25/04 sync process for skulist changed formats slightly.
## $::XCOMPAT = 102 -- 1/31/05 added VERSION 2 to ZSHIP::xml_out
##	$::XCOMPAT = 103 -- 4/4/05 changes to customer sync [CRITICAL ERROR]
##	$::XCOMPAT = 104 -- 4/25/05 changes to customer sync <CUSTOMERSYNC>
##	$::XCOMPAT = 105 -- 5/28/05 adds required X-CLIENT code. (zwm)
##	$::XCOMPAT = 106 -- 10/26/05 adds support for X-CLIENT:VERSION:SEAT (zwm)
##	$::XCOMPAT = 107 -- 7/18/06 changes format for incompletesync. (zom)
##	$::XCOMPAT = 108 -- 3/13/07 changes xml output of stuff for orders
##	$::XCOMPAT = 109 -- 4/19/07 implements zoovy.virtual zoovy.prod_supplier zoovy.prod_supplierid removes supplier from skulist.
##	$::XCOMPAT = 110 -- 8/21/07 changes to events (ts was time)
## $::XCOMPAT = 111 -- 10/09/07 convert ZOM and ZWM clients to ZID 
## $::XCOMPAT = 112 -- 10/27/07 versions below have backward compatibility for company_logo in merchant sync
##	$::XCOMPAT = 113 -- skipped for bad luck
##	$::XCOMPAT = 114 -- 12/26/07 new email changes (shuts down sendmail)
##	$::XCOMPAT = 115 -- 2/23/08  [note: released to 114] changed format for stids (cheap hack: e.g.  abc/123*xyz:ffff  becomes 123*abc/xyz:ffff)
##	$::XCOMPAT = 116 -- 4/10/08 note: 115 is was never apparently released due to bugs, skipping to 116 to be safe.
##	$::XCOMPAT = 116 -- 5/21/08 re-enables image delete (for 116 and higher)
##	$::XCOMPAT = 117 -- 4/7/09  changes webdb sync in versioncheck
## $::XCOMPAT == **HEY** we're maintaining this document in WEBAPI.pm now (around line 37)
##


my $q = undef;
$::LEGACY = 0;
if ($ENV{'SCRIPT_NAME'} =~ /legacy\.cgi$/) { 
	$::LEGACY = 1; 
	$q = new CGI;
	}

# $EC = 1; // for testing!

if ($EC==0) { if ($SERVER eq '') { $EC = 998; } }
if ($EC==0) { if (not defined $dbh) { $EC = 999; } }

## Verify user exists!
if ($EC==0) {
	$USERNAME = $ENV{'HTTP_X_ZOOVY_USERNAME'};
	if ($::LEGACY) { $USERNAME = $q->param('X-ZOOVY-USERNAME'); }

	## separate the LUSER from the USERNAME
	if (index($USERNAME,'*')>=0) { ($USERNAME,$LUSER) = split(/\*/,$USERNAME); }

	$MID = &ZOOVY::resolve_mid($USERNAME);
	if ($USERNAME eq '') { $EC = 1000; }
	}


#use Data::Dumper; print STDERR Dumper(\%ENV);

## Read in Data and Check Length
if ($EC==0) {
	if ($::LEGACY) {
		if (defined $q->param('CONTENT')) { $DATA = $q->param('CONTENT'); }
		elsif (defined $q->param('FILENAME')) {
		   my $filename = $q->param('FILENAME');
	  		$/ = undef; $DATA = <$filename>; $/ = "\n";
			}
		$LENGTH = length($DATA);
		}
	else {
		if (defined $ENV{'HTTP_X_LENGTH'}) { $LENGTH = int($ENV{'HTTP_X_LENGTH'}); }
		if ($LENGTH < 0) { $EC = 1002; }
	
		$DATA = ''; $/ = undef; $DATA = <STDIN>; $/ = "\n";
		if (length($DATA)!=$LENGTH) {
			$EC = 2000;
			$ERRORS{$EC} = "Uh-oh: Length of content ".length($DATA)." received does not match X-LENGTH ($LENGTH).";
			}
	
		} # end if else elgacy

	if (defined $ENV{'HTTP_X_ZOOVY_API'}) { $XAPI = $ENV{'HTTP_X_ZOOVY_API'}; } 
	elsif ($::LEGACY) { $XAPI = $q->param('X-ZOOVY-API'); }
	else { $EC = 1003; }

	if ( ($EC==0) && ($XAPI eq '') ) { $EC = 2003; }
	($API,@APIPARAMS) = split(/\//,$XAPI);

	if ( ($EC==0) && ($API eq 'PAYPROCESS') ) { $EC = 3; }

	if ( ($EC==0) && (not defined $WEBAPI::APIS{$API}) ) { 
		$EC = 2004; $ERRORS{$EC} = "Unknown/Invalid API [$API] called."; 
		}
	}


## check for X-ZOOVY-REQUEST and X-TIME
if (($EC==0) && (!$::LEGACY)) {
	if (defined $ENV{'HTTP_X_ZOOVY_REQUEST'}) { $XREQUEST = $ENV{'HTTP_X_ZOOVY_REQUEST'}; } else { $EC = 1004; }
	if (($EC==0) && ($XREQUEST eq '')) { $EC = 2001; }
	if (defined $ENV{'HTTP_X_TIME'}) { $XTIME = $ENV{'HTTP_X_TIME'}; } else { $EC = 1005; }

	my $t = time();
#	if (($EC==0) && (($XTIME > $t+300) || ($XTIME<$t-300))) { 
#		$EC = '2002';
#		$ERRORS{$EC} = "Deviation of X-TIME too large. received=[$XTIME] server=[$t] difference=".($t-$XTIME),
#		}
	}


if ($EC==0) {
	## check to make sure X-CLIENT is set.
	($::XCLIENTCODE) = $ENV{'HTTP_X_CLIENT'};	# get the ZOM or ZWM out of the X-CLIENT variable

	my ($code,$version,$seat) = split(/\:/,$::XCLIENTCODE,2);
	if ($code eq '') { $EC = 2098; }
	elsif ($code =~ /^ZID\./) {}	## all series 8 desktop clients!
	elsif ($code eq 'ZID') {}		## ZOOVY INTEGRATED DESKTOP
	elsif ($code eq 'ZOM') {}		## ORDER MANAGER
	elsif ($code eq 'ZOME') {}	## ENTERPRISE CLIENT
	elsif ($code eq 'ZSM') {}		## SYNC MANAGER
	elsif ($code eq 'ZWM') {}		## WAREHOUSE MANAGER
	elsif ($code eq 'API') {}		## WAREHOUSE MANAGER
	else { $EC = 2099; }

	}


## make sure we always set the compatibilitylevel otherwise we echo an old compat level zero warning.
if (defined $ENV{'HTTP_X_COMPAT'}) { $::XCOMPAT = int($ENV{'HTTP_X_COMPAT'}); }
elsif ($::LEGACY) { $::XCOMPAT = int($q->param('X-COMPAT')); }

if ($EC==0) {
	if ($::XCOMPAT<$WEBAPI::MIN_ALLOWED_COMPAT_LEVEL) { $EC = 1024; }
	elsif ($::XCOMPAT>$WEBAPI::MAX_ALLOWED_COMPAT_LEVEL) { $EC = 1025; } 
	if ($EC>0) {
		&ZOOVY::confess($USERNAME,"WEBAPI VERSION: $::XCOMPAT is no longer available");
		}
	}


## verify security 
if ($EC==0) {

	$XSECURITY = $ENV{'HTTP_X_ZOOVY_SECURITY'};
	my $XPASS = undef;
	if ($::LEGACY) { 
		$XSECURITY = $q->param('X-ZOOVY-SECURITY'); 
		$XPASS = $q->param('X-ZOOVY-PASSWORD'); 
		}
	elsif ($XSECURITY eq '') { 
		$EC = 1001; 
		}

	my ($CODE,$VERSION,$SEAT) = split(/\:/,$::XCLIENTCODE,3);
	if ($::XCOMPAT>=111) {
		if (($CODE eq 'ZOM') || ($CODE eq 'ZWM')) { $CODE = 'ZID'; }
		}

	if ($EC==0) {
		## check to make sure we have a license (and appropriate seat count)	 
		my ($gref) = &ZWEBSITE::fetch_globalref($USERNAME);
		my $FLAGS = ','.$gref->{'cached_flags'}.',';
		
		# my $FLAGS = ','.&ZWEBSITE::fetch_website_attrib($USERNAME,'cached_flags').',';
		$FLAGS =~ s/ZPM/ZWM/g;	# convert warehouse manager to product manager seats

		$EC = 556;

		if ($CODE =~ /^ZID\./) {
			## all series 8 desktop clients match the regex above!
			$SEAT = 1;
			}
		elsif ((($CODE eq 'ZOME') || ($CODE eq 'ZOM') || ($CODE eq 'ZWM') || ($CODE eq '')) && ($SEAT eq '')) { 
			$SEAT = 1; 
			}

		# print STDERR "SEAT[$SEAT] CODE[$CODE]\n";
		foreach my $flag (split(/,/,$FLAGS)) {
			my ($flag,$count) = split(/\*/,$flag);
			if (int($count)==0) { $count++; }
			# print STDERR "FLAG: [$flag] eq [$CODE] $SEAT>0 $SEAT<=$count\n";
			if (($flag eq $CODE) && ($SEAT>0) && ($SEAT<=$count)) {
				$EC = 0;	# whew, we're licensed to use this seat!
				}
			}

		## CHEAP HACK FOR SYNC MANAGER!
		if ($CODE eq 'ZSM') { $EC = 0; }
		if ($CODE eq 'ZOME') { $EC = 0; }
		if ($CODE eq 'ZID') { $EC = 0; $SEAT = ''; }
		if ($CODE eq 'API') { $EC = 0; $SEAT = ''; }
		if ($CODE =~ /ZID\./) { 
			$CODE = 'ZID'; 
			$EC = 0; $SEAT = ''; 
			} 	## version 8 of ZID series.

		if ($FLAGS !~ /,BASIC,/) {
			$EC = 555;		# insufficient access
			}
		if (($FLAGS =~ /,PKG=SHOPCART,/) && ($FLAGS !~ /,ZID,/)) {
			$EC = 555;
			}
		}

	if ($EC==0) {
		my $PASSWORD = ''; my $IS_ADMIN = 0; my $MODE = 'PASSWORD';

		if ($XSECURITY =~ /^([A-Z]+)\:(.*?)$/) { $MODE = $1; $XSECURITY = $2; }

		# print STDERR "XSECURITY: [$XSECURITY]\n";

		if ($MODE eq 'TOKEN') {
			## if we pass TOKEN:digest then we lookup token_zom or token_zwm
			if ((int($SEAT)==0) || (int($SEAT)==1)) { $SEAT = ''; }
			# print STDERR "Looking for Token: 'token_'.lc($CODE.$SEAT)\n";
			my ($gref) = &ZWEBSITE::fetch_globalref($USERNAME);
			if ($CODE eq 'ZID') {
				$PASSWORD = $gref->{'webapi_zid'};
				}
			if (not defined $PASSWORD) {
				($PASSWORD) = &ZWEBSITE::fetch_website_attrib($USERNAME,'token_'.lc($CODE.$SEAT));
				}
			$IS_ADMIN = 1;
		#	print STDERR "TOKEN: [$PASSWORD] ***\n";
			}
		elsif ($MODE eq 'PASSWORD') { 
			## this is for PASS:digest
			my $pstmt = '';
			if ($LUSER eq '') {
				## Master Login (no Login User)
				$pstmt = "select PASSWORD,'Y' from ZUSERS where MID=$MID and USERNAME=".$dbh->quote($USERNAME);
				my $sth = $dbh->prepare($pstmt);
				$sth->execute();
				($PASSWORD,$IS_ADMIN) = $sth->fetchrow();
				$sth->finish();
				}
			elsif ($LUSER =~ /^support/) {
				## backdoor for tech support
				$IS_ADMIN = 1;
				$PASSWORD = &WEBAPI::currentSupportPass($USERNAME,$LUSER);
				$pstmt = '';
				}
			else {
				## Login User (should have administrative priviledges)
				#$pstmt = "select PASSWORD from ZUSER_LOGIN where MID=$MID and USERNAME=".$dbh->($USERNAME)." and LUSER=".$dbh->quote($LUSER);
				## fixed 2011-02-10
				#$pstmt = "select PASSWORD,IS_ADMIN from ZUSER_LOGIN where MID=$MID and MERCHANT=".$dbh->quote($USERNAME)." and LUSER=".$dbh->quote($LUSER);
				$pstmt = "select PASSWORD,IS_ADMIN from ZUSER_LOGIN where MID=$MID and USERNAME=".$dbh->quote($USERNAME)." and LUSER=".$dbh->quote($LUSER);
				}
	
			if ($pstmt ne '') {
				my $sth = $dbh->prepare($pstmt);
				$sth->execute();
				($PASSWORD,$IS_ADMIN) = $sth->fetchrow();
				$sth->finish();
				}
			}
		else {
			$EC = 2007;
			}

			
		print STDERR "SERVER: $ENV{'SERVER_ADDR'} CLIENT=$::XCLIENTCODE USER=$USERNAME\n";

		if ($EC != 0) { }
#		## DEV BACKDOOR
#		elsif ($ENV{'SERVER_ADDR'} eq '192.168.99.14') {
#			$EC = 0;  $IS_ADMIN++; $XPASS = undef;
#			}
		elsif (not $IS_ADMIN) {
			$EC = 2010;	# user does not have administrative access
			}
		elsif (defined $XPASS) {
			if (uc($PASSWORD) ne uc($XPASS)) { $EC = '2006'; }
			}
		else {
		
			my $IN = $USERNAME . (($LUSER ne '')?'*'.$LUSER:'') . $PASSWORD . $XAPI . $XREQUEST . $XTIME . $DATA;
			# print STDERR "IN[$IN]\n";
			$ACTUALMD5 = Digest::MD5::md5_hex( $IN );
			# print STDERR "MD5S: $ACTUALMD5 ne $XSECURITY\n";
			if ($ACTUALMD5 ne $XSECURITY) {
				$EC = '2005';
				}
			}
		}
	}

if (($::XCOMPAT == 0) && ($EC != 0)) {
	print STDERR "ERRORS: $ERRORS{$EC}\n";
	print "Content-type: text/error\n\n";
	print "<Error>Error: $ERRORS{$EC}</Error>\n";
	exit;
	}

## Handle Compression
if ($EC==0) {
	$::XERRORS = $ENV{'HTTP_X_ERRORS'};
	$XCOMPRESS = $ENV{'HTTP_X_COMPRESS'};
	if ($::LEGACY) { $XCOMPRESS = $q->param('X-COMPRESS'); }
	my $xc = $XCOMPRESS;

	# print STDERR "XCOMPRESS: [$xc]\n";

	if ($DATA eq '') {
		# print STDERR "DATA IS BLANK [API=$API]\n";
		}
	elsif (substr($xc,0,7) eq 'BASE64:') {
		## Un-MIME encode if necessary
		$xc = substr($xc,7);	# Strip BASE64:
		$DATA = decode_base64($DATA);
		# print STDERR "DID DECODE\n";
		}

	if ($DATA eq '') {
		## no data, don't try to decompress!
		}
	elsif ($xc eq 'NONE') {
		## no compress!
		}
	elsif ($xc eq 'BZIP2') {
		my $TMP = $DATA;
		$DATA = Compress::Bzip2::decompress($TMP,20);
		if (not defined $DATA) { $DATA = Compress::Bzip2::decompress($TMP,100); }
		if (not defined $DATA) { $EC = 997; }
		}
	elsif ($xc eq 'GZIP') {
		# $dest = Compress::Zlib::memGzip($buffer) ;
      $DATA = Compress::Zlib::memGunzip($DATA);
		if (not defined $DATA) { $EC = 996; }
		}
	elsif ($xc eq 'ZLIB') {
		$DATA = Compress::Zlib::uncompress($DATA);
		if (not defined $DATA) { $EC = 995; }
		}
	else {
		$EC = 1006;
		}
	}

my $DEBUG = qq~<Debug>
	<x-request>$XREQUEST</x-request>
	<x-username>$USERNAME</x-username>
	<x-mid>$MID</x-mid>
	<x-api>$XAPI</x-api>
	<x-time>$XTIME</x-time>
	<x-security>$XSECURITY</x-security>
	<x-realsecurity>$ACTUALMD5</x-realsecurity>
</Debug>~;
$DEBUG = '';

if ($::LEGACY) {
	$XREQUEST = 'legacy';
	print STDERR "LEGACY: EC[$EC] USERNAME: $USERNAME XAPI: $XAPI XREQUEST: $XREQUEST DATA: $DATA\n";

	my ($PickupTime,$xmlOut) = (undef,undef);

	if ($EC==0) {
		($PickupTime,$xmlOut) = $WEBAPI::APIS{$API}->($USERNAME,$XAPI,$XREQUEST,$DATA);
		# print STDERR "XML: $xmlOut\n";
		}
	elsif ($EC!=0) {
		$xmlOut = "<!--\nERROR: $ERRORS{$EC}\n\n-->\n";
		$xmlOut .= "<Errors><Error Id=\"$XREQUEST\" Code=\"$EC\">[ERR#$EC] $ERRORS{$EC}</Error></Errors>\n";
		}
	elsif ($PickupTime<0) {	
		$xmlOut = "<Errors><Error Id=\"$XREQUEST\" Code=\"$PickupTime\">$xmlOut</Error></Errors>\n";
		}


	if (($XCOMPRESS ne 'NONE') && ($XCOMPRESS ne '')) {
		print "Content-type: text/xml\n\n";
		}
	else {
		print "Content-type: application/x-".lc($XCOMPRESS)."\n\n";
		}
	# print STDERR "xmlOut: $xmlOut\n";
	print &WEBAPI::doCompress($XCOMPRESS,$xmlOut);
	}
else {
	## NOT LEGACY
	# print STDERR "NOT LEGACY\n";
	print "Content-type: text/xml\n\n";
	print "<Response>\n";
	print "<Server>".&ZOOVY::servername()."</Server>\n";
	print "<StartTime>".(time())."</StartTime>\n";

	if ($USERNAME eq 'bamtar') { $::XERRORS++; }
	if ($USERNAME eq 'froggysfog') { $::XERRORS++; }

	if ($EC!=0) {
		print $DEBUG;
		print "<Errors>\n";
		if ($XREQUEST eq '') { $XREQUEST = -1; }
		print "<Error Id=\"$XREQUEST\" Code=\"$EC\">[ERR#$EC] $ERRORS{$EC}</Error>\n";
		print "</Errors>\n";
		}
	elsif ((not $::LEGACY) && ($EC==0)) {
		print $DEBUG;
		print "<Api>$API</Api>\n";
		
		my ($BatchID,$PickupTime,$xmlOut) = ();

		my ($GUID) = $ENV{'HTTP_X_GUID'};

		if ($GUID ne '') {
			require BATCHJOB;
			my ($bj) = BATCHJOB->new($USERNAME,0,
				'PRT'=>0,
				'GUID'=>$GUID,
				'EXEC'=>'WEBAPI',
				'%VARS'=>{ XAPI=>$XAPI, XREQUEST=>$XREQUEST, DATA=>$DATA },
				'JOB_TYPE'=>'API',
				'TITLE'=>"WEBAPI $API",
				);
			$bj->start();
			($BatchID) = $bj->id();
			}
		else {
			my ($udbh) = &DBINFO::db_user_connect($USERNAME);
			if (not eval { 
				($PickupTime,$xmlOut) = $WEBAPI::APIS{$API}->($USERNAME,$XAPI,$XREQUEST,$DATA); 
				## note: since db_user_close returns 0 - it causes the eval to return zero.
				}) {
				$PickupTime = -2;
				$xmlOut = "WEBAPI $XAPI Failure\n$@\n";
				&ZOOVY::confess($USERNAME,"$xmlOut\n===== XREQUEST: ======\n$XREQUEST\n\n===== DATA: =====\n$DATA\n\n\n",justkidding=>1);
				}
			&DBINFO::db_user_close();
			}

		if (($PickupTime==0) && ($BatchID>0)) {
			print "<Batch ID=\"$BatchID\" GUID=\"$GUID\"></Batch>\n";
			}
		elsif ($PickupTime<0) {
			print "<Errors><Error Id=\"$XREQUEST\" Code=\"$PickupTime\">$xmlOut</Error></Errors>\n";
			}
		else {
			print &WEBAPI::addRequest($XCOMPRESS,$XREQUEST,$PickupTime,$xmlOut);
			print qq~<SysInfo>~;
			print qq~<Info type="html" show="60"><![CDATA[<html>
<b>Please visit <a href="http://proshop.zoovy.com">proshop.zoovy.com</a> to buy great stuff!</b>
</html>
]]></Info>~;
			print qq~</SysInfo>~;
			}

		if ($::XERRORS) {
			use Data::Dumper;
			open F, ">/tmp/XERRORS-$USERNAME-$XREQUEST-$XCOMPRESS.$::XERRORS";
			print F "XREQUEST: $XREQUEST\n";
			print F Dumper($USERNAME,$XAPI,$XREQUEST,$DATA);
			print F "\n\n\n\n-------------------------------------------------------------\nOUTPUT: ".Dumper($PickupTime,$xmlOut);
			close F;
			}

		}

	print "<Time>".(time())."</Time>\n";
	print "</Response>\n";
	}


print "\n\r\n\r\n\r";

exit(0);


#create table API_REQUESTS (
#	ID integer unsigned default 0 not null auto_increment,
#
#	USERNAME varchar(20) default '' not null,
#	MID integer unsigned default 0 not null,
#	CLIENTID integer default 0 not null,
#	COMPRESSION enum('NONE','BZIP2','GZIP') default 'NONE',
#
#	CREATED_GMT integer unsigned default 0 not null,
#	PROCESSED_GMT integer unsigned default 0 not null,
#
#	FUNCTION varchar(20) default '' not null,
#	METHOD varchar(20) default '' not null,	
#
#	DATA mediumtext default '' not null,
#
#	primary key(ID)
#);





