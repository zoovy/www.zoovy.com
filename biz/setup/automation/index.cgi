#!/usr/bin/perl

use strict;
use lib "/httpd/modules";
require ZOOVY;
require GTOOLS;
require LUSER;
require SYNDICATION;
require ZWEBSITE;
require CUSTOMER::TICKET;

my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }
my $dbh = &DBINFO::db_zoovy_connect();

my ($prtinfo) = &ZWEBSITE::prtinfo($USERNAME,$PRT);
my $NS = $prtinfo->{'profile'};
my $webdb = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);

my @BC = (
	{ name=>'Setup', link=>'/biz/setup' }, 
	{ name=>'Site Automation' },
	);
my $template_file = '';
my $VERB = $ZOOVY::cgiv->{'VERB'};

if ($VERB eq '') { $VERB = ''; }

#if ($VERB eq 'NEW') {
#	require EVENT::PANELS;
#	$GTOOLS::TAG{'<!-- NEW_EVENT -->'} = &EVENT::PANELS::EventEdit();
#	$template_file = 'new.shtml';
#	}

if ($VERB eq 'ADD') {
	my %event = ();
	$event{'type'} = $ZOOVY::cgiv->{'type'};
	$event{'hint'} = $ZOOVY::cgiv->{'hint'};
	$event{'if'} = $ZOOVY::cgiv->{'if'};
	$event{'then'} = $ZOOVY::cgiv->{'then'};
	&ZWEBSITE::add_event($USERNAME,\%event);
	$VERB = '';
	}


if ($VERB eq 'NUKE') {
	my $type = $ZOOVY::cgiv->{'TYPE'};
	my ($ref) = &ZWEBSITE::fetch_globalref($USERNAME);
	my $eventsref = &ZWEBSITE::get_events($USERNAME,$type);
	my @EVENTS = ();
	for (my $i = scalar(@{$eventsref}); --$i>=0; ) {
		if ($eventsref->[$i]->{'id'} eq $ZOOVY::cgiv->{'ID'}) {
			## found match
			}
		else {
			push @EVENTS, $eventsref->[$i];
			}
		}
	$ref->{'%events'}->{$type} = \@EVENTS;
	&ZWEBSITE::save_globalref($USERNAME,$ref);
	$VERB = '';
	}

if (($VERB eq 'SUSPEND') || ($VERB eq 'ACTIVATE')) {
	my $type = $ZOOVY::cgiv->{'TYPE'};
	my ($ref) = &ZWEBSITE::fetch_globalref($USERNAME);
	my $eventsref = &ZWEBSITE::get_events($USERNAME,$type);
	for (my $i = scalar(@{$eventsref}); --$i>=0; ) {
		if ($eventsref->[$i]->{'id'} eq $ZOOVY::cgiv->{'ID'}) {
			if ($VERB eq 'SUSPEND') { $eventsref->[$i]->{'ignore'}++; }
			if ($VERB eq 'ACTIVATE') { delete $eventsref->[$i]->{'ignore'}; }
			}
		}	
	&ZWEBSITE::save_globalref($USERNAME,$ref);
	$VERB = '';
	}


if ($VERB eq '') {
	my ($ref) = &ZWEBSITE::fetch_globalref($USERNAME);
	if (not defined $ref->{'%events'}) { $ref->{'%events'} = {}; }
	
	my $c = '';
	foreach my $type (sort keys %{$ref->{'%events'}}) {
		$c .= "<tr><td colspan=2 class='zoovysub1header'>Event: $type</td></tr>";
		my $pos = 0;
		foreach my $e (@{$ref->{'%events'}->{$type}}) {
			$c .= "<tr>";
			$c .= "<td>";
			if (not defined $e->{'ignore'}) { $e->{'ignore'} = 0; }
			if ($e->{'ignore'}) {
				$c .= "<a href=\"index.cgi?VERB=ACTIVATE&TYPE=$type&ID=$e->{'id'}\">[ACTIVATE]</a><br>";
				$c .= "<a href=\"index.cgi?VERB=NUKE&TYPE=$type&ID=$e->{'id'}\">[DELETE]</a><br>";
				}
			else {
				$c .= "<a href=\"index.cgi?VERB=SUSPEND&TYPE=$type&ID=$e->{'id'}\">[SUSPEND]</a>";
				}
			
			$c .= "</td>";
			$c .= "<td>$e->{'hint'}<br><div class='hint'>IF: $e->{'if'}<br>THEN: $e->{'then'}</div></td>";
			$c .= "</tr>";
			$pos++;
			}
		}
	
	if ($c eq '') {
		$GTOOLS::TAG{'<!-- EVENTS -->'} = "<tr><td><i>No Events Created Yet</i></td></tr>";
		}
	else {
		$GTOOLS::TAG{'<!-- EVENTS -->'} = $c;
		}

	$template_file = 'index.shtml';
	}
&DBINFO::db_zoovy_close();

&GTOOLS::output(
	file=>$template_file,
	header=>1,
	bc=>\@BC,
	js=>2+4+8,
	tabs=>[
		{ selected=>(($VERB eq '')?1:0), link=>"index.cgi?VERB=", name=>'Events' },
#		{ selected=>(($VERB eq 'NEW')?1:0), link=>"index.cgi?VERB=NEW", name=>'New' },
#		{ selected=>(($VERB eq 'LOGS')?1:0), link=>"index.cgi?VERB=LOGS", name=>'CRM Log' },
		],
	
	);



