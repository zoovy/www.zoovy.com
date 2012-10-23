#!/usr/bin/perl

use lib "/httpd/modules";
use CGI;
use GTOOLS;
use ZOOVY;
use ZWEBSITE;

$q = new CGI;
require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_P&16');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

if (index($FLAGS,',L2,')>-1) { $FLAGS .= ',YAHOO,'; }

if ($FLAGS !~ /,YAHOO,/) {
	&GTOOLS::output(title=>'Yahoo Store Management',file=>'denied.shtml',header=>1);
	exit;
	}

$ACTION = uc($q->param('ACTION'));
%webdb = &ZWEBSITE::fetch_website_db($USERNAME);


if ($ACTION eq 'SAVEINVENTORY')
	{
	my $yahoo = '';
	if (defined($q->param('yahoo_sync'))) { $yahoo = '1,'; } else { $yahoo = '0,'; }
	$yahoo .= $q->param('yahoo_behavior');
	$webdb{'inv_yahoo'} = $yahoo; 
	&ZWEBSITE::save_website_db($USERNAME,\%webdb);
	$GTOOLS::TAG{"<!-- MESSAGE -->"} = "Successfully Saved Changes!<br>";
	}

if ($ACTION eq 'SAVEORDER')
	{
	if (not defined $q->param('yahoo_ordersync')) {
		$webdb{'yahoo_ordersync'} = '';
		} 
	else {
		my $c = $q->param('yorderpass');
		$c =~ s/\W+//g;
		my $yahoo_str = "1,$c,";
		if (defined $q->param('yahoo_createcustomer')) { $yahoo_str .= '1,'; } else { $yahoo_str .= '0,'; }
		if (defined $q->param('yahoo_optin')) { $yahoo_str .= '1,'; } else { $yahoo_str .= '0,'; }
		if (defined $q->param('yahoo_process')) { $yahoo_str .= '1,'; } else { $yahoo_str .= '0,'; }
		if (defined $q->param('yahoo_notify')) { $yahoo_str .= '1,'; } else { $yahoo_str .= '0,'; }		
		$yahoo_str .= $q->param('yahoo_orderid').',';

		$webdb{'yahoo_ordersync'} = $yahoo_str;
		}

	&ZWEBSITE::save_website_db($USERNAME,\%webdb);
	$GTOOLS::TAG{"<!-- MESSAGE -->"} = "Successfully Saved Changes!<br>";
	}

if ($ZOOVY::cgiv->{'VERB'} eq 'SHOWCATS') {
	
	require NAVCAT;
	$NC = NAVCAT->new($USERNAME,PRT=>$PRT);
	$c = qq~
<input type="button" onClick="expFrm.VERB.value=''; expFrm.action='index.cgi'; expFrm.submit();" value="Hide Categories"><br>
<input type="hidden" name="CATEGORIES" value="1">
~;
	foreach my $p (sort $NC->paths()) {
		$c .= "<input type='checkbox' name='CAT-$p'> $p<br>\n";
		}
	$c .= qq~
<br>
Important Note: When selecting categories you must select a date range from the list above (even if that date range is all products)
~;
	$GTOOLS::TAG{'<!-- CATEGORY -->'} = $c;
	}
else {
	$c = qq~
<input type="button" onClick="expFrm.VERB.value='SHOWCATS'; expFrm.action='index.cgi'; expFrm.submit();" value="Select Categories">
<input type='hidden' name='CATEGORIES' value='0'>
	~;

	$GTOOLS::TAG{'<!-- CATEGORY -->'} = $c;
	}

my ($yahoo_sync,$yahoo_behavior) = split(',',$webdb{'inv_yahoo'});
if ($yahoo_sync) { $GTOOLS::TAG{'<!-- YAHOO_SYNC -->'} = ' CHECKED '; }
else { $GTOOLS::TAG{'<!-- YAHOO_SYNC -->'} = ''; }
$GTOOLS::TAG{'<!-- YAHOO_ACTUAL -->'} = '';
$GTOOLS::TAG{'<!-- YAHOO_INFLATED -->'} = '';
$GTOOLS::TAG{'<!-- YAHOO_SAFE -->'} = '';
$GTOOLS::TAG{'<!-- YAHOO_'.uc($yahoo_behavior).' -->'} = ' SELECTED '; 

$GTOOLS::TAG{'<!-- YORDERCUSTOMER -->'} = '';
$GTOOLS::TAG{'<!-- YORDEROPTIN -->'} = '';
$GTOOLS::TAG{'<!-- YORDERPROCESS -->'} = '';
$GTOOLS::TAG{'<!-- YORDERNOTIFY -->'} = '';
$GTOOLS::TAG{'<!-- YAHOO_ORDERID_0 -->'} = '';
$GTOOLS::TAG{'<!-- YAHOO_ORDERID_1 -->'} = '';
$GTOOLS::TAG{'<!-- YAHOO_ORDERID_2 -->'} = '';

my ($yordersync,$yorderpass,$ycustomer,$yoptin,$yprocess,$ynotify,$yorderid) = split(',',&ZWEBSITE::fetch_website_attrib($USERNAME,'yahoo_ordersync'));
if ($yordersync)
	{
	$GTOOLS::TAG{'<!-- YORDERSYNC -->'} = 'CHECKED';
	$GTOOLS::TAG{'<!-- YORDERPASS -->'} = $yorderpass;
	$GTOOLS::TAG{'<!-- YAHOO_ORDERID_'.$yorderid.' -->'} = 'SELECTED';
	if ($ycustomer) { $GTOOLS::TAG{'<!-- YORDERCUSTOMER -->'} = ' CHECKED '; } 
	if ($yoptin) { $GTOOLS::TAG{'<!-- YORDEROPTIN -->'} = ' CHECKED '; } 
	if ($yprocess) { $GTOOLS::TAG{'<!-- YORDERPROCESS -->'} = ' CHECKED '; } 
	if ($ynotify) { $GTOOLS::TAG{'<!-- YORDERNOTIFY -->'} = ' CHECKED '; } 
	} else {
	$GTOOLS::TAG{'<!-- YORDERSYNC -->'} = '';
	$GTOOLS::TAG{'<!-- YORDERPASS -->'} = '';
	}

$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;

&GTOOLS::output(
   'title'=>'Yahoo Store Management',
   'file'=>'index.shtml',
   'header'=>'1',
   'help'=>'#50375',
   'tabs'=>[
      ],
   'bc'=>[
      { name=>'Syndication',link=>'http://www.zoovy.com/biz/syndication','target'=>'_top', },
      { name=>'Yahoo Store Management',link=>'http://www.zoovy.com/biz/syndication/yahoo','target'=>'_top', },
      ],
   );

exit;
