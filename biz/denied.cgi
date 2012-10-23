#!/usr/bin/perl

use lib "/httpd/modules";
use ZOOVY;
use GTOOLS;

my ($MERCHANT,$FLAGS,$MID,$USERNAME,$RESELLER) = ZOOVY::authenticate("/biz/setup",2);

$GTOOLS::TAG{'<!-- REFERER -->'} = $ZOOVY::cgiv->{'URI'};
$GTOOLS::TAG{'<!-- NEED_FLAG -->'} = $ZOOVY::cgiv->{'NEEDED'};
$GTOOLS::TAG{'<!-- HAVE_FLAG -->'} = $FLAGS;
$GTOOLS::TAG{'<!-- HAVE_FLAG -->'} =~ s/,/, /gs;

%MAP= (
	'_ADMIN'=>'"Is Administrator" ',
	'_S&1'=>'Setup Full Access',
	'_S&2'=>'Setup Allow: Update Website',
	'_S&4'=>'Setup Allow: Manage Images',
	'_S&8'=>'Setup Allow: Payment/Shipping/Checkout',
	'_P&1'=>'Products: Grant Full Acces',
	'_P&2'=>'Products: Add/Update',
	'_P&4'=>'Products: Remove',
	'_P&8'=>'Products: Create Channels',
	'_M&1'=>'Manage: Grant Full Access',
	'_M&2'=>'Manage Allow: Reports',
	'_M&4'=>'Manage Allow: Channel Management',
	'_M&8'=>'Manage Allow: Customer Management',
	'_M&16'=>'Manage Allow: CSV Import/Export',
	'_O&1'=>'Orders Full Access',
	'_O&2'=>'Orders Allow: View Orders',
	'_O&4'=>'Orders Allow: Add/Update Invoices',
	'_O&8'=>'Orders Allow: View/Update Payment Detail',
	);

my $c = '';
foreach my $need (split(/\|/,$ZOOVY::cgiv->{'NEEDED'})) {
	$c .= "<tr><td>[$need] $MAP{$need} Functionality</td></tr>";
	}

if ($c eq '') {
	$c .= "<tr><td><i>Internal error: could not find correct flag in the access table. This is probably an internal error, please let support know.</i></td></tr>";
	}
$GTOOLS::TAG{'<!-- MAP -->'} = $c;

&GTOOLS::output(
	file=>'denied.shtml',
	header=>1,
	title=>'Access Denied',
	bc=>[ { name=>'Access Denied' } ]
	);


