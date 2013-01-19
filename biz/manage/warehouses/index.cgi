#!/usr/bin/perl

use strict;

use lib "/httpd/modules";
use Data::Dumper;
require GTOOLS;
require LUSER;
require ZOOVY;
require DBINFO;
require WAREHOUSE;
require ZTOOLKIT::BARCODE;

my @MSGS = ();

my ($LU) = LUSER->authenticate();
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }
if (index($FLAGS,'BASIC')==-1) { print "Location: /biz\n\n"; exit; }

my ($udbh) = &DBINFO::db_user_connect($USERNAME);

my $template_file = '';
my $VERB = $ZOOVY::cgiv->{'VERB'};


if ($VERB eq 'ZONE-CREATE-LOCATIONS') {
	my $ZONE_CODE = $ZOOVY::cgiv->{'ZONE_CODE'};
	my $BEGIN_ROW = $ZOOVY::cgiv->{'begin-row'};
	my $END_ROW = $ZOOVY::cgiv->{'end-row'};
	my $BEGIN_SHELF = $ZOOVY::cgiv->{'begin-shelf'};
	my $END_SHELF = $ZOOVY::cgiv->{'end-shelf'};
	my $BEGIN_SLOT = $ZOOVY::cgiv->{'begin-slot'};
	my $END_SLOT = $ZOOVY::cgiv->{'end-slot'};

	print STDERR "BEGIN_ROW: $BEGIN_ROW END_ROW: $END_ROW\n";
	print STDERR "BEGIN_SHELF: $BEGIN_SHELF END_SHELF: $END_SHELF\n";
	print STDERR "BEGIN_SLOT: $BEGIN_SLOT END_SLOT: $END_SLOT\n";

	my ($CODE) = $ZOOVY::cgiv->{'CODE'};
	my ($w) = WAREHOUSE->new($USERNAME,'CODE'=>$CODE);
	my $i = 0;
	foreach my $row ($BEGIN_ROW .. $END_ROW) {
		foreach my $shelf ($BEGIN_SHELF .. $END_SHELF) {
			foreach my $slot ($BEGIN_SLOT .. $END_SLOT) {
				print STDERR "'ROW'=>$row,'SHELF'=>$shelf,'SLOT'=>$slot,\n";
				$w->add_zone_location($ZONE_CODE,'ROW'=>$row,'SHELF'=>$shelf,'SLOT'=>$slot,'LUSER'=>$LUSERNAME);
				$i++;
				}
			}
		}

	if ($i>0) {
		push @MSGS, "SUCCESS|Created $i new slots";
		}
	else {
		push @MSGS, "ERROR|Failed to create any slots, please check your number ranges";
		}

	$VERB = 'ZONE-EDIT';
	}


if (($VERB eq 'WAREHOUSE-CREATE') || ($VERB eq 'WAREHOUSE-SAVE')) {
	my $CODE = &WAREHOUSE::valid_warehouse_code($ZOOVY::cgiv->{'WAREHOUSE_CODE'});

	my $v = undef;
	if ($VERB eq 'WAREHOUSE-CREATE') {
		if (&WAREHOUSE::exists($USERNAME,$CODE)) {
			$ZOOVY::cgiv->{'CODE'} = $CODE;
			$VERB = 'EDIT';
			push @MSGS, "WARN|Warehouse Code:$CODE already exists - cannot create, switching to edit.";
			}
		else {
			($v) = WAREHOUSE->new($USERNAME,'NEW'=>$CODE);
			}
		}
	elsif ($VERB eq 'WAREHOUSE-SAVE') {
		if (not &WAREHOUSE::exists($USERNAME,$CODE)) {
			$ZOOVY::cgiv->{'CODE'} = $CODE;
			$VERB = 'NEW';
			push @MSGS, "WARN|Warehouse Code:$CODE does not exist - cannot edit, switching to create.";
			}
		else {
			($v) = WAREHOUSE->new($USERNAME,'CODE'=>$CODE);
			}
		}


	if (defined $v) {
		$v->set('WAREHOUSE_TITLE',$ZOOVY::cgiv->{'WAREHOUSE_TITLE'});
		$v->set('WAREHOUSE_ZIP',$ZOOVY::cgiv->{'WAREHOUSE_ZIP'});
		$v->set('WAREHOUSE_CITY',$ZOOVY::cgiv->{'WAREHOUSE_CITY'});
		$v->set('WAREHOUSE_STATE',$ZOOVY::cgiv->{'WAREHOUSE_STATE'});
		$v->set('SHIPPING_LATENCY_IN_DAYS',$ZOOVY::cgiv->{'SHIPPING_LATENCY_IN_DAYS'});
		$v->set('SHIPPING_CUTOFF_HOUR_PST',$ZOOVY::cgiv->{'SHIPPING_CUTOFF_HOUR_PST'});
		$v->save();
		$VERB = '';
		}
	}


if ($VERB eq 'DELETE') {
	my ($CODE) = &WAREHOUSE::valid_warehouse_code($ZOOVY::cgiv->{'CODE'});
	my ($v) = WAREHOUSE->new($USERNAME,'CODE'=>$CODE);
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
		$GTOOLS::TAG{'<!-- VERB -->'} = 'WAREHOUSE-CREATE';
		$GTOOLS::TAG{'<!-- WAREHOUSE_CODE_INPUT -->'} = qq~
		<input maxlength=3 size=3 type="textbox" name="WAREHOUSE_CODE" value="">
		<div class="hint">A 3 digit code consisting of letters A-Z and 0-9.</div>
		~;
		$GTOOLS::TAG{'<!-- HEADER -->'} = 'New Warehouse';
		$GTOOLS::TAG{'<!-- BUTTON -->'} = qq~
	<input type="submit" class="button" value=" Create Warehouse ">
	~;

		}

	if ($VERB eq 'EDIT') {
		$GTOOLS::TAG{'<!-- VERB -->'} = 'WAREHOUSE-SAVE';
		my ($CODE) = &WAREHOUSE::valid_warehouse_code($ZOOVY::cgiv->{'CODE'});
		$GTOOLS::TAG{'<!-- WAREHOUSE_CODE_INPUT -->'} = qq~
		$CODE
		<input type="hidden" name="WAREHOUSE_CODE" value="$CODE">
		~;
		$GTOOLS::TAG{'<!-- HEADER -->'} = "Edit Warehouse: $CODE";
		$GTOOLS::TAG{'<!-- BUTTON -->'} = qq~
	<input type="submit" class="button" value=" Save Warehouse $CODE ">
	~;
		my ($v) = WAREHOUSE->new($USERNAME,'CODE'=>$CODE);
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


if ($VERB eq 'ZONE-DELETE') {

	my ($CODE) = $ZOOVY::cgiv->{'CODE'};
	my ($w) = WAREHOUSE->new($USERNAME,'CODE'=>$CODE);

	my $ZONE_CODE = $ZOOVY::cgiv->{'ZONE_CODE'};
	$w->delete_zone($ZONE_CODE);
	
	$VERB = '';
	}


if (($VERB eq 'SAVE-ZONE') || ($VERB eq 'NEW-ZONE')) {
	my ($CODE) = $ZOOVY::cgiv->{'CODE'};
	my ($w) = WAREHOUSE->new($USERNAME,'CODE'=>$CODE);

	my $ZONE_CODE = $ZOOVY::cgiv->{'ZONE_CODE'};
	my $ZONE_TYPE = $ZOOVY::cgiv->{'ZONE_TYPE'};
	$w->add_zone(
		$ZONE_CODE,
		$ZONE_TYPE,
		'TITLE'=>$ZOOVY::cgiv->{'ZONE_TITLE'},
		'PREFERENCE'=>int($ZOOVY::cgiv->{'ZONE_PREFERENCE'})
		);		

	$VERB = 'ZONE-EDIT';	
	}




if (($VERB eq 'ZONE-ADD') || ($VERB eq 'ZONE-EDIT')) {
	my ($CODE) = $ZOOVY::cgiv->{'CODE'};
	$GTOOLS::TAG{'<!-- CODE -->'} = $CODE;
	my ($w) = WAREHOUSE->new($USERNAME,'CODE'=>$CODE);

	my $ZONE_CODE = $ZOOVY::cgiv->{'ZONE_CODE'};
	$GTOOLS::TAG{'<!-- ZONE_CODE -->'} = $ZONE_CODE;

	my $zoneref = undef;
	if ($VERB eq 'ZONE-ADD') {
		$GTOOLS::TAG{'<!-- HEADER -->'} = 'Create New Zone';
		$zoneref->{'ZONE_TYPE'} = $ZOOVY::cgiv->{'ZONE_TYPE'};
		$zoneref->{'ZONE_TITLE'} = $ZOOVY::cgiv->{'ZONE_TITLE'};
		$zoneref->{'ZONE_PREFERENCE'} = $ZOOVY::cgiv->{'ZONE_PREFERENCE'};
		$GTOOLS::TAG{'<!-- VERB -->'} = 'NEW-ZONE'; 
		}
	else {
		$GTOOLS::TAG{'<!-- HEADER -->'} = "Edit Zone $ZONE_CODE";
		($zoneref) = $w->get_zone($ZONE_CODE);
		$GTOOLS::TAG{'<!-- VERB -->'} = 'SAVE-ZONE'; 
		}

		
	my @zonetype_options = ();
	foreach my $ztref (@WAREHOUSE::ZONE_TYPES) {
		push @zonetype_options, [ $ztref->{'type'}, sprintf("%s: %s",$ztref->{'title'},$ztref->{'hint'}) ];
		}
	$GTOOLS::TAG{'<!-- ZONE_TITLE -->'} = $zoneref->{'ZONE_TITLE'};
	$GTOOLS::TAG{'<!-- ZONE_PREFERENCE -->'} = $zoneref->{'ZONE_PREFERENCE'};
	$GTOOLS::TAG{'<!-- ZONE_TYPES -->'} = "<select name=\"ZONE_TYPE\">";
	foreach my $row (@zonetype_options) {
		my ($p,$v) = ();
		if (ref($row) eq '') {
			$p = $row; $v = $row;
			}
		elsif (ref($row) eq 'ARRAY') {
			($v,$p) = @{$row};
			}
		my $selected = ($v eq $zoneref->{'ZONE_TYPE'})?'selected':'';
		$GTOOLS::TAG{'<!-- ZONE_TYPES -->'} .= "<option $selected value=\"$v\">$p</option>";
		}
	$GTOOLS::TAG{'<!-- ZONE_TYPES -->'} .= "</select>";

	$GTOOLS::TAG{'<!-- BUTTON -->'} = qq~
		<input type="submit" class="button" value=" Save Warehouse Zone ">
		<input type="button" onClick="navigateTo('/biz/manage/warehouses/index.cgi');" class="button" value=" Exit ">
		~;

	if ($VERB eq 'ZONE-ADD') {
		$template_file = 'addzone.shtml';
		}
	elsif ($VERB eq 'ZONE-EDIT') {
		$template_file = 'editzone.shtml';

		my $c = '';
		my $locations = $w->list_zone_locations($ZONE_CODE);
		if (scalar(@{$locations})==0) {
			$c .= "<tr><td colspan=3><i>No locations configured.</td></tr>";
			}
		else {
			foreach my $location (@{$locations}) {
		#		my $txt = "$ZONE_CODE:$location->{'ROW'}-$location->{'SHELF'}-$location->{'SLOT'}";
		#		my $imgurl = &ZTOOLKIT::BARCODE::code39_url($txt);
				$c .= "<tr><td>$ZONE_CODE:$location->{'ROW'}-$location->{'SHELF'}-$location->{'SLOT'}</td></tr>";
				}
			}
		$GTOOLS::TAG{'<!-- LOCATIONS -->'} = $c;
		}

	}


if ($VERB eq '') {
	$template_file = 'index.shtml';

	my ($warehousesref) = WAREHOUSE::lookup($USERNAME);

	my $c = '';
	foreach my $vref (@{$warehousesref}) {
		$c .= "<tr>";
		$c .= "<td>";
			$c .= sprintf("<button class=\"minibutton\" onClick=\"navigateTo('/biz/manage/warehouses/index.cgi?VERB=ZONE-ADD&CODE=%s');\">Add Zone</button>",$vref->code());
			$c .= sprintf("<button class=\"minibutton\" onClick=\"navigateTo('/biz/manage/warehouses/index.cgi?VERB=EDIT&CODE=%s');\">Edit</button>",$vref->code());
			$c .= sprintf("<button class=\"minibutton\" onClick=\"navigateTo('/biz/manage/warehouses/index.cgi?VERB=DELETE&CODE=%s');\">Delete</button>",$vref->code());
		$c .= "</td>";
		$c .= sprintf("<td>%s</td>",$vref->code());
		$c .= "<td>WAREHOUSE</td>";
		$c .= sprintf("<td>%s</td>",$vref->get('WAREHOUSE_TITLE'));
		$c .= sprintf("<td>%s</td>",$vref->get('MODIFIED_TS'));
		$c .= "</tr>";
		
		my ($w) = WAREHOUSE->new($USERNAME,'DBREF'=>$vref);
		my $zonesar = $w->list_zones();
		if (scalar(@{$zonesar})==0) {
			$c .= "<tr>";
			$c .= "<td></td>";
			$c .= "<td colspan=3><i>No zones configured</td>";
			$c .= "</tr>";
			}
		else {
			foreach my $zoneref (@{$zonesar}) {
				$c .= "<tr>";
				$c .= "<td align=\"right\">";
				$c .= sprintf("<button class=\"minibutton\" onClick=\"navigateTo('/biz/manage/warehouses/index.cgi?VERB=ZONE-EDIT&CODE=%s&ZONE_CODE=%s');\">Edit</button>",$vref->code(),$zoneref->{'ZONE_CODE'});
				$c .= sprintf("<button class=\"minibutton\" onClick=\"navigateTo('/biz/manage/warehouses/index.cgi?VERB=ZONE-DELETE&CODE=%s&ZONE_CODE=%s');\">Delete</button>",$vref->code(),$zoneref->{'ZONE_CODE'});
				$c .= "</td>";
				$c .= "<td>$zoneref->{'WAREHOUSE_CODE'}*$zoneref->{'ZONE_CODE'}</td><td>$zoneref->{'ZONE_TYPE'}</td><td>(Zone) $zoneref->{'ZONE_TITLE'}</td>";
				$c .= "</tr>";
				}
			}

		}
	if ($c eq '') {
		$c .= "<tr><td colspan=5><i>No warehouses have been defined. Please add one</td></tr>";
		}
	else {
		$c = qq~
<tr class='zoovysub1header'>
	<td></td>
</tr>
$c
~;
		}
	$GTOOLS::TAG{'<!-- WAREHOUSES -->'} = $c;
	}

my @TABS = ();
push @TABS, { name=>'Current Warehouses', link=>"/biz/manage/warehouses/index.cgi", selected=>(($VERB eq '')?1:0) };
push @TABS, { name=>'New Warehouses', link=>"/biz/manage/warehouses/index.cgi?VERB=NEW", selected=>(($VERB eq 'NEW')?1:0) };

&DBINFO::db_user_close();
&GTOOLS::output('*LU'=>$LU,header=>1,file=>$template_file,tabs=>\@TABS,msgs=>\@MSGS);


