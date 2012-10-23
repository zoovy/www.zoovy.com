#!/usr/bin/perl

use strict;
use lib "/httpd/modules";
use OVERSTOCK::API;
use SYNDICATION;
use CGI;
use ZOOVY;
use DBINFO;

my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("/biz/syndication",2,'_P&16');
if ($USERNAME eq '') { exit; }

my $q = new CGI;
my $VERB = $q->param('VERB');
my $PRT = int($q->param('PRT'));

if ($VERB eq 'SUCCESS') {
	my %params = ();
	my $is_dev = ($q->param('dev'))?1:0;
	if ($is_dev) { $params{'*'}++; }
	my ($r,$rmsg) = &OVERSTOCK::API::apiRequest($USERNAME,'GetUser',\%params);	

	

	print STDERR $rmsg."\n";
	my ($so) = SYNDICATION->new($USERNAME,"#$PRT",'OAS');
	if ($r==0) {
		my $USERID = '';
		my $SCREENNAME = '';
		if ($rmsg =~ /<UserId>(.*?)<\/UserId>/) { $USERID = $1; }
		if ($rmsg =~ /<ScreenName>(.*?)<\/ScreenName>/) { $SCREENNAME = $1; }

		tie my %s, 'SYNDICATION', THIS=>$so;
		$s{'.os_userid'} = $USERID;
		$s{'.os_screenname'} = $SCREENNAME;
		$s{'.os_registered'} = time();
		untie %s;
		$so->save(0);

		#$pstmt = "update OVERSTOCK_USERS set STATUS_MSG='Succesfully Registered',OS_USERID=".$dbh->quote($USERID).",OS_SCREENNAME=".$dbh->quote($SCREENNAME)." where MERCHANT=".$dbh->quote($USERNAME);
		#print STDERR $pstmt."\n";
		#$dbh->do($pstmt);
		print "Location: http://www.zoovy.com/biz/syndication/overstock\n\n"; exit;
		## not reached!
		}
	else {
		$so->nuke();
		$VERB = 'REGISTER';	# lets try it again!
		}

	}


##
## phase1 - get an authkey.
##
if ($VERB eq 'REGISTER') {
	my %params = ();

	my $is_dev = ($q->param('dev'))?1:0;
	if ($is_dev) { $params{'*'}++; }
	
	my ($r,$rmsg) = &OVERSTOCK::API::apiRequest('','GetCredentials',\%params);
	print STDERR "RMSG: $rmsg\n";

	my $URL = '';
	my $AUTHID = ''; 
	if ($rmsg =~ /<AuthenticationId>(.*?)<\/AuthenticationId>/) { $AUTHID = $1; } 
	if ($rmsg =~ /\<LoginURL\>(.*?)\<\/LoginURL\>/s) {
		require URI::Escape;
		$URL = &ZOOVY::dcode($1);
		# $URL .= "&RedirectURL=".URI::Escape::uri_escape("http://www.zoovy.com/biz/syndication/overstock/index.cgi");
		# $URL .= "&RedirectURL=".URI::Escape::uri_escape("http://www.zoovy.com/biz/syndication/");
		$URL .= "&RedirectURL=".URI::Escape::uri_escape("http://webapi.zoovy.com/webapi/overstock/redirect.cgi?VERB=SUCCESS&PRT=$PRT&dev=$is_dev");
		}
	else {
		}

	# my $dbh = DBINFO::db_zoovy_connect();
	# my $qtUSERNAME = $dbh->quote($USERNAME);
	my ($so) = SYNDICATION->new($USERNAME,"#$PRT",'OAS');
	
	tie my %s, 'SYNDICATION', THIS=>$so;
	$s{'.authkey'} = $AUTHID;
	$s{'.is_dev'} = $is_dev;
	untie %s;

	$so->save(0);

	#$pstmt = "delete from OVERSTOCK_USERS where MERCHANT=$qtUSERNAME";
	#print STDERR $pstmt."\n";	
	#$dbh->do($pstmt);

	#my $DEV = ($q->param('dev'))?1:0;
	#$pstmt = "insert into OVERSTOCK_USERS (MID,MERCHANT,CREATED_GMT,DEV,AUTHKEY) values ";
	#$pstmt .= " ($MID,$qtUSERNAME,".time().",$DEV,".$dbh->quote($AUTHID).")";
	#print STDERR $pstmt."\n";
	#$dbh->do($pstmt);
	

	if ($URL eq '') {
		print "Content-type: text/plain\n\n";
		print "Error, could not obtain credentials from Overstock";
		}
	else {
		print "Location: $URL\n\n";
		}

	}

&DBINFO::db_zoovy_close();
exit;

print "Content-type: text/plain\n\n";
use Data::Dumper;
print Dumper($q);
