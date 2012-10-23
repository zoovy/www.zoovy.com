#!/usr/bin/perl -w
use strict;

use lib "/httpd/modules";
require GTOOLS;
require ZOOVY;
require AUTH;


# gotta run init so we read in the cookies
&ZOOVY::init();
&GTOOLS::init();

if ($ZOOVY::cookies->{'zjsid'} ne '') {
	&AUTH::fake_setup_global_vars($ZOOVY::cookies->{'zjsid'});
	print STDERR "ZOOVY::USER: $ZOOVY::USERNAME\n";
	# $ZOOVY::USERNAME = $ZOOVY::cookies->{'zjsid'};
	print STDERR "ZOOVY SESSIN: $ZOOVY::cookies->{'zjsid'}\n";
	}

#my $html = '';
#$html .= '<a href="external/body.shtml" target="body" onMouseOver="mousein(1)" onMouseOut="mouseout(1)" onFocus="this.blur()"><img name="link1" border="0" width="80" height="20" src="images/incomplete.gif"></a>&nbsp;';
#$html .= '<a href="recent.shtml" target="body" onMouseOver="mousein(2)" onMouseOut="mouseout(2)" onFocus="this.blur()"><img name="link2" border="0" width="80" height="20" src="images/recent.gif"></a>';
#$html .= '<a href="pending.shtml" target="body" onMouseOver="mousein(3)" onMouseOut="mouseout(3)" onFocus="this.blur()"><img name="link3" border="0" width="80" height="20" src="images/pending.gif"></a>';
#$html .= '<a href="approved.shtml" target="body" onMouseOver="mousein(4)" onMouseOut="mouseout(4)" onFocus="this.blur()"><img name="link4" border="0" width="80" height="20" src="images/approved.gif"></a>';
#$html .= '<a href="completed.shtml" target="body" onMouseOver="mousein(5)" onMouseOut="mouseout(5)" onFocus="this.blur()"><img name="link5" border="0" width="80" height="20" src="images/completed.gif"></a>';
#$html .= '<a href="cancelled.shtml" target="body" onMouseOver="mousein(6)" onMouseOut="mouseout(6)" onFocus="this.blur()"><img name="link6" border="0" width="80" height="20" src="images/cancelled.gif"></a>&nbsp;';
#$html .= '<a href="search.shtml" target="body" onMouseOver="mousein(7)" onMouseOut="mouseout(7)" onFocus="this.blur()"><img name="link7" border="0" width="80" height="20" src="images/search2.gif"></a>';
# &GTOOLS::print_form($html,'title.shtml',1,'guide/orderoverview.php');


&GTOOLS::output(
	'title'=>'Orders',
	'file'=>'title.shtml',
	'header'=>'1',
	'tabs'=>[
		{ button=>1, name=>'[Create]',link=>'external/fastorder.cgi','target'=>'body', },
		{ name=>'Incomplete',link=>'external/body.shtml','target'=>'body', },
		{ name=>'Recent',link=>'body.cgi?CMD=RECENT','target'=>'body', },
		{ name=>'Review',link=>'body.cgi?CMD=REVIEW','target'=>'body', },
		{ name=>'Hold',link=>'body.cgi?CMD=HOLD','target'=>'body', },
		{ name=>'Pending',link=>'body.cgi?CMD=PENDING','target'=>'body', },
		{ name=>'Approved',link=>'body.cgi?CMD=APPROVED','target'=>'body', },
		{ name=>'Processing',link=>'body.cgi?CMD=PROCESS','target'=>'body', },
		{ name=>'Completed',link=>'body.cgi?CMD=COMPLETED','target'=>'body', },
		{ name=>'Cancelled',link=>'body.cgi?CMD=CANCELLED','target'=>'body', },
		{ name=>'Search',link=>'search.shtml','target'=>'body', },
		],
	'bc'=>[
		{ name=>'Orders',link=>'https://www.zoovy.com/biz/orders','target'=>'_top', },
		],
	);

