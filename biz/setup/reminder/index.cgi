#!/usr/bin/perl

use lib "/httpd/modules";
use GTOOLS;
use ZOOVY;
use CGI;
use ZWEBSITE;


my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("/biz/setup",2,'_S&8');
if ($USERNAME eq '') { exit; }
if ($FLAGS =~ /,L1,/) { $FLAGS .= ',EBAY,'; }


$template_file = 'index.shtml';
if ($FLAGS !~ /,EBAY,/) {
	$template_file = 'deny.shtml';
	}

$q = new CGI;
$ACTION = $q->param('ACTION');

%webdb = &ZWEBSITE::fetch_website_db($USERNAME);
if ($ACTION eq 'SAVE')
	{
	if (defined($q->param('auto_feedback')))
		{
		$webdb{'auto_feedback'} = 1;
		} else {
		$webdb{'auto_feedback'} = 0;
		}
	$webdb{'auto_ext_freq'} = $q->param('auto_ext_freq');
	if (defined($q->param('auto_feedback_suppress')))
		{
		$webdb{'auto_feedback_suppress'} = 1;
		} else {
		$webdb{'auto_feedback_suppress'} = 0;
		}
	&ZWEBSITE::save_website_db($USERNAME,\%webdb);
	$GTOOLS::TAG{"<!-- MESSAGE -->"} = '<font color="red">Changes Saved.</font>'; 
	}


if (!defined($webdb{'auto_ext_freq'})) { $webdb{'auto_ext_freq'} = 0; }
$GTOOLS::TAG{'<!-- AEF0 -->'} = '';
$GTOOLS::TAG{'<!-- AEF1 -->'} = '';
$GTOOLS::TAG{'<!-- AEF2 -->'} = '';
$GTOOLS::TAG{'<!-- AEF3 -->'} = '';
$GTOOLS::TAG{'<!-- AEF7 -->'} = '';
$GTOOLS::TAG{'<!-- AEF'.$webdb{'auto_ext_freq'}.' -->'} = ' SELECTED ';
if ($webdb{'auto_feedback_suppress'})
	{
	$GTOOLS::TAG{'<!-- AFS_CHECKED -->'} = 'CHECKED';
	} else {
	$GTOOLS::TAG{'<!-- AFS_CHECKED -->'} = '';
	}

if ($webdb{'auto_feedback'})
	{
	$GTOOLS::TAG{'<!-- AUTO_FEEDBACK -->'} = 'CHECKED';
	} else {
	$GTOOLS::TAG{'<!-- AUTO_FEEDBACK -->'} = '';
	}


#$GTOOLS::TAG{'<!-- MESSAGE -->'} = &ZOOVY::incode($webdb{'auto_ext_freq'});
&GTOOLS::output(
   'title'=>'Setup : Automation Settings',
   'file'=>$template_file,
   'header'=>'1',
   'help'=>'#50347',
   'tabs'=>[
      ],
   'bc'=>[
      { name=>'Setup',link=>'http://www.zoovy.com/biz/setup','target'=>'_top', },
      { name=>'Automation',link=>'http://www.zoovy.com/biz/setup/reminder','target'=>'_top', },
      ],
   );



