#!/usr/bin/perl

use JSON::XS;

use lib "/httpd/modules";
use ZOOVY;
use DBINFO;
use GTOOLS;
use ZTOOLKIT;
use LUSER;
use BATCHJOB;

my ($LU) = LUSER->authenticate();
if (not defined $LU) { warn "Auth"; exit; }

#use Data::Dumper;
#print STDERR Dumper($LU);

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { warn "No auth"; exit; }
$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;

my ($VERB) = $ZOOVY::cgiv->{'VERB'};
my ($bj) = undef;
my %jsresult = ();

my $JOBID = int($ZOOVY::cgiv->{'JOB'});
my $ERROR = undef;


if ($VERB eq 'VIEW') {
	## VIEW accepts GUID instead JOB= ... doesn't actually work.
	}

##
## user requested an abort, at this point it does nothing, aside from tell them it was aborted and flag the
##		job so it doesn't bill them. the job will still finish, but in the future we might be able to notify
##		the batch program via a pipe that it's time to DIE
##
if ($VERB eq 'ABORT') {
	my $dbh = &DBINFO::db_zoovy_connect();
	$pstmt = "update BATCH_JOBS set STATUS='ABORT',STATUS_MSG='Abort Requested',ABORT_GMT=".time()." where MID=$MID /* $USERNAME */ and ID=$JOBID";
	print STDERR $pstmt."\n";
	$dbh->do($pstmt);
	&DBINFO::db_zoovy_close();
	$VERB = 'LOAD';
	}

##
## cleanup is verb which lets us know the item is effectively "deleted" and should not appear
##		.. (we'll actually clean them up later with a batch process)
##
if ($VERB eq 'CLEANUP') {
#	my $dbh = &DBINFO::db_zoovy_connect();
#	$pstmt = "update BATCH_JOBS set CLEANUP_GMT=".time()." where MID=$MID /* $USERNAME */ and ID=$JOBID";
#	print STDERR $pstmt."\n";
#	$dbh->do($pstmt);
#	&DBINFO::db_zoovy_close();
	my ($bj) = BATCHJOB->new($USERNAME,$JOBID);
	$bj->cleanup();

	# $pstmt = "update PRIVATE_FILES set EXPIRES_GMT
	$VERB = 'LOAD';
	}


##
## this will add a new job, it should *REALLY* require GUID, but for now we'll just throw an 
##	annoying warning.
##
if (($VERB eq 'ADD') || ($VERB eq 'NEW')) {
	## pass VERB=ADD&EXEC=JOB

	my $IS_DUP = 0;
	if ($ZOOVY::cgiv->{'GUID'}) {
		($JOBID) = &BATCHJOB::resolve_guid($USERNAME,$ZOOVY::cgiv->{'GUID'});
		print STDERR "GUID: $JOBID\n";
		if ($JOBID>0) { $IS_DUP++; }
		}
	else {
		warn "batch/index.cgi called VERB=ADD|NEW without GUID";
		$ZOOVY::cgiv->{'GUID'} = &BATCHJOB::make_guid();
		}

	($bj) = BATCHJOB->new($USERNAME,$JOBID,
		PRT=>$PRT,
		GUID=>$ZOOVY::cgiv->{'GUID'},
		EXEC=>$ZOOVY::cgiv->{'EXEC'},
		VARS=>&ZTOOLKIT::buildparams($ZOOVY::cgiv,1),
		'*LU'=>$LU,
		);

	if (not defined $bj) {
		$ERROR = "Could not add job"; 
		}
	elsif ($IS_DUP) {
		## we've already run this (or we're running it)
		}
	else {
		$bj->start();
		}
	}
elsif ($VERB eq 'LOAD') {
	## pass VERB=LOAD&JOB=####
	($bj) = BATCHJOB->new($USERNAME,int($JOBID));
	if (not defined $bj) {
		$ERROR = "Could not load job $JOBID .. internal error.";
		}
	}
else {
	$ERROR = 'required VERB parameter wasnt passed, to batch.cgi.';
	}


## SANITY: lets make sure all is kosher.
if ((not defined $bj) || (ref($bj) ne 'BATCHJOB')) {
	$ERROR = $bj->{'err'};
	if ((not defined $ERROR) || ($ERROR eq '')) { 
		$ERROR = 'Unknown internal error:<br>something went unspeakably wrong in batch/index.cgi, this is really really bad.'; 
		}
	$bj = undef;
	}
elsif ($bj->{'STATUS'} eq 'ERROR') {
	$ERROR = "JOB ERROR - $bj->{'STATUS_MSG'}";
	}

if (ref($bj) eq 'BATCHJOB') { $JOBID = $bj->id(); }

##
## SANITY: $JOBID is set at this point, or it won't be!
##


## Hmm.. if the job is running.. how long has it been running (more than two hours is an error)
if (defined $ERROR) {
	}
elsif ( 
	(defined $bj) && 	## yeah, it needs to be defined.
	(($bj->{'STATUS'} eq 'RUNNING') || ($bj->{'STATUS'} eq 'NEW')) &&  	## NEW or RUNNING
	($bj->{'CREATED_GMT'}<(time()-(3600*2))) ## and created more than two hours ago.
	) {
	## job has been running too long. WAY too long. .. lets cancel it.
	$ERROR = sprintf("Job auto-cancelled after %d seconds (was:%s)",
		(time()-$bj->{'CREATED_GMT'}),
		$bj->{'STATUS_MSG'});
	$bj->update('STATUS'=>'ERROR',ABORT_GMT=>time(),'STATUS_MSG'=>$ERROR);
	}


require ADVERT;
my @URLS = ();				## an array of advertising URLS
if (defined $ERROR) {
	if ($ERROR eq '') {
		## this line should *NEVER* be reached.
		$ERROR = "batch/index.cgi had ERROR defined, but it was blank! - bad programmer, no cookie.";
		}

	$GTOOLS::TAG{'<!-- REPORT_BODY -->'} = qq~
		<div class='caution-box'>
		ERROR: $ERROR
		</div>
		<br>
		<i>This message is most likely caused a software bug. 
		If you do not know what specifically caused this error, 
		please open a support ticket with the steps necessary to reproduce this issue.</i>
		<br>
		<br>
		~;
	
	if ($JOBID>0) {
		$GTOOLS::TAG{'<!-- REPORT_BODY -->'} .= qq~
		<hr>
		A job was created, however your account will not be debited any job credits because of this error.<br>
<input class="button" onClick="document.batchFrm.JOB.value='$JOBID'; document.batchFrm.VERB.value='CLEANUP'; document.batchFrm.submit();" type="button" value="Clean Up/Remove">
		~;
		}
	$GTOOLS::TAG{'<!-- JOB -->'} = $JOBID;
	$GTOOLS::TAG{'<!-- REPORT_HEADER -->'} = "*** ERROR JOB# $JOBID ****";
	@URLS = ('/biz/batch/cartoon_bug.jpg');
	}
else {
	$GTOOLS::TAG{'<!-- JOB -->'} = $bj->id();
	$GTOOLS::TAG{'<!-- REPORT_HEADER -->'} = 'Job#'.$bj->id();
	@URLS = &ADVERT::retrieve_urls($USERNAME,$FLAGS,10);
	## this will cause us to download all slogs.
	$bj->reset_slog_ack();
	}
my $out = '';  foreach my $url (@URLS) { $out .= "'$url',"; } chop($out);
$GTOOLS::TAG{'<!-- JS_ARRAY -->'} = $out;
$GTOOLS::TAG{'<!-- FIRST_URL -->'} = $URLS[0];


##
## SANITY: at this point $bj is set, or $ERROR is
##
if (defined $bj) {
	%jsresult = $bj->read();
	}

if ((defined $bj) && ($bj->{'CLEANUP_GMT'}>0)) {
	$GTOOLS::TAG{'<!-- REPORT_HEADER -->'} = 'Cleanup on Job#'.$bj->id();
	$GTOOLS::TAG{'<!-- REPORT_BODY -->'} = qq~
This job has been removed/cleaned up.
<br>
Use the navigation bar at the top of the screen to proceed.<br>
<br>
<a href="/biz/reports">Return to Reports</a>
~;
	}
elsif (defined $ERROR) {
	## do nothing!
	}
elsif ($bj->{'STATUS'} eq 'ABORT') {
	$GTOOLS::TAG{'<!-- REPORT_HEADER -->'} = 'Aborted Job#'.$bj->id();
	$jsresult{'status_detail'} = qq~
<b>An abort was requested for this job.</b><br>
<br>
<hr>
No job debits will be applied to your account for this job.
If you wish to remove this job from your job list, you may use cleanup the button below.
<br>
	~;
	}
elsif (($bj->{'STATUS'} eq 'RUNNING') || ($bj->{'STATUS'} eq 'NEW')) {
	$GTOOLS::TAG{'<!-- JOB -->'} = $bj->id();
	$GTOOLS::TAG{'<!-- REPORT_HEADER -->'} = "Running Job#".$bj->id();
	$GTOOLS::TAG{'<!-- JS_UPDATE_STATUS -->'} = '1';
	}
elsif ($bj->{'STATUS'} eq 'SUCCESS') {
	$GTOOLS::TAG{'<!-- JOB -->'} = $bj->id();
	$GTOOLS::TAG{'<!-- REPORT_HEADER -->'} = "Finished Job#".$bj->id();
	$GTOOLS::TAG{'<!-- JS_UPDATE_STATUS -->'} = '0';
	}
else {
	$jsresult{'status_detail'} = qq~Unknown Job Status: "$bj->{'STATUS'}"~;
	$GTOOLS::TAG{'<!-- JS_UPDATE_STATUS -->'} = '0';
	}

my $out = JSON::XS::encode_json(\%jsresult);
print STDERR "OUT: $out\n";
$GTOOLS::TAG{'<!-- INITIAL_JSON -->'} = $out;

my $HEADER = $ZOOVY::cgiv->{'HEADER'};
## by default, always show tabs.
if (not defined $HEADER) { $HEADER++; }

&GTOOLS::output(file=>'index.shtml',
	blank=>($HEADER==0)?1:0,
	jquery=>1,
	header=>1,
head=>q~
~);

