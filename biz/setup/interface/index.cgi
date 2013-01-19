#!/usr/bin/perl

use strict;
use Data::Dumper;
use JSON::XS;
use lib "/httpd/modules";
require ZOOVY;
require GTOOLS;
require LUSER;
require ZWEBSITE;
require PRODUCT::PANELS;
require LISTING::EBAY;

my ($LU) = LUSER->authenticate(flags=>'_S&1');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }
my $dbh = &DBINFO::db_zoovy_connect();

my ($prtinfo) = &ZWEBSITE::prtinfo($USERNAME,$PRT);
my $NS = $prtinfo->{'profile'};
my $webdb = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);

my @BC = (
	{ name=>'Setup', link=>'/biz/setup' }, 
	{ name=>'Interface' },
	);
my $template_file = '';
my $VERB = $ZOOVY::cgiv->{'VERB'};

if ($VERB eq '') { $VERB = ''; }


if ($LUSERNAME eq 'SUPPORT') {
	}
elsif (not $LU->is_level(7)) {
	$GTOOLS::TAG{'<!-- REASON -->'} = '<i>Account level insufficient.</i>';
	$VERB = 'DENY';
	}
elsif (not $LU->is_admin()) {
	$GTOOLS::TAG{'<!-- REASON -->'} = "<i>Requires Administrative priviledges.</i>";
	$VERB = 'DENY';
	}


if ($VERB eq 'DENY') {
	$template_file = 'denied.shtml';
	}

if ($VERB eq 'RESET') {
	&ZWEBSITE::globalset_attribs($USERNAME,'prodedit-positions'=>'');
	$VERB = '';
	}

if ($VERB eq 'SAVE') {

	my %positions = ();
	my %gref_updates = ();

	foreach my $panel (@{&PRODUCT::PANELS::return_user_panels($LU)}) {
		my $panelid = $panel->{'id'};
		if ($panel->{'priority'} != $ZOOVY::cgiv->{ $panelid }) {
			$positions{ $panelid } = int($ZOOVY::cgiv->{ $panelid });

			## don't let a user save a panel that is less than zero.
			if ($positions{ $panelid }<0) { $positions{ $panelid } = 0; }
			}

		if ($panelid eq 'ebay2') {
			## EBAY2 PANEL EDITOR SAVE
			my $fields = LISTING::EBAY::ebay_fields();
			my @list = ();
			foreach my $field (@{$fields}) {
				if ($ZOOVY::cgiv->{"ebay2.$field->{'id'}"}) { push @list, $field->{'id'}; }
				}
			$gref_updates{'%interface'} = { 'prodedit.ebay2'=>join("|",@list) };
			}

		if ($panelid eq 'flexedit') {
			## FLEXEDIT PANEL EDITOR SAVE
			my $flexref = undef;
			if ($ZOOVY::cgiv->{'flexedit.json'} ne '') {
				$flexref = &JSON::XS::decode_json($ZOOVY::cgiv->{'flexedit.json'});
				}
			if (not defined $flexref) {}
			elsif (scalar{@{$flexref}}==0) { $flexref = undef; }
			$gref_updates{'@flexedit'} = $flexref;
			}

		}


	my $str = &ZTOOLKIT::buildparams(\%positions);
	$gref_updates{'prodedit-positions'} = $str;
	&ZWEBSITE::globalset_attribs($USERNAME,%gref_updates);
	$VERB = '';
	}


##
## 
##
if ($VERB eq '') {
	$template_file = 'index.shtml';
	my $globalref = &ZWEBSITE::fetch_globalref($USERNAME);
	my $c = '';
	foreach my $panel (@{&PRODUCT::PANELS::return_user_panels($LU)}) {
		# $c .= "<tr><td>".Dumper($panel)."</td></tr>";

		my $hint = '';
		if ($panel->{'conditional'}) { $hint = 'This panel is displayed conditionally based on your product attributes.</div>'; }
		if ($panel->{'position'} == 0) { $hint = "Panel is currently disabled."; }

		$c .= qq~<tr class="zoovysub1header">
	<td>$panel->{'id'}: $panel->{'title'}</td>
</tr>
<tr>
	<td colspan=2>
	Priority: <input type="textbox" name="$panel->{'id'}" value="$panel->{'position'}" size="4"><br>
	<div class="hint">$hint</div>
	</td>
</tr>
~;
		if ($panel->{'id'} eq 'ebay2') {
			my $fields = LISTING::EBAY::ebay_fields();
			my %enabled = ();
			if (defined $globalref->{'%interface'}->{'prodedit.ebay2'}) {
				foreach my $id (split(/\|/,$globalref->{'%interface'}->{'prodedit.ebay2'})) { $enabled{$id}++; }
				}
			my $d = '';
			my $r = '';
			foreach my $field (@{$fields}) {
				($r) = ($r eq 'r0')?'r1':'r0';
				my $checked = ($enabled{$field->{'id'}})?'checked':'';
				my $title = ($field->{'title'})?sprintf("%s<br>",$field->{'title'}):'';
				my $hint = ($field->{'hint'})?"$field->{'hint'}<br>":'';
				my $profile = ($field->{'ns'} eq 'profile')?"<div class='hint'>Normally configured in the profile</div>":"";
				my $defaults = ($field->{'loadfrom'})?"<div class='hint'>Defaults from: $field->{'loadfrom'}</div><br>":'';
				
				$d .= "<tr class='$r'><td valign=top><input type=checkbox $checked name=\"ebay2.$field->{'id'}\"></td><td valign=top>$field->{'id'}</td><td valign=top>$title$hint$defaults$profile</td></tr>";
				}
			$c .= "<tr><td valign=top colspan=2><table width=100%>$d</table></td></tr>";			
			}

		if ($panel->{'id'} eq 'flexedit') {
			# my $json = Data::Dumper::Dumper($globalref->{'@flexedit'});
			if (not defined $globalref->{'@flexedit'}) { $globalref->{'@flexedit'} = []; }
			my $json = '';
			if (scalar(@{$globalref->{'@flexedit'}})>0) {
				$json = &ZOOVY::incode(&JSON::XS::encode_json($globalref->{'@flexedit'}));
				}

			$c .= qq~
<tr>
	<td colspan=2>
	<textarea cols=70 rows=3 onFocus="this.rows=30;"  name="flexedit.json">$json</textarea>
	</td>
</tr>
~;
			}


		}
	$GTOOLS::TAG{'<!-- PANELS -->'} = $c;
	}


&DBINFO::db_zoovy_close();

&GTOOLS::output('*LU'=>$LU,
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



