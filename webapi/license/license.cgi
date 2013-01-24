#!/usr/bin/perl


use lib "/httpd/modules";
use DBINFO;
use ZOOVY;
use ZTOOLKIT;
use strict;
use ZACCOUNT;

use CGI;

my $q = new CGI;

print "Content-type: text/xml\n\n";
print "<?xml version=\"1.0\"?>\n";
my $ACTION = $q->param('ACTION');

my $USERNAME = lc($q->param("USERNAME"));
my $PASSWORD = $q->param("PASSWORD");
my $CLIENT = $q->param('CLIENTID');

if (not defined $CLIENT) { $CLIENT = 'UNKNOWN'; }
elsif ($CLIENT =~ /merch/i) { $CLIENT = 'ZPM'; }
elsif ($CLIENT =~ /order/i) { $CLIENT = 'ZOM'; }

my $dbh = &DBINFO::db_zoovy_connect();

my $MID = 0;
my $ALLOWED = 0;

my $ERROR = '';
if ($CLIENT ne 'ZPM' && $CLIENT ne 'ZOM') {
	$ERROR = 'Unknown client '.$CLIENT;
	}
elsif ($USERNAME eq '') {	
	$ERROR = 'No username specified.';
	}
elsif ($PASSWORD eq '') {
	$ERROR = 'No password specified.';
	}
elsif (!ZOOVY::verifypassword($USERNAME,$PASSWORD,1)) {
	$ERROR = 'Invalid Password';
	}
else {
	$ALLOWED = &allowed($USERNAME,$CLIENT);
	if ($ALLOWED == 0) {
		$ERROR = 'No '.$CLIENT.' clients are allowed for account '.$USERNAME;
		}
	}

if ($ERROR eq '') {
	$MID = &ZOOVY::resolve_mid($USERNAME);
	}

print STDERR "ERROR: $ERROR\n";

if ($ERROR ne '') {
	print "<RegisterResponse><Error>$ERROR</Error></RegisterResponse>";
	}
elsif ($ACTION eq 'REQUEST') {
	print "<RequestResponse>\n";

	if ($ERROR eq '') {
		## Allowed is the total number available if none were registered.
		print "<Allowed>$ALLOWED</Allowed>\n";
	
		my $pstmt = '';
		$pstmt = "select STATION_ID,STATION_NAME,RESETS from ZPM_REGISTRATIONS where MID=".$MID." and CLIENTCODE=".$dbh->quote($CLIENT)." and SUSPENDED=0";
		print STDERR $pstmt."\n";

		my $sth = $dbh->prepare($pstmt);
		$sth->execute();
		my $COUNT = $sth->rows();

		## Count is the total number registered, which are not suspended.
		print "<Count>$COUNT</Count>\n";

		my $clientid = $ALLOWED;
		my %clients = ();
		while ( my ($ID,$NAME,$RESETS) = $sth->fetchrow() ) {
			$clients{$ID}++;
			next if ($clientid--<=0);
			print "<Client Id=\"$ID\" Name=\"$NAME\" Resets=\"$RESETS\"/>\n";
			}

		## this will create clients that are avaialable, but don't yet exist
		$clientid = -1;
		if ($CLIENT eq 'ZPM') { $clientid = 1; }
		elsif ($CLIENT eq 'ZOM') { $clientid = 1024; }
		
		while ( ($ALLOWED-$COUNT) >0) {
			## this would probably be a good place to un-suspend licenses rather than creating new ones!
			if (not defined $clients{$clientid}) { 
				print "<Client Id=\"$clientid\" Name=\"Station $clientid\" Resets=\"0\"/>\n";
				$pstmt = "insert into ZPM_REGISTRATIONS (MID,MERCHANT,CLIENTCODE,STATION_ID,STATION_NAME,CHANNELCOUNT,MODIFIED) ";
				$pstmt .= " values($MID,".$dbh->quote($USERNAME).",".$dbh->quote($CLIENT).",$clientid,'Station $clientid',1,now())";
				print STDERR $pstmt."\n";
				if ($dbh->do($pstmt)) { $COUNT++; } else { $clientid++; }
				}
			else {
				$clientid++;
				}
			}
		
		}
	else {
		print "<Allowed>-1</Allowed>\n<Count>-1</Count>\n";
		print "<ErrorCode>1</ErrorCode>\n";
		print "<ErrorMsg>$ERROR</ErrorMsg>\n";
		}

	print "</RequestResponse>\n";
	}
elsif ($ACTION eq 'REGISTER') {	
	##
	my $STATIONID = $q->param('STATIONID');			## station number
	my $STATION = $q->param('STATION');					## station is the name e.g. "Becky's Computer"

	if ($STATIONID eq '') {
		$ERROR = "Client ID not passed.";
		}

	if ($STATION eq '') {
		$ERROR = 'Station Name not passed.';
		}

	my $pstmt = "select count(*) from ZPM_REGISTRATIONS where CLIENTCODE=".$dbh->quote($CLIENT)." and MID=".$MID." and SUSPENDED=0";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	my ($COUNT) = $sth->fetchrow();
	$sth->finish();

	$pstmt = "select STATION_ID,CHANNELCOUNT from ZPM_REGISTRATIONS where MID=".$MID." and CLIENTCODE=".$dbh->quote($CLIENT)." and STATION_ID=".$dbh->quote($STATIONID);
	$sth = $dbh->prepare($pstmt);
	$sth->execute();
	my ($STATION_EXISTS,$CHANNELCOUNT) = $sth->fetchrow();
	if (not defined $STATION_EXISTS) { $STATION_EXISTS = 0; }
	if (not defined $CHANNELCOUNT) { $CHANNELCOUNT = 1; }
	$sth->finish();

	print STDERR "COUNT: $COUNT ALLOWED: $ALLOWED\n";
	if ($COUNT>$ALLOWED) {
		$ERROR = "Already have $COUNT clients, only $ALLOWED are allowed - please correct by visiting http://www.zoovy.com/biz/register/zpm"; 
		}		
	elsif ($COUNT==$ALLOWED) {
		if ($STATION_EXISTS==0) {
			$ERROR = 'Cannot register a new client, not enough allowed clients.';
			}
		}
	else {
		# everything seems okay.
		}

	print "<RegisterResponse>\n";
	print "<Username>$USERNAME</Username>\n";
	if ($ERROR ne '') {
		print "<Error>$ERROR</Error>\n";
		}
	else {
		my $key = genkey();	

		my $pstmt = '';
		if ($STATION_EXISTS) {
			$pstmt = "update ZPM_REGISTRATIONS set RESETS=RESETS+1,REGISTRATION=".$dbh->quote($key).",CHANNELCOUNT=CHANNELCOUNT+1000,MODIFIED=now(),STATION_NAME=".$dbh->quote($STATION)." where CLIENTCODE=".$dbh->quote($CLIENT)." and STATION_ID=".$dbh->quote($STATIONID)." and MID=$MID limit 1";
			print STDERR $pstmt."\n";
			$CHANNELCOUNT+=1000;
			}
		else {
			$pstmt = "insert into ZPM_REGISTRATIONS (MID,MERCHANT,MODIFIED,CLIENTCODE,STATION_ID,STATION_NAME,REGISTRATION,CHANNELCOUNT,RESETS)";
			$pstmt .= " values ($MID,".$dbh->quote($USERNAME).",now(),".$dbh->quote($CLIENT).",".$dbh->quote($STATIONID).",".$dbh->quote($STATION).",".$dbh->quote($key).",$CHANNELCOUNT,0)";
			}
		$dbh->do($pstmt);

		print "<Username>$USERNAME</Username>\n";
		print "<StationName>$STATION</StationName>\n";
		print "<ClientId>$STATIONID</ClientId>\n";
		print "<LicenseKey>$key</LicenseKey>\n";
		print "<ChannelCounter>$CHANNELCOUNT</ChannelCounter>\n";		

		}
	print "</RegisterResponse>\n";

	}
else {
	print "<RegisterResponse><Error>Could not determine action $ACTION</Error></RegisterResponse>\n";
	}

&DBINFO::db_zoovy_close();

sub genkey {
	srand(time());
	my $key = '';
	for (my $x=0; $x<32; $x++) {
		my $ch = rand()*$$%36;
		if ($ch<26) { $ch = chr(ord('a')+$ch); }
		else { $ch = chr( ord('0')+ ($ch-26) ); }
		$key .= $ch;
		}
	return($key);
}

sub allowed {
	my ($USERNAME,$CLIENT) = @_;

	my $FLAGS = &ZACCOUNT::BUILD_FLAG_CACHE($USERNAME);
	$FLAGS = ",$FLAGS,";
	my $count = 0;

	if ($CLIENT eq 'ZOM') {
	if ($FLAGS =~ /(ZOM.*?),/) {
		$FLAGS = $1;
		if ($FLAGS =~ /\*(.*?)$/) {
			$count = $1;
			}
		else {
			$count = 1;
			}
		}
		}
	
	if ($CLIENT eq 'ZPM') {
	if ($FLAGS =~ /(ZPM.*?),/) {
		$FLAGS = $1;
		if ($FLAGS =~ /\*(.*?)$/) {
			$count = $1;
			}
		else {
			$count = 1;
			}
		}
		}
	
	return($count);
}
