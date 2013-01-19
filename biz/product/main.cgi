#!/usr/bin/perl

use lib "/httpd/modules";
use GTOOLS;
use ZOOVY;

$template_file = "main.shtml";
my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("/biz/setup",2,'_P&2');
if ($USERNAME eq '') { exit; }

if (index($FLAGS,'LITE')!=-1) {
	$GTOOLS::TAG{'<!-- LITE_HIDE_ON -->'} = '<!--';
	$GTOOLS::TAG{'<!-- LITE_HIDE_OFF -->'} = '-->';
	}
&GTOOLS::output(title=>"",file=>$template_file,header=>1);
