#!/usr/bin/perl

use lib "/httpd/modules";
use ZOOVY;
use ZACCOUNT;
use ZUSER;
use CGI;
use ZMAIL;
use GTOOLS;
use DBINFO;

($USERNAME,$FLAGS) = &ZOOVY::authenticate("/biz",1);
$q = new CGI;


$template_file = 'extension-denied.shtml';
#if (!defined($q->param('reason')))
#	{
#	$template_file = "extension.shtml";
#	} else {
#
#	if ($FLAGS !~ /RENEW/)
#		{
#		&ZACCOUNT::create_exception_flags($USERNAME,"TRIAL,",5,0);
#		&ZACCOUNT::create_exception_flags($USERNAME,"RENEW",365,0);
#		$dbh = &DBINFO::db_zoovy_connect();
#		$pstmt = "select OWNER from ZUSER_FOLLOWUP where USERNAME=".$dbh->quote($USERNAME);
#		$sth = $dbh->prepare($pstmt);
#		$sth->execute();
#		($OWNER) = $sth->fetchrow();
#		&DBINFO::db_zoovy_close();
#		$msg = "RENEW was granted.\n";
#		$msg .= "OWNER: $OWNER\n";
#		&ZMAIL::sendmail($USERNAME,'brian@zoovy.com',"$USERNAME did RENEW",$msg);
##		&ZMAIL::sendmail($USERNAME,$OWNER.'@zoovy.com',"$USERNAME did RENEW",$msg);
##		$template_file = "extension-granted.shtml";
##		} else {
#		$template_file = "extension-denied.shtml";
#		}
#	}

&GTOOLS::output(title=>"Request Extension",file=>$template_file,header=>1);
