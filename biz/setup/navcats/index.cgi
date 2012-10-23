#!/usr/bin/perl

use lib "/httpd/modules";
use NAVCAT;
use GTOOLS;
use NAVCAT::CHOOSER;
use Data::Dumper;

my $template_file = 'index.shtml';

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

if (index($FLAGS,'BASIC')==-1) { 
	print "Location: /biz\n\n"; exit; 
	}
else {
	my $RESTRICTED = 0;
	my $NC = NAVCAT->new($USERNAME,PRT=>$PRT);
	if ($FLAGS !~ /,WEB,/) { $RESTRICTED = 1; }

	##
	## outputs 
	##
	
	my ($html) = NAVCAT::CHOOSER::buildLevel($LU,$NC,'.',restricted=>$RESTRICTED);

	$GTOOLS::TAG{'<!-- NAVCAT_CHOOSER -->'} = $html . $js;

	require GTOOLS::Table;
	# ($html,$js) = GTOOLS::Table::buildProductTable('brian',['TS67','TS30','TTS24'],height=>200,dragdrop=>1);
	# $js = "<script><!--\n$js\n//--></script>";
	# $GTOOLS::TAG{'<!-- PRODUCT_FINDER -->'} = $html . $js;
	&GTOOLS::output(
		title=>'Setup: Manage Navcats',
		help=>'#50555',
		jquery=>1,
		zmvc=>1,
		file=>$template_file, header=>1, bc=>[
		{ name=>'Setup', link=>'http://www.zoovy.com/biz/setup', },
		{ name=>'Manage Navcats', link=>'http://www.zoovy.com/biz/setup/navcats', }
		]
		);
	}

