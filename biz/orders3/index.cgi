#!/usr/bin/perl


use lib "/httpd/modules";
use GTOOLS;
require ZOOVY;
require AUTH;


# gotta run init so we read in the cookies
&ZOOVY::init();
&GTOOLS::init();

if ($ZOOVY::cookies->{'zjsid'} ne '') {
	&AUTH::fake_setup_global_vars($ZOOVY::cookies->{'zjsid'});
	print STDERR "ZOOVY::USER: $ZOOVY::USERNAME\n";
	# $ZOOVY::USERNAME = $ZOOVY::cookies->{'zjsid'};
	print STDERR "ZOOVY SESSIN: $ZOOVY::cookies->{'zjsid'}\n";
	}

&GTOOLS::output(file=>'index.shtml',jquery=>1,zmvc=>1,header=>1);

