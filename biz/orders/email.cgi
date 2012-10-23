#!/usr/bin/perl

use lib "/httpd/modules";
require GTOOLS;
require ORDER;
require SITE;
#require TOXML::EMAIL;
# require ORDER::EMAIL;
# require AUTOEMAIL;
require SITE::EMAILS;
require ZOOVY;
require ZTOOLKIT;
require CART2;
use CGI;
use Data::Dumper;
use strict;


require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_O&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $q = new CGI;
my $CMD = uc($q->param('CMD'));
if (!defined($CMD)) { $CMD = ''; }

my $ORDERS = $q->param('ORDERS');
$GTOOLS::TAG{'<!-- ORDERS -->'} = $ORDERS;

my $messageid = $q->param('message');
$GTOOLS::TAG{'<!-- message -->'} = $messageid;

my $AREA = uc($q->param('AREA'));
$GTOOLS::TAG{'<!-- AREA -->'} = $AREA;

my $SORTBY = lc($q->param('SORTBY'));
$GTOOLS::TAG{'<!-- SORTBY -->'} = $SORTBY;


if ($CMD eq '') {
	print "Content-type: text/html\n\n";
	print "<body>Javascript command failure, please retry. If this message persists please contact technical support.</body>\n";
	} 
elsif ($CMD eq 'SENDNOW') {

	my $c = '';

	$|++;

	$c .= "<head><STYLE>\n<!--\nTD { font-face: arial; font-size: 10pt; }\n-->\n</STYLE>\n</head>\n";
	$c .= "<body><center>";

	my @ar = ();
	foreach my $oid (split(/,/,$ORDERS)) {
		next if ($oid eq '');
		push @ar, $oid;
		}
	foreach my $key ($q->param()) {
		if ($key =~ /^order\-(.*?)$/) {
			push @ar, $1; 
			}
		}

	$c .= "<h1>Sending email for ".scalar(@ar)." orders.</h1>";
	$c .= "<table width='60%'><tr><Td><center>When complete, use the buttons along the top to return.</center><br><b>Email Results:</b></td></tr></table>\n";


	foreach my $oid (sort @ar) { 

		next if ($oid eq '');
	
		my ($CART2) = CART2->new_from_oid($USERNAME,$oid);

		my $error = undef;
		if (not $error) { 
			my $PROFILE = $CART2->in_get('our/profile');
			if ($PROFILE eq '') { $PROFILE = 'DEFAULT'; }

			my $email = $CART2->in_get('bill/email');
			$c .= "<div><table width='60%'><tr><Td>Emailing $email for $oid</td></tr>";

			my $MSGSUBJECT = $q->param('MSGSUBJECT');
			my $MSGBODY = $q->param('MSGBODY');

			my ($SREF) = SITE->new($USERNAME,'PRT'=>$CART2->prt(),'NS'=>$PROFILE);
			my ($se) = SITE::EMAILS->new($USERNAME,'*SITE'=>$SREF); # NS=>$PROFILE,PRT=>$PRT,GLOBALS=>1);
			my ($ERR) = $se->send($messageid,'*SITE'=>$SREF,'*CART2'=>$CART2,MSGBODY=>$MSGBODY,MSGSUBJECT=>$MSGSUBJECT);		

			if ($ERR==0) { 
				}
			elsif (defined $SITE::EMAILS::ERRORS{$ERR}) {
				$error = $SITE::EMAILS::ERRORS{$ERR}; 
				}
			else {
				$error = "UNDEFINED EMAIL ERROR CODE #$ERR";
				}
			$se = undef;
			}

		if ($error ne '') {
			$c .= "<tr><td><font color=red>&nbsp;&nbsp;$error</font></td></tr>";
			}

		}
	$c .= "</table></div>\n";
	$c .= "<h1>Finished.</h1>\n";
	$c .= "<a target='body' href='move.cgi?AREA=$AREA&SORTBY=$SORTBY'>Click here to Exit</a></center></body>";
	$GTOOLS::TAG{'<!-- BODY -->'} = $c;

	&GTOOLS::output(header=>1,file=>'email-out.shtml');
	}
 
elsif ($CMD eq 'REVIEW') {

	my ($SREF) = SITE->new($USERNAME,'PRT'=>$PRT);
	my ($se) = SITE::EMAILS->new($USERNAME,'*SITE'=>$SREF);
	my ($ref) = $se->getref($messageid);

	use Data::Dumper;
	$GTOOLS::TAG{'<!-- MSGTITLE -->'} = &ZOOVY::incode($ref->{'MSGTITLE'});
	$GTOOLS::TAG{'<!-- MSGBODY -->'} = &ZOOVY::incode($ref->{'MSGBODY'});

	$GTOOLS::TAG{'<!-- MSGTYPE -->'} = $ref->{'MSGTYPE'};

	my $c = '';
	my @ar = split(/,/,$ORDERS);
	foreach my $o (@ar) { $c .= "<input type='hidden' name='order-$o' value='on'>\n"; }
	$GTOOLS::TAG{'<!-- ORDERS_DEFINED -->'} = $c;
			
#	my $msgref = &AUTOEMAIL::safefetch_message($USERNAME,$message);
#	if (scalar(@ar)==1) {
#		my ($o,$error) = ORDER->new($USERNAME,$ar[0]);
#		next if (not defined $o);
#		next if ($error ne '');
#
#		my ($tagref) = &ORDER::EMAIL::customer_email($USERNAME,$ar[0],$message,undef,1,$o);
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
	


	&GTOOLS::output(file=>'email-review.shtml',header=>1);
	}
