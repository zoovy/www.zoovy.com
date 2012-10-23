#!/usr/bin/perl

use strict;

use lib "/httpd/modules";
use Data::Dumper;
require GTOOLS;
require LUSER;
require ZOOVY;
require DBINFO;
require VENDOR;

my @MSGS = ();

my ($LU) = LUSER->authenticate();
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }
if (index($FLAGS,'BASIC')==-1) { print "Location: /biz\n\n"; exit; }

my ($udbh) = &DBINFO::db_user_connect($USERNAME);

my $template_file = '';
my $VERB = $ZOOVY::cgiv->{'VERB'};


#$/*
#   VENDORS: businesses we buy from
#   each vendor is assigned a 6 digit code that is used to create a unique inventory zone
#*/
# create table VENDORS (
#     ID integer unsigned auto_increment,
#     USERNAME varchar(20) default '' not null,
#     MID integer unsigned default 0 not null,
#     CREATED_TS timestamp  default 0 not null,
#     MODIFIED_TS timestamp  default 0 not null,
#     VENDOR_CODE varchar(6) default '' not null,
#     VENDOR_NAME varchar(41) default '' not null,
#     QB_REFERENCE_ID varchar(41) default '' not null,
#     ADDR1 varchar(41) default '' not null,
#     ADDR2 varchar(41) default '' not null,
#     CITY varchar(31) default '' not null,
#     STATE varchar(21) default '' not null,
#     POSTALCODE varchar(31) default '' not null,
#     PHONE varchar(21) default '' not null,
#     CONTACT varchar(41) default '' not null,
#     EMAIL varchar(100) default '' not null,
#     primary key(ID),
#     unique (MID,VENDOR_CODE)
#   );


if (($VERB eq 'VENDOR-CREATE') || ($VERB eq 'VENDOR-SAVE')) {
	my $CODE = &VENDOR::valid_vendor_code($ZOOVY::cgiv->{'VENDOR_CODE'});

	my $v = undef;
	if ($VERB eq 'VENDOR-CREATE') {
		if (&VENDOR::exists($USERNAME,$CODE)) {
			$ZOOVY::cgiv->{'CODE'} = $CODE;
			$VERB = 'EDIT';
			push @MSGS, "WARN|Vendor Code:$CODE already exists - cannot create, switching to edit.";
			}
		else {
			($v) = VENDOR->new($USERNAME,'NEW'=>$CODE);
			}
		}
	elsif ($VERB eq 'VENDOR-SAVE') {
		if (not &VENDOR::exists($USERNAME,$CODE)) {
			$ZOOVY::cgiv->{'CODE'} = $CODE;
			$VERB = 'NEW';
			push @MSGS, "WARN|Vendor Code:$CODE does not exist - cannot edit, switching to create.";
			}
		else {
			($v) = VENDOR->new($USERNAME,'CODE'=>$CODE);
			}
		}


	if (defined $v) {
		$v->set('VENDOR_NAME',$ZOOVY::cgiv->{'VENDOR_NAME'});
		$v->set('ADDR1',$ZOOVY::cgiv->{'ADDR1'});
		$v->set('ADDR2',$ZOOVY::cgiv->{'ADDR2'});
		$v->set('CITY',$ZOOVY::cgiv->{'CITY'});
		$v->set('STATE',$ZOOVY::cgiv->{'STATE'});
		$v->set('POSTALCODE',$ZOOVY::cgiv->{'POSTALCODE'});
		$v->set('PHONE',$ZOOVY::cgiv->{'PHONE'});
		$v->set('CONTACT',$ZOOVY::cgiv->{'CONTACT'});
		$v->set('EMAIL',$ZOOVY::cgiv->{'EMAIL'});
		$v->save();
		$VERB = '';
		}
	}


if ($VERB eq 'DELETE') {
	my ($CODE) = &VENDOR::valid_vendor_code($ZOOVY::cgiv->{'CODE'});
	my ($v) = VENDOR->new($USERNAME,'CODE'=>$CODE);
	if (defined $v) {
		$v->nuke();
		push @MSGS, "SUCCESS|Deleted vendor: $CODE";
		}
	else {
		push @MSGS, "ERROR|Unknown vendor: $CODE";
		}
	$VERB = '';
	}


if (($VERB eq 'EDIT') || ($VERB eq 'NEW')) {
	if ($VERB eq 'NEW') {
		$GTOOLS::TAG{'<!-- VERB -->'} = 'VENDOR-CREATE';
		$GTOOLS::TAG{'<!-- VENDOR_CODE_INPUT -->'} = qq~
		<input maxlength=6 size=6 type="textbox" name="VENDOR_CODE" value="">
		<div class="hint">A 6 digit code consisting of letters A-Z and 0-9 you will use to refer to this vendor</div>
		~;
		$GTOOLS::TAG{'<!-- HEADER -->'} = 'New Vendor';
		$GTOOLS::TAG{'<!-- BUTTON -->'} = qq~
	<input type="submit" class="button" value=" Create Vendor ">
	~;

		}

	if ($VERB eq 'EDIT') {
		$GTOOLS::TAG{'<!-- VERB -->'} = 'VENDOR-SAVE';
		my ($CODE) = &VENDOR::valid_vendor_code($ZOOVY::cgiv->{'CODE'});
		$GTOOLS::TAG{'<!-- VENDOR_CODE_INPUT -->'} = qq~
		$CODE
		<input type="hidden" name="VENDOR_CODE" value="$CODE">
		~;
		$GTOOLS::TAG{'<!-- HEADER -->'} = "Edit Vendor: $CODE";
		$GTOOLS::TAG{'<!-- BUTTON -->'} = qq~
	<input type="submit" class="button" value=" Save Vendor $CODE ">
	~;
		my ($v) = VENDOR->new($USERNAME,'CODE'=>$CODE);
		if (not defined $v) {
			$VERB = '';
			push @MSGS, "ERROR|Sorry, vendor $CODE does not exist";
			}
		else {
			foreach my $k (keys %{$v}) {
				$GTOOLS::TAG{"<!-- $k -->"} = $v->{$k};
				}
			}
		}
	$template_file = 'new.shtml';
	}

if ($VERB eq '') {
	$template_file = 'index.shtml';

	my ($vendorsref) = VENDOR::lookup($USERNAME);

	my $c = '';
	foreach my $vref (@{$vendorsref}) {
		$c .= "<tr>";
		$c .= "<td>";
			$c .= sprintf("<input type=\"button\" class=\"minibutton\" value=\"Edit\" onClick=\"document.location='index.cgi?VERB=EDIT&CODE=%s'\">",$vref->code());
			$c .= sprintf("<input type=\"button\" class=\"minibutton\" value=\"Delete\" onClick=\"document.location='index.cgi?VERB=DELETE&CODE=%s'\">",$vref->code());
		$c .= "</td>";
		$c .= sprintf("<td>%s</td>",$vref->code());
		$c .= sprintf("<td>%s</td>",$vref->get('VENDOR_NAME'));
		$c .= sprintf("<td>%s</td>",$vref->get('MODIFIED_TS'));
		$c .= "</tr>";
		}
	if ($c eq '') {
		$c .= "<tr><td colspan=5><i>No vendors have been defined. Please add one</td></tr>";
		}
	else {
		$c = qq~
<tr class='zoovysub1header'>
	<td></td>
</tr>
$c
~;
		}
	$GTOOLS::TAG{'<!-- VENDORS -->'} = $c;
	}

my @TABS = ();
push @TABS, { name=>'Current Vendors', link=>"index.cgi", selected=>(($VERB eq '')?1:0) };
push @TABS, { name=>'New Vendor', link=>"index.cgi?VERB=NEW", selected=>(($VERB eq 'NEW')?1:0) };

&DBINFO::db_user_close();
&GTOOLS::output(header=>1,file=>$template_file,tabs=>\@TABS,msgs=>\@MSGS);