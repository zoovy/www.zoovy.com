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

$GTOOLS::TAG{'<!-- PROFILE -->'} = $PROFILE;

my $template_file = 'index.shtml';
if ($FLAGS !~ /,XSELL,/) {
	$template_file = 'deny.shtml';
	}

my @TABS = ();


my @BC = (
      { name=>'Syndication',link=>'http://www.zoovy.com/biz/syndication','target'=>'_top', },
      { name=>'Custom Feeds',link=>'http://www.zoovy.com/biz/syndication/custom','target'=>'_top', },
		);



if ($VERB eq 'CREATE') {
	my ($ID) = $ZOOVY::cgiv->{'log-id'};
	my $map = $ZOOVY::cgiv->{'data-map'};
	my $url = $ZOOVY::cgiv->{'data-url'};
	

	my ($PROFILE) = &ZWEBSITE::prt_get_profile($USERNAME,$PRT);
	my ($so) = SYNDICATION->new($USERNAME,$PROFILE,$ID);
	tie my %s, 'SYNDICATION', THIS=>$so;
	$s{'.title'} = $ZOOVY::cgiv->{'feed-title'};
	$s{'.map'} =  $ZOOVY::cgiv->{'data-map'};
	$s{'.url'} = $ZOOVY::cgiv->{'data-url'};
	$s{'IS_ACTIVE'}=time();
	untie %s;
	$so->save();
	$VERB = '';
	}


if ($VERB eq 'DELETE') {
	my ($ID) = $ZOOVY::cgiv->{'ID'};
	my ($so) = SYNDICATION->new($USERNAME,$PROFILE,$ID);
	$so->nuke();	
	$VERB = '';
	}

if ($VERB eq '') {
	$GTOOLS::TAG{'<!-- PROFILE -->'} = $PROFILE;

	my $c = '';
	my $cnt = 0;
	foreach my $id (1..9) {
		$id = sprintf("C%02d",$id);
		my ($so) = SYNDICATION->new($USERNAME,$PROFILE,$id);
		next if (not $so->{'IS_ACTIVE'});		
		my $title = $so->get('.title');
		my $map = $so->get('.map');
		my $url = $so->get('.url');

		my ($datafile) = $so->filename();

		my $class = ($cnt++%2)?'r0':'r1';
		$c .= "<tr>";
		$c .= "<td valign=top class=\"$class\"><a href='/biz/syndication/custom/index.cgi?VERB=DELETE&ID=$id'>[DEL]</a></td>";		
		$c .= "<td valign=top class=\"$class\">$id</td>";		
		$c .= "<td valign=top class=\"$class\">";
		$c .= "<b>$title</b><br>MAP: $map<br>URL: $url<br>";
		$c .= "<a href=\"http://static.zoovy.com/merchant/$USERNAME/$datafile\">$datafile</a><br>";
		$c .= "Status: ".$so->statustxt()."</td>";
		$c .= "</tr>";
		}
	if ($c eq '') { $c = "<tr><td><i>No custom syndications defined.</i></td></tr>"; }
	$GTOOLS::TAG{'<!-- EXISTING -->'} = $c;

	$template_file = 'index.shtml';
	}


if ($PROFILE ne '') {
	push @TABS, { selected=>($VERB eq 'EDIT')?1:0, 'name'=>'Config', 'link'=>'/biz/syndication/custom/index.cgi?VERB=EDIT&PROFILE='.$PROFILE };
#	push @TABS, { selected=>($VERB eq 'CATEGORIES')?1:0, 'name'=>'Categories', 'link'=>'/biz/syndication/custom/index.cgi?VERB=CATEGORIES&PROFILE='.$PROFILE };
	push @BC, { name=>'Profile: '.$PROFILE };
#	push @BC, { name=>($VERB eq 'EDIT')?'Config':'Categories' };
	}





&GTOOLS::output('*LU'=>$LU,
   'title'=>'Custom Syndication',
   'file'=>$template_file,
	'head'=>qq~<script language="JavaScript1.2" type="text/javascript" src="/biz/syndication/fastlookup.js"></script>~,
   'header'=>'1',
	'js'=>1+2,
   'help'=>'#51002',
   'tabs'=>\@TABS,
   'bc'=>\@BC,
   );

&DBINFO::db_zoovy_close();

