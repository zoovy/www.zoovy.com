#!/usr/bin/perl

use lib "/httpd/modules"; 
use CGI;
use GTOOLS;
use ZOOVY;
use ZWEBSITE;	
use ZTOOLKIT;
use DBINFO;
use NAVCAT;
use SYNDICATION;
use DOMAIN::TOOLS;
use strict;

my $dbh = &DBINFO::db_zoovy_connect();	
require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_P&16');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();

my $PROFILE = $ZOOVY::cgiv->{'PROFILE'};
my ($so) = SYNDICATION->new($USERNAME,$PROFILE,'IMS');
tie my %s, 'SYNDICATION', THIS=>$so;

my $VERB = $ZOOVY::cgiv->{'VERB'};

my @TABS = ();
if ($PROFILE ne '') {
	push @TABS,	{ name=>'Config',selected=>($VERB eq '')?1:0, link=>'/biz/syndication/imshopping/index.cgi' };
	push @TABS, { name=>'Edit',selected=>($VERB eq 'EDIT')?1:0, link=> "/biz/syndication/imshopping/index.cgi?VERB=EDIT&PROFILE=$PROFILE", };
#	push @TABS,	{ name=>"Categories", selected=>($VERB eq 'CATEGORIES')?1:0, link=>"?VERB=CATEGORIES&PROFILE=$PROFILE", };
	push @TABS,	{ name=>"Logs", selected=>($VERB eq 'LOGS')?1:0, link=>"/biz/syndication/imshopping/index.cgi?VERB=LOGS&PROFILE=$PROFILE", };
	push @TABS, { name=>"Diagnostics", selected=>($VERB eq 'DEBUG')?1:0, link=>"/biz/syndication/imshopping/index.cgi?VERB=DEBUG&PROFILE=$PROFILE", };
	push @TABS, { name=>'Webdoc',selected=>($VERB eq 'WEBDOC')?1:0, link=>"/biz/syndication/imshopping/index.cgi?VERB=WEBDOC&DOC=51488&PROFILE=$PROFILE", };

	}

		
my @BC = (
      { name=>'Syndication',link=>'http://www.zoovy.com/biz/syndication','target'=>'_top', },
      { name=>'Imshopping',link=>'http://www.zoovy.com/biz/syndication/imshopping','target'=>'_top', },
      );


my $template_file = 'index.shtml';
if ($FLAGS !~ /,XSELL,/) {
	$template_file = 'deny.shtml';
	}

my $q = undef;

if ($VERB eq 'DELETE') {
	$so->nuke();
	$VERB = '';
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



if ($VERB eq 'SAVE') {
	$s{'.user'} = $ZOOVY::cgiv->{'user'};
	$s{'.pass'} = $ZOOVY::cgiv->{'pass'};
	$s{'.ftp_dir'} = $ZOOVY::cgiv->{'ftp_dir'};

   my $qtSCHEDULE = "''";
   if ($FLAGS =~ /,WS,/) {
		$s{'.schedule'} = $ZOOVY::cgiv->{'SCHEDULE'};
      &ZWEBSITE::save_website_attrib($USERNAME,'bizrate_schedule',$s{'.schedule'});
      }


	my $changed = 0;

	&ZWEBSITE::save_website_attrib($USERNAME,'imshopping',time());

	$VERB = 'EDIT';
	}


if ($VERB eq 'EDIT') {
	my $PROFILE = $ZOOVY::cgiv->{'PROFILE'};
	$GTOOLS::TAG{'<!-- PROFILE -->'} = $PROFILE;
	push @BC, { name=>'Edit Profile: '.$PROFILE };


	$GTOOLS::TAG{'<!-- USER -->'} = $s{'.user'};
	$GTOOLS::TAG{'<!-- PASS -->'} = $s{'.pass'};
	$GTOOLS::TAG{'<!-- FTP_DIR -->'} = &ZOOVY::incode($s{'.ftp_dir'});

   $GTOOLS::TAG{'<!-- GUID -->'} = $so->guid();
   $GTOOLS::TAG{'<!-- VIEW_URL -->'} = $so->url_to_privatefile();

	$GTOOLS::TAG{'<!-- STATUS -->'} = $so->statustxt();
	$GTOOLS::TAG{'<!-- STATUS -->'} =~ s/\//<br>/g;


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


if ($VERB eq 'LOGS') {
   $GTOOLS::TAG{'<!-- LOGS -->'} = $so->summarylog();
   $template_file = '_/syndication-logs.shtml';
   }



if ($VERB eq 'WEBDOC') {
	$template_file = &GTOOLS::gimmewebdoc($LU,$ZOOVY::cgiv->{'DOC'});
	}

if ($VERB eq '') {
	my $profref = &DOMAIN::TOOLS::syndication_profiles($USERNAME,PRT=>$PRT);
	my $c = '';
	my $cnt = 0;
	my $ts = 0;
	foreach my $ns (sort keys %{$profref}) {
		my $class = ($cnt++%2)?'r0':'r1';
		$c .= "<tr>";
		$c .= "<td class=\"$class\"><b>$ns =&gt; $profref->{$ns}</b><br>";
		$c .= "<a href=\"/biz/syndication/imshopping/index.cgi?VERB=EDIT&PROFILE=$ns\">EDIT</a>";
		$c .= " | ";
		$c .= "<a href=\"/biz/batch/index.cgi?VERB=ADD&EXEC=SYNDICATION&DST=IMS&PROFILE=$ns&GUID=$ts\">PUBLISH</a>";
		$c .= "</td>";
		$c .= "</tr>";
		my ($s) = SYNDICATION->new($USERNAME,$ns,'IMS');
		$c .= "<tr><td class=\"$class\">Status: ".$s->statustxt()."<br><br></td></tr>";
		}
	$GTOOLS::TAG{'<!-- PROFILES -->'} = $c;
	$template_file = 'index.shtml';
	}



&GTOOLS::output(
   'title'=>'Imshopping Syndication',
   'file'=>$template_file,
   'header'=>'1',
   'help'=>'#51488',
   'tabs'=>\@TABS,
   'bc'=>\@BC,
   );

&DBINFO::db_zoovy_close();

