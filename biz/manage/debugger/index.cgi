#!/usr/bin/perl

use strict;
use lib "/httpd/modules";
require LUSER;
require GTOOLS;
require ZWEBSITE;

my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $template_file = '';
my $VERB = $ZOOVY::cgiv->{'VERB'};
my ($webdbref) = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);

my $ajaxdebugfile = &ZOOVY::resolve_userpath($USERNAME)."/ajax-debug-log.txt";

if ($VERB eq 'AJAX_LOG') {
	open F, "<$ajaxdebugfile"; $/ = undef;
	$GTOOLS::TAG{'<!-- AJAX_LOG -->'} = <F>;
	close F; $/ = "\n";

	if ($GTOOLS::TAG{'<!-- AJAX_LOG -->'} eq '') {
		$GTOOLS::TAG{'<!-- AJAX_LOG -->'} = "No AJAX events logged";
		}
	$template_file = 'ajax-log.shtml';
	}


if ($VERB eq 'SAVE') {
	$webdbref->{'debugger'} = 0;
	$webdbref->{'debugger'} += (defined $ZOOVY::cgiv->{'ajax-debugger'})?1:0;
	&ZWEBSITE::save_website_dbref($USERNAME,$webdbref,$PRT);

	unlink $ajaxdebugfile;
	$VERB = '';
	}

if ($VERB eq '') {
	$GTOOLS::TAG{'<!-- AJAX-DEBUGGER -->'} = ($webdbref->{'debugger'}&1)?'checked':'';
	$template_file = 'index.shtml';
	}

my @TABS = ();
push @TABS, { name=>'config', link=>'/biz/utilities/debugger' };
push @TABS, { name=>'ajax-log', link=>'/biz/utilities/debugger?VERB=AJAX_LOG' };

&GTOOLS::output('*LU'=>$LU,tabs=>\@TABS,file=>$template_file,header=>1);