#!/usr/bin/perl -w

use lib "/httpd/modules";
use GTOOLS;
use ZOOVY;
use ZWEBSITE;

&ZOOVY::init();
&GTOOLS::init();

my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("/biz/setup",2,'_S&2');
if ($USERNAME eq '') { exit; }
my $template_file = 'deny.shtml';

if ((index($FLAGS,'L3')>=0) || (index($FLAGS,'D3')>=0)) { $FLAGS .= ',API,'; }


if ($FLAGS !~ /,API,/) {
	# access denied
	$template_file = 'deny.shtml';
	} 
else {
	my $webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME);

	$ACTION = $ZOOVY::cgiv->{'ACTION'};
	if ($ACTION eq "SAVE") {
		my $foo = 
			$ZOOVY::cgiv->{'billing_info'}.','.
			(($ZOOVY::cgiv->{'strip_prices'})?1:0).','.
			(($ZOOVY::cgiv->{'strip_payment'})?1:0).','.
			uc($ZOOVY::cgiv->{'order_format'}).','.	
			(($ZOOVY::cgiv->{'smart_recovery'})?1:0).','.'0,0,0,'.
			$ZOOVY::cgiv->{'export_url'};
		$webdbref->{'order_dispatch_defaults'} = $foo;

		if (not defined $ZOOVY::cgiv->{'inv_api_url'}) { $ZOOVY::cgiv->{'inv_api_url'} = ''; }
		$webdbref->{'inv_api_url'} = $ZOOVY::cgiv->{'inv_api_url'};	
		if (not defined $ZOOVY::cgiv->{'inv_source'}) { $ZOOVY::cgiv->{'inv_source'} = 0; }
		$webdbref->{'inv_source'} = $ZOOVY::cgiv->{'inv_source'};
		if (not defined $ZOOVY::cgiv->{'inv_api_mode'}) { $ZOOVY::cgiv->{'inv_api_mode'} = 0; }
		$webdbref->{'inv_api_mode'} = $ZOOVY::cgiv->{'inv_api_mode'};
		$webdbref->{'order_dispatch_mode'} = $ZOOVY::cgiv->{'order_dispatch_mode'};
		$webdbref->{'order_dispatch_url'} = $ZOOVY::cgiv->{'dispatch_url'};

		&ZWEBSITE::save_website_dbref($USERNAME,$webdbref);
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<font face='arial' color='red' size='4'><b>Successfully Saved Changes!</b></font><br>";
		}

	$foo = $webdbref->{'order_dispatch_defaults'};
	if (!defined($foo) || $foo eq '') {
		($billing_info,$strip_prices,$strip_payment,$format,$recovery) = split(',','2,1,1,ZOOVY,1');
		} else {
		($billing_info,$strip_prices,$strip_payment,$format,$recovery) = split(',',$foo);
		} 

	$GTOOLS::TAG{'<!-- BILLING_INFO_0 -->'} = '';
	$GTOOLS::TAG{'<!-- BILLING_INFO_1 -->'} = '';
	$GTOOLS::TAG{'<!-- BILLING_INFO_2 -->'} = '';
	$GTOOLS::TAG{'<!-- BILLING_INFO_'.$billing_info.' -->'} = 'checked';
	if ($strip_prices) { $GTOOLS::TAG{'<!-- STRIP_PRICES_CHECKED -->'} = 'checked'; } else { $GTOOLS::TAG{'<!-- STRIP_PRICES_CHECKED -->'} = ''; }
	if ($strip_payment) { $GTOOLS::TAG{'<!-- STRIP_PAYMENT_CHECKED -->'} = 'checked'; } else { $GTOOLS::TAG{'<!-- STRIP_PAYMENT_CHECKED -->'} = ''; }

	$GTOOLS::TAG{'<!-- ORDER_FORMAT_ZOOVY -->'} = '';
	$GTOOLS::TAG{'<!-- ORDER_FORMAT_OBI -->'} = '';
	$GTOOLS::TAG{'<!-- ORDER_FORMAT_XML -->'} = '';
	$GTOOLS::TAG{'<!-- ORDER_FORMAT_XCBL -->'} = '';
	$GTOOLS::TAG{'<!-- ORDER_FORMAT_XML108 -->'} = '';
	$GTOOLS::TAG{'<!-- ORDER_FORMAT_'.$format.' -->'} = 'selected';

	$GTOOLS::TAG{'<!-- EXPORT_URL -->'} = $webdbref->{'order_dispatch_url'};
	
	$foo = $webdbref->{'order_dispatch_mode'};
	$GTOOLS::TAG{'<!-- ORDER_DISPATCH_ENABLE_0 -->'} = '';	
	$GTOOLS::TAG{'<!-- ORDER_DISPATCH_ENABLE_1 -->'} = '';	
	$GTOOLS::TAG{'<!-- ORDER_DISPATCH_ENABLE_9 -->'} = '';	
	$GTOOLS::TAG{'<!-- ORDER_DISPATCH_ENABLE_'.$foo.' -->'} = 'selected';

	if ($recovery) { $GTOOLS::TAG{'<!-- RECOVERY_CHECKED -->'} = 'checked'; } else { $GTOOLS::TAG{'<!-- RECOVERY_CHECKED -->'} = ''; }


	my $inv_source_0 = '';
	my $inv_source_1 = '';
	my $inv_source_2 = '';
	if ($webdb{'inv_source'} == 0) { $inv_source_0 = 'checked'; } 
	if ($webdb{'inv_source'} == 1) { $inv_source_1 = 'checked'; } 
	if ($webdb{'inv_source'} == 2) { $inv_source_2 = 'checked'; } 
	my $inv_api_mode_0 = '';
	my $inv_api_mode_1 = '';
	if ($webdb{'inv_api_mode'} == 0) { $inv_api_mode_0 = 'checked'; } 
	if ($webdb{'inv_api_mode'} == 1) { $inv_api_mode_1 = 'checked'; } 

	$GTOOLS::TAG{'<!-- DEVELOPER -->'} = qq~
	<tr><td colspan='2' bgcolor='FFFFFF'>
	<b>Inventory API Settings</b><br>
	&nbsp;&nbsp; <input type='radio' name='inv_source' $inv_source_0 value='0'> Use Local Store Inventory<br>
	&nbsp;&nbsp; <input type='radio' name='inv_source' $inv_source_1 value='1'> Use Local Store Inventory + Remote API<br>
	&nbsp;&nbsp; <input type='radio' name='inv_source' $inv_source_2 value='2'> Use Remote API Only<br>
	<br>
	&nbsp;&nbsp; Remote API URL: <i>(hint: http://webapi.zoovy.com/webapi/merchant/inventoryapi.cgi/USER=store)</i><br>
	&nbsp;&nbsp; <input type='textbox' name='inv_api_url' value='$webdb{'inv_api_url'}' size='90'><br>
	<Br>
	&nbsp;&nbsp; Action on API Failure:<br>
	&nbsp;&nbsp; <input type='radio' name='inv_api_mode' $inv_api_mode_0 value='0'> Return inventory not available (will allow purchase).<br>
	&nbsp;&nbsp; <input type='radio' name='inv_api_mode' $inv_api_mode_1 value='1'> Force inventory quantity to 0 (do not allow purchase).<br>
	</td></tr>
	~;

	$template_file = 'index.shtml';
}

&GTOOLS::output(
   'title'=>'Setup : Order Dispatch',
   'file'=>$template_file,
   'header'=>'1',
   'help'=>'#50672',
   'tabs'=>[
      ],
   'bc'=>[
      { name=>'Setup',link=>'http://www.zoovy.com/biz/setup','target'=>'_top', },
      { name=>'Order Dispatching',link=>'http://www.zoovy.com/biz/setup/dispatch','target'=>'_top', },
      ],
   );
