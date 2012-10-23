#!/usr/bin/perl

my %lookup = ( 
	#'eric' => '6199948649@vtext.com',
	#'ericmail' => 'ez@zoovy.com',
	# 'kateo'=>'6198615331@vtext.com',
	'brian'=>'7604199953@vtext.com',
	'brian'=>'gru3hunt3r@gmail.com',
	'lizm'=>'9144004305@vtext.com',
	'nickd'=>'7609947938@vtext.com',
	'fredk'=>'6199874607@txt.att.net',
	'beckymail'=>'becky@zoovy.com',
	# 'jhunt'=>'9089100478@messaging.sprintpcs.com',
	'techsupport'=>'techsupport@zoovy.com',
	'becky'=>'7605330953@vtext.com',
	'logger'=>'brian@zoovy.com',
	# 'zoovycell'=>'7602135870@mobile.att.net',
	# 'david' => '7608467660@mycingular.com',
	# 'davidmail'=>'david@zoovy.com',
	# 'richard' =>'7606136834@tmomail.net',
	# 'richardmail'=>'richard@zoovy.com',
	# 'techpager'=>'8584675038@my2way.com',
	# 'techpager'=>'8584675119@my2way.com',
	);

use Text::Wrap;
$Text::Wrap::columns = 80;


use lib "/httpd/modules";
use ZOOVY;
use SUPPORT;
use GTOOLS;

my @TABS = ();
my @MSGS = ();

my @BC = ();
my @MSGS = ();
use strict;
push @BC, {title=>'Support' };

my $template_file = 'index.shtml';

require LUSER;
my ($LU) = LUSER->authenticate();
if (not defined $LU) { exit; }


my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

#my $LU = undef;
#my $MID = 0;
#my $FLAGS = '';
#my $USERNAME = 'brian';
#my $LUSERNAME = 'brian';

#$USERNAME = 'bamtar';
#$MID = &ZOOVY::resolve_mid($USERNAME);

$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;
$GTOOLS::TAG{'<!-- LUSERNAME -->'} = $LUSERNAME;

my $VERB = $ZOOVY::cgiv->{'VERB'};
my $TICKETID = $ZOOVY::cgiv->{'ID'};
my $zdbh = &DBINFO::db_zoovy_connect();




#if ($FLAGS =~ /,TRIAL,/) {
#	$VERB = 'DENYSUPPORT';
#	$template_file = 'need-billing.shtml';
#	}

if (($FLAGS =~ /DENYSUPPORT/) || ($FLAGS =~ /LOCKOUT/)) {
	$VERB = 'DENYSUPPORT';
	$template_file = 'denied.shtml';
	}


if ($VERB eq 'CONTACT-SAVE') {
	}

if ($VERB eq 'CONTACT') {
	$template_file = 'contact.shtml';
	}

if ($VERB eq 'HISTORY') {
	my $pstmt = "select date_format(CREATED,'%Y-%m') as YM from TICKET_BILLING where MID=$MID /* $USERNAME */ and CREATED>date_sub(now(),interval 90 day) group by YM order by YM desc";
	print STDERR $pstmt."\n";
	my $sthx = $zdbh->prepare($pstmt);
	$sthx->execute();
	my $c = '';
	while ( my ($YM) = $sthx->fetchrow() ) {
		$c .= "<tr>";		
		$c .= "<td class='small' nowrap align='center' valign='top'>$YM</td>";
		$c .= "<td>";


#mysql> desc TICKET_BILLING;
#+-------------+------------------+------+-----+---------------------+----------------+
#| Field       | Type             | Null | Key | Default             | Extra          |
#+-------------+------------------+------+-----+---------------------+----------------+
#| ID          | int(10) unsigned | NO   | PRI | NULL                | auto_increment |
#| USERNAME    | varchar(20)      | NO   |     | NULL                |                |
#| MID         | int(10) unsigned | NO   | MUL | 0                   |                |
#| TECH        | varchar(10)      | NO   |     | NULL                |                |
#| CREATED     | datetime         | NO   |     | 0000-00-00 00:00:00 |                |
#| DURATION    | time             | NO   |     | 00:00:00            |                |
#| COMMENT     | varchar(60)      | NO   |     | NULL                |                |
#| TICKET_ID   | int(10) unsigned | YES  |     | 0                   |                |
#| TASK_ID     | int(10) unsigned | YES  |     | 0                   |                |
#| BILLCLASS   | varchar(7)       | NO   |     | NULL                |                |
#| SETTLED_GMT | int(10) unsigned | NO   | MUL | 0                   |                |
#| LOCK_ID     | int(10) unsigned | NO   |     | 0                   |                |
#| LOCK_GMT    | int(10) unsigned | NO   |     | 0                   |                |
#| DONOTBILL   | tinyint(4)       | NO   |     | 0                   |                |
#| BS_TXN      | int(10) unsigned | NO   |     | 0                   |                |
#+-------------+------------------+------+-----+---------------------+----------------+
#15 rows in set (0.00 sec)

		$c .= "<table width=100%>";
		$c .= "<tr>";
		$c .= "<td width='50' class='zoovysub1header'>ticket</td>";
		$c .= "<td width='50' class='zoovysub1header'>duration</td>";
		$c .= "<td width='50' class='zoovysub1header'>tech</td>";
		$c .= "<td width='100' class='zoovysub1header'>created</td>";
		$c .= "<td class='zoovysub1header'>comment</td>";
		$c .= "</tr>";
		my ($yyyy,$mm) = split(/-/,$YM);
		$pstmt = "select * from TICKET_BILLING where MID=$MID /* $USERNAME */ and CREATED>='${yyyy}${mm}01000000' and CREATED<date_add('${yyyy}${mm}01000000',interval 1 month);";
		print STDERR $pstmt."\n";
		my $sth = $zdbh->prepare($pstmt);
		$sth->execute();
		my $r = '';
		while ( my $hashref = $sth->fetchrow_hashref() ) {

			$r = ($r eq 'r0')?'r1':'r0';
			my $pretty = $hashref->{'COMMENT'};
			if ($hashref->{'BILLCLASS'} ne '') {
				$pretty = $hashref->{'BILLCLASS'}.' '.$pretty;
				}

			if ($hashref->{'DONOTBILL'}>0) { $pretty = '[DNB] '.$pretty; }
			if ($hashref->{'BS_TXN'}>0) { $pretty = '[TXN: '.$hashref->{'BS_TXN'}.'] '.$pretty; }

			$c .= "<tr>";
			$c .= "<td class='$r' style='vertical-align: top; font-size: 7pt;'>";
			$c .= "<a href='index.cgi?VERB=TICKET-VIEW&ID=$hashref->{'TICKET_ID'}'>";
				$c .= "$hashref->{'TICKET_ID'}";
			$c .= "</a></td>";
			$c .= "<td class='$r' style='vertical-align: top; font-size: 7pt;'>$hashref->{'DURATION'}</td>";
			$c .= "<td class='$r' style='vertical-align: top; font-size: 7pt;'>$hashref->{'TECH'}</td>";
			$c .= "<td class='$r' style='vertical-align: top; font-size: 7pt;'>$hashref->{'CREATED'}</td>";
			$c .= "<td class='$r' style='vertical-align: top; font-size: 7pt;'>$pretty</td>";
			$c .= "</tr>";
			}
		$sth->finish();
		$c .= "</table>";

#		$c .= "<td class='small' valign='top'>$hashref->{'TOTALCONTACTS'}</td>";
#		$c .= "<td class='small' valign='top'>$hashref->{'TOTALMIN'}</td>";
#		$hashref->{'SUMMARY'} =~ s/^[\n\r\s]+//gs;
#		$c .= "<td class='small' valign='top'>$hashref->{'SUMMARY'}</td>";
		$c .= "</tr>";
		}
	$sthx->finish();
	if ($c eq '') { $c = '<tr><Td><i>No Activity</i></td></tr>'; }
	$GTOOLS::TAG{'<!-- HISTORY -->'} = $c;

	$template_file = 'history.shtml';
	}





##
##
##
if ($VERB eq 'BILLING') {
	my $PREPAIDDEBITS = 0; 

#mysql> desc TICKET_BILLING;
#+-------------+------------------+------+-----+---------------------+----------------+
#| Field       | Type             | Null | Key | Default             | Extra          |
#+-------------+------------------+------+-----+---------------------+----------------+
#| ID          | int(10) unsigned | NO   | PRI | NULL                | auto_increment |
#| USERNAME    | varchar(20)      | NO   |     | NULL                |                |
#| MID         | int(10) unsigned | NO   | MUL | 0                   |                |
#| TECH        | varchar(10)      | NO   |     | NULL                |                |
#| CREATED     | datetime         | NO   |     | 0000-00-00 00:00:00 |                |
#| DURATION    | time             | NO   |     | 00:00:00            |                |
#| COMMENT     | varchar(60)      | NO   |     | NULL                |                |
#| TICKET_ID   | int(10) unsigned | YES  |     | 0                   |                |
#| TASK_ID     | int(10) unsigned | YES  |     | 0                   |                |
#| BILLCLASS   | varchar(7)       | NO   |     | NULL                |                |
#| SETTLED_GMT | int(10) unsigned | NO   | MUL | 0                   |                |
#| LOCK_ID     | int(10) unsigned | NO   |     | 0                   |                |
#| LOCK_GMT    | int(10) unsigned | NO   |     | 0                   |                |
#| DONOTBILL   | tinyint(4)       | NO   |     | 0                   |                |
#| BS_TXN      | int(10) unsigned | NO   |     | 0                   |                |
#+-------------+------------------+------+-----+---------------------+----------------+
#15 rows in set (0.00 sec)

	my $pstmt = "select * from TICKET_BILLING where MID=$MID /* $USERNAME */ and SETTLED_GMT=0";
	my $sth = $zdbh->prepare($pstmt);
	$sth->execute();
	my $c = '';
	use Data::Dumper;
	while (my $hashref = $sth->fetchrow_hashref()) {
		# $c .= "<tr><Td><pre>".Dumper($hashref)."</pre></td></tr>\n";
		$c .= "<tr>";
		$c .= "<td valign='top' nowrap class='small'>".&ZTOOLKIT::pretty_date(&ZTOOLKIT::mysql_to_unixtime($hashref->{'CREATED'}),0)."</td>";
		$c .= "<td valign='top' nowrap class='small'>".$hashref->{'TECH'}."</td>";
		$c .= "<td valign='top' nowrap class='small'>".$hashref->{'DURATION'}."</td>";
		$c .= "<td valign='top' class='small'>".$hashref->{'COMMENT'}.'</td>';
		$c .= "<td valign='top' nowrap class='small'>".$hashref->{'TICKET_ID'}.'</td>';
		
		$c .= "<td valign='top' nowrap align='right' class='small'>";
		$c .= $hashref->{'BILLCLASS'};
		if ($hashref->{'DONOTBILL'}) { $c .= "/WAIVED"; }
		$c .= '</td>';

		$c .= "</tr>";
		$PREPAIDDEBITS += $hashref->{'BILLMIN'};
		}
	if ($c eq '') { $c .= "<tr><td class='small'><i>No pending service charges found.</td></tr>"; }
	$GTOOLS::TAG{'<!-- FT_LOGS -->'} = $c;

	$pstmt = "select * from PREPAID_MINUTES where MID=$MID /* $USERNAME */ and (EXPIRES_GMT=0 or EXPIRES_GMT>unix_timestamp(now()))";
	$sth = $zdbh->prepare($pstmt);
	$sth->execute();
	$c = '';
	use Data::Dumper;
	my $PREPAIDCREDITS = 0;
	my $r = '';
	my %CLASSES = ();
	while ( my $hashref = $sth->fetchrow_hashref() ) {
		# $c .= '<tr><td class='small'>'.Dumper($hashref).'</td></tr>';
		$r = ($r eq 'r0')?'r1':'r0';
		$c .= "<tr class=$r>";
		$CLASSES{ $hashref->{'JOBTYPE'} } += $hashref->{'TOTALMIN'};
		my $b36id = &SUPPORT::base36($hashref->{'ID'});
		$c .= "<td valign=top class='small'>".$b36id."</td>";

		$c .= "<td valign=top class='small'>";
		if ($hashref->{'JOBTYPE'} eq 'IMP') {
			$c .= "Implementation Only";
			}
		elsif ($hashref->{'JOBTYPE'} eq 'TIDA') {
			$c .= "IMP/MKT/BSM Services";
			}
		elsif ($hashref->{'JOBTYPE'} eq 'DESIGN') {
			$c .= "Design/Build/QA";
			}
		$c .= "</td>";

		if ($hashref->{'TECH'} eq '') { 	
			$c .= "<td valign=top nowrap class='small'>** UNRESTRICTED **</td>"; 
			}
		else {
			$c .= "<td valign=top class='small'>$hashref->{'TECH'}</a></td>";
			}
		

		$c .= "<td valign=top class='small'>".$hashref->{'TOTALMIN'}."</td>";
		$c .= "<td nowrap valign=top class='small'>".&ZTOOLKIT::pretty_date($hashref->{'CREATED_GMT'},3)."</td>";
		if ($hashref->{'EXPIRES_GMT'}>0) {
			$c .= "<td nowrap valign=top class='small'>".&ZTOOLKIT::pretty_date($hashref->{'EXPIRES_GMT'},0)."</td>";
			}
		else {
			$c .= "<td class='small'>Never</td>";
			}
		$c .= "<td>".&ZOOVY::incode($hashref->{'STATUS'})."</td>";
		$c .= "</tr>";
		$PREPAIDCREDITS += $hashref->{'TOTALMIN'};
		
		}
	if	($c eq '') { $c = '<tr><Td><i>None Available</i></td></tr>'; }

	if ($PREPAIDCREDITS-$PREPAIDDEBITS>0) {
		$c .= "<tr><td colspan=7><hr></td></tr>";
		foreach my $class (keys %CLASSES) {
			my $pretty = $class;
			if ($pretty eq 'IMP') { $pretty = 'Implementation Only'; }
			if ($pretty eq 'TIDA') { $pretty = 'Implementation/Marketing'; }
			if ($pretty eq 'DESIGN') { $pretty = 'Design/Build/QA'; }
			$c .= "<tr><td class='small' class='zoovysub1header' colspan='3' align='right'>Available $pretty Minutes:</td><td class='small' colspan='3' class='zoovysub1header'>$CLASSES{$class}</td></tr>";
			}
		if ($PREPAIDDEBITS>0) {
			$c .= "<tr><td class='small' class='zoovysub1header' colspan='3' align='right'>Total Prepaid Minutes:</td><td class='small' colspan='3' class='zoovysub1header'>$PREPAIDCREDITS</td></tr>";
			$c .= "<tr><td class='small' class='zoovysub1header' colspan='3' align='right'>Pending Debits:</td><td class='small' colspan='3' class='zoovysub1header'>-$PREPAIDDEBITS</td></tr>";
			}
		$c .= "<tr><td class='small' class='zoovysub1header' colspan='3' align='right'><b>Total Available Minutes:</b></td><td class='small' colspan='3' class='zoovysub1header'><b>".($PREPAIDCREDITS-$PREPAIDDEBITS)."</b></td></tr>";
		}
	
	$GTOOLS::TAG{'<!-- FASTTRACKS -->'} = $c;
	$template_file = 'billing.shtml';
	}


push @TABS, { name=>"Create Ticket", selected=>($VERB eq 'TICKET-CREATE')?1:0, link=>"index.cgi?VERB=TICKET-CREATE" };
push @TABS, { name=>"Active Tickets" };

# push @TABS, { name=>"Contact Details", selected=>($VERB eq 'CONTACT')?1:0, link=>"index.cgi?VERB=CONTACT" };
if (($VERB eq 'BILLING') || ($VERB eq 'HISTORY')) {
	push @TABS, { name=>"Unused Time", selected=>($VERB eq 'BILLING')?1:0, link=>"index.cgi?VERB=BILLING" };
	push @TABS, { name=>"Billing History", selected=>($VERB eq 'HISTORY')?1:0, link=>"index.cgi?VERB=HISTORY" };
	}


##
##
##
my %DOWTEXT = (
	'1' => 'Mon',
	'2' => 'Tue',
	'3' => 'Wed',
	'4' => 'Thu',
	'5' => 'Fri',
	'6' => 'Sat',
	'7' => 'Sun',
	);

my %MONTEXT = (
	'1' => 'January',
	'2' => 'February',
	'3' => 'March',
	'4' => 'April',
	'5' => 'May',
	'6' => 'June',
	'7' => 'July',
	'8' => 'August',
	'9' => 'September',
	'10' => 'October',
	'11' => 'November',
	'12' => 'December',
	);


my $CLASS = $ZOOVY::cgiv->{'CLASS'};
my $qtCLASS = $zdbh->quote($CLASS);


if (($VERB =~ /APPT-/) || ($VERB eq 'CALENDAR')) {
	$GTOOLS::TAG{'<!-- CLASS -->'} = $CLASS;

	if ($CLASS eq 'BPP') {
		$GTOOLS::TAG{'<!-- BILLABLE -->'} = qq~
<b>Best Partner Practice Appointments:</b><br>
Intended Purpose: BPP meetings are broken into three sections: 1. general business discussion, 2. what you might not
know, 3. upcoming features.  During this time there is opportunity for interactive Q&A and a chance to make 
feature requests and be invited to participate in upcoming pilots. <br>
<br>
Clients who participate in our BPP incentive program may schedule these meetings once per quarter for free, and are 
required to have at least one per year to remain in the program. 
Hourly rate for additional appointments and non BPP-members is outlined in our 
<a href="http://webdoc.zoovy.com/doc/50551">billing guidelines.</a>
~;
		}
	elsif ($CLASS eq 'GEEK') {
		$GTOOLS::TAG{'<!-- BILLABLE -->'} = qq~
<b>Geek Services:</b><br>
Intended purpose: Zoovy will provide IT services on various issues such as network configuration, 
database administration, operating system configuration. These services are considered ancilliary to the Zoovy offering.  <br>
Reminder: This is not a free service, please review our <a href="http://webdoc.zoovy.com/doc/50551">billing guidelines.</a><br>
~;
		}
	elsif ($CLASS eq 'MKT') {
		$GTOOLS::TAG{'<!-- BILLABLE -->'} = qq~
<b>Marketing Services:</b><br>
Intended purpose: Zoovy will provide Marketing Analysis services on various issues such as 
Search Engine Optimization, ROI/Conversion Tracking, Adwords/CPC. 
These services are considered ancilliary to the Zoovy offering.  <br>
Reminder: This is not a free service, please review our <a href="http://webdoc.zoovy.com/doc/50551">billing guidelines.</a><br>
~;
		}
	elsif ($CLASS eq 'DESIGN') {
		$GTOOLS::TAG{'<!-- BILLABLE -->'} = qq~
<b>Design Services:</b><br>
Intended purpose: consultation with a graphic designer to discuss asthetics of a current or upcoming design project.<br>
Reminder: This is not a free service, please review our <a href="http://webdoc.zoovy.com/doc/50551">billing guidelines.</a><br>
~;
		}
	else {
		$GTOOLS::TAG{'<!-- BILLABLE -->'} = qq~
<b>Implementation Services:</b><br>
Please note: the appointment system will allow you to schedule as much time as you need.<br>
It is your responsibility to ensure you stay within your time budget. 
<br>
You can see how much time is available by clicking the Support Credits &amp;
Balances link in the left hand navigation.
<br>
Zoovy does not provide outbound phone support for Canadian customers unless those customers provide a toll-free number.<br>
<br>
~;
		}
	
	$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;
	$GTOOLS::TAG{'<!-- ID -->'} = $ZOOVY::cgiv->{'ID'};

	my $pstmt = "select ID,TECH,XTECHS,JOBTYPE from PREPAID_MINUTES where MID=$MID /* $USERNAME */ order by ID desc";
	print STDERR $pstmt."\n";
	my $sth = $zdbh->prepare($pstmt);
	$sth->execute();
	my ($fasttrack,$MYTECH,$XTECHS,$JOBTYPE) = $sth->fetchrow();
	$GTOOLS::TAG{'<!-- TECH -->'} = ($MYTECH)?"with ".ucfirst($MYTECH):'';
	#if (!defined($fasttrack)) { $VERB = 'DENY'; }
	$sth->finish();

	if ($FLAGS =~ /,TRIAL,/) { $VERB = 'APPT-DENY'; }
	}

if ($VERB eq 'APPT-DENY') {
	$template_file = 'appt-deny.shtml';
	}

########################### CANCEL CODE ###################################
if ($VERB eq 'APPT-CANCEL') {
	$template_file = 'appt-cancel.shtml';
	$GTOOLS::TAG{'<!-- ID -->'} = $ZOOVY::cgiv->{'ID'};
	}

########################## CANCEL CONFIRM CODE #############################
if ($VERB eq 'APPT-CANCELCONFIRM') {
	$VERB = '';

	my $pstmt = "select TECH,TOPIC,BEGINS from SCHEDULE_RESERVATIONS where ID=".$zdbh->quote($ZOOVY::cgiv->{'ID'})." and MID=$MID /* $USERNAME */";
	my $sth = $zdbh->prepare($pstmt);
	$sth->execute();
	my ($tech,$topic,$begins) = $sth->fetchrow();
	$sth->finish();

	$pstmt = "delete from SCHEDULE_RESERVATIONS where ID=".$zdbh->quote($ZOOVY::cgiv->{'ID'})." and USERNAME=".$zdbh->quote($USERNAME);
	print STDERR $pstmt."\n";
	$zdbh->do($pstmt);

	my $hashref = ();
	## changed to LUSER - patti - 20070611
	## email is now account email vs DEFAULT profile's support email
	require LUSER;
	my ($LU) = LUSER->new($USERNAME);
	$hashref->{'%FIRSTNAME%'} = $LU->get("zoovy:firstname");
	$hashref->{'%LASTNAME%'} = $LU->get("zoovy:lastname");
	$hashref->{'%FULLNAME%'} = $LU->get("zoovy:fullname");
	$hashref->{'%EMAIL%'} = $LU->get("zoovy:email");
	if ($hashref->{'%EMAIL%'} eq '') { 
		$hashref->{'%EMAIL%'} = $LU->get("zoovy:support_email");
		}

	# $hashref = &ZMAIL::load_user($USERNAME);
	$hashref->{'%USERNAME%'} = $USERNAME;
	$hashref->{'%TOPIC%'} = $topic;
	$hashref->{'%BEGINS%'} = $begins;

	require ZMAIL;
	&ZMAIL::send_html("$tech\@zoovy.com",$hashref->{'%EMAIL%'},$hashref,"APPOINTMENT CANCELLATION CONFIRMATION",'messages/cancel.html','messages/cancel.txt',"$tech\@zoovy.com");

	#use Data::Dumper;
	#print STDERR Dumper($hashref);
	print STDERR "cancelconfirm called!\n";
	}


########################### CONFIRM CODE ##################################
if ($VERB eq 'APPT-CONFIRM') {

	my $pstmt = "select count(*) from SCHEDULE_RESERVATIONS where SCHEDULEID=".$zdbh->quote($ZOOVY::cgiv->{'SCHEDULEID'})." and BEGINS=".$zdbh->quote($ZOOVY::cgiv->{'BEGINS'});
	print STDERR $pstmt."\n";
	my $sth = $zdbh->prepare($pstmt);
	$sth->execute();
	my ($count) = $sth->fetchrow();
	$sth->finish();

	if ($ZOOVY::cgiv->{'sameday'} eq '') {
		$VERB = 'APPT-CREATE';
		$GTOOLS::TAG{'<!-- ERROR -->'} = 'ERROR: You must accept the same day appointment terms.';
		}
	elsif ($ZOOVY::cgiv->{'phone1'} eq '') {
		$GTOOLS::TAG{'<!-- ERROR -->'} = 'ERROR: You must have a phone number!';
		$VERB = 'APPT-CREATE';
		}
	elsif ($count>0) {
		$GTOOLS::TAG{'<!-- ERROR -->'} = 'ERROR: Appointment already scheduled.';
		&GTOOLS::print_form('','error.shtml',1);
		exit;
		}
	elsif ( length($ZOOVY::cgiv->{'TOPIC'})<10 ) {
		$VERB = 'APPT-CREATE';
		$GTOOLS::TAG{'<!-- ERROR -->'} = 'ERROR: You must specify a topic of at least 10 characters';
		}
	else {

		my $TOPIC = $ZOOVY::cgiv->{'TOPIC'}."<br>\n";
		$TOPIC .= "phone: ".$ZOOVY::cgiv->{'phone1'}." \n";
		if ($ZOOVY::cgiv->{'phone2'} ne '') {
			$TOPIC .= "<br>alt/phone: ".$ZOOVY::cgiv->{'phone2'}." \n";
			}

		($pstmt) = &DBINFO::insert($zdbh,'SCHEDULE_RESERVATIONS',{
			'*CREATED'=>'now()',
			TECH=>$ZOOVY::cgiv->{'TECH'},
			TOPIC=>$TOPIC,
			USERNAME=>$USERNAME,
			MID=>$MID,
			LUSER=>$LUSERNAME,
			BEGINS=>$ZOOVY::cgiv->{'BEGINS'},
			DURATION=>$ZOOVY::cgiv->{'DURATION'},
			SCHEDULEID=>$ZOOVY::cgiv->{'SCHEDULEID'},
			},debug=>2);

		$zdbh->do($pstmt);

#		$pstmt = "insert into SCHEDULE_RESERVATIONS (ID,CREATED,TECH,TOPIC,USERNAME,BEGINS,DURATION,SCHEDULEID) values(0,now(),";
#		$pstmt .= $zdbh->quote($ZOOVY::cgiv->{'TECH'}).",";
#		$pstmt .= $zdbh->quote($TOPIC).",";
#		$pstmt .= $zdbh->quote($USERNAME).",";
#		$pstmt .= $zdbh->quote($ZOOVY::cgiv->{'BEGINS'}).",";
#		$pstmt .= $zdbh->quote($ZOOVY::cgiv->{'DURATION'}).",";
#		$pstmt .= $zdbh->quote($ZOOVY::cgiv->{'SCHEDULEID'}).")";
#		print STDERR $pstmt."\n";
#		$sth = $zdbh->prepare($pstmt);
#		$sth->execute();

		my $tech = $ZOOVY::cgiv->{'TECH'};
		$tech =~ s/\W+//g;

		my $hashref = ();
		## changed to LUSER - patti - 20070611
		## email is now account email vs DEFAULT profile's support email	
		require LUSER;
		my ($LU) = LUSER->new($USERNAME);
		$hashref->{'%FIRSTNAME%'} = $LU->get("zoovy:firstname");
		$hashref->{'%LASTNAME%'} = $LU->get("zoovy:lastname");
		$hashref->{'%FULLNAME%'} = $LU->get("zoovy:fullname");
		$hashref->{'%EMAIL%'} = $LU->get("zoovy:email");
		# $hashref = &ZMAIL::load_user($USERNAME);

		require ZMAIL;
		$hashref->{'%TECH%'} = $tech;
		$hashref->{'%TOPIC%'} = $TOPIC;
		$hashref->{'%USERNAME%'} = $USERNAME;
		$hashref->{'%BEGINS%'} = $ZOOVY::cgiv->{'BEGINS'};
		$hashref->{'%DURATION'} = $ZOOVY::cgiv->{'DURATION'};
		$hashref->{'%SAMEDAY_HTML%'} = '';
		$hashref->{'%SAMEDAY_TXT%'} = '';

		my $title = "Training Appointment Confirmation";
		if ($ZOOVY::cgiv->{'sameday'} eq 'on') {
			$hashref->{'%SAMEDAY_HTML%'} = '<font color="RED"><b>IMPORTANT: THIS IS NOT A CONFIRMATION - SAME DAY APPOINTMENTS CAN ONLY BE RESERVED, NOT CONFIRMED.</b></font>';
			$hashref->{'%SAMEDAY_TXT%'} = 'IMPORTANT: THIS IS NOT A CONFIRMATION - SAME DAY APPOINTMENTS CAN ONLY BE RESERVED, NOT CONFIRMED.';

			$title = "SAME DAY Training Appointment - *TENATIVE*";
			&ZMAIL::send_html("$tech\@zoovy.com",$hashref->{'%EMAIL%'},$hashref,$title,'messages/confirm.html','messages/confirm.txt',"$tech\@zoovy.com");	
			}
		else {
			&ZMAIL::send_html("$tech\@zoovy.com",$hashref->{'%EMAIL%'},$hashref,$title,'messages/confirm.html','messages/confirm.txt',"$tech\@zoovy.com");	
			}

		print STDERR "Confirm Appointment!\n";
		$VERB = '';
		}

	}





##
##
##

########################### SCHEDULE CODE ##################################
if ($VERB eq 'APPT-CREATE') {
	$GTOOLS::TAG{'<!-- TECH -->'} = $ZOOVY::cgiv->{'TECH'};
	$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;
	$GTOOLS::TAG{'<!-- DATE -->'} = $ZOOVY::cgiv->{'DATE'};
	
	my $pstmt = "select BEGINTIME,ENDTIME,TECH,CLASS,HOLD_DAYS from SCHEDULE_APPOINTMENTS where ID=".$zdbh->quote($ZOOVY::cgiv->{'ID'});
	my $sth = $zdbh->prepare($pstmt);
	$sth->execute();
	if ($sth->rows()>0) {
		my ($year,$month,$day) = split(/-/,$ZOOVY::cgiv->{'DATE'});
		my ($beginspst,$ends,$tech,$class,$hold) = $sth->fetchrow();
			
		# calc EST
		my $beginsest = $beginspst;
		$beginsest = (substr($beginsest,0,index($beginsest,':'))+3).":".substr($beginsest,index($beginsest,':')+1);

		# figure out duration of the appointment
		my ($beginH,$beginM,$beginS) = split(/:/,$beginspst);
		my ($endH,$endM,$endS) = split(/:/,$ends);
		print STDERR "$year,$month,$day,$beginH,$beginM,$beginS,$year,$month,$day,$endH,$endM,$endS\n";
		my ($d,$h,$m,$s) = &Date::Calc::Delta_DHMS($year,$month,$day,$beginH,$beginM,$beginS,$year,$month,$day,$endH,$endM,$endS);
		$m += $h*60;

		$GTOOLS::TAG{'<!-- BEGIN_PRETTY_EST -->'} = "$month/$day/$year $beginspst";
		$GTOOLS::TAG{'<!-- BEGIN_PRETTY_PST -->'} = "$month/$day/$year $beginsest";
		$GTOOLS::TAG{'<!-- END_PRETTY -->'} = "$month/$day/$year $ends";
		$GTOOLS::TAG{'<!-- BEGINS -->'} = "$year-$month-$day $beginspst";

		my ($thisyear,$thismonth,$thisday) = &Date::Calc::Today();
		if ($year == $thisyear && $month == $thismonth && $day == $thisday) {
			## this is a same day appointment
			$GTOOLS::TAG{'<!-- SAME_DAY -->'} = qq~
<font color='red'>IMPORTANT RULES REGARDING SAME DAY APPOINTMENT SCHEDULING</font><br>
Same day appointments are a courtesy to our customers, however they are unconfirmed. 
Zoovy support personnel automatically receive their schedules each morning, 
and subsequently plan their days and other activities accordingly. 

When you schedule a same day appointment, you are doing so with the knowledge that you are only making a reservation - the appointment is not guaranteed. 
Our technicians will do their best to email you and confirm/deny the appointment via email. 
Since it is a best effort appointment, if you are not available, or for any reason the appointment doesn't happen you will not be charged.<br>

</font>
&nbsp;&nbsp;&nbsp; <u><input type="checkbox" name="sameday"> I agree to the terms above.</u><br>
<br>
			~;
			}
		else {
			$GTOOLS::TAG{'<!-- SAME_DAY -->'} = qq~ <input type="hidden" name="sameday" value="no">~;
			}


		
		$GTOOLS::TAG{'<!-- TECH -->'} = $tech;
		$GTOOLS::TAG{'<!-- DURATION -->'} = $m;
		$GTOOLS::TAG{'<!-- SCHEDULEID -->'} = $ZOOVY::cgiv->{'ID'};
		my ($LU) = LUSER->new($USERNAME);
		$GTOOLS::TAG{'<!-- PHONE1 -->'} = $LU->get('zoovy:phone');
		$GTOOLS::TAG{'<!-- PHONE2 -->'} = $LU->get('zoovy:support_phone');
		if ($GTOOLS::TAG{'<!-- PHONE1 -->'} eq $GTOOLS::TAG{'<!-- PHONE2 -->'}) {
			$GTOOLS::TAG{'<!-- PHONE2 -->'} = '';
			}

		

#		if (uc($class) eq 'DESIGN') {
#			$GTOOLS::TAG{'<!-- TECH_NOTICE -->'} = qq~
#<tr>
#	<td colspan='3'>
#	<font color='red'><b>NOTICE: You are about to schedule time with a </font><font color=blue>GRAPHICS DESIGN</font><font color=red> specialist</b></font><br>
#This indivdual specializes in graphic design and HTML integration for the Zoovy system. 
#Appointments for other topics will be cancelled, or routed to another technician.
#	</td>
#</tr>
#~;
#			}


#		if (lc($tech) eq 'becky') {
#			$GTOOLS::TAG{'<!-- TECH_NOTICE -->'} = qq~
#<tr>
#	<td colspan='3'>
#	<font color='red'><b>NOTICE: You are about to schedule time with a specialist</b></font><br>
#Becky is one of the programmers who maintains the Windows Product Manager and Windows Order Manager application.
#Becky's training appointments are available exclusively to assist customers with their Quickbooks integration.
#Becky is intimately familiar with the Quickbooks application, and also quite adept at handling most accounting issues.
#If the purpose for your appointment isn't to discuss Quickbooks it will probably be cancelled and/or routed to another technician. 
#To make the most of your time - you should not schedule your Quickbooks training until after you've installed Order Manager, 
#and synchronized your invoices.
#	</td>
#</tr>
#~;
#			}
#
#		if (lc($tech) eq 'eric') {
#			$GTOOLS::TAG{'<!-- TECH_NOTICE -->'} = qq~
#<tr>
#	<td colspan='3'>
#	<font color='red'><b>NOTICE: You are about to schedule time with a specialist</b></font><br>
#Eric is the person who is responsible for maintaining the DNS and Zoovymail services. 
#He has appointments available exclusively to discuss those subjects.
#Eric does not do regular training, 
#if you attempt to schedule a regular e-commerce training sessions with him the appointment will be cancelled.
#	</td>
#</tr>
#~;
#			}


#		if (lc($tech) eq 'brian') {
#			$GTOOLS::TAG{'<!-- TECH_NOTICE -->'} = qq~
#<tr>
#	<td colspan='3'>
#	<font color='red'><b>NOTICE: You are about to schedule time with a specialist</b></font><br>
#Brian is the co-founder and system architect of Zoovy. Employee #1 at Zoovy - there is no question he cannot answer.
#	</td>
#</tr>
#~;
#			}


		$template_file = 'appt-create.shtml';
		}
	else {
		$VERB = '';
		}
	}


########################### CALENDAR CODE ##################################

if (($VERB eq 'CALENDAR') && ($FLAGS =~ /,TRIAL,/)) {
	$VERB = 'CALENDAR-DENIED';
	$template_file = 'denied.shtml';
	}


##
##
##
if ($VERB eq 'CALENDAR') {
	$GTOOLS::TAG{'<!-- CLASS -->'} = $ZOOVY::cgiv->{'CLASS'};
	$GTOOLS::TAG{'<!-- TIME_ -->'} = '';
	$GTOOLS::TAG{'<!-- TIME_BEFORE -->'} = '';
	$GTOOLS::TAG{'<!-- TIME_AFTER -->'} = '';
	$GTOOLS::TAG{'<!-- TIME_EARLY -->'} = '';
	$GTOOLS::TAG{'<!-- TIME_LATE -->'} = '';
	$GTOOLS::TAG{'<!-- TIME_'.$ZOOVY::cgiv->{'TIME'}.' -->'} = 'selected'; 

	$template_file = 'calendar.shtml';
	my $c = '';

	# only show tomorrow
	# ($year,$month,$day) = &Date::Calc::Add_Delta_Days(&Date::Calc::Today(),1);

	# include today
	my ($thisYear,$thisMonth,$thisDay, $thisHour,$thisMin,$thisSec) = &Date::Calc::Today_and_Now();	
	my $year = $thisYear;
	my $month = $thisMonth;
	my $day = $thisDay;


# override
# $day =
# $month = 
# $year = 

	my $daysinmonth = &Date::Calc::Days_in_Month($year,$month);
	$GTOOLS::TAG{'<!-- DEBUG -->'} = "Year[$year] Month[$month] Day[$day] DaysinMonth[$daysinmonth]\n";
	my $daystoprint = &Date::Calc::Day_of_Week($year,$month,$day);
	$daystoprint -= 1;	# sunday is normally 7, we want it to be 6
	$c = qq~
<tr>
	<td class='zoovytableheader' colspan='7'>$MONTEXT{$month} $year</td>
</tr>
<tr>
	<td class='zoovysub2header' style='width:100px;'>Mon</td>
	<td class='zoovysub2header' style='width:100px;'>Tue</td>
	<Td class='zoovysub2header' style='width:100px;'>Wed</td>
	<td class='zoovysub2header' style='width:100px;'>Thu</td>
	<td class='zoovysub2header' style='width:100px;'>Fri</td>
	<td class='zoovysub2header' style='width:100px;'>Sat</td>
	<td class='zoovysub2header' style='width:100px;'>Sun</td>
</tr>\n~;
	$c .= qq~<tr style="height:100px;">\n~;

	if ($daystoprint>0) {
		my $todays_date = $day;
		$GTOOLS::TAG{'<!-- DEBUG -->'} .= "Daystoprint[$daystoprint]\n";
		while ( $daystoprint-- > 0) { 
			## NOTE: this where we ought to write the day of week.
			$c .= "<td valign='top' class='r1 border_right border_bottom' height=100><h3 align='right'></h3>\n"; 
			}
		}	

	$daystoprint += 15;
	my $dow = &Date::Calc::Day_of_Week($year,$month,$day); $dow--;	
	while ( ($daystoprint-- > 0) || ($dow != 7)) {
		if ($dow >= 7) { $dow = 1; } 
		else { $dow++; }

		if (($day == $thisDay) && ($month == $thisMonth)) {
			$c .= "<td valign='top' class='rx border_right border_bottom'><h3 align='right'>$day</h3>\n";
			$c .= "<b><font color='red'>TODAY!</font></b>\n";
			}
		else { 
			$c .= "<td valign='top' class='r0 border_right border_bottom' height=100><h3 align='right'>$day</h3>\n";
			}
	
	## figure out which appointments are available
	#	$pstmt = "select ID,DOW,BEGINTIME,ENDTIME,TECH from SCHEDULE_APPOINTMENTS where DOW=".$zdbh->quote($DOWTEXT{$dow});
	#	if ($MYTECH ne '') { $pstmt .= " and TECH=".$zdbh->quote($MYTECH); }
	#	$pstmt .= " order by BEGINTIME";
	#	print STDERR $pstmt."\n";
	#	$sth = $zdbh->prepare($pstmt);
	#	$sth->execute();
	#	$DOWHASH = ();
	#	while ( $hashref = $sth->fetchrow_hashref() ) {
	#		push @{$DOWHASH{$hashref->{'DOW'}}}, $hashref;
	#		}
	#	$sth->finish();


	# figure out which appointments are available
	my $pstmt = "select ID,BEGINTIME,ENDTIME,TECH,HOLD_DAYS from SCHEDULE_APPOINTMENTS where CLASS=$qtCLASS and DOW=".$zdbh->quote($DOWTEXT{$dow});
	if ($ZOOVY::cgiv->{'TIME'} eq '') {
		# No special time
		}
	elsif ($ZOOVY::cgiv->{'TIME'} eq 'BEFORE') {
		$pstmt .= " and BEGINTIME<'12:00'";
		}
	elsif ($ZOOVY::cgiv->{'TIME'} eq 'AFTER') {
		$pstmt .= " and BEGINTIME>'12:00'"; 
		}
	elsif ($ZOOVY::cgiv->{'TIME'} eq 'EARLY') { 
		$pstmt .= " and BEGINTIME<'7:00'";
		}
	elsif ($ZOOVY::cgiv->{'TIME'} eq 'LATE') {		
		$pstmt .= " and BEGINTIME>'18:00'";
		}


#	if ($MYTECH ne '') { 
#		if ($XTECHS ne '') {
#			my @techs = split(',',$XTECHS);
#			push @techs, $MYTECH;
#			$pstmt .= " and TECH in (";
#			foreach my $t (@techs) { $pstmt .= $zdbh->quote($t).','; }
#			chop($pstmt);
#			$pstmt .= ")";
#			}
#		else {
#			# single trainer
#			$pstmt .= " and TECH=".$zdbh->quote($MYTECH); 
#			}
#		}
	
	$pstmt .= " order by BEGINTIME";
	# print STDERR $pstmt."\n";

	my $sth = $zdbh->prepare($pstmt);
	$sth->execute();

	#my $jt_tech = 0;
	while ( my ($id,$begin,$end,$tech,$holddays) = $sth->fetchrow() ) {
		#next if ($tech eq 'jt' && $jt_tech > 0);

		## HOLDDAYS concept: if it's a monday appt, with a holdday of 3 - then it won't be available 
		##							until 3 days BEFORE the appointment. (e.g. SAT)
		my $AVAILABLE_AFTER = ($holddays==0)?0:&ZTOOLKIT::mysql_to_unixtime(sprintf("%4d%2d%2d000000",$year,$month,$day))-(86400*$holddays);
		next if ( ($holddays>0) && ( $^T < $AVAILABLE_AFTER ) );

		next if ($tech eq 'reneec');
		
		# verify that this particular appointment hasn't be taken already
		my $pstmt = "select ID,USERNAME,TOPIC from SCHEDULE_RESERVATIONS where SCHEDULEID=$id ";
		$pstmt .= " and BEGINS=".$zdbh->quote(sprintf("%4d-%d-%d %s",$year,$month,$day,$begin));
		# print STDERR $pstmt."\n";
		my $sth2 = $zdbh->prepare($pstmt);

		# strip leading zero from time
		if (substr($begin,0,1) eq '0') { $begin = substr($begin,1); }
		if (substr($end,0,1) eq '0') { $end = substr($end,1); }
	
		# figure out duration of the appointment	
		my ($beginH,$beginM,$beginS) = split(/:/,$begin);
		my ($endH,$endM,$endS) = split(/:/,$end);	
		my ($d,$h,$m,$s) = &Date::Calc::Delta_DHMS($year,$month,$day,$beginH,$beginM,$beginS,$year,$month,$day,$endH,$endM,$endS);
		$m += $h*60;

		## go to the next appointment if this one has already passed.
		next if (($day == $thisDay) && ($month = $thisMonth) && ($beginH<($thisHour+1)));
		
		
		# strip trailing seconds on the begin ts
		my $begin = substr($begin,0,-3);
		if (substr($begin,0,2) > 12) {
			$begin = (substr($begin,0,2)-12).":".substr($begin,3);
			}

		# prettyify begin time
		if ($beginH >= 12) { $begin .= "pm"; } else { $begin .= "am"; }

		$sth2->execute();
		if ($sth2->rows() > 0) {
			### Somebody else has something going, if it's us then allow us to delete it, otherwise, don't show it.
			my ($id,$customer,$topic) = $sth2->fetchrow();
		
			if ($customer eq $USERNAME) {
				## JT only wants one appt per day per merchant... so if he's got one scheduled, don't show the other ones
				#if ($tech eq 'jt') { $jt_tech++; }

				$c .= "<div class='rs'><strong>Appointment</strong><br>";
				$c .= qq~<span class='hint'>( <a href='javascript:changeDisplay("uniqueDivID")'>details</a> )</span><br>~;
				$c .= "tech: $tech<br>$m min @ $begin PST<br>";
				$c .= "<div id='uniqueDivID' style='display:none;' class='hint'>$topic</div>";
				$c .= "[<a href=\"index.cgi?CLASS=$CLASS&VERB=APPT-CANCEL&ID=$id\">CANCEL</a>]<br></div>";
				}
			}
		else {
			### Okay, so nobody else has grabbed this appointment.
			$c .= "<a href='index.cgi?CLASS=$CLASS&VERB=APPT-CREATE&TECH=$tech&ID=$id&DATE=$year-$month-$day'>$tech</a>";
			#if ($MYTECH ne '') {
			#	if ($MYTECH ne $tech && $XTECHS ne '') { $c .= " <font color='777777'>"; } else { $c .= "<b>"; }
			#	}
			$c .= "<br>$m min @ $begin PST<br>";
			}
		$sth2->finish();
		}

	# finish off the cell
	$c .= "</td>";
	($year,$month,$day) = &Date::Calc::Add_Delta_Days($year,$month,$day,1);	

	# move to the next row if necessary
	if ($dow == 7) { 
		$c .= "</tr>";
		if ($daystoprint>0) { $c .= "<tr>\n"; }
		}

	if ($day == 1) {
		my $moveover = 7 - $dow;
		while ( $moveover-- > 0) { 
			$c .= "<td valign='top' class='r1 border_right border_bottom' width='75' height=100><h3 align='right'>&nbsp;<br>&nbsp;</td>"; 
			}

		# if we didn't just print a </TR> then add one.
		if ($dow != 1) { $c .= "</tr>"; }

		# print out the month header.
		$c .= qq~
<tr>
	<td class='zoovytableheader' colspan='7'>$MONTEXT{$month} $year</td>
</tr>
<tr>
	<td class='zoovysub2header' style='width:100px;'>Mon</td>
	<td class='zoovysub2header' style='width:100px;'>Tue</td>
	<td class='zoovysub2header' style='width:100px;'>Wed</td>
	<td class='zoovysub2header' style='width:100px;'>Thu</td>
	<td class='zoovysub2header' style='width:100px;'>Fri</td>
	<td class='zoovysub2header' style='width:100px;'>Sat</td>
	<td class='zoovysub2header' style='width:100px;'>Sun</td>
</tr>~;
		$c .= "<tr>\n";	
		$moveover = $dow;
		if ($moveover < 6) {	## PATCH BH 2/27
			## we don't need to move over if it's monday
			while ( $moveover-- > 0) { $c .= "<td valign='top' class='r1 border_right border_bottom' width='75' height=100>&nbsp;<br></td>"; }
			}
		} 

	}
$GTOOLS::TAG{'<!-- CALENDAR -->'} = $c;
}
####################### END CALENDAR CODE ####################################





##
##
##
##

if ($VERB =~ /^TICKET-/) {

	$GTOOLS::TAG{'<!-- NOTES -->'} = $ZOOVY::cgiv->{'notes'};
	$GTOOLS::TAG{'<!-- NOTES -->'} = &ZOOVY::incode($GTOOLS::TAG{'<!-- NOTES -->'});
	$GTOOLS::TAG{'<!-- NOTES -->'} =~ s/[\n]/<br>/gs;		# htmlify output

	$GTOOLS::TAG{'<!-- SUBJECT -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'subject'});

	$GTOOLS::TAG{'<!-- PLATFORM -->'} = CGI->escape($ZOOVY::cgiv->{'platform'});
	$GTOOLS::TAG{'<!-- CONNECTION -->'} = $ZOOVY::cgiv->{'connection'};
	$GTOOLS::TAG{'<!-- TOPIC -->'} = $ZOOVY::cgiv->{'topic'};
	$GTOOLS::TAG{'<!-- DISPOSITION -->'} = $ZOOVY::cgiv->{'disposition'};
	}



if (($VERB eq 'TASK-APPROVE') || ($VERB eq 'TASK-FEEDBACK')) {

	my ($TASKID) = int($ZOOVY::cgiv->{'TASK'});
	my $pstmt = "select TT.TECH,TT.JOB_CODE,TJC.PRETTY,TJC.CLASS,TT.STAGE,TT.TICKET from TICKET_TASKS TT, TASK_JOBCODES TJC where TT.MID=$MID /* $USERNAME */ and TT.ID=$TASKID and TJC.CODE=TT.JOB_CODE";
	my $sth = $zdbh->prepare($pstmt);
	$sth->execute();
	my ($tech,$jc,$pretty,$class,$stage,$ticket) = $sth->fetchrow();
	$sth->finish;
	my $stageref = SUPPORT::get_stageref($class,$stage);

	if (substr($tech,0,1) eq '_') {
		## update the PPM if a trainee task is being updated.
		$pstmt = "update TICKET_TASKS set LAST_MODIFIED_GMT=$^T,STAGE='CUPDATE',DUE_GMT=".(time()+(86400*3))." where MID=$MID /* $USERNAME */ and TICKET=$ticket and JOB_CODE='PPM'";
		print STDERR $pstmt."\n";
		$zdbh->do($pstmt);

		if (1) {
			## notify all PPMs
			my $pstmt = "select TECH from TICKET_TASKS where MID=$MID /* $USERNAME */ and TICKET=$ticket and JOB_CODE='PPM'";
			print STDERR $pstmt."\n";
			my $sth = $zdbh->prepare($pstmt);
			$sth->execute();
			while ( my ($PPM) = $sth->fetchrow() ) {
				&notice($USERNAME,$ticket,$PPM,"$USERNAME PPM/CUPDATE: $pretty",$ZOOVY::cgiv->{'notes'});
				}
			$sth->finish();
			}
		}
	else {
		## send an email notice to the TECH that the customer has updated.
		&notice($USERNAME,$ticket,$tech,"CUPDATE: $pretty",$ZOOVY::cgiv->{'notes'});
		}

	$pstmt = "update TICKET_TASKS set LAST_MODIFIED_GMT=$^T,STAGE='CUPDATE',DUE_GMT=".(time()+(86400*3))." where MID=$MID /* $USERNAME */ and ID=$TASKID";
	print STDERR $pstmt."\n";
	$zdbh->do($pstmt);

	if ($VERB eq 'TASK-APPROVE') {
		}
	elsif ($VERB eq 'TASK-FEEDBACK') {
		## this will fall through to save the notes!
		}

	}



##
##
##
if (($VERB eq 'TASK-APPROVE') || ($VERB eq 'TASK-FEEDBACK') || ($VERB eq 'TICKET-ADDINTERACTION')) {	
	# verify that this ticket belows to this user.
	my $pstmt = "select ID,DISPOSITION,ORIGIN from TICKETS where MID=$MID /* $USERNAME */ and ID=".$zdbh->quote($TICKETID);
	my $sth = $zdbh->prepare($pstmt);
	$sth->execute();
	my ($TICKETID,$DISPOSITION,$ORIGIN) = $sth->fetchrow();
	$sth->finish;

	if ($ORIGIN eq 'PROJECT') {
		## we handle project tickets differently!
		if ($VERB eq 'TICKET-ADDINTERACTION') {
			## update all project managers that the client has updated the ticket.

			$pstmt = "select ID,JOB_CODE,TECH,STAGE from TICKET_TASKS where MID=$MID /* $USERNAME */ and TICKET=".int($TICKETID);
			$sth = $zdbh->prepare($pstmt);
			$sth->execute();
			while ( my ($taskid,$jobcode,$tech,$stage) = $sth->fetchrow() ) {		
			
				if (($jobcode eq 'PPM') && ($stage ne 'NEED_REVIEW')) {				
					## if the ticket is updated, then update the PPM -- UNLESS it's already NEED_REVIEW
					$pstmt = "update TICKET_TASKS set LAST_MODIFIED_GMT=$^T,STAGE='CUPDATE',DUE_GMT=".(time()+(86400*3))." where MID=$MID /* $USERNAME */ and ID=$taskid";
					print STDERR $pstmt."\n";
					$zdbh->do($pstmt);		
					}
				if ($jobcode eq 'PPM') {			
					## notify the TECH that there was interaction.
					&notice($USERNAME,$TICKETID,$tech,"ticket update",$ZOOVY::cgiv->{'notes'});
					}
				}
			$sth->finish();
			}
		}


	## added 2007-08-08, patti - keep the HIGH/MED/LOW disposition, 
	## else change to ACTIVE
	if ($DISPOSITION eq 'LOW' || $DISPOSITION eq 'MED' || $DISPOSITION eq 'HIGH') { }
	else { $DISPOSITION = 'ACTIVE'; }

	$pstmt = "update TICKETS set DIRTY=1,DISPOSITION=".$zdbh->quote($DISPOSITION).
				",STRESS_BOUNCES=STRESS_BOUNCES+1,FOLLOWUPS=FOLLOWUPS+1,LAST_FOLLOWUP=now() ".
				"where ID=".$zdbh->quote($TICKETID)." and MID=$MID /* $USERNAME */ limit 1";
	print STDERR $pstmt."\n";
	$zdbh->do($pstmt);


	($pstmt) = &DBINFO::insert($zdbh,'TICKET_FOLLOWUPS',{
		ID=>0, MID=>$MID, PARENT=>$TICKETID,
		CREATED_GMT=>$^T, CREATEDBY=>$USERNAME,
		COMMENT=>$ZOOVY::cgiv->{'notes'},
		PUBLIC=>2
		},debug=>2);
#	$pstmt = "insert into TICKET_FOLLOWUPS (ID,MID,PARENT,CREATED_GMT,CREATEDBY,COMMENT,PUBLIC) values ";
#	$pstmt .= "(0,$MID,$TICKETID,$^T,".$zdbh->quote($USERNAME).",".$zdbh->quote($ZOOVY::cgiv->{'notes'}).",2)";
	print STDERR $pstmt."\n";
	$zdbh->do($pstmt);

	require TODO;
	my ($t) = TODO->new($USERNAME,LUSER=>$LUSERNAME);
	$t->clearTicket($TICKETID);

	$pstmt = "select ID,SEVERITY,TECH_ASSIGN from INCIDENTS where TICKET=".$zdbh->quote($TICKETID)." and MID=$MID /* $USERNAME */";
	$sth = $zdbh->prepare($pstmt);
	$sth->execute();
	while ( my ($id,$severity,$tech) = $sth->fetchrow() ) {
		$pstmt = "update INCIDENTS set DISPOSITION='OPEN' where TICKET=".$zdbh->quote($TICKETID)." and USERNAME=".$zdbh->quote($USERNAME);
		print STDERR $pstmt."\n";
		$zdbh->do($pstmt);

		open MH, "|/usr/sbin/sendmail -t";
		print MH "From: $USERNAME <ticket+$TICKETID\@support.zoovy.com>\n";
		print MH "To: $tech\@zoovy.com\n";
		print MH "Subject: $USERNAME support ticket\n\n";
		print MH $ZOOVY::cgiv->{'notes'}."\n";
		print MH "\n\nCreated by Customer via http://support.zoovy.com\n Peek URL:\n";
		print MH "https://admin.zoovy.com/support/index.cgi?ACTION=VIEWTICKET&USERNAME=$USERNAME&TICKET=$TICKETID\n";
		close MH;

		if ($severity eq 'FEATURE') {
			$pstmt = "update TICKETS set DISPOSITION='INCIDENT' where ID=".$zdbh->quote($TICKETID);
			print STDERR $pstmt."\n";
			$zdbh->do($pstmt);
			}
		}
	$sth->finish();

	if ($VERB =~ /TICKET-/) { $VERB = ''; }
	else { $VERB = 'TICKET-VIEW'; }
	}



if ($VERB eq 'TICKET-VIEW') {
	$TICKETID = int($TICKETID);
	$template_file = 'ticket-view.shtml';
	$GTOOLS::TAG{'<!-- ID -->'} = $TICKETID;
	my $pstmt = "select * from TICKETS where MID=$MID /* $USERNAME */ and ID=".$zdbh->quote($TICKETID);
	print STDERR $pstmt."\n";
	my $sth = $zdbh->prepare($pstmt);
	$sth->execute();
	my $ticketref = $sth->fetchrow_hashref();
	$sth->finish;

	if (length($ticketref->{'NOTES'})<8192) {
		$GTOOLS::TAG{'<!-- SUMMARY -->'} = &ZOOVY::incode(Text::Wrap::wrap("","",$ticketref->{'NOTES'}));
		}
	else {
		## wrapping is slow so we don't do it on lengths over 8192
		$GTOOLS::TAG{'<!-- SUMMARY -->'} = &ZOOVY::incode($ticketref->{'NOTES'});
		}
	$GTOOLS::TAG{'<!-- STATUS -->'} = $ticketref->{'DISPOSITION'};
	
	if ($ticketref->{'DISPOSITION'} eq 'CLOSED') {
		$GTOOLS::TAG{'<!-- INSTRUCTIONS -->'} = '<i>NOTE: This ticket is currently CLOSED - any comments you save will reopen this ticket.</i>';	

		## clear out any pending todo's on this ticket.
		require TODO;
		my ($t) = TODO->new($USERNAME,writeonly=>1);
		$t->clearTicket($TICKETID);
		}
	elsif ($ticketref->{'DISPOSITION'} eq 'INCIDENT') {
		$GTOOLS::TAG{'<!-- INSTRUCTIONS -->'} = '<i>NOTE: This ticket is currently INCIDENT - meaning that it has been assigned to the technicians above and will be followed up with shortly.</i>';	
		}

	if ($ticketref->{'ORIGIN'} eq 'PROJECT') {

		$GTOOLS::TAG{'<!-- INSTRUCTIONS -->'} .= q~
<i>HINT: Information provided in this area is routed to the project manager.</i>
~;

		my $c;
		my $pstmt = "select TT.ID,TT.TECH,TT.JOB_CODE,TT.STAGE,TT.REVISION,TT.DUE_GMT,TT.NOTE,TT.LAST_MODIFIED_GMT from TICKET_TASKS TT where TT.MID=$MID /* $USERNAME */ and TT.TICKET=$TICKETID";
		$sth = $zdbh->prepare($pstmt);
		$sth->execute();
		my $r = '';
		while ( my ($taskid,$tech,$jc,$stage,$rev,$duegmt,$note,$modgmt) = $sth->fetchrow() ) {

			my ($pretty,$class,$classdetail) = &SUPPORT::get_jobcode($zdbh,$jc);

			$r = ($r eq 'r0')?'r1':'r0'; 
			my $stageref = SUPPORT::get_stageref($class,$stage);

			$tech = uc($tech); 
			if (substr($tech,0,1) eq '_') { 
				$tech = substr($tech,1); 
				$tech = 'Project Manager';
				}

			# $c .= "<tr><td colspan=7>".Dumper($stageref)."</td></tr>";

			$c .= "<tr class=\"$r\">";
			$c .= "<td valign=\"top\"><font color=\"black\">$pretty</font>";
			$c .= "<br><font style='font-size: 8pt;'>- assigned: $tech -- task:$class.$jc.$taskid</font>";
			if ($note ne '') {
				$c .= "<br><font style='font-size: 8pt;'>- task note: $note</font>";
				}
			if ($stageref->{'hint'} ne '') {
				$c .= "<br><font style='font-size: 8pt;'>- task hint: $stageref->{'hint'}</font>";
				}
			if ($stageref->{'customer'}>0) {
				$c .= "<br><font style='font-size: 8pt; color: #CC3333'>- REMINDER: this task is waiting on your feedback or approval!</font>";
				}

			$c .= "</td>";
			if ($stageref->{'customer'}==0) {
				$c .= "<td valign=\"top\">$stage</td>";
				}
			else {
				$c .= "<td valign=\"top\"><b><font color='red'>$stage</font></b></td>";
				}

			$c .= "<td align=\"center\" valign=\"top\">$rev</td>";
			if ($duegmt==0) {
				$c .= "<td valign=\"top\">N/A</td>";
				}
			else {
				$c .= "<td valign=\"top\">".&ZTOOLKIT::pretty_date($duegmt,3)."</td>";
				}
#			$c .= "<td valign=\"top\">".&ZTOOLKIT::pretty_date($modgmt,3)."</td>";
			$c .= "</tr>\n";
			
			if ($rev>0) {
				$c .= "<tr class=\"$r\"><td colspan=7><table width=100% cellpadding=0 cellspacing=0><tr><td nowrap>&nbsp;&nbsp;&nbsp;</td><td>";
				$c .= &build_ticket_attachments($USERNAME,$TICKETID,$taskid);
				$c .= "</td></tr></table></td></tr>";
				}
			if ($stageref->{'customer'}>0) {
				$c .= "<tr class=\"$r\"><td colspan=7><table width=100% cellpadding=0 cellspacing=0><tr><td nowrap>&nbsp;&nbsp;&nbsp;</td><td>";
				$c .= qq~
<form name="frm$taskid" action="index.cgi" method="post">
<input type="hidden" name='VERB' value='TASK-UPDATE'>
<input type="hidden" name="TASK" value="$taskid">
<input type='hidden' name='ID' value='$TICKETID'>
Provide Feedback on Task:<br>
<textarea name="notes" rows=5 cols=60></textarea><br>
<input type="button" onClick="document.frm$taskid.VERB.value='TASK-FEEDBACK'; document.frm$taskid.notes.value = 'FEEDBACK FOR $pretty ($class.$jc.$taskid)' + '\\n' + document.frm$taskid.notes.value; document.frm$taskid.submit();" class="savebutton" value=" Add Feedback "> - or -
<input type="button" onClick="document.frm$taskid.VERB.value='TASK-APPROVE'; document.frm$taskid.notes.value = 'CLIENT APPROVED $pretty ($class.$jc.$taskid)' + '\\n' + document.frm$taskid.notes.value; document.frm$taskid.submit();" class="savebutton" value=" Approve "><br>
<div class="hint">
REMINDER: 
No notes will be saved if  "Approve" is selected. 
To ensure no updates are missed please provide feedback only on this specific task.
Please provide all notes for this task only.
Once a task is Approved no further changes will be accepted.
</div>
</form>
~;
				$c .= "</td></tr></table></td></tr>";
				}

			$c .= "<tr class='$r'><td colspan=7>&nbsp;</td></tr>";

			}
		$sth->finish();
		$c = qq~
<tr>
	<td class="zoovysub1header">Task</td>
	<td class="zoovysub1header">Status</td>
	<td class="zoovysub1header">Rev#</td>
	<td class="zoovysub1header">Due</td>
<!--
	<td class="zoovysub1header">Modified</td>
-->
</tr>
$c
~;
		$c = qq~
<tr>
	<td class="zoovytableheader"> &nbsp; Project Tasks</td>
</tr>
<tr>
	<td><table width=100% border=0 cellpadding=1 cellspacing=0>~.$c.qq~</table></td>
</tr>~;
		$GTOOLS::TAG{'<!-- TASKS -->'} = $c;
		}


	if ($ticketref->{'ID'} ne '') {

		my $techs = &SUPPORT::supportusers();

		$pstmt = "select from_unixtime(CREATED_GMT),CREATEDBY,COMMENT from TICKET_FOLLOWUPS where PUBLIC>0 and PARENT=".$zdbh->quote($TICKETID)." order by ID";
		print STDERR $pstmt."\n";
		$sth = $zdbh->prepare($pstmt);
		$sth->execute();
		my $c = '';
		my $titletype = '';
		while ( my ($created,$createdby,$comment) = $sth->fetchrow() ) {
			if (length($comment)<8192) {
				$comment = Text::Wrap::wrap("","",$comment);
				}
			$comment = &ZOOVY::incode($comment);

			my $img = '';
			if ($createdby eq $USERNAME) { 
				$titletype = 'zoovysub1header'; 
				} 
			else { 
				$titletype = 'zoovysub2header'; 
				my $title = $techs->{$createdby}->{'title'};
				if ($title eq '') { $title = "Zoovy Team Member"; }

				my $display = $techs->{$createdby}->{'display'};
				if ($display eq '') { $display = $createdby; }

				if (-f "/httpd/htdocs/biz/support/staff_images/$createdby.jpg") {
					$img = qq~
					<div><img border=0 width=100 height=100 src="/biz/support/staff_images/$createdby.jpg"></div>
					~;
					}
				else {
					$img = qq~
					<div><img border=0 width=100 height=100 src="/biz/support/staff_images/john.doe.jpg"></div>
					~;
					}
				
				$img .= qq~
					<b>~.$display.qq~</b><br>
					<div class="hint">$title</div><br>
					~;
				}



			$c .= qq~
				<tr>
					<td colspan=2 class="$titletype" style="border-top: 2px dotted #777777"><img height="2" src="/images/blank.gif"></td>
				</tr>
				<tr>
					<td valign=top width=100 class='$titletype'>
					<div class="hint">
					<div>$img</div>
					<br>
					$created
					</div>
					</td>
					<td>
					<table width='100%' bgcolor='FFFFFF'><Tr><td>
						<pre>$comment</pre>
					</td></tr></table>
					</td>
				</tr>
				~;		
			} # end of while loop

		$GTOOLS::TAG{'<!-- FOLLOWUPS -->'} = $c;
	
		&build_ticket_attachments($USERNAME,$TICKETID,0);
		
		## incidents
		$pstmt = "select ID,TECH_ASSIGN,SUMMARY,CREATED,DISPOSITION,SEVERITY from INCIDENTS where TICKET=".$zdbh->quote($TICKETID)." and DISPOSITION='OPEN'";
		print STDERR $pstmt."\n";
		$sth = $zdbh->prepare($pstmt);
		$sth->execute();
		$c = '';
		while ( my ($id,$tech,$summary,$created,$disposition,$severity) = $sth->fetchrow() ) {
			if ($severity eq 'LOW') { $severity = 'MED'; }
			$c .= "<tr><td>$id</td><td>$tech</td><td>$summary</td><td>$disposition</td><td>$severity</td></tr>";
			}
		if ($c ne '') {
			$GTOOLS::TAG{'<!-- INCIDENTS -->'} = '<tr><td colspan=2 bgcolor=\'FF7777\'><b>Incidents:</b> (techs assigned to this ticket)<br><table width=\'100%\' cellpadding=\'1\' cellspacing=\'0\' border=\'0\' bgcolor="FFFFFF">'.$c.'</table></td></tr>';
			}
		} # end of if ticket valid
		
	if ( ($ZOOVY::cgiv->{'disposition'} eq 'warn') ) { $VERB = 'TICKET-WARN'; }
	}




if ($VERB eq 'TICKET-REVIEW') {
	$template_file = 'ticket-review.shtml';

	my ($total,$mypos) = &SUPPORT::callback_status($USERNAME);
	if ($mypos >= 0) { $total = $mypos; }		# either show the next available, or simply show the next appointment this person has.
	$GTOOLS::TAG{'<!-- ESTIMATED_TIME -->'} = &SUPPORT::estimate_time_for_callback($total);

	&build_ticket_attachments($USERNAME,0,0);

	if ( ($ZOOVY::cgiv->{'topic'} eq 'zid') || ( $ZOOVY::cgiv->{'topic'} eq 'zid' )) {
		$GTOOLS::TAG{'<!-- PLATFORM -->'} = qq~
		Platform: <select name="platform">
			<option value="_">please select</option>
			<option value="VISTA-ULTIMATE">Windows Vista Ultimate</option>
			<option value="VISTA-BUSINESS">Windows Vista Business</option>
			<option value="VISTA-HOME">Windows Vista Home</option>
			<option value="XP-PRO">Windows XP Professional</option>
			<option value="XP-HOME">Windows XP Home</option>
			<option value="2000">Windows 2000</option>
		</select><Br>
		~;
		$GTOOLS::TAG{'<!-- CONNECTION -->'} = qq~
		Connection Type: <select name="connection">
			<option value="_">please select</option>
			<option value="cable-dsl-other">Cable/DSL</option>
			<option value="aol">AOL Dialup</option>
			<option value="modem">Dialup ISP</option>
		</select><br>
		~;
		}
	else {	
		$GTOOLS::TAG{'<!-- PLATFORM -->'} = '<input type="hidden" name="platform" value="na">';
		$GTOOLS::TAG{'<!-- CONNECTION -->'} = '<input type="hidden" name="platform" value="unknown">';
		}

	my $warn = '';

	if (length($ZOOVY::cgiv->{'subject'}) == 0) {
		$warn .= "* Please fill in a Subject for this ticket.<br>";
		}
	if (length($ZOOVY::cgiv->{'notes'}) == 0) {
		$warn .= "* Please fill in a Description for this ticket.<br>";
      }
	if (uc($ZOOVY::cgiv->{'notes'}) eq $ZOOVY::cgiv->{'notes'}) {
		$warn .= "* TYPING IN ALL CAPS, according to Internet etiquette is considered shouting and may result in the message being incorrectly categorized as hostile/unprofessional and you may incur additional fees.<br>";
		}
	if ($ZOOVY::cgiv->{'notes'} =~ /[\!]{3,50}/) {
		$warn .= "* Multiple exclaimation marks could cause this message to be categorized as hostile or unprofessional and you may incur additional fees.<br>";
		}

	if ($ZOOVY::cgiv->{'notes'} =~ /internal server error/i) {
		$warn .= "* Internal server errors should be categorized as high priority. There is no charge for internal server errors reported as high priority.<br>";
		}

	if ($ZOOVY::cgiv->{'notes'} =~ /ebay/i) {
		if ($ZOOVY::cgiv->{'notes'} =~ /[\d]{5}/) { } else {
			$warn .= "* Found keyword 'EBAY', but could not locate eBay Item Number.<br>";
			}
		}

	if ($ZOOVY::cgiv->{'notes'} =~ /batch/i) {
		if ($ZOOVY::cgiv->{'notes'} =~ /[\d]{3,6}/) { } else {
			$warn .= "* Found keyword 'BATCH', but could not locate a batch job # (please include one if applicable).<br>";
			}
		}


	if ($ZOOVY::cgiv->{'notes'} =~ /channel/i) {
		if ($ZOOVY::cgiv->{'notes'} =~ /[\d]{5}/) { } else {
			$warn .= "* Found keyword 'CHANNEL', but could not locate Channel Number.<br>";
			}
		}
	if ($ZOOVY::cgiv->{'notes'} =~ /order/i) {
		if ($ZOOVY::cgiv->{'notes'} =~ /[\d]{4}\-[\d]{2}\-[\d]+/) { } else {
			$warn .= "* Found keyword 'ORDER', but could not locate Order ID.<br>";
			}
		}

	if (length($ZOOVY::cgiv->{'notes'})<200) {
		$warn .= "* Message is under the 200 character minimum recommended size 
(and probably does not contain enough detail).<br>
REMINDER: Clients are required to provide at least one example or steps to reproduce whenever possible, or your account
will be billed for any research necessary to diagnose the issue.
<br>";
		}

	if (length($ZOOVY::cgiv->{'notes'})>2000) { 
		$warn .= "* Message exceeds 2,000 character recommended limit.<br>";
		}
	if (($ZOOVY::cgiv->{'disposition'} eq 'warn') && ($FLAGS =~ /,TRIAL,/)) {
		$GTOOLS::TAG{'<!-- DISPOSITION -->'} = "low";
		$warn .= q~
<div style='background-color: #FF0000;'>
<b><font color="#FFFF00">
Sorry, but as a TRIAL user you can only put in LOW priority tickets.
</font></b>
</div>
~;
		}
	elsif ($ZOOVY::cgiv->{'disposition'} eq 'warn') {
		$warn .= q~
<div style='background-color: #FF0000;'>
<b><font color="#FFFF00">
* You are about to create a High Priority ticket. By doing so you acknowledge the following:<br>
<ul>
<li> We do monitor our system health using a variety of services, and we routinely have people monitoring the ticket queue for medium/low priority over the weekends.
<li> We do NOT under any circumstances provide weekend, or evening technical support services "How can I?"
A high priority ticket will alert a variety of senior level employees within our organization and we firmly believe this is a priviledge, not a right.
<li> We care a lot about our clients, so issues which cause substantial sales or significantly disrupt operations, as such issues which we believe consitute emergencies are FREE 
More detail on this can be found here: (<a target="_webdoc" href="http://webdoc.zoovy.com/doc/50551">Emergency Guidelines: WebDoc 50551</a>)
<li> For all other issues a fee of $100 for the first issue will be applied to your account, $250 for the second, and $500 for each ticket thereafter in a 1 year period, 
repeated (ab)use regardless of merit will be deemend a "known unreliable configuration" will result in revokation of emergency priviledges.  
<li> Clients processing in excess of $1m monthly sales or $10m annually may be eligible for alternative escalation procedures (direct contacts) within our organization. 
<li> Please check the recent news for announcements of known issues or services offline for maintenance before putting in a high priority ticket.
<li> Unprofessional tickets which use profane language, gratitious use of explanation marks !!!, ALL CAPS, or tell us that they should not under any circustmances 
be billed are *always* billable regardless of circumstance or severity. 
<li> Always include a current phone number, and exactly what steps were needed to reproduce the issue. 
<li> There are no exceptions to this policy. 
</ul> 
<br>
Examples of Free/Billable:
We are disappointed when clients don't submit a high priority ticket because of fear of getting billed, in other case we'd rather not be pulled out of a family dinner for something that isn't what
we'd consider an emergency. Below is a short list of the most *common* reasons we receive high priority tickets, they outline what we consider billable/non-billable to help clients 
understand what is an acceptable use of this service:
<ul>
<li> If you got an Internal Server Error on a critical service - Acceptable Use, Free. Please let us know right now. 
<li> When the home page or category is not loading (or corrupt), or cart is not letting items be added, or all customers in US cannot checkout - Acceptable Use, free (assuming it's not a blatant configuration issue)
<li> An employee ran a batch job which just cratered your store with no backup - Acceptable Use, it will be billable, but getting back online is probably more important. 
<li> You need to get new amazing XYZ service working because it will increase sales by 1000% - Unacceptable. it will be a $500 minimum fee, warning, possible sanctions.
<li> You have a radio/tv/media campaign going live in 1 hour and a coupon isn't working - Acceptable.  Billable, $500 minimum fee, warning, possible future sanctions for repeated abuse. (A lack of planning on your part is NOT an emergency on ours)
<li> You're angry about another (already known) ticket/issue and you want to let us know what a crappy job you think we're doing - Unacceptable. $500 minimum fee, warning or 1 year ban from high priority tickets, or potential account termination.
<li> You believe there may be a problem someplace because you haven't generated enough sales for the day - Absolutely No, not ever.  $500 minimum fee, warning, possible sanctions, repeated abuse will result in revocation of priviledges.
</ul>

</font></b>
</div>
~;
		$GTOOLS::TAG{'<!-- DISPOSITION -->'} = "high";
		}
	if ($warn ne '') {
		$GTOOLS::TAG{'<!-- WARNINGS -->'} = "<font color='red'><b>WARNINGS:</b><br>$warn</font><br>";
		}

	my $c = '';
	require WEBDOC::OZMO;
	my $resultsref = &WEBDOC::OZMO::ask_question($ZOOVY::cgiv->{'subject'}.' '.$ZOOVY::cgiv->{'subject'}.' '.$ZOOVY::cgiv->{'notes'});
	if ((defined $resultsref) && (scalar(@{$resultsref})>0)) { 
		foreach my $faqref (@{$resultsref}) {
			$c .= "<tr><td valign='top'>";
			$c .= $faqref->{'QUESTION'}."<br>";
			if ($faqref->{'DOCID'}>0) {
				$c .= sprintf("<div class=\"hint\"><a href=\"http://webdoc.zoovy.com/doc-%d\">Read WebDoc #%d</a></div>",$faqref->{'DOCID'},$faqref->{'DOCID'});
				}
			$c .= "</td></tr>";	
			}
		}
	
	$GTOOLS::TAG{'<!-- FAQS -->'} = $c;
	}








if ($VERB eq 'TICKET-UPDATE') {
	$TICKETID = $ZOOVY::cgiv->{'ID'};
	my $qtNOTES = $zdbh->quote($ZOOVY::cgiv->{'notes'});
	my $qtDISPOSITION = $zdbh->quote($ZOOVY::cgiv->{'disposition'});
	my $qtID = $zdbh->quote($TICKETID);
	my $qtUSERNAME = $zdbh->quote($USERNAME);

	my $OTHERSQL = '';
	if ($ZOOVY::cgiv->{'disposition'} eq 'closed')
		{
		$OTHERSQL = 'ENDTS=now(),';
		}

	my $pstmt = "update TICKETS set ".$OTHERSQL."DIRTY=1,NOTES=$qtNOTES,DISPOSITION=$qtDISPOSITION where ID=$qtID and MID=$MID";
	print STDERR $pstmt."\n";
	$zdbh->do($pstmt);
	
	print "Location: index.cgi?msg=Updated+Ticket+".$TICKETID."\n\n";
	}

if ($VERB eq 'TICKET-END') {
	$TICKETID = $ZOOVY::cgiv->{'ID'};
	print "Location: http://www.zoovy.com/biz/support\n\n";
	}




if ($VERB eq 'TICKET-WARN') {
	$template_file = 'warn.shtml';
	if ($FLAGS =~ /TRIAL/) {
		$template_file = 'nomore.shtml';
		}
	if ($FLAGS =~ /CRYWOLF/) {
		$template_file = 'nomore.shtml';
		}
	}

if ($VERB eq 'TICKET-CREATE') {
	$GTOOLS::TAG{'<!-- SUBJECT -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'subject'});
	$GTOOLS::TAG{'<!-- NOTES -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'notes'});

	$GTOOLS::TAG{'<!-- TOPIC_WEB_MANAGER -->'} = (($ZOOVY::cgiv->{'topic'} eq 'web_manager')?'checked':'');
	$GTOOLS::TAG{'<!-- TOPIC_DESKTOP -->'} = (($ZOOVY::cgiv->{'topic'} eq 'desktop')?'checked':'');
	$GTOOLS::TAG{'<!-- TOPIC_ORDER_MANAGER -->'} = (($ZOOVY::cgiv->{'topic'} eq 'order_manager')?'checked':'');
	$GTOOLS::TAG{'<!-- TOPIC_USERS_WEBSITE -->'} = (($ZOOVY::cgiv->{'topic'} eq 'users_website')?'checked':'');
	$GTOOLS::TAG{'<!-- TOPIC_BILLING -->'} = (($ZOOVY::cgiv->{'topic'} eq 'billing')?'checked':'');
	$GTOOLS::TAG{'<!-- TOPIC_EMAIL -->'} = (($ZOOVY::cgiv->{'topic'} eq 'email')?'checked':'');
	$GTOOLS::TAG{'<!-- TOPIC_WEB_MANAGER -->'} = (($ZOOVY::cgiv->{'topic'} eq 'web_manager')?'checked':'');
	$GTOOLS::TAG{'<!-- TOPIC_DOMAINNAME -->'} = (($ZOOVY::cgiv->{'topic'} eq 'domainname')?'checked':'');
	$GTOOLS::TAG{'<!-- TOPIC_CALLBACK -->'} = (($ZOOVY::cgiv->{'topic'} eq 'callback')?'checked':'');
	$GTOOLS::TAG{'<!-- TOPIC_ADVICE -->'} = (($ZOOVY::cgiv->{'topic'} eq 'advice')?'checked':'');
	$GTOOLS::TAG{'<!-- TOPIC_OTHER -->'} = (($ZOOVY::cgiv->{'topic'} eq 'other')?'checked':'');

	$GTOOLS::TAG{'<!-- DISPOSITION_LOW -->'} = (($ZOOVY::cgiv->{'disposition'} eq 'low')?'checked':'');
	$GTOOLS::TAG{'<!-- DISPOSITION_MED -->'} = (($ZOOVY::cgiv->{'disposition'} eq 'med')?'checked':'');
	$GTOOLS::TAG{'<!-- DISPOSITION_HIGH -->'} = (($ZOOVY::cgiv->{'disposition'} eq 'high')?'checked':'');
	$template_file = 'ticket-create.shtml';
	}


if ($VERB eq 'TICKET-SAVE') {
	my $notes = $ZOOVY::cgiv->{'notes'};

	if ($ZOOVY::cgiv->{'topic'} ne '') { $notes = "Topic: ".$ZOOVY::cgiv->{'topic'}."\n".$notes; }
	if ($ZOOVY::cgiv->{'connection'} ne '') { $notes = "Connection: ".$ZOOVY::cgiv->{'connection'}."\n".$notes; }
	if ($ZOOVY::cgiv->{'platform'} ne '') { $notes = "Platform: ".$ZOOVY::cgiv->{'platform'}."\n".$notes; }

	my $disp = uc($ZOOVY::cgiv->{'disposition'});
	if ($disp ne 'LOW' && $disp ne 'MED' && $disp ne 'HIGH') { $disp = 'LOW'; }

	my $subject = $ZOOVY::cgiv->{'subject'};
	if (not defined $subject) { $subject = ''; }

	my $callback = $ZOOVY::cgiv->{'callback'}?1:0;
	my $private = $ZOOVY::cgiv->{'private'}?1:0;

	my $is_highpriority = 0;
	if ($ZOOVY::cgiv->{'disposition'} eq 'high') {
		require ZOOVY;
		require ZTOOLKIT;
		my $ph = $LU->get('zoovy:phone');
		my $date = &ZTOOLKIT::pretty_date(time(),1);
		alert('URGENT: '.$USERNAME,'PH: '.$ph."\n".$notes."\n",(keys %lookup));
		$notes = qq~***********************************************
**	HIGH PRIORITY TICKET: $date
***********************************************~.$notes;
		$is_highpriority++;
		}

	$notes =~ s/<br>/\n/ig;	 #this is necessary since we converted [\n]'s to output earlier (around line 966)
	
	my ($TICKET) = &SUPPORT::createticket($USERNAME,
			LUSER=>$LUSERNAME,
			ORIGIN=>'WEB', DISPOSITION=>$disp,
			BODY=>$notes,
			SUBJECT=>$subject,
			CALLBACK=>$callback,
			PUBLIC=>(not $private)?1:0,
			NOTIFY=>1,
			IS_HIGHPRIORITY=>($is_highpriority),
			);

	my $pstmt = '';
	if ($TICKET>0) {
		## associate any attached files
		$pstmt = "update TICKET_ATTACHED_FILES set TICKET=".$TICKET." where TICKET=0 and MID=$MID /* $USERNAME */";
		print STDERR $pstmt."\n";
		$zdbh->do($pstmt);
		}		

	#if (defined $tech && $tech ne '' && $tech) {
	#	open MH, "|/usr/sbin/sendmail -t";
	#	print MH "From: $USERNAME <ticket+$TICKET\@support.zoovy.com>\n";
	#	print MH "To: $tech\@zoovy.com\n";
	#	print MH "Subject: $USERNAME support ticket\n\n";
	#	print MH "\n\nCreated by Customer via http://support.zoovy.com\n Peek URL:\n";
	#	print MH "https://admin.zoovy.com/support/index.cgi?ACTION=PEEK&CUSTOMER=$USERNAME&ID=$TICKET\n";
	#	close MH;
	#	}

#	if ($callback) {
#		require URI::Escape;
#		print "Location: http://www.zoovy.com/biz/support/callback/index.cgi?TICKET=$TICKET&topic=".URI::Escape::uri_escape($subject)."\n\n";
#		exit;
#		}
#	else {
#		print "Location: index.cgi?msg=Created+Ticket+".$TICKET."\n\n";
#		exit;
#		}
	$VERB = '';
	}


sub notice {
	my ($USERNAME,$TICKETID,$TECH,$title,$msg) = @_;

#	print "!! ALERT ======> LEVEL: $level, $msg\n";

	open MH, "|/usr/sbin/sendmail -t -f ticket\@zoovy.com";
	
	print MH "To: $TECH\@zoovy.com\n";
	print MH "From: ticket\@zoovy.com\n";
	print MH "ReplyTo: ticket\@zoovy.com\n";
	print MH "Subject: $USERNAME; $title\n\n";
	print MH "$msg\n\n";
	print MH "https://admin.zoovy.com/support/index.cgi?ACTION=VIEWTICKET&USERNAME=$USERNAME&TICKET=$TICKETID\n";
	print MH "{{user:$USERNAME;ticket:$TICKETID}}\n";
	close MH;
}


sub alert {
	my ($title, $msg, @users) = @_;

#	print "!! ALERT ======> LEVEL: $level, $msg\n";

	foreach my $user (@users)
		{
#		print "!! Contacting: $user ($lookup{$user})\n";
		open MH, "|/usr/sbin/sendmail -t -f err\@zoovy.com";
	
		print MH "To: $lookup{$user}\n";
		print MH "From: err\@zoovy.com\n";
		print MH "Subject: $title\n\n";
		print MH "$msg\n";

#		print "Msg ($msg) sent.\n";		

		close MH;
		}	
}


sub build_ticket_attachments {
	my ($USERNAME,$TICKET,$TASK) = @_;

		my $c = '<table></table>';
		$c = '';
		my $pstmt = "select CREATED,UPLOAD_FILENAME,STORED_NAME from TICKET_ATTACHED_FILES where TICKET=".$zdbh->quote($TICKET)." and MID=$MID /* $USERNAME */ and PUBLIC>0 and TASK=$TASK";

		print STDERR $pstmt."\n";
		my $sth = $zdbh->prepare($pstmt);
		$sth->execute();
		my $counter=0; my $class;
		my $path = &ZOOVY::resolve_userpath($USERNAME);
		while ( my ($created,$uploaded,$local) = $sth->fetchrow()) {
			if ($counter++ % 2==0) { $class='on'; } else { $class = 'off'; }

			my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,$blksize,$blocks) = stat($path."/".$local);
			next if ($size == 0);
			$size = sprintf("%.1f",$size/1024);

			if ($local =~ /^IMAGES\/(.*?)$/) {
				$local = "http://static.zoovy.com/merchant/$USERNAME/$1";
				}

			$c .= qq~
			<tr>
				<td class='$class'> <a target="_blank" href="$local">$uploaded</a></td>
				<td class='$class'>$created</td>
				<td class='$class'>$size</td>
			</tr>
			~;
			}
		$sth->finish();

		if ($c ne '') {
			my $div = "<div style=\"font-size: 8pt;\">";
			$c = qq~
			<table bgcolor='FFFFFF' cellpadding='1' cellspacing='0' border='0' width='100%'>
				<tr>
					<td class='zoovysub2header'>${div}Attached File</div></td>
					<td class='zoovysub2header'>${div}Created</div></td>
					<td class='zoovysub2header'>${div}Size (K)</div></td>
				</tr>
				$c
			</table>
			<br>
			~;
			}
		$GTOOLS::TAG{'<!-- ATTACHMENTS -->'} = $c;
}






##
##
##

if ($VERB eq 'CALLBACK-CANCEL') {
	my $pstmt = "delete from CALLBACKS where MID=$MID /* MERCHANT=$USERNAME */ and ACTIVE=1";
	$zdbh->do($pstmt);

	$pstmt = "update TICKETS set DISPOSITION='CLOSED',CLOSED_COUNT=CLOSED_COUNT+1 where DISPOSITION='CALLBACK'";
	$zdbh->do($pstmt);
	$VERB = '';
	}

if ($VERB eq 'CALLBACK-SAVE') {
	my ($totalcount) = &SUPPORT::callback_status($USERNAME);
	$GTOOLS::TAG{'<!-- CURRENT -->'} = $totalcount;
	$GTOOLS::TAG{'<!-- ESTIMATED -->'} = &SUPPORT::estimate_time_for_callback($totalcount);
	$GTOOLS::TAG{'<!-- TICKET -->'} = $ZOOVY::cgiv->{'TICKET'};

	my $contact = $ZOOVY::cgiv->{'askfor'};
	if (not defined $contact) {
		$contact = $LU->get('zoovy:contact');
		}

	my $phone1 = $ZOOVY::cgiv->{'phone1'};
	if (not defined $phone1) { $phone1 = $LU->get('zoovy:support_phone'); }

	my $phone2 = $ZOOVY::cgiv->{'phone2'};
	if (not defined $phone2) { $phone2 = $LU->get('zoovy:phone'); }

	my $errors = 0;
	if (length($phone1)<10) {
		$GTOOLS::TAG{'<!-- PHONE1_ERROR -->'} = '<font color="red"><br>Phone number is required</font>';
		$errors++;
		}
	if (length($contact)<5) {
		$GTOOLS::TAG{'<!-- CONTACT_ERROR -->'} = '<font color="red"><br>Contact name is required</font>';
		$errors++;
		}

	if (not $errors) {
 		my $qtTOPIC = $ZOOVY::cgiv->{'topic'};
		my $qtTICKET = int($ZOOVY::cgiv->{'TICKET'});
		if ($qtTICKET eq '0' || $qtTICKET eq '') {
			($qtTICKET) = &SUPPORT::createticket($USERNAME,
				ORIGIN=>'CALLBACK',
				DISPOSITION=>'CALLBACK',
				SUBJECT=>'Ticket created for callback',
				LUSER=>$LUSERNAME,
				NOTIFY=>0,
				MESSAGE=>"Callback Ticket: $qtTOPIC\nCONTACT: $contact\nPHONE: $phone1\nPHONE: $phone2\nNOTES: ".$ZOOVY::cgiv->{'notes'}
				);
			}

		if (not defined $qtTOPIC) { $qtTOPIC = "'Unknown'"; } else { $qtTOPIC = $zdbh->quote($qtTOPIC); }
		if (not defined $qtTICKET) { 
			$qtTICKET = 0; 
			} 
		else { 
			$qtTICKET = int($qtTICKET);
			}
		my $pstmt = "delete from CALLBACKS where MID=$MID /* MERCHANT=$USERNAME */ and ACTIVE=1";
		$zdbh->do($pstmt);
	
		require ZTOOLKIT;
		require ZWEBSITE;
		my %params = ();
		$params{'START_HOUR'} = $ZOOVY::cgiv->{'START_HOUR'};
		$params{'END_HOUR'} = $ZOOVY::cgiv->{'END_HOUR'};
		$params{'WEEKENDS'} = $ZOOVY::cgiv->{'WEEKENDS'};
		$params{'PHONE2'} = $ZOOVY::cgiv->{'phone2'};
		$params{'PHONE1'} = $ZOOVY::cgiv->{'phone1'};
		$params{'ASKFOR'} = $ZOOVY::cgiv->{'askfor'};
		&ZWEBSITE::save_website_attrib($USERNAME,'callback',&ZTOOLKIT::buildparams(\%params));


		$pstmt = &DBINFO::insert($zdbh,'CALLBACKS',{
			USERNAME=>$USERNAME,
			MID=>$MID,
			ACTIVE=>1,
			TICKET=>$qtTICKET,
			TOPIC=>$qtTOPIC,
			ASKFOR=>$contact,
			PHONE1=>$phone1,
			PHONE2=>$phone2,
			CALLNOTE=>$ZOOVY::cgiv->{'notes'},
			'*CREATED'=>'now()',
			BILLTIME=>15,
			START_HOUR=>int($params{'START_HOUR'}),
			END_HOUR=>int($params{'END_HOUR'}),
			WEEKENDS=>int($params{'WEEKENDS'}),
			},debug=>2);
		print STDERR $pstmt."\n";
		$zdbh->do($pstmt);
		$VERB = '';
		}
	else {	
		$GTOOLS::TAG{'<!-- ERRORS -->'} = "Something bad happened";
		$VERB = 'CALLBACK';
		}
	}



if ($VERB eq 'CALLBACK') {
	my ($totalcount,$myposition) = &SUPPORT::callback_status($USERNAME);
	$GTOOLS::TAG{'<!-- WAITING -->'} = $totalcount;

	$template_file = 'callback.shtml';

	if ($myposition>=0) {
		$GTOOLS::TAG{'<!-- POSITION -->'} = $myposition;
		$GTOOLS::TAG{'<!-- ESTIMATED_TIME -->'} = &SUPPORT::estimate_time_for_callback($myposition);
		$template_file = 'callback.shtml';
		}
	else {
		my $pstmt = "select ID,date_format(from_unixtime(CREATED_GMT),'%a %b %d'),SUBJECT from TICKETS where MID=$MID /* $USERNAME */ order by ID desc limit 0,50";
		print STDERR $pstmt."\n";
		my $sth = $zdbh->prepare($pstmt);
		$sth->execute();
		my $c = '';
		while ( my ($id,$created,$subject) = $sth->fetchrow() ) {
			if ($subject eq '') { $subject = 'No subject provided'; }
			$c .= "<option ";
			if ($id eq $ZOOVY::cgiv->{'TICKET'}) { $c .= 'selected'; }
			$c .= " value=\"$id\">#$id - $subject [$created]</option>\n";
			}
		$GTOOLS::TAG{'<!-- TICKETS -->'} = $c; 
		$sth->finish();
		}

	my $phone1 = $ZOOVY::cgiv->{'phone1'};
	if (not defined $phone1) { $phone1 = $LU->get('zoovy:support_phone'); }

	my $phone2 = $ZOOVY::cgiv->{'phone2'};
	if (not defined $phone2) { $phone2 = $LU->get('zoovy:phone'); }

	my $contact = $ZOOVY::cgiv->{'askfor'};
	if (not defined $contact) {
		$contact = $LU->get('zoovy:contact');
		}

	$GTOOLS::TAG{'<!-- TOPIC -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'topic'});
	$GTOOLS::TAG{'<!-- PHONE2 -->'} = &ZOOVY::incode($phone2);
	$GTOOLS::TAG{'<!-- PHONE1 -->'} = &ZOOVY::incode($phone1);
	$GTOOLS::TAG{'<!-- CONTACT -->'} = &ZOOVY::incode($contact);
	$GTOOLS::TAG{'<!-- NOTES -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'notes'});
	$GTOOLS::TAG{'<!-- SUPPORT_TAB -->'} = &SUPPORT::do_header();
	}




##
##
##

print STDERR "VERB: $VERB\n";
if (($VERB eq '') || ($VERB eq 'REPORT-ACTIVE') || ($VERB eq 'REPORT-HISTORY') || ($VERB =~ /REPORT-/)) {
	my $pstmt = "select count(*) from TICKETS where DISPOSITION in ('LOW','MED','HIGH','ACTIVE')";
	my $sth = $zdbh->prepare($pstmt);
	$sth->execute();
	($GTOOLS::TAG{'<!-- TOTAL_TICKET_COUNT -->'}) = $sth->fetchrow();
	$sth->finish();
	my ($total,$mypos) = &SUPPORT::callback_status($USERNAME);
	if ($mypos >= 0) {
		## has a callback	
		$GTOOLS::TAG{'<!-- CALLBACK_STATUS -->'} = "<font color='red'>&nbsp;&nbsp;&nbsp; Callback Scheduled: There are currently $mypos pending calls ahead of you.<br>";
		}
	else {
		## no callback scheduled
		$GTOOLS::TAG{'<!-- CALLBACK_STATUS -->'} = "&nbsp;&nbsp;&nbsp; Next Available Call: ".&SUPPORT::estimate_time_for_callback($total);
		}

	$GTOOLS::TAG{'<!-- REPORT_TITLE -->'} = "Open/Recent Tickets";
	$pstmt = "select * from TICKETS where (MID=$MID and DISPOSITION in ('LOW','MED','HIGH','ACTIVE','OTHER','WAITING','INCIDENT')) or (MID=$MID and CLOSED_GMT>unix_timestamp(date_sub(now(),interval 15 day))) order by ID desc";

	if ($VERB eq 'REPORT-HISTORY') {
		$GTOOLS::TAG{'<!-- REPORT_TITLE -->'} = "Full Ticket History";
		$pstmt = "select * from TICKETS where MID=$MID order by ID desc";
		$template_file = 'report-history.shtml';
		}

	if ($VERB eq 'REPORT-WAITING') {
		$GTOOLS::TAG{'<!-- REPORT_TITLE -->'} = "Waiting on Response from Customer Tickets ";
		$pstmt = "select * from TICKETS where MID=$MID and DISPOSITION in ('WAITING') order by ID desc";
		}

	print STDERR $pstmt."\n";
	$sth = $zdbh->prepare($pstmt);
	$sth->execute();
	my $c = '';
	my $counter++;
	my $r = "r0";
	while (my $hashref = $sth->fetchrow_hashref()) {	
		next if ($hashref->{'TECH'} eq '@CARP');
		$r = ($r eq 'r0')?'r1':'r0';
		if ($VERB eq 'REPORT-WAITING') {
			## don't flag waiting tickets as red on the waiting report
			}
		elsif ($hashref->{'DISPOSITION'} eq 'WAITING') { 
			$r = 'rs'; 
			}


		$c .= "<tr class=\"$r\">";
		$c .= "<td>";
		$c .= qq~
		<table border='0' cellpadding='0' cellspacing='0' width='100%'>
		<tr>
			<td class="zoovysub1header"><input type='button' class='button' value='Edit' onClick="document.location='index.cgi?VERB=TICKET-VIEW&ID=$hashref->{'ID'}';"> #$hashref->{'ID'}: $hashref->{'SUBJECT'}</a></td>
			<td valign=top align=right class="zoovysub1header"></td>
		</tr>
		<tr>
			<td valign=top>
		~;
	
		my $length = 640;
		if ($hashref->{'DISPOSITION'} ne 'WAITING') { $length=200; }
		my $NOTES = $hashref->{'NOTES'};
		$NOTES =~ s/\</&lt;/g;
		$NOTES =~ s/\>/&gt;/g;
	
		$c .= "<pre>".Text::Wrap::wrap("","",substr($NOTES,0,$length))."</pre>\n<br>";
		if (length($hashref->{'NOTES'})>640) {
			$c .= "<i>... continued ...</i><br>";
			}

		if ($hashref->{'DISPOSITION'} eq 'INCIDENT') {
			$c .= "<font color='blue'>This matter has been referred to a technician. Review the incident list to see who is working on this issue.</font>";
			}
		elsif ($hashref->{'DISPOSITION'} eq 'WAITING') {
			$c .= "<font color='red'><b>NOTICE: This ticket is WAITING, which means a technician has requested additional information from you - please click the 'Edit' button above.</b></font>";
			}

		$c .= qq~
			</td>
			<td valign=top nowrap align='right'>
				<font size='1'> Created: ~.&ZTOOLKIT::pretty_date($hashref->{'CREATED_GMT'},3);
		if ($hashref->{'LUSER'} ne '') {
			$c .= "<br>Created by: ".$hashref->{'LUSER'};
			}

		if ($hashref->{'DISPOSITION'} eq 'LOW' || $hashref->{'DISPOSITION'} eq 'MED') { $hashref->{'DISPOSITION'} = 'ACTIVE'; }
		$c .= "<br>Disposition: ".$hashref->{'DISPOSITION'};
		if ($hashref->{'DISPOSITION'} eq 'LOW' || $hashref->{'DISPOSITION'} eq 'MED') { $hashref->{'DISPOSITION'} = 'ACTIVE'; }
		$c .= "<br>Public: ".($hashref->{'PUBLIC'}?'Yes':'No');
		if ($hashref->{'TECH'} ne '' && $hashref->{'TECH'} ne 'nobody') {
			$c .= "<br>Tech: $hashref->{'TECH'}<br>";
			}
		$c .= "</td></tr></table>";

	#	$c .= "<a href=\"javascript:openWindow('followup.cgi?TICKET=$hashref->{'ID'}');\">Append Followup</a><br>\n";
	#	$c .= "<a href=\"javascript:openWindow('attach.cgi?TICKET=$hashref->{'ID'}');\">Attach File</a><br>\n";
		$c .= "</td>";
		$c .= "</tr>";
		}
	if ($c eq '') {
		$c .= '<tr><td bgcolor="white"><i>No Open Tickets Exist</i></td></tr>';
		}
	$sth->finish();
	$GTOOLS::TAG{'<!-- TICKETS -->'} = $c;


	###############

	}





##
##
##

my $PROJECTS = '';
my $APPOINTMENTS = '';

if (1) {
	my %TICKETS = ();

	my $pstmt = "select ID,SUBJECT from TICKETS where ORIGIN='PROJECT' and MID=$MID /* $USERNAME */ and DISPOSITION in ('ACTIVE','LOW','MED','OTHER','WAITING','INCIDENT','CALLBACK','NEEDINFO');";
	print STDERR $pstmt."\n";
	my $sth = $zdbh->prepare($pstmt);
	$sth->execute();
	while ( my ($TICKET,$SUBJECT) = $sth->fetchrow() ) {
		next if (defined $TICKETS{$TICKET}); $TICKETS{$TICKET}++;
		$SUBJECT =~ s/^PROJECT:[\s]+//gs;
		$PROJECTS .= qq~<tr><td class="small" valign='top'><a href="index.cgi?VERB=TICKET-VIEW&ID=$TICKET">#$TICKET</a></td><td class="small" valign='top'>$SUBJECT</td></tr>~;
		}
	$sth->finish();

	$pstmt = "select TICKET,SUMMARY from INCIDENTS where MID=$MID /* $USERNAME */ and DISPOSITION='OPEN' order by ID desc";
	print STDERR $pstmt."\n";
	$sth = $zdbh->prepare($pstmt);
	$sth->execute();
	while (my ($TICKET,$SUBJECT) = $sth->fetchrow()) {
		next if (defined $TICKETS{$TICKET}); $TICKETS{$TICKET}++;
		$SUBJECT =~ s/^PROJECT:[\s]+//gs;
		$PROJECTS .= qq~<tr><td class="small" valign='top'><a href="index.cgi?VERB=TICKET-VIEW&ID=$TICKET">#$TICKET</a></td><td class="small" valign='top'>$SUBJECT</td></tr>~;
		}
	$sth->finish();

	if ($PROJECTS ne '') {
		$PROJECTS = "<table>$PROJECTS</table>";
		}
	else {
		$PROJECTS = "<i class='small'>No open projects</i>";
		}

	$APPOINTMENTS = '';
	#$pstmt = "select * from SCHEDULE_RESERVATIONS where MID=1";
	#$pstmt = "select SR.TECH,SR.BEGINS,SR.DURATION,SR.SCHEDULEID,SA.CLASS from SCHEDULE_RESERVATIONS SR,SCHEDULE_APPOINTMENTS SA where SA.ID=SR.SCHEDULEID and SR.MID=1 and BEGINS>date_sub(now(),interval 30 minute);";
	$pstmt = "select SR.ID,SR.TECH,unix_timestamp(SR.BEGINS),SR.DURATION,SR.SCHEDULEID,SR.TOPIC from SCHEDULE_RESERVATIONS SR where SR.MID=$MID /* $USERNAME */ and BEGINS>date_sub(now(),interval 30 minute);";
	$sth = $zdbh->prepare($pstmt);
	$sth->execute();
	while ( my ($id,$tech,$begin_gmt,$duration,$scheduleid,$topic) = $sth->fetchrow() ) {
		$APPOINTMENTS .= "<tr><td><div class=\"box_body small\">($duration min) ".&ZTOOLKIT::pretty_date($begin_gmt,1)."<br> w/$tech <a href=\"index.cgi?VERB=APPT-CANCEL&ID=$id\">[CANCEL]</a></div></td></tr>";
		}
	$sth->finish();
	if ($APPOINTMENTS ne '') { $APPOINTMENTS = "<table width=100%><tr><td class='zoovysub2header'>Upcoming Appointments</td></tr>$APPOINTMENTS</table>"; }

	}


require URI::Escape;
my $params = URI::Escape::uri_escape("user=brian");

my $CHAT_CODE = q~
<!-- BEGIN ProvideSupport.com Graphics Chat Button Code -->
<div id="ciB4MQ" style="z-index:100;position:absolute"></div><div id="scB4MQ" style="display:inline"></div><div id="sdB4MQ" style="display:none"></div><script type="text/javascript">var seB4MQ=document.createElement("script");seB4MQ.type="text/javascript";var seB4MQs=(location.protocol.indexOf("https")==0?"https":"http")+"://image.providesupport.com/js/zoovy/safe-standard.js?ps_h=B4MQ\u0026ps_t="+new Date().getTime()+"\u0026username=~.$USERNAME.'*'.$LUSERNAME.q~";setTimeout("seB4MQ.src=seB4MQs;document.getElementById('sdB4MQ').appendChild(seB4MQ)",1)</script><noscript><div style="display:inline"><a href="http://www.providesupport.com?messenger=zoovy">Live Customer Support</a></div></noscript>
<!-- END ProvideSupport.com Graphics Chat Button Code -->
~;

#$CHAT_CODE = q~
#<!-- BEGIN ProvideSupport.com Pass Information Chat Button Code -->
#<div id="cirG1G" style="z-index:100;position:absolute"></div><div id="scrG1G" style="display:inline"></div><div id="sdrG1G" style="display:none"></div><script type="text/javascript">var serG1G=document.createElement("script");serG1G.type="text/javascript";var serG1Gs=(location.protocol.indexOf("https")==0?"https":"http")+"://image.providesupport.com/js/zoovy/safe-standard.js?ps_h=rG1G\u0026ps_t="+new Date().getTime()+"\u0026username=USERNAME";setTimeout("serG1G.src=serG1Gs;document.getElementById('sdrG1G').appendChild(serG1G)",1)</script><noscript><div style="display:inline"><a href="http://www.providesupport.com?messenger=zoovy">Live Customer Support</a></div></noscript>
#<!-- END ProvideSupport.com Pass Information Chat Button Code -->
#~;

$GTOOLS::TAG{'<!-- SUPPORT_SIDEBAR_BEGIN -->'} = qq~
<center>
<table width=100% cellspacing=0 cellpadding=0>
<tr><td width="5"><img src="/images/blank.gif" width="5"></td><td valign="top" width="200">
<!-- BEGIN_SIDEBAR -->
<br>

<div class="box">
<div class="box_header"> Online Documentation</div>
<div class="box_body small">
		<form action="http://www.zoovy.com/webdoc/index.cgi">
		<input type="hidden" name="VERB" value="SEARCH">
		Question or Keywords: <input type="textbox" size="30" name="keywords" value=""> <input type="submit" value=" Search " class="button">
		</form>
</div></div>

<div class="box">
<div class="box_header"> Electronic Tickets</div>
<div class="box_body small">
<a title="request assistance from Zoovy Technical support." href="/biz/support/index.cgi?VERB=TICKET-CREATE">Create New Ticket</a><br>
<a title="recently updated issues." href="/biz/support/index.cgi?VERB=REPORT-ACTIVE">Recent Tickets</a><br>
<a title="display all tickets you have created." href="/biz/support/index.cgi?VERB=REPORT-HISTORY">Ticket History</a><br>
<a title="display all tickets you have created." href="/biz/support/index.cgi?VERB=REPORT-WAITING">Need Action</a><br>
</div></div>

<div class="box">
<div class="box_header"> Phone Support</div>
<div class="box_body small">
Toll Free: 866-899-6689 x 3<br>
<hr>
Tech Hours: 6am till 6pm PST M-F<br>
Operator will answer 24 x 7 x 365<br>
<a href="/biz/support/index.cgi?VERB=CALLBACK">Request Tech Callback</a> | <a href="http://webdoc.zoovy.com/doc/50736">Policies</a>
</div></div>


<div class="box">
<div class="box_header"> Projects &amp; Incidents</div>
<div class="box_body small">
$PROJECTS
</div></div>


<div class="box">
<div class="box_header"> Schedule Appointment</div>
<div class="box_body small">
$APPOINTMENTS
	<a href="/biz/support/index.cgi?VERB=CALENDAR&CLASS=IMP">Implementation Assist.</a><br>
	<a href="/biz/support/index.cgi?VERB=CALENDAR&CLASS=DESIGN">Graphic Design Meet.</a><br>
	<a href="/biz/support/index.cgi?VERB=CALENDAR&CLASS=GEEK">Geek Services</a><br>
	<a href="/biz/support/index.cgi?VERB=CALENDAR&CLASS=MKT">Marketing Assistance</a><br>
<!--
	<a href="/biz/support/index.cgi?VERB=CALENDAR&CLASS=BPP">BPP Review</a><br>
-->
<br>	
<a href="/biz/support/index.cgi?VERB=BILLING">Support Credits &amp; Balances</a>
</div></div>

<div class="box">
<div class="box_header"> Live Assistance</div>
<div class="box_body small">

$CHAT_CODE
<br>
Chat sessions are treated as an implementation session with a 10 minute minimum.  If no technicians are available (no live chat button appears), please submit a support ticket.
</div>
</div>
</div>

<!-- END_SIDEBAR -->
</td><td>&nbsp;</td><td valign="top" width=*>
<!-- BEGIN_BODY -->
~;

$GTOOLS::TAG{'<!-- SUPPORT_SIDEBAR_END -->'} = qq~
<!-- END_BODY -->
</td></tr>
</table>
~;




if ($VERB eq '') { $VERB = 'MAIN'; }
if ($TICKETID eq '') { $TICKETID = 0; }

&GTOOLS::output(header=>1,title=>"Support Area: $USERNAME($LUSERNAME) .. $VERB/$TICKETID",file=>$template_file,bc=>\@BC,tabs=>\@TABS,msgs=>\@MSGS);
&DBINFO::db_zoovy_close();

