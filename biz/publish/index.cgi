#!/usr/bin/perl

use strict;
use lib "/httpd/modules";
require ZOOVY;
require GTOOLS;
require LUSER;

my $dbh = &DBINFO::db_zoovy_connect();
my ($LU) = LUSER->authenticate();
if (not defined $LU) { warn "Auth"; exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { warn "No auth"; exit; }


my $template_file = 'index.shtml';
my @BC = ();
push @BC, { name=>"Publishing" };

my $VERB = $ZOOVY::cgiv->{'VERB'};

if ($FLAGS !~ /PUBLISH/) {
	$template_file = 'denied.shtml';
	$VERB = 'DENIED';
	}

#if ($VERB eq 'PUBLISH') {
#	$GTOOLS::TAG{'<!-- PUBLISH_STATUS -->'} = qq~
#		<form action=""><input type=submit class="button" value="Publish New Version"></form>
#		~;
#
#	$template_file = 'index.shtml';
#	}
#
if ($VERB eq 'RELOAD') {
	$VERB = '';
	}

if ($VERB eq 'PUBLISH') {
	
	my $pstmt = "select count(*) from QUEUE where MID=$MID /* $USERNAME */ and PROCESS='PUBLISH' and COMPLETED_GMT=0";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	my ($count) = $sth->fetchrow();
	$sth->finish();

	if ($count==0) {
		$LU->log("PUBLISH","Requested publish site","INFO");
		&DBINFO::insert($dbh,'QUEUE',{
			USERNAME=>$USERNAME,
			MID=>$MID,
			PROCESS=>'PUBLISH',
			PARAMETERS=>"?LUSER=$LUSERNAME&VERB=RUN",
			CREATED_GMT=>time(),
			NEEDITBY_GMT=>time()+300,
			},debug=>1);
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<div class='success'>Publish queued - please wait 5 minutes.</div>";
		}
	else {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<div class='error'>There is already a publish pending.</div>";
		}

	$VERB = '';
	}


if ($VERB eq 'HALT') {
	
	my $pstmt = "select count(*) from QUEUE where MID=$MID /* $USERNAME */ and PROCESS='PUBLISH' and COMPLETED_GMT=0";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	my ($count) = $sth->fetchrow();
	$sth->finish();

	if ($count==0) {
		$LU->log("PUBLISH","Requested PUBLISH Stop","INFO");
		&DBINFO::insert($dbh,'QUEUE',{
			USERNAME=>$USERNAME,
			MID=>$MID,
			PROCESS=>'PUBLISH',
			PARAMETERS=>"?LUSER=$LUSERNAME&VERB=HALT",
			CREATED_GMT=>time(),
			NEEDITBY_GMT=>time()+300,
			},debug=>1);
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<div class='success'>Publish HALT request received - please wait 5 minutes.</div>";
		}
	else {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<div class='error'>There is already a publish pending.</div>";
		}

	$VERB = '';
	}

##
if ($VERB eq '') {

	my $c = '';
	my $pstmt = "select PARAMETERS,CREATED_GMT,NEEDITBY_GMT,COMPLETED_GMT,RESULT from QUEUE where MID=$MID /* $USERNAME */ and PROCESS='PUBLISH' order by ID desc limit 0,10";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	while ( my ($params,$createdgmt,$needitby,$finishedgmt,$result) = $sth->fetchrow() ) {
		my ($ref) = &ZTOOLKIT::urlparams($params);

		if ($finishedgmt == 0) {
			$finishedgmt = "<b>NOT FINISHED</b>";
			}
		$c .= "<tr><td>$ref->{'LUSER'}</td><td>$ref->{'VERB'}</td><td>".&ZTOOLKIT::pretty_date($createdgmt,1)."</td><td>".&ZTOOLKIT::pretty_date($finishedgmt,1)."</td><td>$result</td></tr>";
		}
	$sth->finish();
	if ($c eq '') { 
		$c = "<tr><td><i>No Publish cycles have been performed.</i></td></tr>";
		}
	else {
		$c = "<tr><td><b>User</b></td><td><b>Created</b></td><td><b>Completed</b></td></tr>".$c;
		}
	$GTOOLS::TAG{'<!-- PUBLISHES -->'} = $c;

	$template_file = 'index.shtml'; 
	}


my @TABS = ();
#push @TABS, { name=>"Publish Controls", link=>"index.cgi?VERB=PUBLISH",
#selected=>(($VERB eq 'PUBLISH')?1:0) }; push @TABS, { name=>"My Sites",
#link=>"index.cgi?VERB=SITES", selected=>(($VERB eq 'SITES')?1:0) };
#DBINFO::db_zoovy_close();

&GTOOLS::output(
	header=>1,
	bc=>\@BC,
	tabs=>\@TABS,
	title=>"Site Publishing",
	help=>"#50727",
	file=>$template_file,
	);

