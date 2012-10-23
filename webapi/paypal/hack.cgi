#!/usr/bin/perl

use CGI;
use Data::Dumper;
use URI::Escape;

# print STDERR Dumper(\%ENV);
$q = new CGI;

$uri = $ENV{'REQUEST_URI'}.'/';
my $username = 'www';
if ($uri =~ /\/USERNAME\=(.*?)[\/\?]+/)
{
	$username = $1;
}

$parameters = '';
if (defined $q->param('add'))
{
	$qty = $q->param('add');
	if (not defined $qty) { $qty = 1; }
	$qty = uri_escape($qty);

	$id = $q->param('item_number');
	if (not defined $id) { $id = '_'; }
	$id = uri_escape($id);

	$desc = $q->param('item_name');
	if (not defined $desc) { $desc = '_'; }
	$desc = uri_escape($desc);

	$amount = $q->param('amount');
	if (not defined $amount) { $amount = 0; }
	$amount =~ s/[^\d\.]+//igs;
	$amount = uri_escape($amount);

	$parameters = "desc=$desc&qty=$qty&price=$amount&taxable=1&product_id=$id";
}

print "Location: http://$username.zoovy.com/cart.cgis?$parameters\n\n";

