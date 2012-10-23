#!/usr/bin/perl

use lib "/httpd/modules";
require GTOOLS;
use CGI;
require ZWEBSITE;
require ZSHIP;
require ZSHIP::GLOBAL;
use Data::Dumper;



require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }



my @BC = ();
push @BC, { name=>'Setup',link=>'http://www.zoovy.com/biz/setup','target'=>'_top', };
push @BC, { name=>'Shipping',link=>'http://www.zoovy.com/biz/setup/shipping','target'=>'_top', };
push @BC, { name=>'Global Tuning' };

$q = new CGI;
$ACTION = $q->param('ACTION');
%webdb = &ZWEBSITE::fetch_website_db($USERNAME,$PRT);



if ($ACTION eq 'WT_TOGGLE') {
	$TYPE = lc($q->param('TYPE'));
	if ($TYPE eq 'dom') 
		{ 
		$webdb{'globalwt_enable'} -= int($webdb{'globalwt_enable'}) & 1;
		if ($q->param('KEY')>0) { $webdb{'globalwt_enable'} += 1; }
		}
	if ($TYPE eq 'int') 
		{ 
		$webdb{'globalwt_enable'} -= int($webdb{'globalwt_enable'}) & 8;
		if ($q->param('KEY')>0) { $webdb{'globalwt_enable'} += 8; }
		}
	$LU->log("SETUP.SHIPPING.GLOBAL","Saved Global Tuning DOM Settings","SAVE");
	&ZWEBSITE::save_website_dbref($USERNAME,\%webdb,$PRT);
	$ACTION = '';
	}

if ($ACTION eq "SAVE-WEIGHT")
	{
	$TYPE = lc($q->param('TYPE'));
	$weight = $q->param('MAXWT');
	$price = $q->param('PRICE');

	if (defined($weight) && defined($price))
		{
		$weight =~ s/[^0-9\.]//g;
		$price =~ s/[^0-9\.]//g;
		$hashref = &ZSHIP::GLOBAL::decode_weightbased_string($webdb{'globalwt_'.$TYPE.'_data'});
		$hashref->{$weight} = "$price";
		$webdb{'globalwt_'.$TYPE.'_data'} = &ZSHIP::GLOBAL::encode_weightbased_string($hashref);
#		print STDERR "Saving ....\n".Dumper($hashref);
		$LU->log("SETUP.SHIPPING.GLOBAL","Saved Global Tuning Weight Settings","SAVE");
		&ZWEBSITE::save_website_dbref($USERNAME,\%webdb,$PRT);
		}

	$ACTION = '';
	}

if ($ACTION eq 'DELETE')
	{
	$TYPE = lc($q->param('TYPE'));
	$hashref = &ZSHIP::GLOBAL::decode_weightbased_string($webdb{'globalwt_'.$TYPE.'_data'});
	delete $hashref->{$q->param('KEY')};
	$webdb{'globalwt_'.$TYPE.'_data'} = &ZSHIP::GLOBAL::encode_weightbased_string($hashref);
#	print STDERR "Saving ....\n".Dumper($hashref);
	$LU->log("SETUP.SHIPPING.GLOBAL","Deleted Global Tuning Settings","SAVE");
	&ZWEBSITE::save_website_dbref($USERNAME,\%webdb,$PRT);	
	$ACTION = '';
	}


if ($ACTION eq '')
	{

	# set the enabled checkbox status
	if ( (int($webdb{'globalwt_enable'}) & 1) == 1) 
		{ $GTOOLS::TAG{'<!-- WT_DOM_BUTTON -->'} = "<input type='button' value=' Enabled ' onClick='window.location=\"global.cgi?ACTION=WT_TOGGLE&TYPE=DOM&KEY=0\"' style='width: 75; font-size: 8pt; font-family: helvetica;'>"; } 
	else 
		{ $GTOOLS::TAG{'<!-- WT_DOM_BUTTON -->'} = "<input type='button' value=' Disabled ' onClick='window.location=\"global.cgi?ACTION=WT_TOGGLE&TYPE=DOM&KEY=1\"' style='width: 75; font-size: 8pt; font-family: helvetica;'>"; } 

	# set the enabled checkbox status
	if ( (int($webdb{'globalwt_enable'}) & 8) == 8) 
		{ $GTOOLS::TAG{'<!-- WT_INT_BUTTON -->'} = "<input type='button' value=' Enabled ' onClick='window.location=\"global.cgi?ACTION=WT_TOGGLE&TYPE=INT&KEY=0\"' style='width: 75; font-size: 8pt; font-family: helvetica;'>"; } 
	else 
		{ $GTOOLS::TAG{'<!-- WT_INT_BUTTON -->'} = "<input type='button' value=' Disabled ' onClick='window.location=\"global.cgi?ACTION=WT_TOGGLE&TYPE=INT&KEY=8\"' style='width: 75; font-size: 8pt; font-family: helvetica;'>"; } 

	$c = '';
	$hashref = &ZSHIP::GLOBAL::decode_weightbased_string($webdb{'globalwt_dom_data'});
#	print STDERR "Loading .....\n".Dumper($hashref);
	foreach $k (sort { $a <=> $b; } keys %{$hashref})
		{
		($price, $description) = split(' ',$hashref->{$k},2);
		$c .= "<tr align='center'>";
		$c .= "<td><input type='button' onClick='window.location=\"global.cgi?ACTION=DELETE&TYPE=DOM&KEY=$k\";' value=' Delete ' style='width: 75; font-size: 8pt; font-family: helvetica;'></td>";
		$c .= "<td>$k <font size='1'>ounces</font></td>";
		$c .= "<td>\$$price</td>";
		$c .= "</tr>";
		}
	if (length($c)<=0) { $c .= "<tr><td colspan='3'>No entries have been Added</td></tr>"; }
	$c = "<tr bgcolor='3366CC'><td class='title'><font color='white'>ACTION</td><td class='title'><font color='white'>WEIGHT</td><td class='title'><font color='white'>PRICE</td></tr>".$c;
	$GTOOLS::TAG{'<!-- WEIGHT_DOM_TABLE -->'} = $c;

	$c = '';
	## International Table
	$hashref = &ZSHIP::GLOBAL::decode_weightbased_string($webdb{'globalwt_int_data'});
	foreach $k (sort { $a <=> $b; } keys %{$hashref})
		{
		($price, $description) = split(' ',$hashref->{$k},2);
		$c .= "<tr align='center'>";
		$c .= "<td><input type='button' onClick='window.location=\"global.cgi?ACTION=DELETE&TYPE=INT&KEY=$k\";' value=' Delete ' style='width: 75; font-size: 8pt; font-family: helvetica;'></td>";
		$c .= "<td>$k <font size='1'>ounces</font></td>";
		$c .= "<td>\$$price</td>";
		$c .= "</tr>";
		}
	if (length($c)<=0) { $c .= "<tr><td colspan='3'>No entries have been Added</td></tr>"; }
	$c = "<tr bgcolor='3366CC'><td class='title'><font color='white'>ACTION</td><td class='title'><font color='white'>WEIGHT</td><td class='title'><font color='white'>PRICE</td></tr>".$c;
	$GTOOLS::TAG{'<!-- WEIGHT_INT_TABLE -->'} = $c;

	$template_file = 'global.shtml';
	}

print "Content-type: text/html\n";
print "Pragma: no-cache\n"; # HTTP 1.0 non-caching specification
print "Cache-Control: no-cache\n"; # HTTP 1.1 non-caching specification
print "Expires: 0\n"; # HTTP 1.0 way of saying "expire now"

print "\n";
&GTOOLS::output(help=>'#50811',title=>'',file=>'global.shtml',header=>0,bc=>\@BC);
