#!/usr/bin/perl

use lib "/httpd/modules";
use GTOOLS;
use ZOOVY;

&GTOOLS::init();
&ZOOVY::authenticate();
# load the flags from the cookie

if ($ZOOVY::FLAGS =~ /L1/) { 
	$ZOOVY::FLAGS .= ',EBAY,'; 
	if ($ZOOVY::FLAGS=~ /DEV/) { $ZOOVY::FLAGS .= ',DEV2,'; } 
	}

$c = qq~
<center><table cellpadding="0" border="0" cellspacing="0"><tr><td><img src="/images/blank.gif" height="4" width="10"></td></tr><tr><td>
<table cellspacing="1" cellpadding="0" border="0"><tr>
<td  bgcolor="FFFFFF"><a target="main" href="main.cgi" onMouseOver="mousein(1)" onMouseOut="mouseout(1)" onFocus="this.blur()"><img NAME="link1" SRC="images/general_green.gif" border=0 width="106" height="16" hspace="0" vspace="0"></a></td>
<td  bgcolor="FFFFFF"><a target="main" href="credit.cgi?ACTION=JUMP" onMouseOver="mousein(2)" onMouseOut="mouseout(2)" onFocus="this.blur()"><img NAME="link2" SRC="images/credit_green.gif" border=0 width="106" height="16" hspace="0" vspace="0"></a></td>
~;

if ($ZOOVY::FLAGS =~ /,EBAY,/) {
$c .= qq~
<td  bgcolor="FFFFFF"><a target="main" href="paypal.cgi" onMouseOver="mousein(5)" onMouseOut="mouseout(5)" onFocus="this.blur()"><img NAME="link5" SRC="images/paypal_green.gif" border=0 width="106" height="16" hspace="0" vspace="0"></a></td>
<td  bgcolor="FFFFFF"><a target="main" href="special.cgi" onMouseOver="mousein(3)" onMouseOut="mouseout(3)" onFocus="this.blur()"><img NAME="link3" SRC="images/special_green.gif" border=0 width="106" height="16" hspace="0" vspace="0"></a></td>
~;
}

if (index($ZOOVY::FLAGS,',DEV2,')>=0) {
$c .= qq~
<td  bgcolor="FFFFFF"><a target="main" href="advanced.cgi" onMouseOver="mousein(4)" onMouseOut="mouseout(4)" onFocus="this.blur()"><img NAME="link4" SRC="images/advanced_green.gif" border=0 width="106" height="16" hspace="0" vspace="0"></a></td>
~;
}


$c .= qq~
</tr></table>
</td></tr></table>		   
</center>
~;

&GTOOLS::print_form($c,"title.shtml",1,'topic/payment.php');
