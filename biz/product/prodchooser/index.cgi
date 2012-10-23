#!/usr/bin/perl

use lib "/httpd/modules";
use ZOOVY;
use GTOOLS;
use CGI;

my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("/biz/setup",2,'_P&2');
if ($USERNAME eq '') { exit; }

$GTOOLS::TAG{'<!-- SAVETO -->'} = $ZOOVY::cgiv->{'SAVETO'};
$GTOOLS::TAG{'<!-- CURRENTLY -->'} = $ZOOVY::cgiv->{'CURRENTLY'};

%products = &ZOOVY::fetchproducts_by_name($USERNAME);
%checked = ();
foreach $prod (split(',',$ZOOVY::cgiv->{'CURRENTLY'})) {
	$checked{$prod}++;
	}

$c = '';
foreach $prod (sort keys %products) {
	if (defined($checked{$prod})) { $checkthis = ' checked '; } else { $checkthis = ''; }
	$c .= " <input type='checkbox' $checkthis name='*PROD-$prod'> $prod $products{$prod}<br>\n";
	}
$GTOOLS::TAG{'<!-- PRODLIST -->'} = $c;

&GTOOLS::print_form('','index.shtml',1);


