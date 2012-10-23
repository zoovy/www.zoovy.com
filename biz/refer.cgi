#!/usr/bin/perl

use lib "/httpd/modules";
use ZOOVY;
use GT;

&ZOOVY::init();
my ($MERCHANT) = &ZOOVY::authenticate();
$GT::TAG{'<!-- MERCHANT -->'} = $MERCHANT;
$GT::TAG{'<!-- YOURNAME -->'} = &ZOOVY::fetchmerchant_attrib($MERCHANT,'zoovy:firstname').' '.&ZOOVY::fetchmerchant_attrib($MERCHANT,'zoovy:lastname');

$template_file = 'refer.shtml';
if ($ZOOVY::cgiv->{'ACTION'} eq 'THANKS') {
	$template_file = 'refer-thanks.shtml';
	}

&GT::print_form('',$template_file,1);
