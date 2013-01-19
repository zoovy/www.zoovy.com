#!/usr/bin/perl

use strict;
use lib "/httpd/modules";
use SYNDICATION;
use GTOOLS;


require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_P&16');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }
$GTOOLS::TAG{'<!-- PRT -->'} = $PRT;

my $template_file = 'index.shtml';
my $VERB = $ZOOVY::cgiv->{'VERB'};

if ($FLAGS !~ /,WS,/) {
	$template_file = 'denied.shtml'; 
	$VERB = 'DENIED';
	}


my @BC = (
      { name=>'Syndication',link=>'http://www.zoovy.com/biz/syndication','target'=>'_top', },
      { name=>'DOBA Wholesale Supplier',link=>'http://www.zoovy.com/biz/syndication/doba','target'=>'_top', },
      );






my $so = ();
my %s = ();
($so) = SYNDICATION->new($USERNAME,"#$PRT",'DOB');
tie %s, 'SYNDICATION', THIS=>$so;


## BEGIN DEBUGGER
if ($VERB eq 'GOGO-DEBUG') {
	$GTOOLS::TAG{'<!-- DEBUG-OUTPUT -->'} = $so->runDebug(type=>'product',TRACEPID=>$ZOOVY::cgiv->{'PID'});
	$VERB = 'DEBUG';
	}
if ($VERB eq 'DEBUG') {
	if ($GTOOLS::TAG{'<!-- DEBUG-OUTPUT -->'} eq '') { 
		$GTOOLS::TAG{'<!-- DEBUG-OUTPUT -->'} = '<i>Please specify a product</i>'; 
		}
	$GTOOLS::TAG{'<!-- PID -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'PID'});
	$template_file = '_/syndication-debug.shtml';
	}
## END DEBUGGER


if ($VERB eq 'WEBDOC') {
	$template_file = &GTOOLS::gimmewebdoc($LU,$ZOOVY::cgiv->{'DOC'});
	}




if (($VERB eq 'SAVE') || ($VERB eq 'SAVE-AND-SUBMIT')) {
	## 
	if ($ZOOVY::cgiv->{'RESET_FEED'}) {
		my ($st) = $so->stash();
		if (defined $st) { 
			$st->nuke(); 
			$GTOOLS::TAG{'<!-- MSG -->'} = qq~<div class="success">Stashes reset, you probably want to create a feed now.</div>~;
			}
		}

	$s{'IS_ACTIVE'} = (defined $ZOOVY::cgiv->{'enable'})?1:0;
	if ($s{'IS_ACTIVE'}>0) {
		$s{'IS_ACTIVE'} += int($ZOOVY::cgiv->{'product_submission'});
		}
	$s{'.ftp_user'} = $ZOOVY::cgiv->{'ftp_user'};
	$s{'.ftp_pass'} = $ZOOVY::cgiv->{'ftp_pass'};
	$s{'.doba_user'} = $ZOOVY::cgiv->{'doba_user'};
	$s{'.doba_pass'} = $ZOOVY::cgiv->{'doba_pass'};
	$s{'.schedule'} = $ZOOVY::cgiv->{'schedule'};
	$s{'.images_optional'} = (defined $ZOOVY::cgiv->{'images_optional'})?1:0;
	$s{'.submission'} = $ZOOVY::cgiv->{'submission'};

	if (defined $ZOOVY::cgiv->{'NEEDS_IMAGES'}) {
		$s{'NEEDS_IMAGES'}++;
		}
	if (defined $ZOOVY::cgiv->{'NEEDS_PRODUCTS'}) {
		$s{'NEEDS_PRODUCTS'}++;
		$s{'NEXTRUN_GMT'}=$^T;
		}
	$so->save();

	if ($VERB eq 'SAVE') { $VERB = ''; }
	}

##
##
##
if ($VERB eq 'FILES') {
	require LUSER::FILES;
	my ($LF) = LUSER::FILES->new($USERNAME,LU=>$LU);

	my $results = $LF->list(type=>'DOBA');
	my $c = '';
	foreach my $file (@{$results}) {
		$c .= "<tr>";
		$c .= "<td>$file->{'%META'}->{'type'}</td>";
		$c .= "<td><a href=\"/biz/setup/private/index.cgi/$file->{'TITLE'}?VERB=DOWNLOAD&GUID=$file->{'GUID'}&FILE=$file->{'FILE'}\">$file->{'TITLE'}</a></td>";
		$c .= "<td>$file->{'CREATED'}</td>";
		$c .= "<td>$file->{'SIZE'}</td>";
		$c .= "</tr>";
		}
	$GTOOLS::TAG{'<!-- FILES -->'} = $c;
	# $GTOOLS::TAG{'<!-- FILES -->'} = '<table><tr><td><pre>'.Dumper($results).'</pre></td></tr></table>';
	$template_file = '_/syndication-files.shtml';
	}


if ($VERB eq 'LOGS') {
   $GTOOLS::TAG{'<!-- LOGS -->'} = $so->summarylog();
   $template_file = '_/syndication-logs.shtml';
   }



##
##
##
if ($VERB eq 'SAVE-AND-SUBMIT') {
	my ($bj) = $so->createBatchJob('product','*LU'=>$LU);
	## NOTE: $bj should be a ref

	if (ref($bj) eq 'BATCHJOB')  {
		my $JOBID = $bj->id(); 
		print "Location: /biz/batch/index.cgi?VERB=LOAD&JOB=$JOBID\n\n";
		exit;
		}
	elsif ((ref($bj) eq 'HASH') && (defined $bj->{'err'})) {
		$GTOOLS::TAG{'<!-- JOB_ERROR -->'} = qq~<div class="error">$bj->{'err'}</div>~;
		}
	else {
		$GTOOLS::TAG{'<!-- JOB_ERROR -->'} = qq~<div class="error">UNKNOWN RESPONSE FORMAT FROM BATCHJOB</div>~;
		}
	$VERB = '';
	}

##
##
##
if ($VERB eq '') {
	if ($s{'.validation_errors'}==0) {
		$GTOOLS::TAG{'<!-- PRODUCT_VALIDATION -->'} = "Product feed contained no validation errors";
		}
	else {
		my $url = sprintf("/biz/setup/private/index.cgi/download.csv?VERB=DOWNLOAD&GUID=%s",
			$s{'.validation_log_file'},
			$s{'.validation_log_file'});
			
		$GTOOLS::TAG{'<!-- PRODUCT_VALIDATION -->'} = qq~
Product feed contained $s{'.validation_errors'} errors.<br>
<a href="$url">Download Validation Log</a><br>
<div class="hint">
HINT: The validation log may also be imported as a CSV file to correct the values.
</div>
~;
		}



	$GTOOLS::TAG{'<!-- FTP_USER -->'} = $s{'.ftp_user'};
	$GTOOLS::TAG{'<!-- FTP_PASS -->'} = $s{'.ftp_pass'};
	$GTOOLS::TAG{'<!-- DOBA_USER -->'} = $s{'.doba_user'};
	$GTOOLS::TAG{'<!-- DOBA_PASS -->'} = $s{'.doba_pass'};
	$GTOOLS::TAG{'<!-- CB_ENABLE_DOBA -->'} = ($s{'IS_ACTIVE'})?'checked':'';
	$GTOOLS::TAG{'<!-- CB_IMAGES_OPTIONAL -->'} = ($s{'.images_optional'})?'checked':'';
	$GTOOLS::TAG{'<!-- PRODUCT_SUBMISSION_66 -->'} = (($s{'IS_ACTIVE'} & 66)==66)?'selected':'';
	$GTOOLS::TAG{'<!-- PRODUCT_SUBMISSION_64 -->'} = (($s{'IS_ACTIVE'} & 66)==64)?'selected':'';
	$GTOOLS::TAG{'<!-- PRODUCT_SUBMISSION_0 -->'} = (($s{'IS_ACTIVE'} & 66)==0)?'selected':'';

	if ($s{'IS_ACTIVE'}==0) {
		$GTOOLS::TAG{'<!-- TEST_ONLY_WARNING -->'} = qq~<div class="warning">WARNING: Not currently active.</div>~;
		}
	elsif (($s{'IS_ACTIVE'}&2)==2) {
		$GTOOLS::TAG{'<!-- TEST_ONLY_WARNING -->'} = qq~<div class="warning">WARNING: Currently configured in TEST mode, files are not actually transmitted.</div>~;
		}

	if ($FLAGS =~ /,WS,/) {
		my $c = '<option value="">Not Set</option>';
		require WHOLESALE;
		foreach my $sch (@{&WHOLESALE::list_schedules($USERNAME)}) {
			$c .= "<option ".(($s{'.schedule'} eq $sch)?'selected':'')." value=\"$sch\">$sch</option>\n";
			}
		$GTOOLS::TAG{'<!-- SCHEDULE -->'} = $c;
		}
	else {
		$s{'.schedule'} = '';
		$GTOOLS::TAG{'<!-- SCHEDULE -->'} = '<option value="">Not Available</option>';
		}


#	$GTOOLS::TAG{'<!-- IMAGES_LASTRUN -->'} = &ZTOOLKIT::pretty_date(int($s{'.last_images_gmt'}),1);
#	if ($s{'NEEDS_IMAGES'}) { $GTOOLS::TAG{'<!-- IMAGES_LASTRUN -->'} = '<i>Request Pending</i>'; }
        $GTOOLS::TAG{'<!-- PRODUCTS_LASTRUN -->'} = &ZTOOLKIT::pretty_date(int($s{'PRODUCTS_LASTRUN_GMT'}),1);
	if ($s{'NEEDS_PRODUCTS'}) { $GTOOLS::TAG{'<!-- PRODUCTS_LASTRUN -->'} = '<i>Request Pending</i>'; }

	$template_file = 'index.shtml';
	}

untie %s;

my @TABS = ();
push @TABS, { selected=>($VERB eq '')?1:0, 'name'=>'Config', 'link'=>'/biz/syndication/doba/index.cgi' };
push @TABS, { selected=>($VERB eq 'LOGS')?1:0, 'name'=>'Logs', 'link'=>'/biz/syndication/doba/index.cgi?VERB=LOGS' };
push @TABS, { selected=>($VERB eq 'FILES')?1:0, 'name'=>'Files', 'link'=>'/biz/syndication/doba/index.cgi?VERB=FILES' };
push @TABS, { name=>"Diagnostics", selected=>($VERB eq 'DEBUG')?1:0, link=>"/biz/syndication/doba/index.cgi?VERB=DEBUG", };
push @TABS, { name=>'Webdoc',selected=>($VERB eq 'WEBDOC')?1:0, link=>"/biz/syndication/doba/index.cgi?VERB=WEBDOC&DOC=51368", };


&GTOOLS::output('tabs'=>\@TABS,'bc'=>\@BC,file=>$template_file,header=>1);

