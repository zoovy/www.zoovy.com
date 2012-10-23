#!/usr/bin/perl

use strict;

use lib "/httpd/modules"; 
use CGI;
require GTOOLS;
use Text::CSV_XS;
use Data::Dumper;
require ZOOVY;
require ZWEBSITE;	
require ZSHIP;

require LUSER;
my $csv = Text::CSV_XS->new ();
my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }


my $webdbref = ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
my $onload = '';
my $VERB = $ZOOVY::cgiv->{'VERB'};


##
## tax is a csv, one per line:
##	0 = type
## 1 = match value
## 2 = rate
##	3 = bwvalue
## 4 = zone (comment/hint)
## 5 = expires
##



my $template_file = "index.shtml";
if ($VERB eq 'ADD') {

	my %ref = ();
	my @ref = ();
	my $err = '';

	if ($ZOOVY::cgiv->{'type'} eq '') { $err = "Please select a match type"; }
	my $type = $ZOOVY::cgiv->{'type'};
	push @ref, $type;

	my $match = '';
	if ($type eq 'state') { 
		$match = uc($ZOOVY::cgiv->{'match-state'}); 
		if ($match eq '') { $err = "State cannot be left blank!"; }
		}
	elsif ($type eq 'city') {
		$match = uc($ZOOVY::cgiv->{'match-citys'}).'+'.$ZOOVY::cgiv->{'match-cityc'};
		if ($match eq '') { $err = "State or City cannot be left blank!"; }
		}
	elsif ($type eq 'zipspan') {
		my $zipstart = int($ZOOVY::cgiv->{'match-zipstart'});
		my $zipend = int($ZOOVY::cgiv->{'match-zipend'});

		if ($zipstart == $zipend) { $match = sprintf("%05d",$zipend); }
		elsif ($zipend<$zipstart) { $match = sprintf("%05d-%05d",$zipend,$zipstart); }
		else { $match = sprintf("%05d-%05d",$zipstart,$zipend); }
		if ($match eq '') { $err = "Zip code must be provided!"; }
		}
	elsif ($type eq 'zip4') {
		$match = uc($ZOOVY::cgiv->{'match-zip4'});
		if ($match eq '') { $err = "Zip code + 4 must be provided!"; }
		}
	elsif ($type eq 'country') {
		$match = uc($ZOOVY::cgiv->{'match-country'});		
		if ($match eq '') { $err = "Country must be provided!"; }
		}
	elsif ($type eq 'intprovince') {
		$match = uc($ZOOVY::cgiv->{'match-ipcountry'});		
		if ($match eq '') { $err = "Country must be provided!"; }
		if ($ZOOVY::cgiv->{'match-ipstate'} eq '') { 
			$err = "Province must be provided!"; 
			}
		else {
			my $tmp = lc($ZOOVY::cgiv->{'match-ipstate'});
			$match = "$match+$tmp";
			}
		}
	elsif ($type eq 'intzip') {
		$match = uc($ZOOVY::cgiv->{'match-izcountry'});		
		if ($match eq '') { $err = "Country must be provided!"; }
		if ($ZOOVY::cgiv->{'match-izzip'} eq '') { 
			$err = "ZIP must be provided!"; 
			}
		else {
			my $tmp = lc($ZOOVY::cgiv->{'match-izzip'});
			$match = "$match+$tmp";
			}
		
		}
		
	push @ref, $match;
	if ($ZOOVY::cgiv->{'rate'} eq '') { $err = "You must provide a number for tax rate"; }
	elsif ($ZOOVY::cgiv->{'rate'} =~ /[^0-9\.]/) { $err = "You must provide a number for tax rate"; }

	push @ref, sprintf("%.3f",$ZOOVY::cgiv->{'rate'});
	my $val = 0;
	if ($ZOOVY::cgiv->{'SHIPPING'}) { $val += 2; }
	if ($ZOOVY::cgiv->{'HANDLING'}) { $val += 4; }
	if ($ZOOVY::cgiv->{'INSURANCE'}) { $val += 8; }
	if ($ZOOVY::cgiv->{'SPECIAL'}) { $val += 16; }
	if ($val>0) { $val = $val+1; }
	push @ref, $val;

	my $zone = $ZOOVY::cgiv->{'zone'};
	$zone =~ s/,/ /g;
	push @ref, $zone;

	my $expires =  $ZOOVY::cgiv->{'expires'};
	$expires =~ s/[^\d]+//g;
	push @ref, $expires;

	if ($err eq '') {
		my $status = $csv->combine(@ref);  # combine columns into a string
		my $line = $csv->string();
		$webdbref->{'tax_rules'} .= $line."\n";
		&ZWEBSITE::save_website_dbref($USERNAME,$webdbref,$PRT);
		}
	else {
		$GTOOLS::TAG{'<!-- ERROR_ADD -->'} = "<font color='red'>$err</font>";
		}

	$VERB = '';
	}


if ($VERB eq 'DEL') {
	my @lines = split(/\n/,$webdbref->{'tax_rules'});
	$lines[ int($ZOOVY::cgiv->{'LINE'}) ] = undef;
	my $txt = '';
	foreach my $line (@lines) {
		next if ($line eq '');
		$txt .= $line."\n";
		}
	$webdbref->{'tax_rules'} = $txt;
	&ZWEBSITE::save_website_dbref($USERNAME,$webdbref,$PRT);
	$VERB = '';
	}


##
##
##
if ($VERB eq '') {
	my $rules = $webdbref->{'tax_rules'};
	my $c = '';

	$GTOOLS::TAG{'<!-- MATCH-STATE -->'} = &ZOOVY::incode($ZOOVY::cgi->{'match-state'});
	$GTOOLS::TAG{'<!-- MATCH-CITYS -->'} = &ZOOVY::incode($ZOOVY::cgi->{'match-citys'});
	$GTOOLS::TAG{'<!-- MATCH-CITYC -->'} = &ZOOVY::incode($ZOOVY::cgi->{'match-cityc'});
	$GTOOLS::TAG{'<!-- MATCH-ZIPSTART -->'} = &ZOOVY::incode($ZOOVY::cgi->{'match-zipstart'});
	$GTOOLS::TAG{'<!-- MATCH-ZIPEND -->'} = &ZOOVY::incode($ZOOVY::cgi->{'match-zipend'});
	$GTOOLS::TAG{'<!-- MATCH-ZIP4 -->'} = &ZOOVY::incode($ZOOVY::cgi->{'match-zip4'});
	$GTOOLS::TAG{'<!-- MATCH-COUNTRY -->'} = &ZOOVY::incode($ZOOVY::cgi->{'match-country'});
	$GTOOLS::TAG{'<!-- RATE -->'} = &ZOOVY::incode($ZOOVY::cgi->{'rate'});
	$GTOOLS::TAG{'<!-- ZONE -->'} = &ZOOVY::incode($ZOOVY::cgi->{'zone'});
	$GTOOLS::TAG{'<!-- CHK_SHIPPING -->'} = (defined $ZOOVY::cgi->{'SHIPPING'})?'checked':'';
	$GTOOLS::TAG{'<!-- CHK_HANDLING -->'} = (defined $ZOOVY::cgi->{'HANDLING'})?'checked':'';
	$GTOOLS::TAG{'<!-- CHK_INSURANCE -->'} = (defined $ZOOVY::cgi->{'INSRUANCE'})?'checked':'';
	$GTOOLS::TAG{'<!-- CHK_SPECIAL -->'} = (defined $ZOOVY::cgi->{'SPECIAL'})?'checked':'';

	$GTOOLS::TAG{'<!-- OPT_STATE -->'} = ($ZOOVY::cgiv->{'type'} eq 'state')?'selected':'';
	$GTOOLS::TAG{'<!-- OPT_CITY -->'} = ($ZOOVY::cgiv->{'type'} eq 'city')?'selected':'';
	$GTOOLS::TAG{'<!-- OPT_ZIPSPAN -->'} = ($ZOOVY::cgiv->{'type'} eq 'zipspan')?'selected':'';
	$GTOOLS::TAG{'<!-- OPT_ZIP4 -->'} = ($ZOOVY::cgiv->{'type'} eq 'zip4')?'selected':'';
	$GTOOLS::TAG{'<!-- OPT_COUNTRY -->'} = ($ZOOVY::cgiv->{'type'} eq 'country')?'selected':'';
	$GTOOLS::TAG{'<!-- OPT_INTPROVINCE -->'} = ($ZOOVY::cgiv->{'type'} eq 'intprovince')?'selected':'';
	$GTOOLS::TAG{'<!-- OPT_INTZIP -->'} = ($ZOOVY::cgiv->{'type'} eq 'intzip')?'selected':'';
	$GTOOLS::TAG{'<!-- MATCH-IPCOUNTRY -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'match-ipcountry'});
	$GTOOLS::TAG{'<!-- MATCH-IPSTATE -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'match-ipstate'});
	$GTOOLS::TAG{'<!-- MATCH-IZCOUNTRY -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'match-izcountry'});
	$GTOOLS::TAG{'<!-- MATCH-IZZIP -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'match-izzip'});

	$GTOOLS::TAG{'<!-- EXPIRES -->'} = &ZOOVY::incode($ZOOVY::cgi->{'expires'});
	$GTOOLS::TAG{'<!-- GROUP -->'} = &ZOOVY::incode($ZOOVY::cgi->{'group'});


	$onload = "showHint(document.addFrm['type']);";

	if ($rules eq '') {
		$c .= "<tr><td><i>There are no existing rules, please add some.</td></tr>";
		}
	else {
		$c .= q~<tr class="zoovysub1header">
<td>&nbsp;</td>
<td>Match Type</td>
<td>Match Value</td>
<td>Percentage</td>
<td>Shipping</td>
<td>Handling</td>
<td>Insurance</td>
<td>Spec. Fee</td>
<td>Zone</td>
<td>Expires</td>
<td>Group</td>
</tr>~;
		my $count = 0;
		my %USED_ZIPS = ();
		foreach my $line (split(/[\n\r]+/,$webdbref->{'tax_rules'})) {
			my $status  = $csv->parse($line);       # parse a CSV string into fields
			my @data = $csv->fields();           # get the parsed fields


			if ($data[0] eq 'zipspan') {
				my ($from,$to) = split(/-/,$data[1],2);
				$from = int($from);
				$to = int($to);
				if ($to == 0) { $to = $from; }
				if ($from == 0) { $from = $to; }
				# $c .= "<tr><td colspan=6 class='rs'>BROKE: from=$from to=$to</td></tr>\n";

				foreach my $zip ($from .. $to) { 
					if (defined $USED_ZIPS{$zip}) { 
						$c .= "<tr><td>&nbsp;</td><td colspan=8 class='rs'>WARNING: zip $zip overlaps with: $USED_ZIPS{$zip}</td></tr>";
						}
					else {
						$USED_ZIPS{$zip} = "line[$count] $data[1]";
						# $c .= "<tr><td colspan=6 class='rs'>saving zip: $zip</td></tr>";
						}
					}
				}

			
			$c .= "<tr>";
			$c .= "<td><a href=\"index.cgi?VERB=DEL&LINE=$count\">[remove]</a> &nbsp;-&nbsp; </td>";
			my ($method,$data) = ();
			my $match = $data[1]; 
			if ($data[0] eq 'state') { 
				$method = "State"; 
				$match = $ZSHIP::STATE_ABBREVIATIONS{ uc($data[1]) };
				if ($match eq '') { $match = "**ERR:$data[1]**"; }
				}
			elsif ($data[0] eq 'city') { 
				$method = "City"; 
				my ($state,$city) = split(/[ \|\-\+\.\,]/,$data[1],2);
				$state = $ZSHIP::STATE_ABBREVIATIONS{ uc($state) };
				$match = "$state, $city";
				if (($state eq '') || ($city eq '')) { $match = "**ERR:$data[1]**"; }
				}
			elsif ($data[0] eq 'zipspan') { 
				$method = "Zip Range"; 
				my ($from,$to) = split(/-/,$data[1],2);

				if ($from eq '') { $match = "**ERR:$data[1]**"; }
				elsif ($to eq '') { $match = $from; }
				else { $match = "$from to $to"; }				
				}
			elsif ($data[0] eq 'zip4') { 
				$method = "Zip+4"; 
				}
			elsif ($data[0] eq 'country') { 
				$method = "Country"; 
				my ($info) = &ZSHIP::resolve_country(ISO=>$data[1]);
				if (not defined $info) { 
					$match = "**ERR:$data[1]**"; 
					}
				else {
					$match = $info->{'Z'};
					}
				}
			elsif (substr($data[0],0,1) eq '#') {
				$c .= "<td bgcolor='#FFFFCC' colspan=7>$data[0]</td>";
				$method = '';
				}
			elsif ($data[0] eq 'intprovince') {
				$method = "Int-Province"; 
				my ($country,$province) = split(/\+/,$data[1],2);
				my ($info) = &ZSHIP::resolve_country(ISO=>$country);
				if (not defined $info) { 
					$match = "**ERR:$data[1]**"; 
					}
				else {
					$match = $info->{'Z'}.' - '.$province;
					}
				}
			elsif ($data[0] eq 'intzip') {
				$method = "Int-Postal"; 
				my ($country,$zip) = split(/\+/,$data[1],2);
				my ($info) = &ZSHIP::resolve_country(ISO=>$country);
				if (not defined $info) { 
					$match = "**ERR:$data[1]**"; 
					}
				else {
					$match = $info->{'Z'}.' - '.$zip;
					}
				}
			else { 
				$method = "**UNKNOWN:$data[0]**"; 
				}
			
			if ($method ne '') {
				$c .= "<td>$method</td>";
				$c .= "<td>$match</td>";
				$c .= "<td>".sprintf("%.3f",$data[2])."%</td>";

				if (($data[3] & 1)==0) {
					## remember: bit = 1 enable
					$c .= "<td align=center>-</td>";
					$c .= "<td align=center>-</td>";
					$c .= "<td align=center>-</td>";
					$c .= "<td align=center>-</td>";
					}
				else {
					$c .= "<td align=center>".(($data[3] & 2)?'Y':'N')."</td>";
					$c .= "<td align=center>".(($data[3] & 4)?'Y':'N')."</td>";
					$c .= "<td align=center>".(($data[3] & 8)?'Y':'N')."</td>";
					$c .= "<td align=center>".(($data[3] & 16)?'Y':'N')."</td>";
					}

				my $zone = $data[4];
				$c .= "<td>$zone</td>";

				my $expires = $data[5];
				$c .= "<td>$expires</td>";

				my $group = $data[6];
				$c .= "<td>$group</td>";
				}

			$c .= "</tr>";


			$count++;
			}
		}

	$GTOOLS::TAG{'<!-- EXISTING_RULES -->'} = $c;
	}


##
##
##
if ($VERB eq 'ADVANCED-SAVE') {
	$VERB = 'ADVANCED';
	$webdbref->{'tax_rules'} = $ZOOVY::cgiv->{'tax_rules'};
	&ZWEBSITE::save_website_dbref($USERNAME,$webdbref,$PRT);
	}

if ($VERB eq 'ADVANCED') {
	$template_file = 'advanced.shtml';
	$GTOOLS::TAG{'<!-- TAX_RULES -->'} = &ZOOVY::incode($webdbref->{'tax_rules'});
	}





##
##
##
if ($VERB eq 'DEBUG') {
	$GTOOLS::TAG{'<!-- DEBUG_OUTPUT -->'} = "<i>Please run a test to see output</i>";
	}

if ($VERB eq 'DEBUG-NOW') {
	$VERB = 'DEBUG';

	my (%result) = &ZSHIP::getTaxes($USERNAME,$PRT,
		webdb=>$webdbref,
		city=>$ZOOVY::cgiv->{'city'},
		state=>$ZOOVY::cgiv->{'state'},
		zip=>$ZOOVY::cgiv->{'zip'},
		address1=>$ZOOVY::cgiv->{'address1'},
		country=>$ZOOVY::cgiv->{'country'},
		subtotal=>$ZOOVY::cgiv->{'order_total'},
		shp_total=>$ZOOVY::cgiv->{'shipping_total'},
		debug=>1);

	$GTOOLS::TAG{'<!-- DEBUG_OUTPUT -->'} = qq~
<table border=0 class="zoovytable">
<tr class="zoovysub1header">
	<td></td><td>Tax Rate</td><td>Tax Subtotal</td><td>Amount</td><td>Note</td>
</tr>
<tr>
	<td>Overall:</td>
	<td>$result{'tax_rate'}%</td>
	<td>\$$result{'tax_subtotal'}</td>
	<td><b>\$$result{'tax_total'}</b></td>
	<td> &lt;-- what the customer will pay</td>
</tr>
<tr>
	<td>_state:</td>
	<td>$result{'state_rate'}%</td>
	<td>\$$result{'tax_subtotal'}</td>
	<td>\$$result{'state_total'}</td>
</tr>
<tr>
	<td>_local:</td>
	<td>$result{'local_rate'}%</td>
	<td>\$$result{'tax_subtotal'}</td>
	<td>\$$result{'local_total'}</td>
</tr>
</table>
<br>
<b>TRANSACTION LOG:</b><br>
<pre>$result{'debug'}</pre>
~;

	# $GTOOLS::TAG{'<!-- DEBUG_OUTPUT -->'} .= "<pre>".&ZOOVY::incode(Dumper(\%result))."</pre>";
	}

if ($VERB eq 'DEBUG') {
	$template_file = 'debug.shtml';
	$GTOOLS::TAG{'<!-- COUNTRY -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'country'});
	if ($ZOOVY::cgiv->{'country'} eq '') {
		$GTOOLS::TAG{'<!-- COUNTRY -->'} = 'US';
		}
	$GTOOLS::TAG{'<!-- ORDER_TOTAL -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'order_total'});
	if ($ZOOVY::cgiv->{'order_total'} eq '') {
		$GTOOLS::TAG{'<!-- ORDER_TOTAL -->'} = '100';
		}
	$GTOOLS::TAG{'<!-- SHIPPING_TOTAL -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'shipping_total'});
	if ($ZOOVY::cgiv->{'shipping_total'} eq '') {
		$GTOOLS::TAG{'<!-- SHIPPING_TOTAL -->'} = '100';
		}
	$GTOOLS::TAG{'<!-- STATE -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'state'});
	$GTOOLS::TAG{'<!-- ZIP -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'zip'});
	$GTOOLS::TAG{'<!-- CITY -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'city'});
	$GTOOLS::TAG{'<!-- ADDRESS1 -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'address1'});
	}


my @TABS = ();
push @TABS, { name=>"Rule Wizard", selected=>($VERB eq '')?1:0, link=>"?VERB=", };
push @TABS, { name=>"Expert Mode", selected=>($VERB eq 'ADVANCED')?1:0, link=>"?VERB=ADVANCED", };
push @TABS, { name=>"Test", selected=>($VERB eq 'DEBUG')?1:0, link=>"?VERB=DEBUG", };


my %NEED = ();
if ($LU->get('todo.setup')) {
	require TODO;
	my $t = TODO->new($USERNAME);	
	my ($need,$tasks) = $t->setup_tasks('tax',LU=>$LU,webdb=>$webdbref);
	$GTOOLS::TAG{'<!-- MYTODO -->'} = $t->mytodo_box('tax',$tasks);
   }


##
##
##
&GTOOLS::output(
   'title'=>'Setup : Tax Rules',
   'file'=>$template_file,
   'header'=>'1',
	'todo'=>1,
	'jquery'=>'1',
   'help'=>'#50710',
   'tabs'=>\@TABS,
	'onload'=>$onload,
   'bc'=>[
      { name=>'Setup',link=>'http://www.zoovy.com/biz/setup','target'=>'_top', },
      { name=>'Tax Rules',link=>'http://www.zoovy.com/biz/setup/tax','target'=>'_top', },
      ],
   );


