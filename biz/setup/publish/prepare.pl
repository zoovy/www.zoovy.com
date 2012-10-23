#!/usr/bin/perl

$USERNAME = 'nerdgear';

use lib "/httpd/modules";
require NAVCAT;
&NAVCAT::init();

@urls = ();


# first add the homepage, and other misc urls
push @urls, 'http://'.$USERNAME.'.zoovy.com';

# now lets pull the list of categories
@cats = &NAVCAT::fetch_navcat_fulllist($USERNAME,1);
foreach $cat (@cats) {
	next if ($cat eq '.');
	next if (substr($cat,0,1) eq '*');
	$cat = substr($cat,1);
	push @urls, "http://$USERNAME.zoovy.com/category/$cat";
 	}

# now lets do a list of products
@prods = &ZOOVY::fetchproduct_list_by_merchant($USERNAME);
foreach $prod (@prods) {
	push @urls, "http://$USERNAME.zoovy.com/product/$prod";
	}

use Data::Dumper;
print Dumper(\@urls);
