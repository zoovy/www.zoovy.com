#!/usr/bin/perl

use lib "/httpd/modules";
require LUSER;
require GTOOLS;

my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }


&GTOOLS::output(file=>'index.shtml',header=>1);
