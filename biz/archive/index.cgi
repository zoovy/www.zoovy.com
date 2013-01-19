#!/usr/bin/perl

use strict;
use lib "/httpd/modules";
require GTOOLS;
require ZOOVY;

my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("/biz/setup",2,undef);
if (index($FLAGS,'BASIC')==-1) { print "Location: /biz\n\n"; exit; }

my $ACTION = $ZOOVY::cgiv->{'ACTION'};
my $template_file = 'index.shtml';


&GTOOLS::output(
   'title'=>'Syndication',
   'file'=>$template_file,
   'header'=>'1',
   'help'=>'',
   'tabs'=>[
      ],
   'bc'=>[
      { name=>'Syndication',link=>'http://www.zoovy.com/biz/syndication','target'=>'_top', },
      ],
   );
