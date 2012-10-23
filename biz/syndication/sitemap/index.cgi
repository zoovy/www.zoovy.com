#!/usr/bin/perl

use lib "/httpd/modules"; 
use CGI;
use strict;
require DOMAIN::TOOLS;
require GTOOLS;
require ZOOVY;
require ZWEBSITE;	
require ZTOOLKIT;
require DBINFO;
require SYNDICATION;

my $dbh = &DBINFO::db_zoovy_connect();	
require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_P&16');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $template_file = 'index.shtml';

my @BC = (
      { name=>'Syndication',link=>'http://www.zoovy.com/biz/syndication','target'=>'_top', },
      { name=>'Static Sitemap',link=>'http://www.zoovy.com/biz/syndication/sitemap','target'=>'_top', },
		);



## GOOGLEBASE_FEEDS
#+-------------+-------------+------+-----+---------------------+-------+
#| Field       | Type        | Null | Key | Default             | Extra |
#+-------------+-------------+------+-----+---------------------+-------+
#| ID          | int(11)     |      | PRI | 0                   |       |
#| USERNAME    | varchar(20) |      | UNI |                     |       |
#| CREATED     | datetime    |      |     | 0000-00-00 00:00:00 |       |
#| FTP_SERVER  | varchar(50) |      |     |                     |       |
#| FTP_USER    | varchar(20) |      |     |                     |       |
#| FTP_PASS    | varchar(20) |      |     |                     |       |
#| UPDATED_GMT | int(11)     |      |     | 0                   |       |
#+-------------+-------------+------+-----+---------------------+-------+
#7 rows in set (0.31 sec)

## GOOGLEBASE_LOG;
#+-------------+---------------------------+------+-----+---------+----------------+
#| Field       | Type                      | Null | Key | Default | Extra          |
#+-------------+---------------------------+------+-----+---------+----------------+
#| ID          | int(10) unsigned          | NO   | PRI | NULL    | auto_increment |
#| USERNAME    | varchar(20)               | NO   |     | NULL    |                |
#| DOMAIN      | varchar(150)              | NO   |     | NULL    |                |
#| MID         | int(10) unsigned          | NO   | MUL | 0       |                |
#| CREATED_GMT | int(10) unsigned          | NO   |     | 0       |                |
#| TYPE        | enum('INFO','WARN','ERR') | YES  |     | INFO    |                |
#| MESSAGE     | varchar(255)              | YES  |     | NULL    |                |
#+-------------+---------------------------+------+-----+---------+----------------+
#7 rows in set (0.00 sec)

my $q = undef;
my $VERB = $ZOOVY::cgiv->{'VERB'};

my $PROFILE = $ZOOVY::cgiv->{'PROFILE'};
$GTOOLS::TAG{'<!-- PROFILE -->'} = $PROFILE;
my $so = undef;
if ($PROFILE ne '') {
	($so) = SYNDICATION->new($USERNAME,$PROFILE,'GSM');
	}

if ($VERB eq 'SAVE') {

	tie my %s, 'SYNDICATION', THIS=>$so;

	$s{'.enable'} = (defined $ZOOVY::cgiv->{'enable'})?1:0;
	$s{'.strategy'} = $ZOOVY::cgiv->{'strategy'};

	my $ERROR = '';

	if ($ERROR ne '') {
		$GTOOLS::TAG{'<!-- ERROR -->'} = "<font color='red'>$ERROR</font>";
		}
	else {
		$s{'IS_ACTIVE'} = 1;
		$so->save();
		&ZWEBSITE::save_website_attrib($USERNAME,'googlesitemap',time());
		}
	
	$VERB = 'EDIT';
	}



if ($VERB eq '') {
	my $profref = &DOMAIN::TOOLS::syndication_profiles($USERNAME,PRT=>$PRT);
	my $c = '';
	my $cnt = 0;
	my $ts = time();
	foreach my $ns (sort keys %{$profref}) {
		my $class = ($cnt++%2)?'r0':'r1';
		$c .= "<tr>";
		$c .= "<td class=\"$class\"><b>$ns =&gt; $profref->{$ns}</b><br>";
		$c .= "<a href=\"index.cgi?VERB=EDIT&PROFILE=$ns\">EDIT</a>";
		$c .= " | ";
		$c .= "<a href=\"/biz/batch/index.cgi?VERB=ADD&EXEC=SYNDICATION&DST=GSM&FEEDTYPE=PRODUCTS&PROFILE=$ns&GUID=$ts\">PUBLISH</a>";
		$c .= "</td>";
		$c .= "</tr>";
		my ($s) = SYNDICATION->new($USERNAME,$ns,'GSM');
		$c .= "<tr><td class=\"$class\">Status: ".$s->statustxt()."<br><br></td></tr>";
		}
	$GTOOLS::TAG{'<!-- PROFILES -->'} = $c;
	$template_file = 'index.shtml';
	}



## top CONFIG page
if ($VERB eq 'EDIT') {

	tie my %s, 'SYNDICATION', THIS=>$so;

	$GTOOLS::TAG{'<!-- CHK_ENABLE -->'} = ($s{'.enable'})?'checked':'';

#	$GTOOLS::TAG{'<!-- STRATEGIES -->'} = '';
#	$GTOOLS::TAG{'<!-- STRATEGIES -->'} .= "<select name=\"strategy\">\n";
#	$GTOOLS::TAG{'<!-- STRATEGIES -->'} .= "<option ".(($s{'.strategy'} eq '')?'selected':'')." value=\"\">One monster file</option>";
#	$GTOOLS::TAG{'<!-- STRATEGIES -->'} .= "<option ".(($s{'.strategy'} eq 'navcats')?'selected':'')." value=\"navcats\">Index + one file per top level category</option>";
#	$GTOOLS::TAG{'<!-- STRATEGIES -->'} .= "<option ".(($s{'.strategy'} eq 'navcat-leafs')?'selected':'')." value=\"navcat-leafs\">Index + one file per leaf category</option>";
#	$GTOOLS::TAG{'<!-- STRATEGIES -->'} .= "</select>";

	$GTOOLS::TAG{'<!-- STATUS -->'} = $so->statustxt();

	push @BC, { name=>'Edit Profile: '.$PROFILE };
	$template_file = 'edit.shtml';
	}


&GTOOLS::output(
   'title'=>'GoogleSite Map Generation',
   'file'=>$template_file,
   'header'=>'1',
   'help'=>'#50396',
   'tabs'=>[
		{ name=>'Config',selected=>($VERB eq '')?1:0, link=>'index.cgi' },
      ],
   'bc'=>\@BC,
   );

&DBINFO::db_zoovy_close();
exit;
