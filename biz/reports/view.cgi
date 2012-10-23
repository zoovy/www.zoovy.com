#!/usr/bin/perl

use strict;

use Data::Dumper;
use YAML::Syck;
use URI::Escape;
use POSIX qw (ceil);
use lib "/httpd/modules";
require REPORT;
require GTOOLS;
require GTOOLS::REPORT;
require LUSER;

my $template_file = '';
my $VERB = '';
my $TYPE = '';

#if (defined $R->{'@DASHBOARD'}) {
#	foreach my $db (@{$R->{'@DASHBOARD'}}) {
#		}
#	}
#
#if (defined $R->{'@HEAD'}) {
#	my $out = '';
#	foreach my $db (@{$R->{'@HEAD'}}) {
#		$out .= "<tr><td>".Dumper($db)."</td></tr>";
#		}
#	$GTOOLS::TAG{'<!-- HEADER -->'} = $out;
#	}

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_M&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }


my %S = ();
if ($ZOOVY::cgiv->{'GUID'}) {
	## S and GUID should never be passed *together*
	$S{'GUID'} = $ZOOVY::cgiv->{'GUID'};
	}
## for SYNDICATION viewing (/biz/syndication)
if ($ZOOVY::cgiv->{'DST'}) {
	$S{'DST'} = $ZOOVY::cgiv->{'DST'};
	}
if ($ZOOVY::cgiv->{'PROFILE'}) {
	$S{'PROFILE'} = $ZOOVY::cgiv->{'PROFILE'};
	}

## did we get a S (SESSION) passed?
if (defined $ZOOVY::cgiv->{'S'}) {
   %S = %{&ZTOOLKIT::fast_deserialize($ZOOVY::cgiv->{'S'},1)};
   }
## load in new variables into the serial
foreach my $param (keys %{$ZOOVY::cgiv}) {
   next if ($param eq 'S'); # no sense looping on ourselves!
   next unless (substr($param,0,1) eq '.');   # anything .param is a session (persistent) parameter
   $S{$param} = $ZOOVY::cgiv->{$param};
   }



##
## S (Session) variables:
##		.page 
##		.view
##			DETAIL:
##			SUMMARY:
##			
##


$VERB = $ZOOVY::cgiv->{'VERB'};
$TYPE = $ZOOVY::cgiv->{'TYPE'};
if ($TYPE eq '') { $TYPE = 'REPORT'; }



## SYNDICATION files or any other non-YAML/REPORT file
if ($TYPE ne 'REPORT') {
	my $contents = undef;
	require LUSER::FILES;
	my ($lf) = LUSER::FILES->new($USERNAME);
	my $privatefileref = ();

	## filter by GUID
	if ($S{'GUID'} eq '0') {
		print STDERR "GUID = 0\n";
		}
	elsif ($S{'GUID'} ne '') {
		my $filesref = $lf->list('guid'=>$S{'GUID'});
		$privatefileref = $filesref->[0];
		}

	if (defined $privatefileref) { print STDERR "private file exists\n"; $contents = $lf->view($privatefileref); }
	else { $contents = "This FILE does not exist."; }


	print "Content-type: text/plain\n\n$contents";
	exit;
	}

my $R = undef;
## REPORTS or any other YAML files
if ($S{'GUID'} ne '') {
	print STDERR "GUID: $S{'GUID'}\n";
	$R = REPORT->new_from_guid($USERNAME,$S{'GUID'}); 
	}

if (not defined $R) {
	$VERB = 'ERROR';
	$GTOOLS::TAG{'<!-- MESSAGE -->'} = "Could not load file: $ZOOVY::cgiv->{'GUID'}";
	$template_file = 'output-error.shtml';	
	}

#print STDERR Dumper($R);

if ($VERB eq '') { 
	$VERB = 'HTML'; 
	}
if ($VERB eq 'TOOLBAR') { $VERB = 'HTML'; }

if ($VERB eq 'PRINT') { 
	$template_file = 'output-print.shtml'; 
	my ($html) = &GTOOLS::REPORT::showHTML($R,{},undef);
	$GTOOLS::TAG{'<!-- HTMLTABLE -->'} = $html;
	}

#if ($VERB eq 'EXCEL') {
#	my ($html) = &GTOOLS::REPORT::showHTML($R,{},undef);
#	$GTOOLS::TAG{'<!-- HTMLTABLE -->'} = $html;
#	print "Content-type: application/excel\n\n";
#	&GTOOLS::output(
#		'header'=>0,
#		'file'=>'output-excel.shtml',
#		);
#	exit;
#	}

if ($VERB eq 'CSV') {
	my $txt = '';
	print "Content-type: text/csv\n\n";
	require Text::CSV_XS;
	my $csv = Text::CSV_XS->new({binary=>1});
	my @columns = ();
	foreach my $h (@{$R->{'@HEAD'}}) {
		my $name = $h->{'name'};
		if ($name eq '') { $name = 'Untitled'; }
		push @columns, $name; 
		}
	my $status = $csv->combine(@columns);
	$txt = $csv->string();
	print "$txt\r\n";

	foreach my $row (@{$R->{'@BODY'}}) {
		my $status = $csv->combine(@{$row});
		print $csv->string()."\r\n";
		}	
	exit;
	}

##
## 
##
if ($VERB eq 'HTML') {
	##
	## example params that can be passed:
	##
	$template_file = '';
	my %params = ();

	if (not defined $S{'.view'}) { 
		$S{'.view'} = 'DETAIL:';
		}

	$GTOOLS::TAG{'<!-- TITLE -->'} = $R->{'title'};
	$GTOOLS::TAG{'<!-- SUBTITLE -->'} = $R->{'subtitle'};

	if ($S{'.view'} eq 'SUMMARY:') {
		## SUMMARY VIEW IS
		delete $S{'.searchcol'};
		delete $S{'.searchtxt'};
		$template_file = 'output-summary.shtml';
		my ($html) = &GTOOLS::REPORT::showSummary($R,\%S);
		$GTOOLS::TAG{'<!-- HTMLTABLE -->'} = $html;
		$GTOOLS::TAG{'<!-- TITLE -->'} = $R->{'title'};
		}
	elsif ($S{'.view'} =~ /^DASHBOARD:([\d]+)$/) {
		$template_file = 'output-dashboard.shtml';
		delete $S{'.searchcol'};
		delete $S{'.searchtxt'};

		## STEP -1: Are we looking at the right VIEW of this report?? If not -- call "buildDashboard" and sub out the module
		my ($DBref) = $R->{'@DASHBOARD'}->[int($1)];
		my ($R2) = REPORT->new($USERNAME,'DASHBOARD');
		foreach my $k ('@HEAD','@GRAPHS','groupby','title') {
			## copies fields from DBref to the new report object.
			$R2->{$k} = $DBref->{$k};
			}
		&GTOOLS::REPORT::buildDashboard($R,$R2);

		my ($html) = &GTOOLS::REPORT::showHTML($R2,\%S);
		$GTOOLS::TAG{'<!-- HTMLTABLE -->'} = $html;
		$GTOOLS::TAG{'<!-- TITLE -->'} = $R2->{'title'};
		$GTOOLS::TAG{'<!-- SUBTITLE -->'} = $R2->{'subtitle'};
		}
	elsif (($S{'.view'} eq 'DETAIL:') || (1)) {
		## note this is the "else" case
		## DETAIL VIEW IS THE "!"
		$template_file = 'output-html.shtml'; 
		if ($R->{'ICON'}) { $GTOOLS::TAG{'<!-- ICON -->'} = qq~<img src="$R->{'ICON'}">~;; }

		delete $R->{'@ROWS_SHOW'};
		my @ROWS = ();
		if ($S{'.searchtxt'} ne '') {
			## we are searching for something, so we'll do the search, create alternate @BODY
			my $rowcount = scalar(@{$R->{'@BODY'}});
			my $i = 0;
			while ($i<$rowcount) {
				if (&GTOOLS::REPORT::rowMatches(\%S,$R->{'@BODY'}->[$i]) ) {
					push @ROWS, $i;
					}
				$i++;
				}
			## an array of matching row positions
			}
		else {
			my $count = scalar(@{$R->{'@BODY'}});
			for (my $i=0; $i<$count; $i++) {
				push @ROWS, $i;
				}
			}
		
		if ($S{'.page'} eq '') {
			$S{'.page'} = 1;
			}
		elsif ($S{'.page'} eq '*') {
			## show all data.
			$S{'.page'} = 1;
			$S{'.page_count'} = 1;
			$S{'.page_size'} = scalar(@ROWS);
			}

		if (int($S{'.page_size'})<=0) { 
			$S{'.page_size'} = 50;
			}
		my $PAGE_SIZE = $S{'.page_size'};
		$S{'.page_count'} = POSIX::ceil(scalar(@ROWS)/$S{'.page_size'});

		if ($S{'.page'} <= 0) {
			$S{'.page'} = $S{'.page_count'};
			}
		if ($S{'.page'} > $S{'.page_count'}) {
			$S{'.page'} = 1;
			}

		## cut's the array down to size.
		@ROWS = splice(@ROWS, ( ($S{'.page'}-1)*$S{'.page_size'} ), $S{'.page_size'});
		
		my ($html) = &GTOOLS::REPORT::showHTML($R,\%S,\@ROWS);

		$GTOOLS::TAG{'<!-- PAGINATION_HEADER -->'} = &GTOOLS::REPORT::build_pagination($R,\%S);
		$GTOOLS::TAG{'<!-- FOOTER -->'} = &GTOOLS::REPORT::build_footer($R,\%S);
		$GTOOLS::TAG{'<!-- HTMLTABLE -->'} = $html;
		}
	}

$GTOOLS::TAG{'<!-- TOOLBAR_HEADER -->'} = &GTOOLS::REPORT::build_toolbar($R,\%S);



my ($Stxt) = &ZTOOLKIT::fast_serialize(\%S,1);
my ($Suri) = URI::Escape::uri_escape($Stxt);
$GTOOLS::TAG{'<!-- S -->'} = $Stxt;
$GTOOLS::TAG{'<!-- URI_S -->'} = URI::Escape::uri_escape($Suri);


&GTOOLS::output(
	header=>1,
	tables=>1,
	file=>$template_file,
	);




__DATA__


if ($VERB eq 'CUSTOM') {
	##
	## customAction handlers are complex - basically an "VERB" of "CUSTOM" gets passed, and then
	##		it calls the function $R->customAction in the object (which is different based on the object)
	##
	##
	## NOTE: customActions don't actually need to goto the customAction page -- not unless it's really necessary.
	##				they can also load new @JOBS into the queue. [not implemented but theoritically possible]
	##
	$R = REPORT->load($params{'SESSION'});
	if (defined $R) {
		&REPORT::serialize($R);
		my ($HTML) = $R->customAction($ZOOVY::cgiv->{'_VERB'},$ZOOVY::cgiv->{'_DATA'},\%params,$q);
		if ($HTML eq '') { 
			## a blank HTML result means we should simply display the detail view
			$VERB = 'HTML';
			}
		else {
			$GTOOLS::TAG{'<!-- CUSTOMVERB_HTML -->'} = $HTML;
			$template_file = 'output-customaction.shtml';
			}
		}
	else {
		$VERB = 'ERROR'; 		# doesn't do anything yet!
		}
	}

##
## Handle Verbs!
##
if ($VERB eq 'EMAIL') {
	## EMAIL THE REPORT LOGIC
	$params{'JUMP_PAGE'} = '*';

	my ($HTML) = &GTOOLS::REPORT::showHTML($R,\%params);
	my $EMAIL = $params{'EMAIL'};
	require MIME::Entity;

	$HTML = qq~<html><head><meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<link rel="STYLESHEET" type="text/css" href="http://www.zoovy.com/biz/images/tabs/styles.css"></head>
<body><div align="center"><table width=100%><tr><td>
<h1>$R->{'title'}</h1>
<h2>$R->{'subtitle'}</h2>
<hr></td></tr></table>
$HTML</div></body>
	~;

	open MH, "|/usr/sbin/sendmail -t";
	print MH "From: $EMAIL\n";
	print MH "To: $EMAIL\n";
	print MH "Subject: [Report] $R->{'title'}\n";

	my $altmsg = MIME::Entity->build(Type=>'multipart/alternative',);
	$altmsg->attach(
		Type => 'text/plain',Disposition => 'inline',
		Data => qq~You must have an HTML capable email application to view this report. ~, );

	$altmsg->attach(
		Type => 'text/html',
		Disposition => 'inline',
		Data => $HTML, );

	$altmsg->print(\*MH);	
	close MH;

	$VERB = 'CLOSE';
	}

