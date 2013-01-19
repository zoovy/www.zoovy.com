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

my @TABS = ();


my @BC = (
      { name=>'Syndication',link=>'http://www.zoovy.com/biz/syndication','target'=>'_top', },
      { name=>'eBates.com',link=>'http://www.zoovy.com/biz/syndication/ebates','target'=>'_top', },
		);

if ($VERB eq 'SAVE') {

	my ($so) = SYNDICATION->new($USERNAME,$PROFILE,'EBT');
	tie my %s, 'SYNDICATION', THIS=>$so;
	$s{'IS_ACTIVE'}++;
	$so->save();

	$VERB  = 'EDIT';
	}





#if ($VERB eq 'SAVE-CATEGORIES') {
#	my ($so) = SYNDICATION->new($USERNAME,$PROFILE,'BUY');
#	my ($DOMAIN,$ROOTPATH) = $so->syn_info();
#
#	my ($NC) = NAVCAT->new($USERNAME);
#	foreach my $safe (sort $NC->paths($ROOTPATH)) {
#		my ($pretty, $children, $productstr, $sortby, $metaref) = $NC->get($safe);
#		#my $SUBMIT = ($q->param('navcat-'.$safe) eq 'on')?'1':'';
#		my $SUBMIT = ($ZOOVY::cgiv->{'navcat-'.$safe} ne '')?$ZOOVY::cgiv->{'navcat-'.$safe}:'';
#
#		next if ($SUBMIT eq '' || $SUBMIT eq '- Not Selected -');
#
#		$metaref->{'JELLYFISH'} = $SUBMIT;
#		$NC->set($safe,metaref=>$metaref);
#		}
#	$NC->save();
#	undef $NC;
#	$GTOOLS::TAG{'<!-- MSG -->'} = "<font color='blue'>Successfully saved jellyfish categories.</font><br>";
#	$VERB = 'CATEGORIES';
#	}


if ($VERB eq '') {
	my $profref = &DOMAIN::TOOLS::syndication_profiles($USERNAME,PRT=>$PRT);
	my $c = '';
	my $cnt = 0;
	foreach my $ns (sort keys %{$profref}) {
		my $class = ($cnt++%2)?'r0':'r1';
		$c .= "<tr><td class=\"$class\"><b>$ns =&gt; $profref->{$ns} (<a href=\"index.cgi?VERB=EDIT&PROFILE=$ns\">EDIT</a>)</td></tr>";		
		my ($s) = SYNDICATION->new($USERNAME,$ns,'BUY');
		$c .= "<tr><td class=\"$class\">Status: ".$s->statustxt()."<br><br></td></tr>";
		}
	$GTOOLS::TAG{'<!-- PROFILES -->'} = $c;
	$template_file = 'index.shtml';
	}


if ($PROFILE ne '') {
	push @TABS, { selected=>($VERB eq 'EDIT')?1:0, 'name'=>'Config', 'link'=>'index.cgi?VERB=EDIT&PROFILE='.$PROFILE };
	# push @TABS, { selected=>($VERB eq 'CATEGORIES')?1:0, 'name'=>'Categories', 'link'=>'index.cgi?VERB=CATEGORIES&PROFILE='.$PROFILE };
	push @BC, { name=>'Profile: '.$PROFILE };
	push @BC, { name=>($VERB eq 'EDIT')?'Config':'Categories' };
	}


if ($VERB eq 'EDIT') {
	my ($so) = SYNDICATION->new($USERNAME,$PROFILE,'BUY');
	my ($DOMAIN,$ROOTPATH) = $so->syn_info();
	tie my %s, 'SYNDICATION', THIS=>$so;

	$template_file = 'edit.shtml';
	}


&GTOOLS::output(
   'title'=>'eBates.com Syndication',
   'file'=>$template_file,
	'head'=>qq~<script language="JavaScript1.2" type="text/javascript" src="/biz/syndication/fastlookup.js"></script>~,
   'header'=>'1',
	'js'=>1+2,
   'help'=>'#50379',
   'tabs'=>\@TABS,
   'bc'=>\@BC,
   );

&DBINFO::db_zoovy_close();

