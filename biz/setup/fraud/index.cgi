#!/usr/bin/perl

use strict;

use lib "/httpd/modules";
require ZOOVY;
require GTOOLS;
require DOMAIN::TOOLS;
require DOMAIN;
require Data::GUID;
require LUSER;
require SITE::MSGS;


use Data::Dumper;

my ($LU) = LUSER->authenticate();
if (not defined $LU) { warn "Auth"; exit; }

#use Data::Dumper;
#print STDERR Dumper($LU);

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { warn "No auth"; exit; }

my ($udbh) = &DBINFO::db_user_connect($USERNAME);

my @MSGS = ();
my @BC = (
	{ name=>'Setup', link=>'/biz/setup' }, 
	);
my $template_file = '';
my $VERB = $ZOOVY::cgiv->{'VERB'};

$GTOOLS::TAG{'<!-- PRT -->'} = $PRT;

if ($VERB eq '') {
	}



&DBINFO::db_user_close();

&GTOOLS::output(
	file=>$template_file,
	header=>1,
	bc=>\@BC,
	js=>2+4+8,
	tabs=>\@TABS,
	msgs=>\@MSGS,
	);



