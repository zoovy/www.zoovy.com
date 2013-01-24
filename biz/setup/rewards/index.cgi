#!/usr/bin/perl

use lib "/httpd/modules";
use GTOOLS;
use ZOOVY;
use ZWEBSITE;
use ZTOOLKIT;
use strict;

my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("/biz/manage",2,undef);
if ($USERNAME eq '') { exit; }

my $template_file = 'index.shtml';
my $ACTION = $ZOOVY::cgiv->{'ACTION'};
if ($ACTION eq 'SAVE') {
	my %profile = ();
	$profile{'NAME'} = $ZOOVY::cgiv->{'NAME'};
	$profile{'STARTDATE'} = $ZOOVY::cgiv->{'STARTDATE'};
	$profile{'OPTIONS'} = 0;
	foreach my $i (1..6) {
		$profile{'OPTIONS'} += ((defined $ZOOVY::cgiv->{'opt_'.$i})?(1<<($i-1)):0)
		}
	$profile{'POINTS'} = 0;
	foreach my $i (1..6) {
		$profile{'POINTS'} += ((defined $ZOOVY::cgiv->{'points_'.$i})?(1<<($i-1)):0)
		}
	$profile{'POINTS1_INC'} = $ZOOVY::cgiv->{'points1_inc'};
	$profile{'POINTS2_INC'} = $ZOOVY::cgiv->{'points2_inc'};
	$profile{'POINTS2_BUMP'} = $ZOOVY::cgiv->{'points2_bump'};

	$profile{'BOUNTY_FREESHIP'} = $ZOOVY::cgiv->{'bounty_freeship'};
	foreach my $i (1..3) { 
		$profile{'BOUNTY'.$i.'_INC'} = $ZOOVY::cgiv->{'bounty'.$i.'_inc'}; 
		$profile{'BOUNTY'.$i.'_SUM'} = $ZOOVY::cgiv->{'bounty'.$i.'_sum'}; 
		}
	foreach my $i (11..13) { 
		$profile{'BOUNTY'.$i.'_INC'} = $ZOOVY::cgiv->{'bounty'.$i.'_inc'}; 
		$profile{'BOUNTY'.$i.'_DISC'} = $ZOOVY::cgiv->{'bounty'.$i.'_disc'}; 
		}		

	$profile{'EXPIRE'} = int($ZOOVY::cgiv->{'expire'});
	foreach my $i (1..3) { 
		$profile{'EXPIRE_OPTIONS'} += ((defined $ZOOVY::cgiv->{'expire_options'.$i})?(1<<($i-1)):0)
		}
	$profile{'EXPIRE_DAYS'} = $ZOOVY::cgiv->{'expire_days'};
	$profile{'EXPIRE_GRACEDAYS'} = $ZOOVY::cgiv->{'expire_gracedays'};
	$profile{'EXPIRE_DAILYLOSS'} = $ZOOVY::cgiv->{'expire_dailyloss'};
	$profile{'EXPIRE_MAXLIFE'} = $ZOOVY::cgiv->{'expire_maxlife'};
	$profile{'AUTO_EXPLAIN'} = (defined $ZOOVY::cgiv->{'auto_explain'})?1:0;

	my $profilestr = &ZTOOLKIT::buildparams(\%profile);
	print STDERR "profilestr: $profilestr\n";
	&ZWEBSITE::save_website_attrib($USERNAME,'rewards',$profilestr);

	&ZOOVY::savemerchant_attrib($USERNAME,'zoovy:about_rewards','');
	}


my $profilestr = &ZWEBSITE::fetch_website_attrib($USERNAME,'rewards');
my $params = &ZTOOLKIT::parseparams($profilestr);

## copy over all the high level variables
##		NAME, 
foreach my $k ('NAME','STARTDATE') {
	$GTOOLS::TAG{'<!-- '.$k.' -->'} = (defined $params->{$k})?$params->{$k}:'';
	}

if (not defined $params->{'OPTIONS'}) { $params->{'OPTIONS'} = 0; }
foreach my $i (1..6) {
	$GTOOLS::TAG{'<!-- OPTIONS'.$i.'_CHK -->'} = (($params->{'OPTIONS'}&(1<<($i-1)))>0)?'checked':'';
	}

if (not defined $params->{'POINTS'}) { $params->{'POINTS'} = 0; }
foreach my $i (1..4) {
	$GTOOLS::TAG{'<!-- POINTS'.$i.'_CHK -->'} = (($params->{'POINTS'}&(1<<($i-1)))>0)?'checked':'';
	}
$GTOOLS::TAG{'<!-- POINTS1_INC -->'} = $params->{'POINTS1_INC'};
$GTOOLS::TAG{'<!-- POINTS2_INC -->'} = $params->{'POINTS2_INC'};
$GTOOLS::TAG{'<!-- POINTS2_BUMP -->'} = $params->{'POINTS2_BUMP'};

$GTOOLS::TAG{'<!-- BOUNTY_FREESHIP -->'} = $params->{'BOUNTY_FREESHIP'};
foreach my $i (1,2,3,11,12,13) {
	$GTOOLS::TAG{'<!-- BOUNTY'.$i.'_INC -->'} = $params->{'BOUNTY'.$i.'_INC'};
	$GTOOLS::TAG{'<!-- BOUNTY'.$i.'_DISC -->'} = $params->{'BOUNTY'.$i.'_DISC'};
	$GTOOLS::TAG{'<!-- BOUNTY'.$i.'_SUM -->'} = $params->{'BOUNTY'.$i.'_SUM'};
	}

if (not defined $params->{'EXPIRE'}) { $params->{'EXPIRE'} = 3; }
foreach my $i (1..4) {
	$GTOOLS::TAG{'<!-- EXPIRE'.$i.'_CHK -->'} = ($params->{'EXPIRE'}==$i)?'checked':'';
	}
$GTOOLS::TAG{'<!-- EXPIRE_DAYS -->'} = $params->{'EXPIRE_DAYS'};
$GTOOLS::TAG{'<!-- EXPIRE_GRACEDAYS -->'} = $params->{'EXPIRE_GRACEDAYS'};
$GTOOLS::TAG{'<!-- EXPIRE_DAILYLOSS -->'} = $params->{'EXPIRE_MAXLIFE'};
$GTOOLS::TAG{'<!-- EXPIRE_MAXLIFE -->'} = $params->{'EXPIRE_MAXLIFE'};
$GTOOLS::TAG{'<!-- AUTO_EXPLAIN_CHK -->'} = ($params->{'AUTO_EXPLAIN'})?'checked':'';

if (not defined $params->{'EXPIRE_OPTIONS'}) { $params->{'EXPIRE_OPTIONS'} = 0; }
foreach my $i (1..4) {
	$GTOOLS::TAG{'<!-- EXPIRE_OPTIONS'.$i.'_CHK -->'} = (($params->{'EXPIRE_OPTIONS'}&(1<<($i-1)))>0)?'checked':'';
	}




&GTOOLS::output('*LU'=>$LU,
	'file'=>$template_file,
	'header'=>1,
	'bc'=>[ { 'name'=>'Utilities'}, {'name'=>'Pricing Schedules'} ],
	);


