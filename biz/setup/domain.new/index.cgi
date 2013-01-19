#!/usr/bin/perl

use strict;
use Data::Dumper;
use lib "/httpd/modules";
use GTOOLS;
use LUSER;
use DOMAIN;

my ($LU) = LUSER->authenticate(flags=>'_S&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $VERB = $ZOOVY::cgiv->{'VERB'};

my @MSGS = ();

my @BC = ();
push @BC, { 'name'=>'Setup', 'link'=>'/biz/setup' };
push @BC, { 'name'=>'Domain', 'link'=>'/biz/setup/domain' };

my @TABS = ();
push @TABS, { 'name'=>'Domains', 'link'=>'index.cgi' };
push @TABS, { 'name'=>'Add', 'link'=>'index.cgi?VERB=ADD' };
push @TABS, { 'name'=>'Email', 'link'=>'index.cgi?VERB=EMAIL' };

my $template_file = '';


# cut down marketplaces: amazon, ebay and more.
#too many any-commerce
#part of what makes us great
#buy more frequently
#our apps, which are free

#if ($VERB eq 'EMAIL') {
#	$template_file = 'email.shtml';	
#	}

if ($VERB eq 'DOMAIN-ADD') {
	#	foreach my $ns (@{$profileref}) {
	#		if ($ns eq '') { $ns = 'DEFAULT'; }
#
#			## once a profile is mapped to a partition .. you shouldn't be able to see it on other partitions.
#			my $nsref = &ZOOVY::fetchmerchantns_ref($USERNAME,$ns);
#			next if ($nsref->{'prt:id'} != $PRT);
#
#	      $PROFILES .= "<option ".(($d->{'PROFILE'} eq $ns)?'selected':'')." value=\"$ns\">$ns</option>\n";
#			}


	$template_file = 'domain-add.shtml';
	}

if ($VERB eq '') {
	require DOMAIN::TOOLS;

	my $c = '';
	my (@domains) = DOMAIN::TOOLS::domains($USERNAME,'PRT'=>$PRT);
	foreach my $d (@domains) {
		$c .= qq~<tr><td>$d</td><td><div><!-- STATUS --></div></td></tr>~;
		}
	if ($c eq '') { 
		$c .= "<tr><td><i>No Domains Configured</i></td></tr>";
		}
	$GTOOLS::TAG{'<!-- DOMAINS -->'} = $c;

	$template_file = 'index.shtml';
	}


&GTOOLS::output('*LU'=>$LU,'msgs'=>\@MSGS, 'tabs'=>\@TABS, 'bc'=>\@BC,'file'=>$template_file,'header'=>1,'jquery'=>1);