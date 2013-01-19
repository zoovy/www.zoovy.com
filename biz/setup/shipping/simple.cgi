#!/usr/bin/perl

use lib "/httpd/modules"; 
use CGI;
require GTOOLS;
require ZOOVY;
require ZWEBSITE;	
require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }


	
$q = new CGI;

my @BC = ();
push @BC, { name=>'Setup',link=>'/biz/setup','target'=>'_top', };
push @BC, { name=>'Shipping',link=>'/biz/setup/shipping','target'=>'_top', };
push @BC, { name=>'Simple Shipping' };


if (defined($q->param('MESSAGE')))
	{
	$GTOOLS::TAG{"<!-- MESSAGE -->"} = "<br><table border='2' width='80%' align='center'><tr><td><center><font color='red' size='4' face='helvetica'><b>".$q->param('MESSAGE')."</b></font></center></td></tr></table><br>";
	}

$FLAGS = ZOOVY::RETURN_CUSTOMER_FLAGS($USERNAME);
if ($FLAGS !~ /L1/)
   {
    $GTOOLS::TAG{"<!-- HIDE_L1_ONLY -->"} = " <!-- ";
    $GTOOLS::TAG{"<!-- END_HIDE_L1_ONLY -->"} = " --> ";
   }


$ACTION = $q->param('ACTION');

my $template_file = "simple.shtml";

%webdb = &ZWEBSITE::fetch_website_db($USERNAME,$PRT);

if ($ACTION eq "SAVE")
	{ 
	$webdb{"simple_dom"} = 0;
	if ($q->param('SIMPLE_DOM_ENABLED'))
		{ $webdb{"simple_dom"} += 1; } 
	if ($q->param('SIMPLE2_DOM_ENABLED'))
		{ $webdb{"simple_dom"} += 2; } 
	if ($q->param('SIMPLE4_DOM_ENABLED'))
		{ $webdb{"simple_dom"} += 4; } 
 
	print STDERR "SIMPLE_DOM is: ".$webdb{"simple_dom"}."\n";

	$webdb{"simple_dom_carrier"} = $q->param('SIMPLE_DOM_CARRIER');
	if ($webdb{"simple_dom_carrier"} eq '') { $webdb{'simple_dom_carrier'} = 'Standard Shipping'; }
	$webdb{"simple2_dom_carrier"} = $q->param('SIMPLE2_DOM_CARRIER');
	if ($webdb{"simple2_dom_carrier"} eq '') { $webdb{'simple2_dom_carrier'} = 'Priority Shipping'; }
	$webdb{"simple4_dom_carrier"} = $q->param('SIMPLE4_DOM_CARRIER');
	if ($webdb{"simple4_dom_carrier"} eq '') { $webdb{'simple4_dom_carrier'} = 'Custom Shipping'; }

	$webdb{"simple_dom_first"} = $q->param('SIMPLE_DOM_FIRST')+0;
	$webdb{"simple_dom_next"} = $q->param('SIMPLE_DOM_NEXT')+0;
	$webdb{"simple2_dom_first"} = $q->param('SIMPLE2_DOM_FIRST')+0;
	$webdb{"simple2_dom_next"} = $q->param('SIMPLE2_DOM_NEXT')+0;
	$webdb{"simple4_dom_first"} = $q->param('SIMPLE4_DOM_FIRST')+0;
	$webdb{"simple4_dom_next"} = $q->param('SIMPLE4_DOM_NEXT')+0;

	$webdb{'simple_int'} = 0;
	if ($q->param('SIMPLE_INT_ENABLED'))
		{ $webdb{"simple_int"} += 1; } 
	if ($q->param('SIMPLE2_INT_ENABLED'))
		{ $webdb{"simple_int"} += 2; } 
	if ($q->param('SIMPLE4_INT_ENABLED'))
		{ $webdb{"simple_int"} += 4; } 

	$webdb{"simple_int_carrier"} = $q->param('SIMPLE_INT_CARRIER');
	if ($webdb{"simple_int_carrier"} eq '') { $webdb{'simple_int_carrier'} = 'Shipping'; }
	$webdb{"simple2_int_carrier"} = $q->param('SIMPLE2_INT_CARRIER');
	if ($webdb{"simple2_int_carrier"} eq '') { $webdb{'simple2_int_carrier'} = 'Shipping'; }
	$webdb{"simple4_int_carrier"} = $q->param('SIMPLE4_INT_CARRIER');
	if ($webdb{"simple4_int_carrier"} eq '') { $webdb{'simple4_int_carrier'} = 'Shipping'; }

	$webdb{"simple_int_first"} = $q->param('SIMPLE_INT_FIRST')+0;
	$webdb{"simple_int_next"} = $q->param('SIMPLE_INT_NEXT')+0;
	$webdb{"simple2_int_first"} = $q->param('SIMPLE2_INT_FIRST')+0;
	$webdb{"simple2_int_next"} = $q->param('SIMPLE2_INT_NEXT')+0;
	$webdb{"simple4_int_first"} = $q->param('SIMPLE4_INT_FIRST')+0;
	$webdb{"simple4_int_next"} = $q->param('SIMPLE4_INT_NEXT')+0;
	$GTOOLS::TAG{"<!-- MESSAGE -->"} = "<br><table border='2' width='80%' align='center'><tr><td><center><font color='red' size='4' face='helvetica'><b>Successfully Saved!</b></font></center></td></tr></table><br>";

	$LU->log("SETUP.SHIPPING.SIMPLE","Saved Simple Shipping Settings","SAVE");
	&ZWEBSITE::save_website_dbref($USERNAME,\%webdb,$PRT);		
	}


  if (length($webdb{"simple_dom_carrier"})<=0) { $VALUE = "Standard Shipping"; } else { $VALUE = $webdb{"simple_dom_carrier"}; }
  $GTOOLS::TAG{"<!-- DOM_SIMPLE_CARRIER_VALUE -->"} = "$VALUE";
  if (length($webdb{"simple2_dom_carrier"})<=0) { $VALUE = "Priority Shipping"; } else { $VALUE = $webdb{"simple2_dom_carrier"}; }
  $GTOOLS::TAG{"<!-- DOM_SIMPLE2_CARRIER_VALUE -->"} = "$VALUE";
  if (length($webdb{"simple4_dom_carrier"})<=0) { $VALUE = "Custom Shipping"; } else { $VALUE = $webdb{"simple4_dom_carrier"}; }
  $GTOOLS::TAG{"<!-- DOM_SIMPLE4_CARRIER_VALUE -->"} = "$VALUE";


  $GTOOLS::TAG{"<!-- DOM_SIMPLE_FIRST_VALUE -->"} = ($webdb{"simple_dom_first"})?$webdb{"simple_dom_first"}:0;
  $GTOOLS::TAG{"<!-- DOM_SIMPLE_NEXT_VALUE -->"} = ($webdb{"simple_dom_next"})?$webdb{"simple_dom_next"}:0;
  $GTOOLS::TAG{"<!-- DOM_SIMPLE2_FIRST_VALUE -->"} = ($webdb{"simple2_dom_first"})?$webdb{"simple2_dom_first"}:0;
  $GTOOLS::TAG{"<!-- DOM_SIMPLE2_NEXT_VALUE -->"} = ($webdb{"simple2_dom_next"})?$webdb{"simple2_dom_next"}:0;
  $GTOOLS::TAG{"<!-- DOM_SIMPLE4_FIRST_VALUE -->"} = ($webdb{"simple4_dom_first"})?$webdb{"simple4_dom_first"}:0;
  $GTOOLS::TAG{"<!-- DOM_SIMPLE4_NEXT_VALUE -->"} = ($webdb{"simple4_dom_next"})?$webdb{"simple4_dom_next"}:0;

	print STDERR $webdb{"simple_dom"} ."\n";
  if ( (int($webdb{"simple_dom"}) & 1) == 1 ) { $checked = "checked"; } else { $checked=""; }  
  $GTOOLS::TAG{"<!-- DOM_SIMPLE_ENABLED -->"} = " $checked ";  
  if ( (int($webdb{"simple_dom"}) & 2) == 2 ) { $checked = "checked"; } else { $checked=""; }  
  $GTOOLS::TAG{"<!-- DOM_SIMPLE2_ENABLED -->"} = " $checked ";  
  if ( (int($webdb{"simple_dom"}) & 4) == 4) { $checked = "checked"; } else { $checked=""; }  
  $GTOOLS::TAG{"<!-- DOM_SIMPLE4_ENABLED -->"} = " $checked ";  


  if ( (int($webdb{"simple_int"}) & 1) == 1 ) { $checked = "checked"; } else { $checked=""; }  
  $GTOOLS::TAG{"<!-- INT_SIMPLE_ENABLED -->"} = " $checked ";  
  if ( (int($webdb{"simple_int"}) & 2) == 2 ) { $checked = "checked"; } else { $checked=""; }  
  $GTOOLS::TAG{"<!-- INT_SIMPLE2_ENABLED -->"} = " $checked ";  
  if ( (int($webdb{"simple_int"}) & 4) == 4 ) { $checked = "checked"; } else { $checked=""; }  
  $GTOOLS::TAG{"<!-- INT_SIMPLE4_ENABLED -->"} = " $checked ";  

  if (length($webdb{"simple_int_carrier"})<=0) { $VALUE = "Shipping"; } else { $VALUE = $webdb{"simple_int_carrier"}; }
  $GTOOLS::TAG{"<!-- INT_SIMPLE_CARRIER_VALUE -->"} = "$VALUE"; 
  $GTOOLS::TAG{"<!-- INT_SIMPLE_FIRST_VALUE -->"} = ($webdb{"simple_int_first"})?$webdb{"simple_int_first"}:0;
  $GTOOLS::TAG{"<!-- INT_SIMPLE_NEXT_VALUE -->"} = ($webdb{"simple_int_next"})?$webdb{"simple_int_next"}:0;

  if (length($webdb{"simple2_int_carrier"})<=0) { $VALUE = "Shipping"; } else { $VALUE = $webdb{"simple2_int_carrier"}; }
  $GTOOLS::TAG{"<!-- INT_SIMPLE2_CARRIER_VALUE -->"} = "$VALUE"; 
  $GTOOLS::TAG{"<!-- INT_SIMPLE2_FIRST_VALUE -->"} = ($webdb{"simple2_int_first"})?$webdb{"simple2_int_first"}:0;
  $GTOOLS::TAG{"<!-- INT_SIMPLE2_NEXT_VALUE -->"} = ($webdb{"simple2_int_next"})?$webdb{"simple2_int_next"}:0;

  if (length($webdb{"simple4_int_carrier"})<=0) { $VALUE = "Shipping"; } else { $VALUE = $webdb{"simple4_int_carrier"}; }
  $GTOOLS::TAG{"<!-- INT_SIMPLE4_CARRIER_VALUE -->"} = "$VALUE"; 
  $GTOOLS::TAG{"<!-- INT_SIMPLE4_FIRST_VALUE -->"} = ($webdb{"simple4_int_first"})?$webdb{"simple4_int_first"}:0;
  $GTOOLS::TAG{"<!-- INT_SIMPLE4_NEXT_VALUE -->"} = ($webdb{"simple4_int_next"})?$webdb{"simple4_int_next"}:0;
	
&GTOOLS::output('*LU'=>$LU,title=>"PRT: $PRT".' Shipping: Simple Shipping',help=>'#50814',file=>$template_file,header=>1,bc=>\@BC);


