#!/usr/bin/perl

use lib "/httpd/modules";
use CGI;
use Data::Dumper;
require ORDER;
#require ORDER::EMAIL;
#require AUTOEMAIL;
require ZOOVY;
require ZTOOLKIT;
require DBINFO;
require GTOOLS;
require SITE::EMAILS;
require SITE;

use strict;

my $dbh = &DBINFO::db_zoovy_connect();
require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_O&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }


my $q = new CGI;
my $EXIDS = $q->param('EXIDS');
my $message = $q->param('message');
my $CMD = $q->param('CMD');


my $NS = $ZOOVY::cgiv->{'NS'};
if ($NS eq '') { $NS = 'DEFAULT'; }

print STDERR "CMD is: $CMD\n";

my $template_file = '';

if ($EXIDS eq '') {
	$template_file = 'email-none.shtml';
	$CMD = 'ERR';
	}

if ($CMD eq '' || $CMD eq 'CONTACT') {
#	require AUTOEMAIL;
#	$GTOOLS::TAG{'<!-- ECREATE -->'} = &AUTOEMAIL::safefetch_message($USERNAME,'ecreate')->{'zoovy:title'};
#	$GTOOLS::TAG{'<!-- EREMIND -->'} = &AUTOEMAIL::safefetch_message($USERNAME,'eremind')->{'zoovy:title'};
#	$GTOOLS::TAG{'<!-- ECUSTOM1 -->'} = &AUTOEMAIL::safefetch_message($USERNAME,'ecustom1')->{'zoovy:title'};
#	$GTOOLS::TAG{'<!-- ECUSTOM2 -->'} = &AUTOEMAIL::safefetch_message($USERNAME,'ecustom2')->{'zoovy:title'};
#
	$GTOOLS::TAG{'<!-- EXIDS -->'} = $q->param('EXIDS');
	$GTOOLS::TAG{'<!-- EXIDS_LIST -->'} = $GTOOLS::TAG{'<!-- EXIDS -->'};
	$GTOOLS::TAG{'<!-- EXIDS_LIST -->'} =~ s/,/, /g;

	require SITE;
	my ($SITE) = SITE->new($USERNAME,'PRT'=>$PRT);
	my ($se) = SITE::EMAILS->new($USERNAME,'*SITE'=>$SITE);
	my ($types) = $se->available('INCOMPLETE');

	my $out = '';
	foreach my $type (@{$types}) {
		$se->getref($type->{'MSGID'});
		my $hashref = $se->getref($type->{'MSGID'});
		
		$out .= "<tr><td><input type=\"radio\" name=\"message\" value=\"$type->{'MSGID'}\"></td>".
      			"<td><b>$hashref->{'MSGTITLE'}</b></td>".
      			"<td>$hashref->{'MSGSUBJECT'}</td></tr>";
		}

	$GTOOLS::TAG{'<!-- MESSAGES -->'} = $out;
	
	$template_file = 'email.shtml';
	} 

if ($CMD eq 'REVIEW') {

	require SITE;
	my ($SITE) = SITE->new($USERNAME,'PRT'=>$PRT);
	my ($se) = SITE::EMAILS->new($USERNAME,'*SITE'=>$SITE);
	my $hashref =  $se->getref($q->param('message'));

	$GTOOLS::TAG{'<!-- TITLE -->'} = &ZOOVY::incode($hashref->{'MSGSUBJECT'});
	$GTOOLS::TAG{'<!-- CONTENTS -->'} = &ZOOVY::incode($hashref->{'MSGBODY'});

	$template_file = 'email-review.shtml';


	#my $msgref = &AUTOEMAIL::safefetch_message($USERNAME,$message);
	my @ar = split(/,/,$EXIDS);
	#if (scalar(@ar)==1) {
	#
	#	# my ($tagref) = &ORDER::EMAIL::customer_email($USERNAME,$ar[0],$message,undef,1);
	#	my ($tagref) = &EXTERNAL::build_autoemail_info($USERNAME,$ar[0]);
#
#		use Data::Dumper;
#		print STDERR Dumper($tagref);
#
#		$GTOOLS::TAG{'<!-- TITLE -->'} = &ZOOVY::incode(${&AUTOEMAIL::interpolate(\$msgref->{'zoovy:title'},$tagref)});
#		$GTOOLS::TAG{'<!-- CONTENTS -->'} = &ZOOVY::incode(${&AUTOEMAIL::interpolate(\$msgref->{'zoovy:body'},$tagref)});
#		} else {
#		$GTOOLS::TAG{'<!-- TITLE -->'} = &ZOOVY::incode($msgref->{'zoovy:title'});
#		$GTOOLS::TAG{'<!-- CONTENTS -->'} = &ZOOVY::incode($msgref->{'zoovy:body'});
#		}
#	
	my $c = '';
	foreach my $ox (@ar) { $c .= "<input type='hidden' name='*ID-$ox' value='on'>\n"; }
	$GTOOLS::TAG{'<!-- EXIDS_DEFINED -->'} = $c;
	$GTOOLS::TAG{'<!-- EXIDS -->'} = $EXIDS;
	$GTOOLS::TAG{'<!-- EXIDS_LIST -->'} = $EXIDS;
	$GTOOLS::TAG{'<!-- EXIDS_LIST -->'} =~ s/,/, /g;

#	&GTOOLS::print_form('','email-review.shtml',1);
	} 


if ($CMD eq 'SENDNOW') {

	my $MSGSUBJECT = $q->param('MSGSUBJECT');
	my $MSGBODY = $q->param('MSGBODY');

	require SITE::EMAILS;
	## currently only using DEFAULT profile
	require SITE;
	my ($SITE) = SITE->new($USERNAME,'PRT'=>$PRT);
	my ($se) = SITE::EMAILS->new($USERNAME,'*SITE'=>$SITE);

	$|++;
	print "Content-type: text/html\n\n";
	print "<head><STYLE>\n<!--\nTD { font-face: arial; font-size: 10pt; }\n-->\n</STYLE>\n</head>\n";
	print "<body><center>";

	my @ar = split(/,/,$EXIDS);
	print "<h1>Sending email for ".scalar(@ar)." orders.</h1>";
	print "<table width='60%'><tr><Td><center>When complete, use the buttons along the top to return.</center><br><b>Email Results:</b></td></tr></table>\n";
	# print "$message ($EXIDS)\n";
	foreach my $exid (sort @ar) { 
		next if ($exid eq '');
			
		# my ($warnings) = TOXML::EMAIL::sendmail($USERNAME,$ZOOVY::cgiv->{'message'},undef,CLAIM=>$exid);
		my $error = '';
		require SITE;
		my ($SITE) = SITE->new($USERNAME,'PRT'=>$PRT,'PROFILE'=>$NS);
		my ($se) = SITE::EMAILS->new($USERNAME,'*SITE'=>$SITE);
		my ($ERR) = $se->send($message,
				CLAIM=>$exid,
				MSGBODY=>$MSGBODY,
				MSGSUBJECT=>$MSGSUBJECT,
				);		
		if ($ERR>0) { $error = $SITE::EMAILS::ERRORS{$ERR}; }

		print "<div><table width='60%'><tr><Td>Emailing for claim $exid</td></tr>";
		if ($error ne '') {
			print "<tr><td><font color=red>$error</font></td></tr>";
			}
		print "</table></div>\n";
			

##		if (&ZTOOLKIT::validate_email($email))
##			{
#			my $autoref = &EXTERNAL::build_autoemail_info($USERNAME,$exid);			
#			&AUTOEMAIL::sendmail($USERNAME,$autoref->{'%NAME%'},$msgref,$autoref);
#			print "<div><table width='60%'><tr><Td>Emailing ".$autoref->{'%NAME%'}." for $exid</td></tr></table></div>\n";
#			print STDERR "$USERNAME emailed $autoref->{'%NAME%'}\n";
##			} else {
##			print "<div><table width='60%'><font color='red'>ERROR:</font> Email for order $order not valid. ($email)</td></tr></table></div>\n";
##			}
		}
	$template_file = '';
	}

if ($template_file ne '') {
	&GTOOLS::output(file=>$template_file,header=>1);
	}



&DBINFO::db_zoovy_close();