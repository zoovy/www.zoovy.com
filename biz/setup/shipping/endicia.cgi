#!/usr/bin/perl

use lib '/httpd/modules';
use CGI;
require GTOOLS;
require ZOOVY;
require ZWEBSITE;
use strict;



require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }


if ($FLAGS =~ /,L2,/) { $FLAGS .= ',BASIC,'; }

my $q = new CGI;

if (defined($q->param('MESSAGE'))) {
	$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<br><table border='2' width='80%' align='center'><tr><td><center><font color='red' size='4' face='helvetica'><b>" . $q->param('MESSAGE') . "</b></font></center></td></tr></table><br>";
	}

my @BC = ();
push @BC, { name=>'Setup',link=>'/biz/setup','target'=>'_top', };
push @BC, { name=>'Shipping',link=>'/biz/setup/shipping','target'=>'_top', };
push @BC, { name=>'Endicia' };

my $template_file = '';
my $ACTION = $q->param('ACTION');
if ($FLAGS =~ /,BASIC,/) {
	$GTOOLS::HEADER_IMAGE = '';
	$template_file    = 'endicia.shtml';
	}
else {
	$template_file = 'noaccess.shtml';
	}

my $webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);

if ($ACTION eq 'SAVE') {
	$webdbref->{'endicia_avs'}		= $q->param('ENDICIA_AVS') ? 1 : 0 ;
	$webdbref->{'endicia_serial'} = $q->param('ENDICIA_SERIAL');

	$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<br><table border='2' width='80%' align='center'><tr><td><center><font color='red' size='4' face='helvetica'><b>Saved!</b></font></center></td></tr></table><br>";
	$LU->log("SETUP.SHIPPING.ENDICIA","Saved Settings","SAVE");
	&ZWEBSITE::save_website_dbref($USERNAME, $webdbref,$PRT);
	}

## Domestic settings
$GTOOLS::TAG{'<!-- ENDICIA_AVS_CHECKED -->'}   = $webdbref->{'endicia_avs'} ? 'CHECKED' : '' ;
$GTOOLS::TAG{'<!-- ENDICIA_SERIAL -->'}   = $webdbref->{'endicia_serial'};

&GTOOLS::output('*LU'=>$LU,title=>'', file=>$template_file,header=>1,bc=>\@BC);

exit;

