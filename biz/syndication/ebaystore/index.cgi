#!/usr/bin/perl


##
## CONFIG values:
##		1 - FAVOR_EBAY - list remaining quantites to ebay
##		2 - AUTOPILOT - allow the system to guess on certain settings
##		4 - NOTIFY_NIGHT - send notification emails each night
##		8 - NOTIFY_ALL - send notification emails on all changes
##
##	 128 - LINK  - add a link to the ebay store on out of stock items
##	 256 - CONFIGURATOR - pogs in listings.
##

use lib "/httpd/modules"; 
use CGI;
require GTOOLS;
require ZOOVY;
require ZWEBSITE;	
require ZTOOLKIT;
require DBINFO;
require NAVCAT;
use strict;
use LWP::Simple;
use Storable;
require EBAY2;
require SYNDICATION;
require DOMAIN::TOOLS;
require TOXML;
require LUSER;

my @INVORDER = ('DISABLE','QTY1','SAFE','INSANE');
my %INV = (
	'DISABLE'=>'Disabled (Do not syndicate)',
	'QTY1'=>'Always Qty 1 at a Time [RECOMMENDED]',
	'SAFE'=>'Max Quantities when Configured and Available',
	'INSANE'=>'Always Launch Max Quantities',
	);



my $dbh = &DBINFO::db_zoovy_connect();	
require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_P&16');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

$USERNAME = lc($USERNAME);
$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;
my $VERB = $ZOOVY::cgiv->{'VERB'};

my $template_file = '';
#if ($FLAGS !~ /,EBAY,/) {
#	$template_file = 'deny.shtml'; 
#	$VERB = 'DENY';
#	}

my $PROFILE = &ZWEBSITE::prt_get_profile($USERNAME,$PRT);
$GTOOLS::TAG{'<!-- PROFILE -->'} = $PROFILE;

my $so = ();
my %s = ();
if ($PROFILE ne '') {
	($so) = SYNDICATION->new($USERNAME,$PROFILE,'ESS');
	tie %s, 'SYNDICATION', THIS=>$so;
	}

######
## SANITY: at this point EBAYSTORE_FEEDS is populated
##

if ($VERB eq 'ADMIN') {
	$template_file = 'admin.shtml';
	}

#if ($VERB eq 'RESETASK') {
#	$template_file = 'resetask.shtml';
#	}

#if ($VERB eq 'RESETCONFIRM') {
#	$so->addlog('WARN','*** STORE RESET REQUESTED -- WILL BE PERFORMED ON NEXT RUN ***');
#	$s{'.reset'} = $^T;
#	$VERB = '';
#	}

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




###########################################################################################
##
## Setup
##
###########################################################################################

if ($VERB eq 'SAVE-SETUP') {
	$s{'.inventory'} = $ZOOVY::cgiv->{'INVENTORY'};
	$s{'.cfg_autopilot'} = ($ZOOVY::cgiv->{'ENABLE_AUTOPILOT'})?1:0;
	$s{'.source'} = $ZOOVY::cgiv->{'SOURCE'};
	$s{'.duplicates'} = (defined $ZOOVY::cgiv->{'DUPLICATES'})?1:0;
	$s{'.maxlistings'} = int((defined $ZOOVY::cgiv->{'MAXLISTINGS'})?int($ZOOVY::cgiv->{'MAXLISTINGS'}):-1);
	$s{'.logging'} = (defined $ZOOVY::cgiv->{'LOGGING'})?1:0;
	$s{'.suspend_after_err'} = (defined $ZOOVY::cgiv->{'SUSPEND_AFTER_ERR'})?1:0;
	$s{'.default_profile'} = $ZOOVY::cgiv->{'DEFAULT_PROFILE'};

	my $ERROR = '';
	if ($ERROR ne '') {
		$GTOOLS::TAG{'<!-- ERROR -->'} = "<font color='red'>$ERROR</font>";
		}
	else {
		$s{'IS_ACTIVE'} = 1;
		if ($s{'.inventory'} eq 'DISABLE') { $s{'IS_ACTIVE'} = 0; }
		$s{'DIAG_MSG'} = 'Settings updated.';
		$so->save();
		}

	$VERB = 'EDIT';
	}


#if ($VERB eq 'CHECKSTATUS') {
#
#	require EBAY::SYNDICATE;
#	if (defined $so) {
#		my $edbh = &DBINFO::db_user_connect($USERNAME);
#
#		## Finished - Live:265 New:2 Wait:238 Failed:0
#		my ($livecount,$waitcount,$failedcount) = &EBAY::SYNDICATE::getCounts($USERNAME,$PROFILE,$s{'LASTRUN_GMT'});
#		
#		$s{'DIAG_MSG'} = "Check Status - Live:$livecount Wait:$waitcount Failed:$failedcount (this count may be off if items are listed under another profile)";
#		$so->addlog('SYS',$s{'DIAG_MSG'});
#		$so->save(1);
#
#		&DBINFO::db_user_close();
#		}
#
#
#	$VERB = '';
#	}


my @TABS = ();
my @BC = ();
push @BC, { name=>"Syndication", link=>"/biz/syndication" };
push @BC, { name=>"eBay Store", link=>"/biz/syndication/ebaystore" };
if ($PROFILE ne '') {
	push @TABS, { selected=>($VERB eq 'EDIT')?1:0, name=>'Configuration',link=>'?VERB=EDIT&PROFILE='.$PROFILE,'target'=>'_top', };
	push @TABS, { selected=>($VERB eq 'CATEGORY')?1:0, name=>'Map Categories',link=>'?VERB=CATEGORY&PROFILE='.$PROFILE,'target'=>'_top', };
	push @TABS, { selected=>($VERB eq 'LOGS')?1:0, name=>'Activity Logs',link=>'?VERB=LOGS&PROFILE='.$PROFILE,'target'=>'_top', };
	push @TABS, { selected=>($VERB eq 'REPORTS')?1:0, name=>'Reports',link=>'?VERB=REPORTS&PROFILE='.$PROFILE,'target'=>'_top', };
	push @TABS, { selected=>($VERB eq 'DEBUG')?1:0, name=>'Diagnostics',link=>'?VERB=DEBUG&PROFILE='.$PROFILE,'target'=>'_top', };
	push @BC, { name=>'Profile: '.$PROFILE };
	}


if ($VERB eq 'UPDATENOW') {
	$so->runnow($LU);
	$VERB = '';
	}


if (($VERB eq 'EDIT') || ($VERB eq '')) {
	$template_file = 'index.shtml';

	$GTOOLS::TAG{'<!-- GUID -->'} = time();
	$GTOOLS::TAG{'<!-- PROFILE -->'} = $PROFILE;

	$GTOOLS::TAG{'<!-- EBAYSTORE -->'} = $s{'.ebaystore'};
	$GTOOLS::TAG{'<!-- STATUS -->'} = $so->statustxt();
	$GTOOLS::TAG{'<!-- CATUPDATED -->'} = &ZTOOLKIT::pretty_date($s{'.catupdate_gmt'},1);

	$GTOOLS::TAG{'<!-- ENABLE_AUTOPILOT -->'} = ($s{'.cfg_autopilot'})?'checked':'';

	$GTOOLS::TAG{'<!-- SOURCE_WEBSITE-EBAY -->'} = ($s{'.source'} eq 'WEBSITE-EBAY')?'selected':'';
	$GTOOLS::TAG{'<!-- SOURCE_WEBSITE-ALL -->'} = ($s{'.source'} eq 'WEBSITE-ALL')?'selected':'';
	$GTOOLS::TAG{'<!-- SOURCE_PRODUCTS-ALL -->'} = ($s{'.source'} eq 'PRODUCTS-ALL')?'selected':'';

	$GTOOLS::TAG{'<!-- CHK_DUPLICATES -->'} = ($s{'.duplicates'}>0)?'checked':'';
	$GTOOLS::TAG{'<!-- CHK_LOGGING -->'} = ($s{'.logging'}>0)?'checked':'';
	$GTOOLS::TAG{'<!-- CHK_SUSPEND_AFTER_ERR -->'} = ($s{'.suspend_after_err'}>0)?'checked':'';

	$GTOOLS::TAG{'<!-- INVENTORY -->'} = '';
	foreach my $k (@INVORDER) {
		$GTOOLS::TAG{'<!-- INVENTORY -->'} .= "<option ".(($s{'.inventory'} eq $k)?'selected':'')." value='$k'>$INV{$k}</option>\n";
		}

#	if ($s{'.reset'}) { $GTOOLS::TAG{'<!-- LAST_UPDATE -->'} = 'Pending eBay Store Reset!'; }

	$GTOOLS::TAG{'<!-- MAXLISTINGS -->'} = int($s{'.maxlistings'});
	my $c = '';
	foreach my $ns (@{&ZOOVY::fetchprofiles($USERNAME,PRT=>$PRT)}) {
		my $selected = ($ns eq $s{'.default_profile'})?'selected':'';
		$c .= "<option $selected value=\"$ns\">$ns</option>";
		}
	if ($c eq '') {
		$c .= "<option>-- err: no profiles mapped to prt: $PRT --</option>";
		}
	$GTOOLS::TAG{'<!-- PROFILES -->'} = $c;

	$GTOOLS::TAG{'<!-- HTML_WIZARDS -->'} = "<option value=\"\">Use Profile</option>\n";
	push @BC, { name=>"Configure" };
	}

###########################################################################################
##
## Category
##
###########################################################################################


if ($VERB eq 'SAVE-CATEGORY') {
	my $changed = 0;
	my $NC = NAVCAT->new($USERNAME,PRT=>$PRT);
	foreach my $safe ($NC->paths()) {
		next if (not defined $ZOOVY::cgiv->{'navcat-'.$safe});
		my ($pretty, $children, $productstr, $sortby, $metaref) = $NC->get($safe);
		next if (($metaref->{'EBAYSTORE_CAT'} eq $ZOOVY::cgiv->{'navcat-'.$safe}) && ($metaref->{'EBAY_CAT'} eq $ZOOVY::cgiv->{'ebay-'.$safe}));
		$metaref->{'EBAYSTORE_CAT'} = $ZOOVY::cgiv->{'navcat-'.$safe};
		$metaref->{'EBAY_CAT'} = $ZOOVY::cgiv->{'ebay-'.$safe};

		$NC->set($safe,metaref=>$metaref);
		}
	$NC->save(); undef $NC;

	if ($changed) {
		}

	$VERB = 'CATEGORY';
	}


if ($VERB eq 'CATEGORY') {
	$template_file = 'category.shtml';

	my ($DOMAIN,$ROOTPATH) = $so->syn_info();

	my ($toxml) = TOXML->new('DEFINITION','ebay.auction',USERNAME=>$USERNAME,MID=>$MID);
	my $catref = $toxml->getList('EBAYCAT');

	my %categories = ();
	$categories{''} = 'Not Set';
	## reverse the categories
	foreach my $opt (@{$catref}) {
		$categories{$opt->{'V'}} = $opt->{'T'};
		}

	## SETUP EBAY CATEGORIES
	# &EBAYINFO::grab_storecats($USERNAME);
	my @EBAYCATS = @{&EBAY2::fetch_storecats($USERNAME,$PROFILE)};
	

	##
	## SANITY:  at this point the @EBAYCATS array is populated!
	##
	my $c = '';
	use Data::Dumper;
	
	my $bgcolor = '';
	my $NC = NAVCAT->new($USERNAME,PRT=>$PRT);
	foreach my $safe (sort $NC->paths($ROOTPATH)) {
		next if (substr($safe,0,1) eq '*');
		next if ($safe eq '');

		my ($pretty, $children, $productstr, $sortby, $metaref) = $NC->get($safe);
		# print STDERR "META: $meta\n";
		# next if (substr($pretty,0,1) eq '!'); 		# why not let them use hidden categories

		if ($bgcolor eq 'FFFFFF') { $bgcolor='DEDEDE'; } else { $bgcolor = 'FFFFFF'; }

		my $name = ''; 
		if ($pretty eq '') { $pretty = "UN-NAMED: $safe"; }
		if (substr($safe,0,1) eq '.') {
			foreach (split(/\./,$safe)) { $name .= "&nbsp; - &nbsp; "; } $name .= $pretty;
			if ($safe eq '.') { $name = 'HOMEPAGE'; }
			}
		elsif (substr($safe,0,1) eq '$') {
			$name = "LIST: ".$pretty;
			}
		my $val = $metaref->{'EBAYSTORE_CAT'};
		$c .= "<tr bgcolor='$bgcolor'>";
		$c .= "<td nowrap>$name</td><td>";
		$c .= "<select name=\"navcat-$safe\">";
		$c .= "<option value=\"\">Do not submit category</option>";
		my $selected = '';
		my $found = 0;
		foreach my $cat (@EBAYCATS) {
			my ($catnum,$catname) = split(/,/,$cat,2);
			if ($val eq $catnum) { $found++; $selected = ' selected '; } else { $selected = ''; }
			$c .= "<option $selected value=\"$catnum\">$catname ($catnum)</a>";
			}
		if (($found == 0) && ($val ne '')) {
			$c .= "<option selected value=\"$val\">INVALID: $val</option>\n";
			}
		$c .= "</td>";

		$val = $metaref->{'EBAY_CAT'};
		$c .= "<td valign='top'><input name=\"ebay-$safe\" type=\"textbox\" size=\"6\" value=\"$val\"></td>";
		$c .= "<td valign='top'><a href=\"javascript:openWindow('/biz/syndication/ebaystore/catchooser2008.cgi?V=ebay-$safe');\">[Choose]</a></td>";
		my $fullname = &EBAY2::get_cat_fullname($USERNAME,$val);
                $fullname ||= '[not set]';
                $c .= "<td valign='top'>".$fullname."</td>";
		$c .= "</tr>\n";
		}
	if ($c eq '') { $c = '<tr><td><i>No website categories exist??</i></td></tr>'; }
	$GTOOLS::TAG{'<!-- CATEGORIES -->'} = $c;
	push @BC, { name=>"Map Categories" };
	}


###########################################################################################
##
## Manage
##
###########################################################################################
#if ($VERB eq 'LOG') {
#	$template_file = 'log.shtml';
#
#	my $logsref = $so->logs(3+64+128);
#	if (defined $logsref) {
#		my $c = '';
#
#		my $r = 0;
#		my $PID = '';
#
#		foreach my $logset (@{$logsref}) {
#
#			if (($logset->[3] ne $PID) || ($logset->[3] eq '')) {
#				$r = ($r==0)?1:0;
#				$PID = $logset->[3];
#				}
#			if ($logset->[0] eq 'WARN') { $r = 's'; }
#
#			$c .= "<tr>";
#			$c .= "<td class=\"r$r\">$logset->[0]</td>";
#			if ($PID eq '') {
#				$c .= "<td class=\"r$r\">$logset->[3]</td>";
#				}
#			else {
#				$c .= "<td class=\"r$r\"><a href=\"/biz/product/index.pl?VERB=EDIT&PID=$logset->[3]\">$logset->[3]</a></td>";
#				}
#			$c .= "<td class=\"r$r\">".&ZOOVY::incode($logset->[1])."</td>";
#			$c .= "<td class=\"r$r\">".&ZTOOLKIT::pretty_date($logset->[2],1)."</td></tr>\n";
#			}
#		$GTOOLS::TAG{'<!-- LOGS -->'} = $c;
#		}
#	else {
#		$GTOOLS::TAG{"<!-- LOGS -->"} = '<tr><td><i>there are no logs recorded for this marketplace.</td></tr>';
#		}
#	push @BC, { name=>"Logs" };
#	}

if ($VERB eq 'LOGS') {
   $GTOOLS::TAG{'<!-- LOGS -->'} = $so->summarylog();
   $template_file = '_/syndication-logs.shtml';
   }


if ($VERB eq 'REPORTS') {
	require BATCHJOB;
	$GTOOLS::TAG{'<!-- GUID -->'} = &BATCHJOB::make_guid();
	$template_file = 'reports.shtml';
	push @BC, { name=>"Reports" };
	}

#if ($VERB eq '') {
#	my $profref = &DOMAIN::TOOLS::syndication_profiles($USERNAME);
#	my $c = '';
#	my $cnt = 0;
#	foreach my $ns (sort keys %{$profref}) {
#		my $class = ($cnt++%2)?'r0':'r1';
#		$c .= "<tr><td colspan=3 class=\"$class\"><b>$ns =&gt; $profref->{$ns}</td></tr>";		
#		my ($s) = SYNDICATION->new($USERNAME,$ns,'ESS');
#		$c .= "<tr><td class=\"$class\">Status: ".$s->statustxt()."<br><br></td>";
#		$c .= qq~
#<td class="$class">
#		<input type="button" onClick="document.location='index.cgi?VERB=EDIT&PROFILE=$ns';" class="button" value=" Edit ">
#		<input type="button" onClick="document.location='index.cgi?VERB=UPDATENOW&PROFILE=$ns';" class="button" value="Update Now">
#		<input type="button" onClick="document.location='index.cgi?VERB=CHECKSTATUS&PROFILE=$ns';" class="button" value="Check Status">
#</td>
#		~;
#		$c .= "</tr>";
#		}
#	$GTOOLS::TAG{'<!-- PROFILES -->'} = $c;
#	$template_file = 'index.shtml';
#	push @BC, { name=>"Select Profile" };
#	}





&GTOOLS::output(
   'title'=>'eBay Stores Syndication',
   'file'=>$template_file,
   'header'=>'1',
   'help'=>'#50380',
   'tabs'=>\@TABS,
   'bc'=>\@BC,
   );

&DBINFO::db_zoovy_close();

