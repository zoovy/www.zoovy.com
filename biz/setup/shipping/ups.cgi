#!/usr/bin/perl

use lib "/httpd/modules"; 
require CGI;
require GTOOLS;
require ZOOVY;
require ZWEBSITE;	
require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }


my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("/biz/setup",2,'_S&8');
if ($USERNAME eq '') { exit; }

my @BC = ();
push @BC, { name=>'Setup',link=>'/biz/setup','target'=>'_top', };
push @BC, { name=>'Shipping',link=>'/biz/setup/shipping','target'=>'_top', };
push @BC, { name=>'UPS Legacy' };

	
$q = new CGI;
print $q->header;

if (defined($q->param('MESSAGE')))
	{
	$GTOOLS::TAG{"<!-- MESSAGE -->"} = "<br><table border='2' width='80%' align='center'><tr><td><center><font color='red' size='4' face='helvetica'><b>".$q->param('MESSAGE')."</b></font></center></td></tr></table><br>";
	}


$GTOOLS::HEADER_IMAGE = "shipping_options";


$ACTION = $q->param('ACTION');

my $template_file = "index.shtml";


	if ($FLAGS =~ /,SHIP,/)
		{
		$GTOOLS::HEADER_IMAGE = "ups_configuration";
		$template_file = "ups.shtml"; 
		} else {
		$template_file = "noaccess.shtml";
		}

%webdb = &ZWEBSITE::fetch_website_db($USERNAME,$PRT);

  
  if ($ACTION eq "SAVE")
    {
	if ($q->param('ups_dom')) { $webdb{"ups_dom"} = 1; } else { $webdb{"ups_dom"} = 0; }
     $webdb{"ups_dom_nextday"} = $q->param('ups_dom_nextday'); 
     $webdb{"ups_dom_ground"} = $q->param('ups_dom_ground');
     $webdb{"ups_dom_2day"} = $q->param('ups_dom_2day');
     $webdb{"ups_dom_3day"} = $q->param('ups_dom_3day');
     $webdb{"ups_dom_handling"} = $q->param('ups_dom_handling');

if ($q->param('ups_int')) { $webdb{"ups_int"} = 1; } else { $webdb{"ups_int"} = 0; }
     $webdb{"ups_int_nextday"} = $q->param('ups_int_nextday');
     $webdb{"ups_int_nextnoon"} = $q->param('ups_int_nextnoon');
     $webdb{"ups_int_3day"} = $q->param('ups_int_3day');
     $webdb{"ups_int_handling"} = $q->param('ups_int_handling');

		$GTOOLS::TAG{"<!-- MESSAGE -->"} = "<br><table border='2' width='80%' align='center'><tr><td><center><font color='red' size='4' face='helvetica'><b>Successfully Saved UPS settings!</b></font></center></td></tr></table><br>";

	$LU->log("SETUP.SHIPPING.UPS","Saved UPS Legacy Settings","SAVE");
  &ZWEBSITE::save_website_dbref($USERNAME,\%webdb,$PRT);		
  }

#
# UPS
# if neither simple or complex has been selected, default to complex
#   w/actual rate.
# <!-- 
# <!-- UPS_SHIPMETHODS_FLAT --> = SELECTED"
# <!-- UPS_SHIPMETHODS_WEIGHT --> = SELECTED/""
# <!-- UPS_FLATPRICE -->
 
	$GTOOLS::TAG{"<!-- UPS_DOM_FLATPRICE -->"} =  $webdb{"ups_dom_flatprice"};
	$UPS_DOM_HANDLING = $webdb{"ups_dom_handling"};
   if ($webdb{"ups_dom"} >0)
        { $GTOOLS::TAG{"<!-- UPS_DOM_ENABLED -->"} = "CHECKED"; } 
   else { $GTOOLS::TAG{"<!-- UPS_DOM_ENABLED -->"} = ""; } 

  if ($webdb{"ups_dom_method"} =~ /flat/i)
     {
       $GTOOLS::TAG{"<!-- UPS_DOM_METHOD_FLAT -->"} = "CHECKED";
       $UPS_DOM_METHOD_WEIGHT = "";
     } else {
       $GTOOLS::TAG{"<!-- UPS_DOM_METHOD_FLAT -->"} = "";
       $UPS_DOM_METHOD_WEIGHT = "CHECKED";
     }

   if ($webdb{"ups_dom_nextday"} >0)
      { $UPS_DOM_NEXTDAY = "CHECKED";
      } else { $UPS_DOM_NEXTDAY = ""; }

   if ($webdb{"ups_dom_ground"} >0)
      { $UPS_DOM_GROUND = "CHECKED";
      } else { $UPS_DOM_GROUND = ""; }

   if ($webdb{"ups_dom_2day"} >0)
      { $UPS_DOM_2DAY = "CHECKED";
      } else { $UPS_DOM_2DAY = ""; }

   if ($webdb{"ups_dom_3day"} >0)
      { $UPS_DOM_3DAY = "CHECKED";
      } else { $UPS_DOM_3DAY = ""; }

     # 
     # International Support
     #	
   if ($webdb{"ups_int"} >0)
        { $GTOOLS::TAG{"<!-- UPS_INT_ENABLED -->"} = "CHECKED"; } 
   else { $GTOOLS::TAG{"<!-- UPS_INT_ENABLED -->"} = ""; } 
  $GTOOLS::TAG{"<!-- UPS_INT_FLATPRICE -->"} = $webdb{"ups_int_flatprice"};
  $UPS_INT_HANDLING = $webdb{"ups_int_handling"};
  if ($webdb{"ups_int_method"} =~ /flat/i)
     {
       $GTOOLS::TAG{"<!-- UPS_INT_METHOD_FLAT -->"} = "CHECKED";
       $UPS_INT_METHOD_WEIGHT = "";
     } else {
       $GTOOLS::TAG{"<!-- UPS_INT_METHOD_FLAT -->"} = "";
       $UPS_INT_METHOD_WEIGHT = "CHECKED";
     }

   # shipping methods	
   if ($webdb{"ups_int_nextday"} >0)
        { $UPS_INT_NEXTDAY_ENABLED = "CHECKED"; } 
   else { $UPS_INT_NEXTDAY_ENABLED = ""; } 
   if ($webdb{"ups_int_nextnoon"} >0)
        { $UPS_INT_NEXTNOON_ENABLED = "CHECKED"; } 
   else { $UPS_INT_NEXTNOON_ENABLED = ""; } 
   if ($webdb{"ups_int_3day"} >0)
        { $UPS_INT_3DAY_ENABLED = "CHECKED"; } 
   else { $UPS_INT_3DAY_ENABLED = ""; } 
   

   if ($webdb{"ship_int_risk"} eq "none")
      {
      # these tags make the ups int options hidden in a comment
      $GTOOLS::TAG{"<!-- UPS_HIDE_INT_BEGIN -->"} = "<!--";
      $GTOOLS::TAG{"<!-- UPS_HIDE_INT_END -->"} = "--->";
      } else {
      $GTOOLS::TAG{"<!-- UPS_HIDE_INT_BEGIN -->"} = "";
      $GTOOLS::TAG{"<!-- UPS_HIDE_INT_END -->"} = "";
      }


$GTOOLS::TAG{"<!-- UPS_DOM_WEIGHT -->"} = "";
$GTOOLS::TAG{"<!-- UPS_INT_WEIGHT -->"} = "";

 if ($FLAGS =~ /,BASIC,/) {
	$foo = "";
	$foo .= "<font face=\"Arial\">";
	$foo .= "<input type=\"checkbox\" $UPS_DOM_NEXTDAY  name=\"ups_dom_nextday\" value=\"1\">Next Day Services (Early AM/Priority/Saver)<br>";
	$foo .= "<input type=\"checkbox\" $UPS_DOM_2DAY  name=\"ups_dom_2day\" value=\"1\">Two Day Express<br>";
	$foo .= "<input type=\"checkbox\" $UPS_DOM_3DAY  name=\"ups_dom_3day\" value=\"1\">Three Day Express<br>";
	$foo .= "<input type=\"checkbox\" $UPS_DOM_GROUND  name=\"ups_dom_ground\" value=\"1\">Ground<br>";
	$foo .= "<br>";
	$foo .= "Additional Handling Charge: <input type=\"textbox\" size='6' name=\"ups_dom_handling\" value=\"$UPS_DOM_HANDLING\"><br>";
	$GTOOLS::TAG{"<!-- UPS_DOM_WEIGHT -->"} = $foo;

	$foo = "";
	$foo .= "<font face=\"Arial\">";
	$foo .= "<input type=\"checkbox\" $UPS_INT_NEXTDAY_ENABLED  name=\"ups_int_nextday\" value=\"1\">Next Day Priority<br>";
	$foo .= "<input type=\"checkbox\" $UPS_INT_NEXTNOON_ENABLED  name=\"ups_int_nextnoon\" value=\"1\">Next Day Saver<br>";
	$foo .= "<input type=\"checkbox\" $UPS_INT_3DAY_ENABLED  name=\"ups_int_3day\" value=\"1\">Three Day Express<br>";
	$foo .= "<br>";
	$foo .= "Additional Handling Charge: <input type=\"textbox\" size='6' name=\"ups_int_handling\" value=\"$UPS_INT_HANDLING\"><br>";
	$GTOOLS::TAG{"<!-- UPS_INT_WEIGHT -->"} = $foo;
	}


&GTOOLS::output('*LU'=>$LU,help=>'#50818',title=>'Shipping: UPS Shipping (LEGACY)',header=>1,file=>$template_file);


exit;


