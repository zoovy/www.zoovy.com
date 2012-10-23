#!/usr/bin/perl

#
# http://www.zoovy.com/webapi/worldpac/hack.cgi/USERNAME=autoparts/v=1?
#
# http://catalog.eautopartscatalog.com/default/add?year=1992&make=VO&makeText=Volvo 
# &model=240--004&modelText=240&category=G1&categoryText=Radiator&product=8601127
# &productText=Radiator%26nbsp%3BAlum%2FPlastic&brand=VAL&brandText=Valeo&available=21
# &list=301.49&price=132.01&core=0.00&ships=0&application=000279429
# &catalogProduct=8601127&weight=14.35&partnerSession=null
#

use CGI;
use Data::Dumper;
use URI::Escape;

# print STDERR Dumper(\%ENV);
$q = new CGI;

$uri = $ENV{'REQUEST_URI'}.'/';
my $username = 'www';
if ($uri =~ /\/USERNAME\=(.*?)[\/\?]./) {
	$username = $1;
	}

$parameters = '';

$desc = '';
if ($q->param('brandText') ne '') { $desc .= $q->param('brandText').' '; }
if ($q->param('year') ne '') { $desc .= $q->param('year').' '; }
if ($q->param('core') ne '') { $core .= $q->param('core').' '; }
if ($q->param('makeText') ne '') { $desc .= $q->param('makeText').' '; }
if ($q->param('categoryText') ne '') { $desc .= $q->param('categoryText').' '; }
if ($q->param('productText') ne '') { $desc .= $q->param('productText').' '; }
if ($q->param('available')>0) {
	$desc .= " - ".$q->param('available')." in stock ";
	}
if ($q->param('ships')>0) {
	$desc .= "ships in ".$q->param('ships')." days ";
	}
# strip the trailing space
if (substr($desc,-1) eq ' ') { $desc = substr($desc,0,-1); }
# what the fuck - they actually encode this stuff??
$desc =~ s/&nbsp;/ /igs;

$price = $q->param('price');
# what the fuck is core ??
# what the fuck is ships
# what the fuck is avpplication
$weight = $q->param('weight').'#';
$weight = uri_escape($weight);
$qty = 1;
$product = 'WP-'.$q->param('catalogProduct');

if (not defined $qty) { $qty = 1; }
$qty = uri_escape($qty);

$product = uri_escape($product);


$price =~ s/[^\d\.]+//igs;
if (defined $core) {
	$core =~ s/[^\d\.]+//igs;
	$price += $core; 
	$desc .= " [includes \$".sprintf("%.2f",$core)." core charge]";	
	}
$price = uri_escape($price);
$desc = uri_escape($desc);


$parameters = "desc=$desc&qty=$qty&weight=$weight&price=$price&taxable=1&product_id=$product";



print "Location: http://$username.zoovy.com/cart.cgis?$parameters\n\n";

