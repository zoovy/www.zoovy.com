#!/usr/bin/perl

use strict;
use CGI;
use lib "/httpd/modules";
require GTOOLS;
#require ORDER;
require CART2;
require ZOOVY;


my $q = new CGI;
my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("/biz/setup",2,'_O&4');
if ($USERNAME eq '') { exit; }

my $CMD = $q->param('CMD');
my $ID = $q->param('ID');
$GTOOLS::TAG{'<!-- ID -->'} = $ID;

my ($O2) = CART2->new_from_oid($USERNAME,$ID);


if ($CMD eq 'SAVE') {
	## removed check to see if 'notes' was ''
	## ie allow deletions - patti - 2007-01-15
	$O2->in_set('want/order_notes',$q->param('order_notes'));
	$O2->in_set('flow/private_notes',$q->param('private_notes'));
	$O2->order_save();
	&GTOOLS::output(file=>'close-popup.shtml',header=>1);
	}

if ($CMD eq '') {
	$GTOOLS::TAG{'<!-- ORDER_NOTES -->'} = &ZOOVY::incode($O2->in_get('want/order_notes'));
	$GTOOLS::TAG{'<!-- PRIVATE_NOTES -->'} = &ZOOVY::incode($O2->in_get('flow/private_notes'));

	&GTOOLS::output(file=>'notes.shtml',header=>1);
	}


