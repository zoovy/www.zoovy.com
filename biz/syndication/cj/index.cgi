#!/usr/bin/perl

#
#
#

use lib "/httpd/modules"; 
use CGI;
use GTOOLS;
use ZOOVY;
use ZWEBSITE;	
use ZTOOLKIT;
use DBINFO;
use NAVCAT;
use DOMAIN::TOOLS;
use SYNDICATION;

use strict;

my $dbh = &DBINFO::db_zoovy_connect();	
require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_P&16');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $VERB = $ZOOVY::cgiv->{'VERB'};
my $PROFILE = $ZOOVY::cgiv->{'PROFILE'};
$GTOOLS::TAG{'<!-- PROFILE -->'} = $PROFILE;

my $template_file = 'index.shtml';
if ($FLAGS !~ /,XSELL,/) {
	$template_file = 'deny.shtml';
	}

my $so = undef;
my $DOMAIN = undef;
my $ROOTPATH = undef;
if ($PROFILE ne '') {
	($so) = SYNDICATION->new($USERNAME,$PROFILE,'CJ');
	($DOMAIN,$ROOTPATH) = $so->syn_info();
	}
$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;
$GTOOLS::TAG{'<!-- PROFILE -->'} = $PROFILE;
$GTOOLS::TAG{'<!-- GUID -->'} = time();

my @TABS = ();
my @BC = (
      { name=>'Syndication',link=>'http://www.zoovy.com/biz/syndication','target'=>'_top', },
      { name=>'CommissionJunction',link=>'http://www.zoovy.com/biz/syndication/cj','target'=>'_top', },
		);

if ($VERB eq 'SAVE') {
	tie my %s, 'SYNDICATION', THIS=>$so;

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


	$s{'.cjcid'} = $ZOOVY::cgiv->{'cjcid'};
	$s{'.cjaid'} = $ZOOVY::cgiv->{'cjaid'};
	$s{'.cjsubid'} = $ZOOVY::cgiv->{'cjsubid'};
	$s{'.host'} = $ZOOVY::cgiv->{'host'};
	$s{'.user'} = $ZOOVY::cgiv->{'user'};
	$s{'.pass'} = $ZOOVY::cgiv->{'pass'};
	$s{'.schedule'} = undef;
   if ($FLAGS =~ /,WS,/) {
		$s{'.schedule'} = $ZOOVY::cgiv->{'SCHEDULE'};
      }

	my $ERROR = '';
	if ($ERROR eq '' && $s{'.cjcid'} eq '') { $ERROR = "CJ Customer ID is required"; }
	if ($ERROR eq '' && $s{'.cjaid'} eq '') { $ERROR = "CJ Ad ID is required"; }
	if ($ERROR eq '' && $s{'.cjsubid'} eq '') { $ERROR = "CJ Subscription ID is required"; }
	if ($ERROR eq '' && $s{'.host'} eq '') { $ERROR = "CJ FTP Host is required"; }
	if ($ERROR eq '' && $s{'.user'} eq '') { $ERROR = "CJ FTP username is required"; }
	if ($ERROR eq '' && $s{'.pass'} eq '') { $ERROR = "CJ FTP password is required"; }

	if ($ERROR ne '') {
		$GTOOLS::TAG{'<!-- ERROR -->'} = "<font color='red'>$ERROR</font>";
		}
	else {
		$s{'IS_ACTIVE'} = 1;
		$so->save();
		&ZOOVY::savemerchantns_attrib($USERNAME,$PROFILE,"cj:mid",$s{'.cjcid'});
		&ZWEBSITE::save_website_attrib($USERNAME,'cj',$^T);
		}

	$VERB  = 'EDIT';
	}





if ($VERB eq 'SAVE-CATEGORIES') {
	my ($DOMAIN,$ROOTPATH) = $so->syn_info();

	my ($NC) = NAVCAT->new($USERNAME,PRT=>$PRT);
	foreach my $safe (sort $NC->paths($ROOTPATH)) {
		my ($pretty, $children, $productstr, $sortby, $metaref) = $NC->get($safe);

		$metaref->{'CJ'} = (defined $ZOOVY::cgiv->{'navcat-'.$safe})?1:0;
		$NC->set($safe,metaref=>$metaref);
		}
	$NC->save();
	undef $NC;
	$GTOOLS::TAG{'<!-- MSG -->'} = "<font color='blue'>Successfully saved cj categories.</font><br>";
	$VERB = 'CATEGORIES';
	}


if ($VERB eq '') {
	my $profref = &DOMAIN::TOOLS::syndication_profiles($USERNAME,PRT=>$PRT);
	my $c = '';
	my $cnt = 0;
	my $ts = time();
	foreach my $ns (sort keys %{$profref}) {
		my $class = ($cnt++%2)?'r0':'r1';
		$c .= "<tr><td class=\"$class\"><b>$ns =&gt; $profref->{$ns}</td></tr>";		
		my ($s) = SYNDICATION->new($USERNAME,$ns,'CJ');
		$c .= "<tr><td class=\"$class\">Status: ".$s->statustxt()."<br>";
		$c .= " <a href=\"index.cgi?VERB=EDIT&PROFILE=$ns\">EDIT</a> | ";
		$c .= " <a href=\"/biz/batch/index.cgi?VERB=ADD&EXEC=SYNDICATION&DST=CJ&PROFILE=$ns&GUID=$ts\">PUBLISH</a>";
		$c .= "<br></td></tr>";
		}
	$GTOOLS::TAG{'<!-- PROFILES -->'} = $c;
	$template_file = 'index.shtml';
	}


if ($PROFILE ne '') {
	push @TABS,	{ name=>'Profile',selected=>($VERB eq '')?1:0, link=>'index.cgi' };
	push @TABS, { selected=>($VERB eq 'EDIT')?1:0, 'name'=>'Config', 'link'=>'index.cgi?VERB=EDIT&PROFILE='.$PROFILE };
	push @TABS, { selected=>($VERB eq 'CATEGORIES')?1:0, 'name'=>'Categories', 'link'=>'index.cgi?VERB=CATEGORIES&PROFILE='.$PROFILE };
	push @TABS, { name=>"Logs", selected=>($VERB eq 'LOGS')?1:0, link=>"?VERB=LOGS&PROFILE=$PROFILE", };
	push @TABS, { name=>"Diagnostics", selected=>($VERB eq 'DEBUG')?1:0, link=>"?VERB=DEBUG&PROFILE=$PROFILE", };
   push @TABS, { name=>'Webdoc',selected=>($VERB eq 'WEBDOC')?1:0, link=>"?VERB=WEBDOC&DOC=50593&PROFILE=$PROFILE", };
	push @BC, { name=>'Profile: '.$PROFILE };
	push @BC, { name=>($VERB eq 'EDIT')?'Config':'Categories' };
	}

if ($VERB eq 'WEBDOC') {
	$template_file = &GTOOLS::gimmewebdoc($LU,$ZOOVY::cgiv->{'DOC'});
	}

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


if ($VERB eq 'LOGS') {
	$GTOOLS::TAG{'<!-- LOGS -->'} = $so->summarylog();
	$template_file = '_/syndication-logs.shtml';
	}



if ($VERB eq 'EDIT') {
	my ($DOMAIN,$ROOTPATH) = $so->syn_info();
	tie my %s, 'SYNDICATION', THIS=>$so;

	$GTOOLS::TAG{'<!-- CJCID -->'} = $s{'.cjcid'};
	$GTOOLS::TAG{'<!-- CJAID -->'} = $s{'.cjaid'};
	$GTOOLS::TAG{'<!-- CJSUBID -->'} = $s{'.cjsubid'};
	$GTOOLS::TAG{'<!-- USER -->'} = $s{'.user'};
	$GTOOLS::TAG{'<!-- PASS -->'} = $s{'.pass'};
	$GTOOLS::TAG{'<!-- HOST -->'} = $s{'.host'};
	$GTOOLS::TAG{'<!-- STATUS -->'} = $so->statustxt();
	# $GTOOLS::TAG{'<!-- FILENAME -->'} = "http://static.zoovy.com/merchant/$USERNAME/$PROFILE-cj.xml";
	$GTOOLS::TAG{'<!-- VIEW_URL -->'} = $so->url_to_privatefile();

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


	$template_file = 'edit.shtml';
	}


if ($VERB eq 'CATEGORIES') {

	require SYNDICATION::CATEGORIES;
	my ($CDS) = SYNDICATION::CATEGORIES::CDSLoad('CJ');
	my $PROFILE = $ZOOVY::cgiv->{'PROFILE'};
	my ($DOMAIN,$ROOTPATH) = $so->syn_info();

	my $c = '';
	my $NC = NAVCAT->new($USERNAME,PRT=>$PRT);

	my ($cdsflat) = SYNDICATION::CATEGORIES::CDSFlatten($CDS);

	foreach my $safe (sort $NC->paths($ROOTPATH)) {
		next if (substr($safe,0,1) eq '*');
		next if ($safe eq '');
		my ($pretty, $children, $productstr, $sortby, $metaref) = $NC->get($safe);
		next if (substr($pretty,0,1) eq '!');
	
		my $name = ''; 
		if ($pretty eq '') { $pretty = "UN-NAMED: $safe"; }
		if (substr($safe,0,1) eq '.') {
			foreach (split(/\./,substr($safe,1))) { $name .= "&nbsp; - &nbsp; "; } $name .= $pretty;
			if ($safe eq '.') { $name = 'HOMEPAGE'; }
			}
		elsif (substr($safe,0,1) eq '$') {
			$name = "LIST: ".$pretty;
			}

		my $val = $metaref->{'CJ'};
		if ((not defined $val) || ($val == 0)) { $val = 0; }
		$c .= "<tr>";

		my $checked = ($val)?'checked':'';
		$c .= qq~<td nowrap><input $checked type="checkbox" name="navcat-$safe"></td>~;
		$c .= "<td nowrap>$name</td>";


		$c .= qq~<td nowrap><span id="txt!navcat-$safe">$pretty</span></td>~;
		$c .= "</tr>\n";
		}
	if	($c eq '') { $c = '<tr><td><i>No website categories exist??</i></td></tr>'; }
	$GTOOLS::TAG{'<!-- CATEGORIES -->'} = $c;

	$template_file = 'categories.shtml';
	}

&GTOOLS::output(
   'title'=>'CommissionJunction Product Syndication',
   'file'=>$template_file,
	'head'=>qq~<script language="JavaScript1.2" type="text/javascript" src="/biz/syndication/fastlookup.js"></script>~,
   'header'=>'1',
	'js'=>1+2,
   'help'=>'#51002',
   'tabs'=>\@TABS,
   'bc'=>\@BC,
   );

&DBINFO::db_zoovy_close();

