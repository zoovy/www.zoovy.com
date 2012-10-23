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

my ($PROFILE) = &ZWEBSITE::prt_get_profile($USERNAME,$PRT);
my $PROVIDER = $ZOOVY::cgiv->{'PROVIDER'};

$GTOOLS::TAG{'<!-- PROFILE -->'} = $PROFILE;
$GTOOLS::TAG{'<!-- PROVIDER -->'} = $PROVIDER;

my ($DOMAIN) = &DOMAIN::TOOLS::domain_for_prt($USERNAME,$PRT);
$GTOOLS::TAG{'<!-- DOMAIN -->'} = $DOMAIN;

my ($so) = SYNDICATION->new($USERNAME,$PROFILE,$PROVIDER);
tie my %s, 'SYNDICATION', THIS=>$so;
# $c .= "<tr><td class=\"$class\">Status: ".$s->statustxt()."<br><br></td></tr>";

my $template_file = 'index.shtml';
if ($FLAGS !~ /,XSELL,/) {
	$template_file = 'deny.shtml';
	}

my @TABS = ();

my @BC = (
      { name=>'Syndication',link=>'http://www.zoovy.com/biz/syndication','target'=>'_top', },
		);

my $INFO = $SYNDICATION::PROVIDERS{$PROVIDER};

push @BC, { name=>$INFO->{'title'}, link=>"http://www.zoovy.com/biz/syndication/provider/index.cgi?PROVIDER=$PROVIDER",'target'=>'_top', };
push @BC, { name=>'Profile: '.$PROFILE };
push @BC, { name=>'Domain: '.$DOMAIN };

push @TABS, { selected=>($VERB eq 'EDIT')?1:0, 'name'=>'Config', 'link'=>"index.cgi?VERB=EDIT&PROVIDER=$PROVIDER&PROFILE=$PROFILE" };
push @TABS, { selected=>($VERB eq 'LOGS')?1:0, 'name'=>'Logs', 'link'=>"index.cgi?VERB=LOGS&PROVIDER=$PROVIDER&PROFILE=$PROFILE" };
# push @TABS, { selected=>($VERB eq 'CATEGORIES')?1:0, 'name'=>'Categories', 'link'=>"index.cgi?VERB=CATEGORIES&PROVIDER=$PROVIDER&PROFILE=$PROFILE" };


if ($VERB eq 'SAVE') {
	if ($PROVIDER eq 'BYS') {
		## BUYSAFE 
		}
	elsif ($PROVIDER eq 'PRV') {
		## POWERREVIEWS
		}


#	$s{'.cjcid'} = $ZOOVY::cgiv->{'cjcid'};
#	$s{'.cjaid'} = $ZOOVY::cgiv->{'cjaid'};
#	$s{'.cjsubid'} = $ZOOVY::cgiv->{'cjsubid'};
#	$s{'.host'} = $ZOOVY::cgiv->{'host'};
#	$s{'.user'} = $ZOOVY::cgiv->{'user'};
#	$s{'.pass'} = $ZOOVY::cgiv->{'pass'};
#	$s{'.schedule'} = undef;
   if ($FLAGS =~ /,WS,/) {
		$s{'.schedule'} = $ZOOVY::cgiv->{'SCHEDULE'};
      }

	my $ERROR = '';
#	if ($ERROR eq '' && $s{'.cjcid'} eq '') { $ERROR = "CJ Customer ID is required"; }
#	if ($ERROR eq '' && $s{'.cjaid'} eq '') { $ERROR = "CJ Ad ID is required"; }
#	if ($ERROR eq '' && $s{'.cjsubid'} eq '') { $ERROR = "CJ Subscription ID is required"; }
#	if ($ERROR eq '' && $s{'.host'} eq '') { $ERROR = "CJ FTP Host is required"; }
#	if ($ERROR eq '' && $s{'.user'} eq '') { $ERROR = "CJ FTP username is required"; }
#	if ($ERROR eq '' && $s{'.pass'} eq '') { $ERROR = "CJ FTP password is required"; }

	if ($ERROR ne '') {
		$GTOOLS::TAG{'<!-- ERROR -->'} = "<font color='red'>$ERROR</font>";
		}
	else {
		$s{'IS_ACTIVE'} = 1;
		$so->save();
#		&ZOOVY::savemerchantns_attrib($USERNAME,$PROFILE,"$provider:mid",$s{'.cjcid'});
#		&ZWEBSITE::save_website_attrib($USERNAME,'cj',$^T);
		}

	$VERB  = 'EDIT';
	}


#if ($VERB eq 'SAVE-CATEGORIES') {
#	my ($so) = SYNDICATION->new($USERNAME,$PROFILE,'CJ');
#	my ($DOMAIN,$ROOTPATH) = $so->syn_info();
#
#	my ($NC) = NAVCAT->new($USERNAME);
#	foreach my $safe (sort $NC->paths($ROOTPATH)) {
#		my ($pretty, $children, $productstr, $sortby, $metaref) = $NC->get($safe);
#
#		$metaref->{'CJ'} = (defined $ZOOVY::cgiv->{'navcat-'.$safe})?1:0;
#		$NC->set($safe,metaref=>$metaref);
#		}
#	$NC->save();
#	undef $NC;
#	$GTOOLS::TAG{'<!-- MSG -->'} = "<font color='blue'>Successfully saved cj categories.</font><br>";
#	$VERB = 'CATEGORIES';
#	}


if ($VERB eq '') {
	$VERB = 'EDIT'; 
	}

#	my $profref = &DOMAIN::TOOLS::syndication_profiles($USERNAME);
#	my $c = '';
#	my $cnt = 0;
#	foreach my $ns (sort keys %{$profref}) {
#		my $class = ($cnt++%2)?'r0':'r1';
#		$c .= "<tr><td class=\"$class\"><b>$ns =&gt; $profref->{$ns} (<a href=\"index.cgi?VERB=EDIT&PROFILE=$ns\">EDIT</a>)</td></tr>";		
#		my ($s) = SYNDICATION->new($USERNAME,$ns,'CJ');
#		$c .= "<tr><td class=\"$class\">Status: ".$s->statustxt()."<br><br></td></tr>";
#		}
#	$GTOOLS::TAG{'<!-- PROFILES -->'} = $c;
#	$template_file = 'index.shtml';
#	}


if ($VERB eq 'LOGS') {
   $GTOOLS::TAG{'<!-- LOGS -->'} = $so->summarylog();
   $template_file = '_/syndication-logs.shtml';
   }

if ($VERB eq 'EDIT') {
	my ($DOMAIN,$ROOTPATH) = $so->syn_info();
	tie my %s, 'SYNDICATION', THIS=>$so;

#	$GTOOLS::TAG{'<!-- CJCID -->'} = $s{'.cjcid'};
#	$GTOOLS::TAG{'<!-- CJAID -->'} = $s{'.cjaid'};
#	$GTOOLS::TAG{'<!-- CJSUBID -->'} = $s{'.cjsubid'};
#	$GTOOLS::TAG{'<!-- USER -->'} = $s{'.user'};
#	$GTOOLS::TAG{'<!-- PASS -->'} = $s{'.pass'};
#	$GTOOLS::TAG{'<!-- HOST -->'} = $s{'.host'};
	$GTOOLS::TAG{'<!-- STATUS -->'} = $so->statustxt();
#	$GTOOLS::TAG{'<!-- FILENAME -->'} = "http://static.zoovy.com/merchant/$USERNAME/$PROFILE.xml";

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


	$template_file = 'index.shtml';
	}


#if ($VERB eq 'CATEGORIES') {
#
#	require SYNDICATION::CATEGORIES;
#	my ($CDS) = SYNDICATION::CATEGORIES::CDSLoad('CJ');
#
#	my ($so) = SYNDICATION->new($USERNAME,$PROFILE,'CJ');
#	my $PROFILE = $ZOOVY::cgiv->{'PROFILE'};
#	my ($DOMAIN,$ROOTPATH) = $so->syn_info();
#
#	my $c = '';
#	my $NC = NAVCAT->new($USERNAME);
#
#	my ($cdsflat) = SYNDICATION::CATEGORIES::CDSFlatten($CDS);
#
#	foreach my $safe (sort $NC->paths($ROOTPATH)) {
#		next if (substr($safe,0,1) eq '*');
#		next if ($safe eq '');
#		my ($pretty, $children, $productstr, $sortby, $metaref) = $NC->get($safe);
#		next if (substr($pretty,0,1) eq '!');
#	
#		my $name = ''; 
#		if ($pretty eq '') { $pretty = "UN-NAMED: $safe"; }
#		if (substr($safe,0,1) eq '.') {
#			foreach (split(/\./,substr($safe,1))) { $name .= "&nbsp; - &nbsp; "; } $name .= $pretty;
#			if ($safe eq '.') { $name = 'HOMEPAGE'; }
#			}
#		elsif (substr($safe,0,1) eq '$') {
#			$name = "LIST: ".$pretty;
#			}
#
#		my $val = $metaref->{'CJ'};
#		if ((not defined $val) || ($val == 0)) { $val = 0; }
#		$c .= "<tr>";
#
#		my $checked = ($val)?'checked':'';
#		$c .= qq~<td nowrap><input $checked type="checkbox" name="navcat-$safe"></td>~;
#		$c .= "<td nowrap>$name</td>";
#
#
#		$c .= qq~<td nowrap><span id="txt!navcat-$safe">$pretty</span></td>~;
#		$c .= "</tr>\n";
#		}
#	if	($c eq '') { $c = '<tr><td><i>No website categories exist??</i></td></tr>'; }
#	$GTOOLS::TAG{'<!-- CATEGORIES -->'} = $c;
#
#	$template_file = 'categories.shtml';
#	}
#
&GTOOLS::output(
   'title'=>"$PROVIDER Product Syndication",
   'file'=>$template_file,
	'head'=>qq~<script language="JavaScript1.2" type="text/javascript" src="/biz/syndication/fastlookup.js"></script>~,
   'header'=>'1',
	'js'=>1+2,
   'help'=>'#51002',
   'tabs'=>\@TABS,
   'bc'=>\@BC,
   );

&DBINFO::db_zoovy_close();

