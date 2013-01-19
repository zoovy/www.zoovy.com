#!/usr/bin/perl

use lib "/httpd/modules";
use strict;
use lib "/httpd/modules";
require ZOOVY;
require ZTOOLKIT;
require GTOOLS;
require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_P&16');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;
$GTOOLS::TAG{'<!-- PRT -->'} = $PRT;

my $template_file = 'index.shtml';



&GTOOLS::output('*LU'=>$LU,file=>$template_file,header=>1);

