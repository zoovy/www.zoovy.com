#!/usr/bin/perl

use lib "/httpd/modules";
require GTOOLS;
require ZOOVY;
use strict;

&ZOOVY::init();
&GTOOLS::init();

if ($ZOOVY::cookies->{'zjsid'} ne '') {
	require AUTH;
	&AUTH::fake_setup_global_vars($ZOOVY::cookies->{'zjsid'});
	print STDERR "ZOOVY::USER: $ZOOVY::USERNAME\n";
	# $ZOOVY::USERNAME = $ZOOVY::cookies->{'zjsid'};
	print STDERR "ZOOVY SESSIN: $ZOOVY::cookies->{'zjsid'}\n";
	}


# print "Content-type: text/html\n\n";
&GTOOLS::output(
   'title'=>'Batch Channel Editor',
   'html'=>qq~
<html>
<!-- PRODUCT_TAB -->
</html>
~,
   'header'=>'1',
   'help'=>'#50317',
   'bc'=>[
      { name=>'Product Editor',link=>'http://www.zoovy.com/biz/product','target'=>'_top', },
      ],
	'tabs'=>[
		{ name=>'New Product',link=>'edit.cgi?VERB=CREATE','target'=>'text', },		
		{ name=>'Find',link=>'search.cgi','target'=>'text', },	
		{ name=>'List Products',link=>'listall.cgi?ACTION=LISTALL','target'=>'text', },		]
   );


