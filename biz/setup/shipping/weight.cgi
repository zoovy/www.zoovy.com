#!/usr/bin/perl

use lib "/httpd/modules";
require GTOOLS;
require CGI;
require ZOOVY;
require ZWEBSITE;
require ZSHIP;
require ZSHIP::WEIGHT;

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }


$q=new CGI;

$ACTION = $q->param('ACTION');
$TYPE = $q->param('TYPE');

if ($TYPE ne 'INT') { $TYPE eq 'DOM'; }
$TYPE = lc($TYPE);
$GTOOLS::TAG{"<!-- TYPE -->"} = $TYPE;

# load webdb
$webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);

if ($ACTION eq "SAVE")
	{
   if (uc($q->param('weight_dom')) eq "ON")
		{
		print STDERR "enabling ship pickup\n";
		$webdbref->{'weight_dom'} = 1;
		} else {
		print STDERR "disabling ship pickup\n";
		$webdbref->{'weight_dom'} = 0;
		}

   if (uc($q->param('weight_int')) eq "ON")
		{
		$webdbref->{'weight_int'} = 1;
		} else {
		$webdbref->{'weight_int'} = 0;
		}

	$LU->log("SETUP.SHIPPING.WEIGHTBASED","Saved Weight Based Shipping Settings","SAVE");
	&ZWEBSITE::save_website_dbref($USERNAME,$webdbref,$PRT);
	$ACTION = '';
	}


if ($ACTION eq "SAVE-ADD")
	{
	$weight = $q->param('weight');
	$desc = $q->param('description');
	$price = $q->param('price');
	if (defined($weight) && defined($desc) && defined($price))
		{
		$weight =~ s/[^0-9\.]//g;
		$price =~ s/[^0-9\.]//g;
		$desc = substr($desc,0,25);
		$hashref = &ZSHIP::WEIGHT::decode_weightbased_string($webdbref->{'weight_'.$TYPE.'_data'});
		$hashref->{$weight} = "$price $desc";
		$webdbref->{'weight_'.$TYPE.'_data'} = &ZSHIP::WEIGHT::encode_weightbased_string($hashref);
		$LU->log("SETUP.SHIPPING.WEIGHTBASED","Added Weight Based Shipping Method","SAVE");
		&ZWEBSITE::save_website_dbref($USERNAME,$webdbref,$PRT);
		}

	$ACTION = '';
	}

if ($ACTION eq "ADD")
	{
	$template_file = 'weight-add.shtml';
	}

if ($ACTION eq 'DELETE')
	{
	$hashref = &ZSHIP::WEIGHT::decode_weightbased_string($webdbref->{'weight_'.$TYPE.'_data'});
	delete $hashref->{$q->param('KEY')};
	$webdbref->{'weight_'.$TYPE.'_data'} = &ZSHIP::WEIGHT::encode_weightbased_string($hashref);
	$LU->log("SETUP.SHIPPING.WEIGHTBASED","Deleted Weight Based Shipping Method","SAVE");
	&ZWEBSITE::save_website_dbref($USERNAME,$webdbref,$PRT);	
	$ACTION = '';
	}

if ($ACTION eq '')
	{
	# set the enabled checkbox status
	print STDERR $webdbref->{'ship_pickup'}."\n";
	if ($webdbref->{'weight_dom'}>0) { $GTOOLS::TAG{'<!-- DOM_ENABLED -->'} = " checked "; } 
	else { $GTOOLS::TAG{'<!-- DOM_ENABLED -->'} = " "; }
	if ($webdbref->{'weight_int'}>0) { $GTOOLS::TAG{'<!-- INT_ENABLED -->'} = " checked "; } 
	else { $GTOOLS::TAG{'<!-- INT_ENABLED -->'} = " "; }

	$c = '';
	$hashref = &ZSHIP::WEIGHT::decode_weightbased_string($webdbref->{'weight_dom_data'});
	foreach $k (sort { $a <=> $b; } keys %{$hashref})
		{
		($price, $description) = split(' ',$hashref->{$k},2);
		$c .= "<tr><td><a href='weight.cgi?ACTION=DELETE&KEY=$k&TYPE=dom'>[DELETE]</a></td><td>$k <font size='1'>ounces</font></td><td>\$$price</td><td>$description</td></tr>";
		}
	if (length($c)>0)
		{
		$c = "<tr bgcolor='330066'><td class='title'>ACTION</td><td class='title'>WEIGHT</td><td class='title'>PRICE</td><td class='title'>DESCRIPTION</td></tr>".$c;
		} else {
		$c .= "<tr><td>No Entries Have been Added</td></tr>";
		}
	$GTOOLS::TAG{'<!-- DOM_TABLE -->'} = $c;

	$c = '';
	## International Table
	$hashref = &ZSHIP::WEIGHT::decode_weightbased_string($webdbref->{'weight_int_data'});
	foreach $k (sort { $a <=> $b; } keys %{$hashref})
		{
		($price, $description) = split(' ',$hashref->{$k},2);
		$c .= "<tr><td><a href='weight.cgi?ACTION=DELETE&KEY=$k&TYPE=int'>[DELETE]</a></td><td>$k <font size='1'>ounces</font></td><td>\$$price</td><td>$description</td></tr>";
		}
	if (length($c)>0)
		{
		$c = "<tr bgcolor='330066'><td class='title'>ACTION</td><td class='title'>WEIGHT</td><td class='title'>PRICE</td><td class='title'>DESCRIPTION</td></tr>".$c;
		} else {
		$c .= "<tr><td>No Entries Have been Added</td></tr>";
		}
	$GTOOLS::TAG{'<!-- INT_TABLE -->'} = $c;



	$template_file = 'weight.shtml';
	}

my @BC = ();
push @BC, { name=>'Setup',link=>'/biz/setup','target'=>'_top', };
push @BC, { name=>'Shipping',link=>'/biz/setup/shipping','target'=>'_top', };
push @BC, { name=>'Weight Based' };

&GTOOLS::output('*LU'=>$LU,title=>"Shipping: Weight Based Shipping",help=>'#50816',file=>$template_file,header=>1,bc=>\@BC);
