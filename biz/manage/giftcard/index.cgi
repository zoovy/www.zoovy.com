#!/usr/bin/perl

use URI::Escape;
use lib "/httpd/modules";
require GTOOLS;
require GTOOLS::Table;
require GIFTCARD;
require CUSTOMER;
require CGI;
require ZOOVY;
require ZWEBSITE;
require PRODUCT;
use strict;


require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_ADMIN');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

$GTOOLS::TAG{'<!-- TS -->'} = time();

my $template_file = "index.shtml";
my $VERB = $ZOOVY::cgiv->{'VERB'};
my ($GCID) = int($ZOOVY::cgiv->{'GCID'});
my @MSGS = ();

if ($FLAGS !~ /,CRM,/) {
	$VERB = 'DENIED';
	$template_file = 'denied.shtml';
	}

if ($VERB eq 'SEARCH-NOW') {
	my $searchfor = URI::Escape::uri_escape($ZOOVY::cgiv->{'searchfor'});
	my $cardinfo = undef;

	print STDERR "SEARCH: $searchfor\n";

	if (GIFTCARD::checkCode($searchfor)==0) {
		($cardinfo) = GIFTCARD::lookup($USERNAME,'CODE'=>$searchfor);
		if (not defined $cardinfo) {
			push @MSGS, "WARN|Sorry, the giftcard you are searching for is not valid";
			$VERB = '';
			}
		else {
			## checkCode result of >0 indicates a failure
			## we set GCID if a valid card code, and card exists
			$GCID = $cardinfo->{'GCID'}; $VERB = 'EDIT';
			}
		}
	else {
		## redirect to customer manager
		print "Location: /biz/manage/customer/index.cgi?VERB=SEARCH-NOW&scope=giftcard&searchfor=$searchfor\n\n";
		exit;
		}
	#use Data::Dumper;
	#print STDERR 'CARDINFO' .Dumper($cardinfo,$searchfor,GIFTCARD::checkCode($searchfor));

	}


if ($VERB eq 'SAVEPROD') {

	my $SKU = uc($ZOOVY::cgiv->{'SKU'});
	$SKU =~ s/[^\w\-]+//g;
	$SKU =~ s/^[^A-Z0-9]+//og; # strips anything which not a leading A-Z0-9
	my ($P) = PRODUCT->new($USERNAME,$SKU,'create'=>1);

	my @POGS = ();
	if ($ZOOVY::cgiv->{'ALLOW_NOTE'}) {
		push @POGS, {
			hint=>"Don't forget to include your name and the reason you're sending the giftcard!",
			id=>"#C",
			prompt=>"Gift Message",
			inv=>"0", type=>"textarea", maxlength=>"128", cols=>"40", rows=>"3"			
			};
		}
	if ($ZOOVY::cgiv->{'ALLOW_RECIPIENT'}) {
		push @POGS, {
			id=>"#B", prompt=>"Recipient Email", inv=>"0", type=>"text"
			};
		push @POGS, {
			id=>"#A", prompt=>"Recipient Name", inv=>"0", type=>"text"
			};
		};

	my $RETAIL = $ZOOVY::cgiv->{'RETAIL'};
	$RETAIL =~ s/^\$//;

	$P->store('zoovy:base_price',(defined $RETAIL)?sprintf("%.2f",$RETAIL):'0');
	$P->store('zoovy:base_cost',(defined $RETAIL)?sprintf("%.2f",$RETAIL):'0');
	$P->store('zoovy:taxable',0);
	$P->store('zoovy:prod_name',($RETAIL>0)?sprintf("\$%.2f GiftCard",$RETAIL):'Giftcard');
	$P->store('zoovy:inv_enable',33);
	$P->store('zoovy:fl','p-giftcard');
	$P->store('zoovy:virtual',"PARTNER:GIFTCARD");
	$P->store('zoovy:prod_desc',q~
Or giftcard is the perfect one size fits all gift for any occasion!
~);

	if (int($RETAIL)==0) {
		$RETAIL = undef;
		
		push @POGS,
			{'id'=>"#Z", 'flags'=>1, 'prompt'=>"Gift Amount", 'inv'=>0, 'type'=>'select', 'optional'=>0,
			'@options'=>[
				{ 'v'=>'05', p=>'$5', w=>'0', 'prompt'=>'$5' },
				{ 'v'=>'0A', p=>'$10', w=>'0', 'prompt'=>'$10' },
				{ 'v'=>'19', p=>'$25', w=>'0', 'prompt'=>'$25' },
				{ 'v'=>'32', p=>'$50', w=>'0', 'prompt'=>'$50' },
				{ 'v'=>'64', p=>'$100', w=>'0', 'prompt'=>'$100' },
				]
			};

#		$pogs .= q~<pog id="#Z" flags="1" prompt="Gift Amount" inv="0" type="select" optional="0">
#<option v="05" m="p=$5|w=0">$5</option>
#<option v="0A" m="p=$10|w=0">$10</option>
#<option v="19" m="p=$25|w=0">$25</option>
#<option v="32" m="p=$50|w=0">$50</option>
#<option v="64" m="p=$100|w=0">$100</option>
#</pog>~;
		
		}

	$P->store_pogs(\@POGS);
	$P->folder("/GIFTCARD");
	$P->save();

	$VERB = 'PRODUCTS';
	$GTOOLS::TAG{'<!-- SUCCESS -->'} = "<div class=\"success\">Product $SKU has been created. 
Please go to the Product Editor to map this product to one or more categories on your website.
<br>
<a href=\"/biz/product/index.cgi?VERB=EDIT&PID=$SKU\">[Go Now]</a>

</div>";

	}


if ($VERB eq 'LIST-SERIES') {
	$template_file = 'list-series.shtml';	
	my $seriesrefs = GIFTCARD::list_series($USERNAME);

	my $r = '';
	my $c = '';
	foreach my $sref (@{$seriesrefs}) {
		$r = ($r eq 'r0')?'r1':'r0';
		$c .= "<tr class=\"$r\">";
		my $series_pretty = $sref->{'SRC_SERIES'};
		if ($series_pretty eq '') { $series_pretty = "<i>Series Not Set</i>"; }
		$c .= "<td><a href=\"/biz/manage/giftcard/index.cgi?VERB=SHOW-SERIES&SERIES=$sref->{'SRC_SERIES'}\">$series_pretty</a></td>";
		$c .= "<td>$sref->{'COUNT'}</td>";
		$c .= sprintf("<td>\$%0.2f</td>",$sref->{'BALANCE'});
		$c .= "<td>$sref->{'TXNCNT'}</td>";
		$c .= "<td>".&ZTOOLKIT::pretty_date($sref->{'CREATED_GMT'})."</td>";
		$c .= "</tr>\n";
		}
	if ($c eq '') {
		$c = "<tr><td colspan=5><i>No giftcards created</td></tr>";
		}
	$GTOOLS::TAG{'<!-- SERIES -->'} = $c;
	}


##
##
##
if ($VERB eq 'SAVECARD') {
	my $gcref = {};

	my @LOGS = ();

	my $EXPIRES_GMT = 0;
	if ($ZOOVY::cgiv->{'expires'}) {
		require Date::Parse;
		$EXPIRES_GMT = Date::Parse::str2time(sprintf("%s 23:59:59",$ZOOVY::cgiv->{'expires'}));
		}

	my $BALANCE = sprintf("%.2f",$ZOOVY::cgiv->{'balance'});
	my $CID = 0;
	my $QUANTITY = int($ZOOVY::cgiv->{'quantity'});
	if ($QUANTITY==0) { $QUANTITY = 1; }

	if ($QUANTITY > 1) {
		## we can never create individual gift cards in bulk.
		}
	elsif ($ZOOVY::cgiv->{'email'} ne '') {
		require CUSTOMER;
		$CID = &CUSTOMER::resolve_customer_id($USERNAME,$PRT,$ZOOVY::cgiv->{'email'});
		if ($CID==0) {
			## the customer doesn't exist, create an account.
			my ($c) = CUSTOMER->new($USERNAME,PRT=>$PRT,CREATE=>2,EMAIL=>$ZOOVY::cgiv->{'email'});
			$c->save();
			($CID) = $c->cid();
			push @LOGS, "Created customer account #$CID";
			}
		}

	

	my $cardtype = int($ZOOVY::cgiv->{'cardtype'});

	my $ERROR = undef;
	if ($GCID==0) {
		## some checks before we create new cards.
		if ($ZOOVY::cgiv->{'series'} eq '') {
			## no series specified, no warnings.
			}
		elsif ($QUANTITY==1) {
			$ERROR = "A SERIES identifier is only intended/available for issuing multiple giftcards. hint: try leaving series blank, or re-read the documentation. Series identifiers are optional when issuing less than 50 cards.";
			}
		elsif ($ZOOVY::cgiv->{'email'}) {
			$ERROR = "A SERIES identifier is only intended/available for situations where a giftcard has no specific email address associated with it.";
			}
		elsif ($CID>0) {
			$ERROR = "A SERIES identifier is only intended/available when no customer is specified.";
			}


		if ($QUANTITY==1) {
			}
		elsif (($QUANTITY>0) && ($ZOOVY::cgiv->{'email'})) {
			$ERROR = "Sorry, as a safety mechanism you can only create quantity 1 of a giftcard for a specified customer email. If you actually intended to create multiple giftcards for the same person, you will need to do it by issuing multiple requests.";
			}
		elsif (($QUANTITY>50) && ($ZOOVY::cgiv->{'series'} eq '')) {
			$ERROR = "If you are creating more than 50 giftcards at a time, you MUST use the SERIES functionality";
			}

			
		}

	my @CARDS = ();

	if (defined $ERROR) {
		push @MSGS, "ERROR|$ERROR";
		}
	elsif ($GCID==0) {
		## new card

		my %CARD_VARS = ();
		$CARD_VARS{'NOTE'} = $ZOOVY::cgiv->{'note'};
		$CARD_VARS{'CID'} = $CID;
		$CARD_VARS{'EXPIRES_GMT'} = $EXPIRES_GMT;
		$CARD_VARS{'CREATED_BY'} = $LUSERNAME;
		$CARD_VARS{'CARDTYPE'} = $cardtype;

		if ($ZOOVY::cgiv->{'series'} ne '') {
			$CARD_VARS{'SRC_SERIES'} = uc($ZOOVY::cgiv->{'series'});
			} 

		my ($udbh) = &DBINFO::db_user_connect($USERNAME);
		foreach my $qty (1..$QUANTITY) {
		
			if ($CARD_VARS{'SRC_SERIES'} ne '') { 
				$CARD_VARS{'SRC_GUID'} = sprintf("%s---#%s",$CARD_VARS{'SRC_SERIES'},$qty); 
				}
	
			my ($CODE) = &GIFTCARD::createCard($USERNAME,$PRT,$BALANCE,%CARD_VARS);
			push @CARDS, $CODE;
		
			my ($gcid) = &GIFTCARD::resolve_GCID($USERNAME,$CODE);			
			$LU->log("manage.giftcards.create","Created new card GCID: $gcid","INFO");

			if ($QUANTITY==1) {
				$ZOOVY::cgiv->{'GCID'} = $gcid;
				push @MSGS, "SUCCESS|Created new card: $gcid";
				}
			}
		&DBINFO::db_user_close();

		## NOTE: Don't set $GCID if we are bulk creating cards.
		}
	else {
		## save an (always single) existing card.
		# ($gcref) = &GIFTCARD::lookup($USERNAME,GCID=>$GCID);				
		&GIFTCARD::update($USERNAME,$GCID,
			CID=>$CID,BALANCE=>$BALANCE,NOTE=>$ZOOVY::cgiv->{'note'},
			EXPIRES_GMT=>$EXPIRES_GMT,CID=>$CID,LUSER=>$LUSERNAME,
			CARDTYPE=>$cardtype,
			);
		push @MSGS, "SUCCESS|Updated Card!";
		$LU->log("manage.giftcards.update","Updated new card GCID: $ZOOVY::cgiv->{'GCID'}","INFO");
		}

	## if we had an errors/logs add them to the gift card.
	if ($GCID>0) {
		foreach my $note (@LOGS) {
			GIFTCARD::addLog($USERNAME,$LUSERNAME,$GCID,$note);
			}
		}
	
	if (($CID==0) || ($QUANTITY>1)) {
		## never send email when we don't have a customer account, or we created multiple giftcards.
		}
	elsif ($ZOOVY::cgiv->{'sendemail'} eq 'on') {
		require SITE;
		my ($profile) = &ZOOVY::prt_to_profile($USERNAME,$PRT);
		my ($SITE) = SITE->new($USERNAME,'PRT'=>$PRT,'PROFILE'=>$profile);
		require SITE::EMAILS;
		my ($se) = SITE::EMAILS->new($USERNAME,'*SITE'=>$SITE);
		my ($ERR) = $se->sendmail('AGIFT_NEW',CID=>$CID);
		if ($ERR) {
			push @MSGS, "ERROR|Could not send email (REASON: $ERR)";
			}
		}
	else {
		warn "No email sent";
		}

	if (($ERROR) && ($GCID == 0)) {
		$VERB = 'CREATE';
		}
	elsif ($QUANTITY==1) {
		$VERB = 'EDIT';
		$GCID = $ZOOVY::cgiv->{'GCID'};
		}
	else {
		$VERB = 'BULKLIST';
		$GTOOLS::TAG{'<!-- BULKLIST -->'} = join("\n<br>\n",@CARDS);
		$template_file = 'bulklist.shtml';
		}
	}


if (($VERB eq 'CREATE') || ($VERB eq 'EDIT')) {	
	my $gcref = {};

	if (int($ZOOVY::cgiv->{'CID'})>0) {
		## we'll get passed a CID (customer id) from customer edit		
		$gcref->{'CID'} = int($ZOOVY::cgiv->{'CID'});
		}

	if (($VERB eq 'CREATE') || ($GCID==0)) {
		$GTOOLS::TAG{'<!-- GCID -->'} = '0';
		$GTOOLS::TAG{'<!-- TITLE -->'} = "Create New Card";
		$GTOOLS::TAG{'<!-- HIDE -->'} = qq~style="visibility: collapse;"~;
		$GTOOLS::TAG{'<!-- TRANSACTION_LOG -->'} = qq~<tr><td><i>No transactions have been recorded.</i></td></tr>~;
		$GTOOLS::TAG{'<!-- QUANTITY -->'} = qq~
<tr>
	<td valign="top">Quantity:</td>
	<td>
		<input type="textbox" size="4" name="quantity" value="1"><br>
		<div class="hint">
		HINT: If you select more than quantity 1, no customer or email will be assigned. 
		You may create up to 9,999 giftcards at one time.  A list of pre-authorized card codes will be generated, 
		these can then be merged into a direct mail or other personalized electronic campaign.<br>
		<br>
		REMINDER: Be sure to speak with your accountant regarding gift card liabilities 
and how those will affect your companies balance sheet (especially non-expiring 
cash-equivalent gift cards).

		</div>
	</td>
	<tr>
		<td valign="top">Series Identifier:</td>
		<td>
			<input type="textbox" maxlength="16" size="16" name="series"> <i>(optional)</i>
			<div class="hint">
			Specify a 16 digit series identifier such as "GROUPON YYYYMMDD" or "XYZ TRADESHOW" - 
this will appear in  various reports and dashboards.  

When used - series identifers MUST BE UNIQUE.  If a previous series id is used then cards from the past series will be returned.
This can be useful in the case of a large series where a browser could be closed or crash before the output is recorded.
Series is not compatible with Quantity 1, or when an individual recipient is specified.  
Using SERIES is required when creating more than 50 cards at a time.
			</div>
		</td>
	</tr>
</tr>
~;
		$GTOOLS::TAG{'<!-- CARDTYPE -->'} = qq~
			<select name="cardtype">
			<option value="7">Cash Equivalent</option>
			<option value="3">Promotional</option>
			<option value="1">Exclusive/One Time Use</option>
			</select><br><div class="hint">
		<li> Cash Equivalent the card is a liability until used, equivalent to cash tendered.
		<li> Promotional cards are not a liability and are treated as a coupon.
		<li> Exclusive cards are the same as promotional cards, however only one card may be used per order.
		</div>~;
		}
	else {
		$GTOOLS::TAG{'<!-- GCID -->'} = $GCID;
		$GTOOLS::TAG{'<!-- TITLE -->'} = "Edit Card (# $GCID)";
		($gcref) = &GIFTCARD::lookup($USERNAME,PRT=>$PRT,GCID=>$GCID);	
		$GTOOLS::TAG{'<!-- HIDE -->'} = '';
		
		if ($gcref->{'CARDTYPE'}==1) {
			$GTOOLS::TAG{'<!-- CARDTYPE -->'} = "Exclusive: may not be used with other cards";
			}
		elsif ($gcref->{'CARDTYPE'}==3) {
			$GTOOLS::TAG{'<!-- CARDTYPE -->'} = "Promotional: a combinable coupon (not a liability)";
			}
		if ($gcref->{'CARDTYPE'}==7) {
			$GTOOLS::TAG{'<!-- CARDTYPE -->'} = "Cash Equivalent: combinable, treated as cash tendered.";
			}

		$GTOOLS::TAG{'<!-- cardtype_1 -->'} = ($gcref->{'CARDTYPE'}==1)?'selected':'';
		$GTOOLS::TAG{'<!-- cardtype_3 -->'} = ($gcref->{'CARDTYPE'}==3)?'selected':'';
		$GTOOLS::TAG{'<!-- cardtype_7 -->'} = ($gcref->{'CARDTYPE'}==7)?'selected':'';


#+-------------+----------------------+------+-----+---------+-------+
#| Field       | Type                 | Null | Key | Default | Extra |
#+-------------+----------------------+------+-----+---------+-------+
#| MID         | int(11)              | NO   | MUL | 0       |       |
#| USERNAME    | varchar(20)          | NO   |     | NULL    |       |
#| LUSER       | varchar(10)          | NO   |     | NULL    |       |
#| GCID        | int(10) unsigned     | NO   |     | 0       |       |
#| CREATED_GMT | int(10) unsigned     | NO   |     | 0       |       |
#| NOTE        | varchar(32)          | NO   |     | NULL    |       |
#| TXNCNT      | smallint(5) unsigned | YES  |     | 0       |       |
#| BALANCE     | decimal(7,2)         | YES  |     | NULL    |       |
#+-------------+----------------------+------+-----+---------+-------+
#8 rows in set (0.03 sec)

		
		my $c = '';
		my $logsref = &GIFTCARD::getLogs($USERNAME,$GCID);
		foreach my $ref (@{$logsref}) {
			$c .= "<tr><td align=\"center\">$ref->{'TXNCNT'}</td><td>".&ZTOOLKIT::pretty_date($ref->{'CREATED_GMT'},1)."</td><td>$ref->{'LUSER'}</td><td>$ref->{'NOTE'}</td><td>$ref->{'BALANCE'}</td></tr>";
			}

		if ($c eq '') {
			$c .= "<tr><td><i>ERROR: No transactions have been recorded.</i></td></tr>";
			}
		else {
			$c = qq~
<tr>
	<td class="zoovysub1header">TXN</td>
	<td class="zoovysub1header">CREATED</td>
	<td class="zoovysub1header">USER/APP</td>
	<td class="zoovysub1header">NOTE</td>
	<td class="zoovysub1header">END BALANCE</td>
</tr>
~.$c;
			}
		$GTOOLS::TAG{'<!-- TRANSACTION_LOG -->'} = $c;
		}

	$GTOOLS::TAG{'<!-- BALANCE -->'} = sprintf("%.2f",$gcref->{'BALANCE'});

	$GTOOLS::TAG{'<!-- EMAIL -->'} = '';
	if ($gcref->{'CID'}>0) {
		my ($C) = CUSTOMER->new($USERNAME,CID=>$gcref->{'CID'});
		$GTOOLS::TAG{'<!-- EMAIL -->'} = &ZOOVY::incode($C->get('INFO.EMAIL'));
		}

	$GTOOLS::TAG{'<!-- EXPIRES -->'} = &ZTOOLKIT::pretty_date($gcref->{'EXPIRES_GMT'},-2);
	if ($gcref->{'EXPIRES_GMT'} == 0) { $GTOOLS::TAG{'<!-- EXPIRES -->'} = ''; }

	$GTOOLS::TAG{'<!-- CREATED -->'} = &ZTOOLKIT::pretty_date($gcref->{'CREATED_GMT'});
	$GTOOLS::TAG{'<!-- CREATED_BY -->'} = $gcref->{'CREATED_BY'};
	$GTOOLS::TAG{'<!-- PRT -->'} = $gcref->{'PRT'};
	$GTOOLS::TAG{'<!-- NOTE -->'} = &ZOOVY::incode($gcref->{'NOTE'});
	my $CODE = $gcref->{'CODE'};
	$GTOOLS::TAG{'<!-- CODE -->'} = sprintf("%s-%s-%s-%s",substr($CODE,0,4),substr($CODE,4,4),substr($CODE,8,4),substr($CODE,12));

	$GTOOLS::TAG{'<!-- TRANSCNT -->'} = $gcref->{'TXNCNT'};
	$GTOOLS::TAG{'<!-- LAST_ORDER -->'} = ($gcref->{'LAST_ORDER'} eq '')?'<i>None</i>':$gcref->{'LAST_ORDER'};

	$template_file = 'edit.shtml';
	}





if ($VERB eq 'PRODUCTS') {
	$template_file = 'products.shtml';
	}

if (($VERB eq '') || ($VERB eq 'SHOW-SERIES')) {

	my ($udbh) = &DBINFO::db_user_connect($USERNAME);
	my $webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
	if (($webdbref->{'pay_giftcard'} eq 'NONE') || ($webdbref->{'pay_giftcard'} eq '')) {
		my $c = qq~<div class="warning">WARNING: You do not have giftcards enabled. Please go to Setup / Payment Settings and enable this as a payment method.</div>~;
		$GTOOLS::TAG{'<!-- WARNING -->'} = $c;
		}

	my %VARS = ();
	$VARS{'PRT'} = $PRT;
	if ($VERB eq '') { 
		$GTOOLS::TAG{'<!-- TITLE -->'} = "Recent Certificates (250 Max)";
		$VARS{'LIMIT'} = 250; 
		}
	if ($VERB eq 'SHOW-SERIES') { 
		$VARS{'SERIES'} = $ZOOVY::cgiv->{'SERIES'}; 
		$GTOOLS::TAG{'<!-- TITLE -->'} = "Giftcards in Series: $VARS{'SERIES'}";
		if ($VARS{'SERIES'} eq '') {
			$GTOOLS::TAG{'<!-- TITLE -->'} = "Giftcards NOT in Series";
			}
		}

	my $inforef = &GIFTCARD::list($USERNAME,%VARS);

	my @rows = ();
	foreach my $info (@{$inforef}) {

		my $email = '';
		if ($info->{'CID'}>0) {
			$email = &CUSTOMER::resolve_email($USERNAME,$PRT,$info->{'CID'});
			}

		if ($info->{'LAST_ORDER'} eq '') { $info->{'LAST_ORDER'} = '<i>None</i>'; }

		push @rows, [ 
			1,
			"<center><a href=\"/biz/manage/giftcard/index.cgi?VERB=EDIT&GCID=$info->{'ID'}\"><img width=15 height=20 border=0 src=\"/biz/images/arrows/v_edit-15x20.gif\"></a></center>",
			&GIFTCARD::obfuscateCode($info->{'CODE'}),
			&ZTOOLKIT::pretty_date($info->{'CREATED_GMT'},2),
			&ZTOOLKIT::pretty_date($info->{'EXPIRES_GMT'},2),
			sprintf("%s",$info->{'LAST_ORDER'}),
			$email,
			$info->{'NOTE'},
			$info->{'BALANCE'},
			$info->{'TXNCNT'},
			$info->{'TYPE'},
			$info->{'SRC_SERIES'},
			];
		}
	

	if (@rows==0) {
		push @rows, [ 0, "", "No Giftcards found" ];
		}

	#my $c = '';
	#foreach my $row (@rows) {
	#	$c .= "<tr><td>".join("</td><td>",@{$row})."</td></tr>\n";
	#	}
	#$GTOOLS::TAG{'<!-- ROWS -->'} = $c;


	$GTOOLS::TAG{'<!-- CARDTABLE -->'} = 
		&GTOOLS::Table::buildTable([
		{ width=>0, title=>'', type=>'rowid', },
		{ width=>50, title=>'', },
		{ width=>200, title=>'Code' },
		{ width=>200, title=>'Created' },
		{ width=>200, title=>'Expires' },
		{ width=>100, title=>'Last Order' },
		{ width=>100, title=>'Customer' },
		{ width=>100, title=>'Note' },
		{ width=>100, title=>'Balance' },
		{ width=>100, title=>'Txn#' },
		{ width=>100, title=>'Type' },
		{ width=>100, title=>'Series' }
		],
		\@rows,		
		rowid=>0,
		);

	&DBINFO::db_user_close();
	}

my @TABS = ();
push @TABS, { name=>'Recent', selected=>($VERB eq '')?1:0, link=>'/biz/manage/giftcard/index.cgi?VERB=' };
push @TABS, { name=>'Create Card', selected=>($VERB eq 'CREATE')?1:0, link=>'/biz/manage/giftcard/index.cgi?VERB=CREATE' };
push @TABS, { name=>'Card Series', selected=>($VERB eq 'LIST-SERIES')?1:0, link=>'/biz/manage/giftcard/index.cgi?VERB=LIST-SERIES' };
push @TABS, { name=>'Products', link=>'/biz/manage/giftcard/index.cgi?VERB=PRODUCTS' };


&GTOOLS::output('*LU'=>$LU,'*LU'=>$LU,file=>$template_file,bc=>[
	{ name=>'Utilities' },
	{ name=>'Gift Cards' }
	],
	msgs=>\@MSGS,
	tabs=>\@TABS,
	header=>1,
	jquery=>1,
	);
