#!/usr/bin/perl

use strict;

use Time::Local;
use Time::Zone;
use CGI;
use Date::Calc;
use Date::Parse;
use POSIX;

use lib "/httpd/modules";
use ZOOVY;
use Data::Dumper;
use GTOOLS;
use BATCHJOB;

#my ($USERNAME,$FLAGS) = &ZOOVY::authenticate('/biz/reports',1);
#if (index($FLAGS,'BASIC')==-1) { print "Location: /biz\n\n"; exit; }

my @MSGS = ();

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_M&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $GUID = $ZOOVY::cgiv->{'GUID'};
if ((not defined $GUID) || ($GUID eq '')) {
	$GUID = BATCHJOB::make_guid();
	}
$GTOOLS::TAG{'<!-- GUID -->'} = $GUID;

my %hours = ( 0=>'Midnight', 1=>'1 am', 2=>'2 am', 3=>'3 am', 4=>'4 am', 5=>'5 am', 6=>'6 am', 7=>'7 am', 8=>'8 am', 9=>'9 am', 10=>'10 am', 11=>'11 am',
					12=>'Noon',13=>'1 pm',14=>'2 pm',15=>'3 pm',15=>'3 pm',16=>'4 pm',18=>'6 pm',19=>'7 pm',20=>'8 pm',21=>'9 pm',22=>'10 pm',23=>'11 pm');
my %dom = ( 1=>'1st',15=>'15th' );
my %dows = ( '0'=>'Sunday',1=>'Monday',2=>'Tuesday',3=>'Wednesday',4=>'Thursday',5=>'Friday',6=>'Saturday' );
my $template_file = 'index.shtml';

my @BC = ();
push @BC, { name=>'Reports', link=>'/biz/reports', target=>'_top', };

my $VERB = $ZOOVY::cgiv->{'VERB'};



##
##
##
##
##
if ($VERB =~ /SALES-/) {
	my $begints = 0;
	my $endts = 0;
	my $error = '';

	my $REPORT = $ZOOVY::cgiv->{'REPORT'};
	my $title = 'Unnamed Report';

	# REPORT:SALE_SUMMARY VERB:SALES-BYMONTH
	# print STDERR "REPORT:$REPORT VERB:$VERB\n";

	if ($VERB eq 'SALES-BYMONTH') {
		my $month = $ZOOVY::cgiv->{'month'};
		my $year = $ZOOVY::cgiv->{'year'};
      $begints = &ZTOOLKIT::mysql_to_unixtime(sprintf("%d-%d-01 00:00:00",$year,$month));
      $endts = &ZTOOLKIT::mysql_to_unixtime(sprintf("%d-%d-%d 23:59:59",$year,$month,Date::Calc::Days_in_Month($year,$month)));
 		}
	elsif ($VERB eq 'SALES-BYPERIOD') {
		my $begins = $ZOOVY::cgiv->{'begins'};
		my $ends = $ZOOVY::cgiv->{'ends'};

		print STDERR "begins $begins ends $ends\n";
		if ($begins ne '' && $begins !~ /\d\d\/\d\d\/\d\d/) {
			$begints = 0;
			}
		elsif ($ends ne '' && $ends !~ /\d\d\/\d\d\/\d\d/) {
			$endts = 0;
			}
		else {
			$begints = str2time($begins);
			$endts = str2time($ends);
			}
		}
	elsif ($VERB eq 'SALES-QUICK') {
		if ($ZOOVY::cgiv->{'PERIOD'} eq 'today') {
			$begints = str2time(Date::Calc::Date_to_Text(Date::Calc::Today));
			$endts = $begints + 86400;
			}
		elsif ($ZOOVY::cgiv->{'PERIOD'} eq 'yesterday') {
			$endts = str2time(Date::Calc::Date_to_Text(Date::Calc::Today));
			$begints = $endts - 86400;
			}
		elsif ($ZOOVY::cgiv->{'PERIOD'} eq 'thismonth') {
			$begints = &ZTOOLKIT::mysql_to_unixtime(strftime("%Y-%m-01 00:00:00",localtime()));
			$endts = time();
			}
		elsif ($ZOOVY::cgiv->{'PERIOD'} eq '4week') {
			$begints = time()-(86400*28);
			$endts = time();
			}
		elsif ($ZOOVY::cgiv->{'PERIOD'} eq 'all') {
			$begints = 1;		# make sure there's nothing nasty here!
			$endts = time();
			}
		else {
			$error = "Unknown sales-quick report PERIOD=$ZOOVY::cgiv->{'PERIOD'}";
			}
		}
	elsif ($VERB eq 'SALES-BYINVOICE') {
		require CART2;
		if ($ZOOVY::cgiv->{'startinv'} ne '') {
			my ($O2) = CART2->new_from_oid($USERNAME,$ZOOVY::cgiv->{'startinv'});
			if (defined $O2) { $begints = $O2->in_get('our/order_ts'); } else { $error = "beginnging order not valid"; }
			}
		if ($ZOOVY::cgiv->{'endinv'} ne '') {
			my ($O2) = CART2->new_from_oid($USERNAME,$ZOOVY::cgiv->{'endinv'});
			if (defined $O2) { $endts = $O2->in_get('our/order_ts'); } else { $error = "ending order not valid"; }
			}
		else {
			$endts = time();
			}
		}
	else {
		$error = "Unknown report request: $REPORT";
		}


	if ($begints > $endts) { my $tmp = $begints; $begints = $endts; $endts = $begints; }	# swap backwards values!

	if (($endts == 0) || ($begints ==0) || ($error ne '')) {
		if ($error eq '') { $error = 'Error in date range, please try again!'; }
		push @MSGS, "ERROR|+$error";
		$REPORT = "";
		$VERB = 'INDEX-SALES';
		}
	else {
		my $include_deleted = (defined $ZOOVY::cgiv->{'include_deleted'})?1:0;
		# my $URL = "/biz/reports/output.cgi?ACTION=NEW&REPORT=SALES&verb=period&start_gmt=$begints&end_gmt=$endts&include_deleted=$include_deleted\n\n";
		my %vars = ();
		$vars{'.start_gmt'} = $begints;
		$vars{'.end_gmt'} = $endts;
		$vars{'.include_deleted'} = $include_deleted;
		$vars{'.key'} = $ZOOVY::cgiv->{'key'};

		$vars{'REPORT'} = $ZOOVY::cgiv->{'REPORT'},

		my ($bj) = BATCHJOB->new($USERNAME,0,
			PRT=>$PRT,
			EXEC=>'REPORT',
			'REPORT'=>$ZOOVY::cgiv->{'REPORT'},
			'%VARS'=>\%vars,
			'*LU'=>$LU,
			);
		my $JOBID = $bj->id();
		push @MSGS, "SUCCESS|+Create Job: $JOBID\n";
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = qq~<button class="button" type="button" onClick="
			app.ext.admin_batchJob.a.showBatchJobStatus('$JOBID'); return false;">View Report</button>~;
		$VERB = 'INDEX-SALES';
		}
	}



##
##
##
if ($VERB eq 'INDEX-SALES') {
	my @months = ('January','February','March','April','May','June','July','August','September','October','November','December');
	my $ts = &ZTOOLKIT::timetohash(time());
	my $now_month = $ts->{'mon'};
	my $now_year = $ts->{'year'} + 1900;
	my $year = 2000;
	my $month = $now_month -1;
	if ($month == -1) {
		$month = 11;
		$year = $now_year - 2;
		}
	
	my $count = 1;
	my $c = '';
	for (@months) {
		if ($count == ($now_month + 1)) {
			$c .= "<option value=\"$count\" selected>$_\n";
			}
		else {
			$c .= "<option value=\"$count\">$_\n";
			}
		$count++;
		}
	$GTOOLS::TAG{'<!-- MONTHS -->'} = $c;

	$c = '';
	while ($year <= $now_year) {
		if ($year == $now_year) {
			$c .= "<option value=\"$year\" selected>$year\n";
			}
		else {
			$c .= "<option value=\"$year\">$year\n";
			}
		$year++;
		}
	$GTOOLS::TAG{'<!-- YEARS -->'} = $c;

	$template_file = 'index-sales.shtml';
	push @BC, { name=>'Sales', link=>'/biz/reports/index.cgi?VERB=INDEX-SALES', target=>'_top', };
	}



if ($VERB eq 'INDEX-INVENTORY') {
	$template_file = 'index-inventory.shtml';
	push @BC, { name=>'Inventory', link=>'/biz/reports/index.cgi?VERB=INDEX-INVENTORY', target=>'_top', };
	}



if ($VERB eq 'BATCH-CLEANUP') {
	my $JOBID = $ZOOVY::cgiv->{'JOBID'};
	my ($bj) = BATCHJOB->new($USERNAME,$JOBID);
	if ((not defined $bj) || (ref($bj) ne 'BATCHJOB') || ($bj->id()==0)) {
		push @MSGS, "ERROR|JOB: $JOBID not found or could not be loaded.";
		$VERB = 'BATCH-SEARCH';
		}
	else {
		$bj->cleanup();
		push @MSGS, "SUCCESS|Cleaned up job #$JOBID";	
		$VERB = 'INDEX-BATCH';
		}
	}

##
##
##
if ($VERB eq 'INDEX-BATCH') {
	my $dbh = &DBINFO::db_zoovy_connect();

	my $pstmt = "select ID,TITLE,LUSERNAME,STATUS,BATCH_EXEC,CREATED_GMT,FINISHED_GMT from BATCH_JOBS where MID=$MID /* $USERNAME */ and CLEANUP_GMT=0 order by ID desc";
	# print STDERR $pstmt."\n";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	my $class = '';
	my $c = '';
	while ( my ($ID,$TITLE,$LUSER,$STATUS,$JOBTYPE,$CREATEDTS,$FINISHEDTS) = $sth->fetchrow() ) {
		($class) = ($class eq 'r0')?'r1':'r0';
		$c .= "<tr class=$class>";
		if (($STATUS eq 'NEW') || ($STATUS eq 'RUNNING')) {
			# $c .= "<td valign=top><a href=\"/biz/batch/index.cgi?VERB=LOAD&JOB=$ID\">$ID</a></td>";
			$c .= qq~<td valign=top><button class=\"minibutton\" onClick=\"app.ext.admin_batchJob.a.showBatchJobStatus('$ID'); return false;\">Running $ID</button></td>~;
			}
		else {
			$c .= "<td valign=top><a href=\"/biz/reports/index.cgi?VERB=BATCH-SEARCH-NOW&JOBID=$ID\">$ID</a></td>";
			}
		

		$c .= "<td valign=top>$LUSER</td>";
		$c .= "<td valign=top>$JOBTYPE</td>";
		if ($TITLE eq '') { $TITLE = ".. Title not set .."; }
		$c .= "<td valign=top>$TITLE</td>";
		$c .= "<td valign=top>$STATUS</td>";

		$c .= "<td valign=top>".&ZTOOLKIT::pretty_date($CREATEDTS,2)."</td>";

		if ($FINISHEDTS>0) {
			$c .= "<td valign=top>Finished: ".&ZTOOLKIT::pretty_date($FINISHEDTS,1)."</td>";
			}
		elsif ($CREATEDTS>time()) {
			$c .= "<td valign=top>Waiting</td>";
			}
		elsif ($FINISHEDTS==0) {
			my ($duration) = time() - $CREATEDTS;
			$c .= "<td valign=top>Running: ".&ZTOOLKIT::pretty_time_since(0-$duration,1)."</td>";
			}
		else {
			}
		$c .= "</tr>";
		}
	$sth->finish();

	if ($c eq '') {
		$c = "<tr><td valign=top><i>No Batch Jobs</i></td></tr>";
		}
	else {
		$c = qq~
		<tr class="zoovysub1header">
			<td>JOB ID</td>
			<td>USER</td>
			<td>JOB TYPE</td>
			<td>JOB TITLE</td>
			<td>STATUS</td>
			<td>CREATED</td>
			<td>STATUS</td>
		</tr>
		$c
		~;
		}
	$GTOOLS::TAG{'<!-- JOBS -->'} = $c;

	&DBINFO::db_zoovy_close();


	$template_file = 'index-batch.shtml';
	push @BC, { name=>'Batch Jobs' };
	}









##############################################################################################
##
##
if ($VERB eq 'NUKESCHEDULE') {
	require REPORT::SCHEDULE;
	&REPORT::SCHEDULE::deleteReport($USERNAME,$ZOOVY::cgiv->{'REPORTID'});
	$VERB = 'SCHEDULE';
	}


if ($VERB eq 'SAVESCHEDULE') {
	require REPORT::SCHEDULE;
#	print STDERR Dumper($ZOOVY::cgiv);
	my $REPORTID = 0;
	if ($ZOOVY::cgiv->{'REPORTID'}) { $REPORTID = int($ZOOVY::cgiv->{'REPORTID'}); }
	&REPORT::SCHEDULE::save($REPORTID,$USERNAME,$ZOOVY::cgiv);
	$VERB = 'SCHEDULE';
	}


if ($VERB eq 'EDITSCHEDULE') {
	require REPORT::SCHEDULE;
	my ($hashref) = &REPORT::SCHEDULE::listReports($USERNAME,$ZOOVY::cgiv->{'REPORTID'});
	$ZOOVY::cgiv->{'type'} = $hashref->{'TYPE'};
	$ZOOVY::cgiv->{'report_name'} = $hashref->{'NAME'};
	$ZOOVY::cgiv->{'REPORTID'} = $hashref->{'ID'};
	$ZOOVY::cgiv->{'frequency'} = $hashref->{'P'}->{'FREQ'};
	## copy over other parameter keys such as "EMAIL", "TODO"
	foreach my $k (keys %{$hashref->{'P'}}) {
		$ZOOVY::cgiv->{$k} = $hashref->{'P'}->{$k};
		}
	}

if (($VERB eq 'ADDSCHEDULE') || ($VERB eq 'EDITSCHEDULE')) {
	## passed vars: 
	##		frequency [daily/weekly/monthly/quarterly]
	##		type [sales]
	## 	report_name
	
	$GTOOLS::TAG{'<!-- TYPE -->'} = $ZOOVY::cgiv->{'type'};
	$GTOOLS::TAG{'<!-- FREQUENCY -->'} = $ZOOVY::cgiv->{'frequency'};
	$GTOOLS::TAG{'<!-- REPORT_NAME -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'report_name'});
	$GTOOLS::TAG{'<!-- REPORTID -->'} = $ZOOVY::cgiv->{'REPORTID'};

	$GTOOLS::TAG{'<!-- NOTIFY_EMAIL_CHECKED -->'} = ($ZOOVY::cgiv->{'EMAIL'})?'checked':'';
	$GTOOLS::TAG{'<!-- EMAIL -->'} = ($ZOOVY::cgiv->{'EMAIL'})?($ZOOVY::cgiv->{'EMAIL'}):&ZOOVY::fetchmerchant_attrib($USERNAME,'email');
	$GTOOLS::TAG{'<!-- NOTIFY_TODO_CHECKED -->'} = ($ZOOVY::cgiv->{'TODO'})?'checked':'';
	
	if ($ZOOVY::cgiv->{'frequency'} eq 'DAILY') {
		my $out = '';
		foreach (sort { $a <=> $b; } keys %hours) { $out .= "<option ".(($ZOOVY::cgiv->{'HOUR'} eq $_)?'selected':'')." value=\"$_\">$hours{$_}</option>\n"; }
		$GTOOLS::TAG{'<!-- DAILY -->'} = qq~<b>Daily Report</b><br>Report Start/End Time: <select name="HOUR">$out</select>~;	
		}
	elsif ($ZOOVY::cgiv->{'frequency'} eq 'WEEKLY') {
		my $out = '';
		foreach (sort { $a <=> $b; } keys %dows) { $out .= "<option value=\"$_\">$dows{$_}</option>\n"; }
		$GTOOLS::TAG{'<!-- WEEKLY -->'} = qq~<b>Weekly Report</b><br>Report Day: <select name="DOW">$out</select>~;	
		}
	elsif ($ZOOVY::cgiv->{'frequency'} eq 'MONTHLY') {
		my $out = '';
		foreach (sort { $a <=> $b; } keys %dom) { $out .= "<option value=\"$_\">$dom{$_}</option>\n"; }
		$GTOOLS::TAG{'<!-- MONTHLY -->'} = qq~<b>Monthly Report:</b><br>Report Ending Day: <select name="DOM">$out</select>~;
		}
	else {
		$GTOOLS::TAG{'<!-- QUARTERLY -->'} = qq~<b>Quarterly Report:</b><br>Quarterly reports have no configurable options.~;
		}

	if ($ZOOVY::cgiv->{'type'} eq 'SALES') {
		## Sales report
		$GTOOLS::TAG{'<!-- CONFIG -->'} = qq~<i>Sales report has no configurable options</i><br>~;
		}

	push @BC, { name=>'Scheduling' };
	$template_file = 'schedule.shtml';
	}




if ($VERB eq 'ORDERS') {
	push @BC, { name=>'Orders' };
	$template_file = 'index-orders.shtml';
	}

if ($VERB eq 'WEBSITE') {
	push @BC, { name=>'Website' };
	$template_file = 'index-website.shtml';
	}

if ($VERB eq 'SYNDICATION') {
	push @BC, { name=>'Orders' };
	$template_file = 'index-syndication.shtml';
	}

if ($VERB eq 'BATCH-SEARCH-NOW') {
	push @BC, { 'name'=>'View Report' };
	my $JOBID = $ZOOVY::cgiv->{'JOBID'};
	my ($bj) = BATCHJOB->new($USERNAME,$JOBID);
	if ((not defined $bj) || (ref($bj) ne 'BATCHJOB') || ($bj->id()==0)) {
		push @MSGS, "ERROR|JOB: $JOBID not found or could not be loaded.";
		$VERB = 'BATCH-SEARCH';
		}
	else {
		push @MSGS, "SUCCESS|viewing batch job $JOBID";
		$template_file = 'batchjob-detail.shtml';
		my $slogref = $bj->full_slog();
		my $c = '';
		if (scalar(@{$slogref})==0) {
			$c .= "<tr><td><div class='caution'>Sorry, no status log entries were created for this job.</div></td></tr>";
			}
		my $r = '';
		foreach my $log (@{$slogref}) {
			$r = ($r eq 'r0')?'r1':'r0';
			$c .= "<tr><td class='$r'>$log->[1]</td></tr>";
			}
		$GTOOLS::TAG{'<!-- SLOG_OUTPUT -->'} = $c;

		foreach my $k (keys %{$bj}) {
			$GTOOLS::TAG{"<!-- $k -->"} = $bj->get($k);
			}
		$GTOOLS::TAG{'<!-- CREATED -->'} = &ZTOOLKIT::pretty_date($bj->get('CREATED_GMT'),4);
		$GTOOLS::TAG{'<!-- FINISHED -->'} = &ZTOOLKIT::pretty_date($bj->get('FINISHED_GMT'),4);

		if ($bj->{'BATCH_EXEC'} eq 'REPORT') {
			$GTOOLS::TAG{'<!-- VIEW_URL -->'} = qq~
		<tr><td><button class="button" onClick="navigateTo('/biz/reports/view.cgi?GUID=~.$bj->{'GUID'}.qq~'); return false;">View Report</button></td></tr>
		~;
			}

		# $GTOOLS::TAG{'<!-- OUTPUT -->'} = '<pre>'.Dumper($bj).'</pre>';
		}
	}

if ($VERB eq 'BATCH-SEARCH') {
	push @BC, { name=>'Batch Report: Search' };
	$template_file = 'index-batch-search.shtml';
	}

if ($VERB eq 'SCHEDULE') {
	require REPORT::SCHEDULE;
	push @BC, { name=>'Scheduling' };

	my $out = '';
#	<tr class="white_bg">
#		<td>Synd.</td>
#		<td>My First Report</td>
#		<td>Weekly</td>
#		<td>Mon-Fri</td>
#		<td>Mail: jt@zoovy.com (XLS)</td>
#		<td><input type="checkbox" value="i" name=""></td>
#	</tr>
	my $count = 0;
	foreach my $detail (@{&REPORT::SCHEDULE::listReports($USERNAME)}) {
		print STDERR Dumper($detail);
		my $bgcolor = ($count++%2)?'light':'white_bg';
		$out .= "<tr class=\"$bgcolor\">";
		$out .= "<td nowrap valign='top'>$detail->{'TYPE'}</td>";
		$out .= "<td nowrap valign='top'>$detail->{'NAME'}</td>";
		$out .= "<td nowrap valign='top'>$detail->{'P'}->{'FREQ'}</td>";
		$out .= "<td nowrap valign='top'>".&ZTOOLKIT::pretty_date($detail->{'NEXTRUN_GMT'},1)."</td>";
		$out .= "<td nowrap valign='top'><center>$detail->{'RUNCOUNT'}</center></td>";
		$out .= "<td nowrap valign='top'>$detail->{'NOTIFY'}</td>";
		$out .= "<td nowrap valign='top'><input type=\"radio\" name=\"REPORTID\" value=\"$detail->{'ID'}\"></td>";
		$out .= "</tr>\n";
		}
	if ($out eq '') { $out = "<tr class=\"white_bg\"><td colspan='8'><i>You have no scheduled reports</i></td></tr>\n"; }
	$GTOOLS::TAG{'<!-- ROWS -->'} = $out;

	$template_file = 'index-schedule.shtml';
	}

##
##
##
if ($VERB eq 'STORED') {
	push @BC, { name=>'Stored Reports' };
	$template_file = 'index-stored.shtml';

	require LUSER::FILES;
	my ($lf) = LUSER::FILES->new($USERNAME,LU=>$LU);

	if ($ZOOVY::cgiv->{'DELETE'}) {
		$lf->nuke(ID=>int($ZOOVY::cgiv->{'DELETE'})); 
		}

	my $out = '';
	my $r = '';
	foreach my $report (@{$lf->list(type=>"REPORT")}) {
		$r = ($r eq 'r1')?'r0':'r1';
		$out .= "<tr class='$r'>";
		$out .= "<td><a href=\"index.cgi?VERB=STORED&DELETE=$report->{'ID'}\">[DELETE]</td>";
		$out .= "<td><a href=\"/biz/reports/view.cgi?GUID=$report->{'GUID'}\">[VIEW]</td>";
		$out .= "<td>$report->{'TITLE'}</td>";
		$out .= "<td>".&ZTOOLKIT::pretty_date($report->{'CREATED_GMT'},2)."</td>";
		$out .= "</tr>\n";
		}
	if ($out eq '') { $out = '<tr><td>You have no stored reports.</td></tr>'; }
	$GTOOLS::TAG{'<!-- REPORT_LIST -->'} = $out; $out = '';
	}

if ($VERB eq '') {
	$template_file = 'index.shtml';
	}

my @TABS = ();
push @TABS, { name=>'Reports', link=>'/biz/reports/index.cgi?VERB=', selected=>($VERB eq '')?1:0 };
push @TABS, { name=>'Sales Reports', link=>'/biz/reports/index.cgi?VERB=INDEX-SALES', selected=>($VERB eq 'INDEX-SALES')?1:0 };
push @TABS, { name=>'Inventory', link=>'/biz/reports/index.cgi?VERB=INDEX-INVENTORY', selected=>($VERB eq 'INDEX-INVENTORY')?1:0 };
push @TABS, { name=>'Batch Jobs', link=>'/biz/reports/index.cgi?VERB=INDEX-BATCH', selected=>($VERB eq 'INDEX-BATCH')?1:0 };
push @TABS, { name=>'Job Status', link=>'/biz/reports/index.cgi?VERB=BATCH-SEARCH', selected=>($VERB eq 'INDEX-SEARCH')?1:0 };

&GTOOLS::output('*LU'=>$LU,'*LU'=>$LU,
	title=>'Reports',
	file=>$template_file,
	header=>1,
	'bc'=>\@BC,
	'msgs'=>\@MSGS,
	'tabs'=>\@TABS,
	help=>'#50808',
	);