#!/usr/bin/perl

use lib "/httpd/modules";
use GTOOLS;
use DBINFO;
use ZOOVY;
use ORDER;
use ORDER::BATCH;

&ZOOVY::init();
&GTOOLS::init();

my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("/biz/setup",2,'_O&1');
if ($USERNAME eq '') { exit; }

require BATCHJOB;
$GTOOLS::TAG{'<!-- GUID -->'} = &BATCHJOB::make_guid();

&GTOOLS::output(
   'title'=>'Order Archive Utility',
   'file'=>'index.shtml',
   'header'=>'1',
   'help'=>'#50485',
   'bc'=>[
      { name=>'Utilities',link=>'https://www.zoovy.com/biz/utilities','target'=>'_top', },
      { name=>'Order Archive Tool',link=>'','target'=>'_top', },
      ],
   );

