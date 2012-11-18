#!/usr/bin/perl

use strict;
use lib "/httpd/modules";
require GTOOLS;
require ZOOVY;
require AJAX::PANELS;
require PRODUCT::PANELS;
require LUSER;
require ZWEBSITE;
require INVENTORY;
require PRODUCT;

my $html = '';
my @ERRORS = ();

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_P&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $template_file = 'welcome.shtml';

&GTOOLS::output(file=>$template_file,html=>$html,header=>1,todo=>1,jquery=>1,zmvc=>1);
undef $LU;

exit;


