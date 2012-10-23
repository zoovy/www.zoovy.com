#!/usr/bin/perl
use lib "/httpd/modules";
use ZOOVY;
use GT;
$USERNAME = 'satin';
($tsref,$catref) = &ZOOVY::build_prodinfo_refs($USERNAME);
@ar = keys %{$tsref};
print "SCALAR: ".scalar(@ar)."\n";
my $prodref = &ZOOVY::fetchproducts_into_hashref($USERNAME,\@ar);
@ar = keys %{$prodref};
print "SCALAR: ".scalar(@ar)."\n";



exit;


	$out = '';
	foreach $prod (keys %{$tsref}) {
#		next if ($prod !~ /product-(.*?)/);
#		$prod = substr($prod,8);
		print STDERR $prod."\n<br>";
		$buffer = &ZOOVY::fetchproduct_data($USERNAME,$prod);
		$hashref = &ZOOVY::attrib_handler_ref($buffer);

		$x = 1;
		while ( defined $hashref->{'zoovy:prod_image'.$x} ) { 
			if ($hashref->{'zoovy:prod_image'.$x} ne '') {
				$hashref->{'%IMGURL=zoovy:prod_image'.$x} = &GT::imageurl($USERNAME,$hashref->{'zoovy:prod_image'.$x});
				}
			delete $hashref->{'zoovy:prod_image'.$x}; 
			$x++;
			}
		if (defined $hashref->{'zoovy:prod_thumb'}) {
			$hashref->{'%IMGURL=zoovy:prod_thumb'} = &GT::imageurl($USERNAME,$hashref->{'zoovy:prod_thumb'}).'.jpg';
			delete $hashref->{'zoovy:prod_thumb'}; 
			}
		
		if (defined $ZOOVY::cgiv->{'CATEGORIES'}) {
			$hashref->{'%CATEGORY'} = $catref->{$prod};
			}
	
		if (defined $ZOOVY::cgiv->{'NAVCATS'}) {
			$count = 1;
			foreach $path (&NAVCAT::product_categories($USERNAME,$prod,1)) {
				$hashref->{'%CATEGORY'.($count++).'%'} = $path;
				}
			}

		}