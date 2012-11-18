#!/usr/bin/perl

use lib "/httpd/modules";
require GTOOLS;
require LUSER;
use strict;
require GTOOLS;
require ZOOVY;
require ZTOOLKIT;
require DBINFO;
require ORDER::BATCH;
require CART2;
require LUSER;
#require DBINFO;
#require GTOOLS;
#require ZOOVY;
#require ZSHIP;
#require CART2;
#require INVENTORY;
require ZWEBSITE;
require PRODUCT;

my @MSGS = ();
my ($LU) = LUSER->authenticate(flags=>'_O&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $template_file = '';

# if (index($FLAGS,'BASIC')==-1) { print "Location: /biz\n\n"; exit; }

my $MAX = 1000;


my $VERB = $ZOOVY::cgiv->{'VERB'};
if ($VERB eq '') { $VERB = 'SHOW:RECENT'; }

my $webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
my $gref = &ZWEBSITE::fetch_globalref($USERNAME);

my ($orderset,$statusref,$createdref,$resultar);

my $total = 0;
my $count = 0;
my $startts = time()-(86400*180);
$GTOOLS::TAG{'<!-- TIME -->'} = time();

my $a = "";   # this is used throughout the program as scratch

my $OID = $ZOOVY::cgiv->{'OID'};
$GTOOLS::TAG{"<!-- OID -->"} = $OID;

my $CMD = '';

if ($VERB ne 'EDIT') {
	}
elsif ($OID eq '') {
	push @MSGS, "ISE|+NO ORDER ID WAS RECEIVED! PLEASE CONTACT ZOOVY SUPPORT AND LET THEM KNOW THE ORDER # YOU WERE WORKING ON.";
	}
elsif ($VERB eq 'EDIT') {
	my $cname = &ZOOVY::fetchmerchant_attrib($USERNAME,"zoovy:company_name");
	if (length($cname)<1) { $cname = $USERNAME; }
	$GTOOLS::TAG{"<!-- COMPANY_NAME -->"} = $cname;


	my ($O2) = CART2->new_from_oid($USERNAME,$OID);
	my $stuff2 = $O2->stuff2();
	my %oref = ();
	tie %oref, 'CART2', 'CART2'=>$O2;
	}

my @BC = ();
push @BC, 	{ name=>'Orders',link=>'/biz/orders' };

my $CMD = uc($ZOOVY::cgiv->{'CMD'});
my $AREA = uc($ZOOVY::cgiv->{'AREA'});
my $SORTBY = lc($ZOOVY::cgiv->{'SORTBY'});
$GTOOLS::TAG{'<!-- SORTBY -->'} = $SORTBY;
$GTOOLS::TAG{'<!-- AREA -->'} = $AREA;

#print STDERR "CMD IS: $CMD\n";

if ($CMD eq '') { $CMD = 'RECENT'; }

#if ($CMD eq "DELETE")
#	{
#	&ORDER::nuke_order($USERNAME,$ID);
#	$AREA = 'CANCELLED';
#	}

#if ($CMD eq 'PRINT') {
#	&GTOOLS::print_form('','print.shtml',1);
#	}

my $ORDERIDS = '';

if ($VERB eq 'PAID') {
	require ZPAY;
	require EXTERNAL;
   foreach my $key (keys %{$ZOOVY::cgiv}) { 

		if ($key =~ /order-(.*?)$/) { 
			$ORDERIDS .= "$1,"; 
			my $ID = $1;
#			print STDERR "Flagin $ID as paid\n";
			# my ($o) = ORDER->new($USERNAME,$ID);
			my ($O2) = CART2->new_from_oid($USERNAME,$ID);

			my $method = $O2->in_get('our/payment_method');
			my $PS = $O2->in_get('flow/payment_status');

			if ((substr($PS,0,1) eq '1') || (substr($PS,0,1) eq '4')) {
				foreach my $payrec (@{$O2->payments()}) {
					if (
						($payrec->{'ps'} eq '109') ||
						($payrec->{'ps'} eq '189') || ($payrec->{'ps'} eq '199') ||
						($payrec->{'ps'} eq '489') || ($payrec->{'ps'} eq '499')
						) {
						$O2->process_payment('CAPTURE',$payrec,{});
						}
					}
				}
			else {
				$O2->add_history("Cannot batch change ps=$PS");				
				}

			#if (($method eq 'CREDIT') || ($method eq 'PAYPALEC') || ($method eq 'GOOGLE')) {
			#	
			#	my $payment_status = uc($o->get_attrib('payment_status'));
			#	if (substr($payment_status,0,1) eq '1') {		
			#		my ($result,$msg) = $o->payment('CAPTURE');
			#		$GTOOLS::TAG{'<!-- MESSAGE -->'} .= "($result) $msg<br>\n";
			#		}
			#	}
			#else {
			#	$o->set_payment_status('000',"move.cgi|$LUSERNAME",undef,undef,0);
			#	}

			$O2->order_save();
			}  
		}
	if ($AREA eq '') { $AREA = 'RECENT'; }
	$CMD = uc($AREA);
	}




if ($VERB eq 'MOVE') {
	my @orders = ();
	if ($ZOOVY::cgiv->{'ORDERS'} ne '') {
		@orders = split(/,/,$ZOOVY::cgiv->{'ORDERS'});
		$ORDERIDS = $ZOOVY::cgiv->{'ORDERS'}.',';
		}
	foreach my $key (keys %{$ZOOVY::cgiv}) { 
		if ($key =~ /order-(.*?)$/) { 
			push @orders, $1;
			$ORDERIDS .= "$1,";
			delete $ZOOVY::cgiv->{$key};
			}  
		}
	
	if ($CMD eq 'ARCHIVE') {
		if (scalar(@orders)>0) { &ORDER::BATCH::change_pool($USERNAME,'ARCHIVE',\@orders,$LUSERNAME); }
		$GTOOLS::TAG{'<!-- SCRIPT -->'} = "main.cgi?CMD=COMPLETED&ORDERIDS=$ORDERIDS&SORTBY=$SORTBY";
		$GTOOLS::TAG{'<!-- AREA -->'} = 'completed';
		$template_file = "move.shtml";
		}
	elsif ($CMD eq 'RECENT')
	   {
		if (scalar(@orders)>0) { &ORDER::BATCH::change_pool($USERNAME,'RECENT',\@orders,$LUSERNAME); }
		$GTOOLS::TAG{'<!-- SCRIPT -->'} = "main.cgi?CMD=RECENT&ORDERIDS=$ORDERIDS&SORTBY=$SORTBY";
		$GTOOLS::TAG{'<!-- AREA -->'} = 'recent';
		$template_file = "move.shtml";
	   }
	elsif ($CMD eq 'REVIEW')
	   {
		if (scalar(@orders)>0) { &ORDER::BATCH::change_pool($USERNAME,'REVIEW',\@orders,$LUSERNAME); }
		$GTOOLS::TAG{'<!-- SCRIPT -->'} = "main.cgi?CMD=REVIEW&ORDERIDS=$ORDERIDS&SORTBY=$SORTBY";
		$GTOOLS::TAG{'<!-- AREA -->'} = 'review';
		$template_file = "move.shtml";
	   }
	elsif ($CMD eq 'HOLD')
	   {
		if (scalar(@orders)>0) { &ORDER::BATCH::change_pool($USERNAME,'HOLD',\@orders,$LUSERNAME); }
		$GTOOLS::TAG{'<!-- SCRIPT -->'} = "main.cgi?CMD=HOLD&ORDERIDS=$ORDERIDS&SORTBY=$SORTBY";
		$GTOOLS::TAG{'<!-- AREA -->'} = 'hold';
		$template_file = "move.shtml";
	   }
	elsif ($CMD eq 'PENDING')
	   {
		if (scalar(@orders)>0) { &ORDER::BATCH::change_pool($USERNAME,'PENDING',\@orders,$LUSERNAME); }
		$GTOOLS::TAG{'<!-- SCRIPT -->'} = "main.cgi?CMD=PENDING&ORDERIDS=$ORDERIDS&SORTBY=$SORTBY";
		$GTOOLS::TAG{'<!-- AREA -->'} = 'pending';
		$template_file = "move.shtml";
	   }
	elsif ($CMD eq 'APPROVED')
	   {
		if (scalar(@orders)>0) { &ORDER::BATCH::change_pool($USERNAME,'APPROVED',\@orders,$LUSERNAME); }
		$GTOOLS::TAG{'<!-- SCRIPT -->'} = "main.cgi?CMD=APPROVED&ORDERIDS=$ORDERIDS&SORTBY=$SORTBY";
		$GTOOLS::TAG{'<!-- AREA -->'} = 'approved';
		$template_file = "move.shtml";
	   }
	elsif (($CMD eq 'PROCESS') || ($CMD eq 'PROCESSING')) 
	   {
		if (scalar(@orders)>0) { &ORDER::BATCH::change_pool($USERNAME,'PROCESS',\@orders,$LUSERNAME); }
		$GTOOLS::TAG{'<!-- SCRIPT -->'} = "main.cgi?CMD=PROCESS&ORDERIDS=$ORDERIDS&SORTBY=$SORTBY";
		$GTOOLS::TAG{'<!-- AREA -->'} = 'process';
		$template_file = "move.shtml";
	   }
	elsif ($CMD eq 'COMPLETED')
		{
		$GTOOLS::TAG{'<!-- SCRIPT -->'} = "main.cgi?CMD=COMPLETED&ORDERIDS=$ORDERIDS&SORTBY=$SORTBY";
		if (scalar(@orders)>0) { &ORDER::BATCH::change_pool($USERNAME,'COMPLETED',\@orders,$LUSERNAME); }
		$GTOOLS::TAG{'<!-- AREA -->'} = 'completed';
		$template_file = 'move.shtml';
	   }
	elsif (($CMD eq 'CANCELLED') || ($CMD eq 'DELETED')) {
		$GTOOLS::TAG{'<!-- AREA -->'} = 'Cancelled';
		if (scalar(@orders)>0) { &ORDER::BATCH::change_pool($USERNAME,'CANCELLED',\@orders,$LUSERNAME); }
		$GTOOLS::TAG{'<!-- SCRIPT -->'} = "main.cgi?CMD=CANCELLED&ORDERIDS=$ORDERIDS&SORTBY=$SORTBY";
		$GTOOLS::TAG{'<!-- AREA -->'} = 'cancelled';
		$template_file = "move.shtml";
	   } 
	elsif ($CMD eq 'BACKORDER')
		{
		$GTOOLS::TAG{'<!-- AREA -->'} = 'Backordered';
		if (scalar(@orders)>0) { &ORDER::BATCH::change_pool($USERNAME,'BACKORDER',\@orders,$LUSERNAME); }
		$GTOOLS::TAG{'<!-- SCRIPT -->'} = "main.cgi?CMD=BACKORDER&ORDERIDS=$ORDERIDS&SORTBY=$SORTBY";
		$GTOOLS::TAG{'<!-- AREA -->'} = 'backordered';
		$template_file = "move.shtml";
	   } 
	
	elsif ($CMD eq 'EMAIL') {
	
		my $NS = $ZOOVY::cgiv->{'NS'};
		if ($NS eq '') { $NS = 'DEFAULT'; }
	
		require SITE::EMAILS;
		require SITE;
		my ($SITE) = SITE->new($USERNAME,'PRT'=>$PRT,'NS'=>$NS);
		## currently only using DEFAULT profile
		my ($se) = SITE::EMAILS->new($USERNAME,'*SITE'=>$SITE);
		my ($types) = $se->available('ORDER');
	
		my $out = '';
		foreach my $type (@{$types}) {
			$se->getref($type->{'MSGID'});
			my $hashref = $se->getref($type->{'MSGID'});
			
			$out .= "<tr><td><input type=\"radio\" name=\"message\" value=\"$type->{'MSGID'}\"></td>".
	      			"<td><b>$hashref->{'MSGTITLE'}</b></td>".
	      			"<td>$hashref->{'MSGSUBJECT'}</td></tr>";
			}
	
		$GTOOLS::TAG{'<!-- OUTPUT -->'} = $out; 
	
		if ($ORDERIDS eq '') { $template_file = "email-none.shtml"; } 
		else { $template_file = "email.shtml"; }
		}
	elsif (($CMD eq 'EXPORT') && ($FLAGS !~ /,API,/)) {
		$template_file = "export-deny.shtml";
		}
	elsif ($CMD eq 'EXPORT')
		{
		my ($billing_info,$strip_prices,$strip_payment,$format,$recovery) = ();
		my $foo = &ZWEBSITE::fetch_website_attrib($USERNAME,'order_dispatch_defaults');
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
		$GTOOLS::TAG{'<!-- ORDER_FORMAT_XML -->'} = '';
		$GTOOLS::TAG{'<!-- ORDER_FORMAT_OBI -->'} = '';
		$GTOOLS::TAG{'<!-- ORDER_FORMAT_'.$format.' -->'} = 'selected';
	
		$GTOOLS::TAG{'<!-- EXPORT_URL -->'} = &ZWEBSITE::fetch_website_attrib($USERNAME,'order_dispatch_url');
		
		$foo = &ZWEBSITE::fetch_website_attrib($USERNAME,'order_dispatch_mode');
		$GTOOLS::TAG{'<!-- ORDER_DISPATCH_ENABLE_0 -->'} = '';	
		$GTOOLS::TAG{'<!-- ORDER_DISPATCH_ENABLE_1 -->'} = '';	
		$GTOOLS::TAG{'<!-- ORDER_DISPATCH_ENABLE_9 -->'} = '';	
		$GTOOLS::TAG{'<!-- ORDER_DISPATCH_ENABLE_'.$foo.' -->'} = 'selected';
	
		if ($recovery) { $GTOOLS::TAG{'<!-- RECOVERY_CHECKED -->'} = 'checked'; } else { $GTOOLS::TAG{'<!-- RECOVERY_CHECKED -->'} = ''; }
	
		if ($ORDERIDS eq '')
			{
			$template_file = "export-none.shtml";
			} else {
			$template_file = "export.shtml";
			}
		}
	
	$GTOOLS::TAG{'<!-- ORDER_IDS -->'} = $ORDERIDS;
	#print STDERR "Order ids: $ORDERIDS\n";
	}


##
##
##
##
##
if ($VERB =~ /^SHOW\:/) {
	my $SHOW_POOL = '';
	my $r = undef;

	if ($VERB eq 'SHOW:RECENT') {
		$GTOOLS::TAG{'<!-- AREA -->'} = 'Recent';	
		($r) = ORDER::BATCH::report($USERNAME,DETAIL=>9,'POOL'=>'RECENT','LIMIT'=>$MAX);
		push @BC, { name=>'Recent', link=>"/biz/orders?VERB=$VERB" };
		}
	elsif ($VERB eq 'SHOW:PENDING') {
		$GTOOLS::TAG{'<!-- AREA -->'} = 'Pending';
		($r) = ORDER::BATCH::report($USERNAME,DETAIL=>9,'POOL'=>'PENDING','LIMIT'=>$MAX);
		push @BC, { name=>'Pending', link=>"/biz/orders?VERB=$VERB" };
	   }
	elsif ($VERB eq 'SHOW:REVIEW') {
		$GTOOLS::TAG{'<!-- AREA -->'} = 'Review';
		($r) = ORDER::BATCH::report($USERNAME,DETAIL=>9,'POOL'=>'REVIEW','LIMIT'=>$MAX);
		push @BC, { name=>'Review', link=>"/biz/orders?VERB=$VERB" };
	   }
	elsif ($VERB eq 'SHOW:HOLD') {
		$GTOOLS::TAG{'<!-- AREA -->'} = 'Hold';	
		($r) = ORDER::BATCH::report($USERNAME,DETAIL=>9,'POOL'=>'HOLD','LIMIT'=>$MAX);
		push @BC, { name=>'Hold', link=>"/biz/orders?VERB=$VERB" };
		}
	elsif ($VERB eq 'SHOW:APPROVED') {
		$GTOOLS::TAG{'<!-- AREA -->'} = 'Approved';
		($r) = ORDER::BATCH::report($USERNAME,DETAIL=>9,'POOL'=>'APPROVED','LIMIT'=>$MAX);
		push @BC, { name=>'Approved', link=>"/biz/orders?VERB=$VERB" };
		}
	elsif ($VERB eq 'SHOW:PROCESS') {
		$GTOOLS::TAG{'<!-- AREA -->'} = 'Process';
		($r) = ORDER::BATCH::report($USERNAME,DETAIL=>9,'POOL'=>'PROCESS','LIMIT'=>$MAX);
		push @BC, { name=>'Process', link=>"/biz/orders?VERB=$VERB" };
	   }
	elsif ($VERB eq 'SHOW:COMPLETED') {
		$GTOOLS::TAG{'<!-- AREA -->'} = 'Completed';
		my ($CLUSTER) = &ZOOVY::resolve_cluster($USERNAME);
		if (($CLUSTER eq 'SNAP') || ($CLUSTER eq 'DAGOBAH')) {
			$r = [];
			}
		else {
			($r) = ORDER::BATCH::report($USERNAME,DETAIL=>9,'POOL'=>'COMPLETED','SINCE'=>$startts,'LIMIT'=>$MAX);
			}
		push @MSGS, 'WARN|+Note: orders will only appear in this list for 180 days after being last modified/synced - please search by order # to bring up orders beyond that time.';
		push @BC, { name=>'Completed', link=>"/biz/orders?VERB=$VERB" };
		}
	elsif ($VERB eq 'SHOW:CANCELLED') {
		$GTOOLS::TAG{'<!-- AREA -->'} = 'Cancelled';
		($r) = ORDER::BATCH::report($USERNAME,DETAIL=>9,'POOL'=>'DELETED','SINCE'=>$startts,'LIMIT'=>$MAX);
		push @MSGS, 'WARN|+orders will only appear in this list for 180 days after being last modified/synced - please search by order # to bring up orders beyond that time.';
		push @BC, { name=>'Cancelled', link=>"/biz/orders?VERB=$VERB" };
		} 
	elsif ($VERB eq 'SHOW:BACKORDER') {
	   $GTOOLS::TAG{'<!-- AREA -->'} = 'Backordered';
		$GTOOLS::TAG{'<!-- NEXT -->'} = '';
		($r) = ORDER::BATCH::report($USERNAME,DETAIL=>9,'POOL'=>'BACKORDER','SINCE'=>$startts,'LIMIT'=>$MAX);
		if ($count==$MAX) {
			push @MSGS, qq~WARN|+Maximum order count of $MAX reached. Please use search to find specific orders.~;
			}
		push @BC, { name=>'Backorder', link=>"/biz/orders?VERB=$VERB" };
		}
	elsif ($VERB eq 'SHOW:SEARCH') {
		$SHOW_POOL = '';
		$GTOOLS::TAG{'<!-- NEXT -->'} = '';
		my $find_text = $ZOOVY::cgiv->{'find_text'};
		my $search_field = $ZOOVY::cgiv->{'search_field'};
		my %resultset = ();
		my %searchset = ();

		$find_text =~ s/^[\s\t]+//gs; 	# strip leading spaces
		$find_text =~ s/[\s\t]+$//gs; 	# strip trailing spaces

		my @ORDERS = ();

		# check if they just searched for an order, if so then just do a quick lookup
		if ($find_text =~ /\d{4}-\d{2}-\d+$/) {
			## orderid shortcut
			$find_text =~ s/[^\d\-]//g;		# strip out whitespace, etc.
			# my ($o, $error) = ORDER->new($USERNAME, $find_text);
			my ($O2) = CART2->new_from_oid($USERNAME, $find_text);
			if (defined $O2) {
				push @ORDERS, $find_text;
				}
			}
		elsif (&ZTOOLKIT::validate_email($find_text)) {
			## email shortcut
			($r) = ORDER::BATCH::report($USERNAME,DETAIL=>9,'BILL_EMAIL'=>$find_text,'WEB_SCOPE'=>1);
			}
		elsif ($ZOOVY::cgiv->{'search_field'} eq 'AMAZON') {
			require AMAZON3;
	
			require ORDER::BATCH;
			my ($result) = ORDER::BATCH::report($USERNAME,EREFID=>$find_text);
			foreach my $set (@{$result}) {
				push @ORDERS, $set->{'ORDERID'};
				}

		## added $USERNAME to the values passed to 'AMAZON3::resolve_orderid' to enable the
		## opening of the user database for the new amazon cluster specific tables. at 2010-08-30
			if (scalar(@ORDERS)==0) {
			 	my ($MID,$ORDERID) = &AMAZON3::resolve_orderid($USERNAME, $find_text);
			#	my ($MID,$ORDERID) = &AMAZON3::resolve_orderid($find_text);
				if (defined $ORDERID) {
					push @ORDERS, $ORDERID;
					}
				}
			}
		elsif ($ZOOVY::cgiv->{'search_field'} eq 'GOOGLECHECKOUT') {
			require ZPAY::GOOGLE;
			my ($ORDERID) = &ZPAY::GOOGLE::resolve_orderid($USERNAME,$find_text);
			push @ORDERS, $ORDERID;
			}

		if (defined $r) {
			## search has been performed, result-set is populated.
			}
		elsif (scalar(@ORDERS)>0) {
			($r) = ORDER::BATCH::report($USERNAME,DETAIL=>9,'@OIDS'=>\@ORDERS);	
			$SHOW_POOL++;
			}
		elsif (scalar(@ORDERS)==0) {
	
			my %params = ();
		
			$params{'WEB_SCOPE'} = 365;
	
			if ($ZOOVY::cgiv->{'search_field'} eq 'BILL_FULLNAME') {
				$params{'BILL_FULLNAME'} = $find_text;
				}
			if ($ZOOVY::cgiv->{'search_field'} eq 'BILL_PHONE') {
				$params{'BILL_PHONE'} = $find_text;
				$params{'BILL_PHONE'} =~ s/[^\d]+//gs;	 #strip non-numeric
				}
			elsif ($ZOOVY::cgiv->{'search_field'} eq 'EBAY') {
				$params{'EBAY'} = $find_text;
				}
			elsif ($ZOOVY::cgiv->{'search_field'} eq 'EREFID') {
				$params{'EREFID'} = $find_text;
				}
			elsif ($ZOOVY::cgiv->{'search_field'} eq 'DATA') {
				$params{'DATA'} = $find_text;
				}

			$params{'LIMIT'} = 100;
			if ($ZOOVY::cgiv->{'find_status'} eq 'ANY') {
				$params{'POOL'} = '';
				$SHOW_POOL++;
				}
			elsif ($ZOOVY::cgiv->{'find_status'} eq 'RECENT') {
				$params{'POOL'} = 'RECENT';		
				}
			elsif ($ZOOVY::cgiv->{'find_status'} eq 'PENDING') {
				$params{'POOL'} = 'PENDING';		
				}
			elsif ($ZOOVY::cgiv->{'find_status'} eq 'APPROVED') {
				$params{'POOL'} = 'APPROVED';		
				}	
			elsif ($ZOOVY::cgiv->{'find_status'} eq 'COMPLETED') {
				$params{'POOL'} = 'COMPLETED';		
				}
			elsif ($ZOOVY::cgiv->{'find_status'} eq 'CANCELED') {
				$params{'POOL'} = 'CANCELED';		
				}
			elsif ($ZOOVY::cgiv->{'find_status'} eq 'BACKORDER') {
				$params{'POOL'} = 'BACKORDER';		
				}
			else {
				$SHOW_POOL++;
				}
	
			($r) = ORDER::BATCH::report($USERNAME,DETAIL=>9,%params);
			}
		else {
			die("never reached!");
			}

		$GTOOLS::TAG{'<!-- AREA -->'} = "Searching for \"$find_text\" in ".$ZOOVY::cgiv->{'find_status'};
		}


	my @POOLS = (
		{ pool=>'RECENT', prompt=>'Recent', },
		{ pool=>'PENDING', prompt=>'Pending', },
		{ pool=>'REVIEW', prompt=>'Review', },
		{ pool=>'HOLD', prompt=>'Hold', },
		{ pool=>'APPROVED', prompt=>'Approved', },
		{ pool=>'PROCESS', prompt=>'Process', },
		{ pool=>'COMPLETED', prompt=>'Completed', },
		{ pool=>'DELETED', prompt=>'Cancelled', },
		{ pool=>'BACKORDER', prompt=>'Backorder', },
		{ pool=>'PREORDER', prompt=>'PreOrder', },
		);

	if ($VERB eq 'COMPLETED') {
		push @POOLS, { pool=>'ARCHIVE', prompt=>'Archive' };
		}

	my $FOOTER = '';
	$FOOTER .= "<tr>";
	foreach my $ref (@POOLS) {
		next if ($ref->{'pool'} eq $VERB);
	
		next if ($ref->{'pool'} eq 'BACKORDER');
		next if ($ref->{'pool'} eq 'PREORDER');

		$FOOTER .= qq~<td nowrap>
		<input type="radio" name="CMD" for="MOVE:$ref->{'pool'}" value="MOVE:$ref->{'pool'}">
		<label id="MOVE:$ref->{'pool'}">$ref->{'prompt'}</label></td><td>&nbsp;</td>~;
		}
	$FOOTER .= qq~
		<td rowspan="2" valign="middle">&nbsp;
		<input onClick="" style="width: 40px; height: 20px; font-size: 8pt; font-face: arial;" class="button" type="button" value="  Go   "></td>
	</tr>
	<tr>
		<td><input type="radio" for="PAID" name="VERB" value="PAID">
		<label id="PAID">Flag as Paid</label></td>
		<td>&nbsp;</td>
		<td><input type="radio" for="EMAIL" name="VERB" value="EMAIL">
		<label id="EMAIL">Send Email</label></td>
		<td>&nbsp;</td>
	</tr>
	~;
	$GTOOLS::TAG{'<!-- FOOTER -->'} = $FOOTER;


	if (not defined $r) {
			}
	elsif ((defined $r) && (scalar(@{$r})>0)) {
		my $c = "";
		my %ORDERS = ();

		my $BGCOLOR = "CCCCCC";
		#$c .= "<table width=\"100%\" cellpadding=\"3\" cellspacing=\"0\" border=\"0\">";

		$c .= "<tr>";
		$c .= "<td bgcolor=\"$BGCOLOR\"><a href=\"#\" onClick=\"toggleAll();\"><img border=\"0\" width=\"18\" height=\"18\" src=\"/biz/orders/images/green_check.gif\"></a></td>"; 
		$c .= "<td bgcolor=\"$BGCOLOR\"><a href=\"javascript:sortBy('$VERB','ID');\"><font size=\"2\" face=\"Arial\" color=\"000000\"><b>ID</a></font></td>";
		if ($SHOW_POOL) { 
			$c .= "<td bgcolor=\"$BGCOLOR\"><font size=\"2\" face=\"Arial\" color=\"000000\"><b>STATUS</font></td>"; 
			}
		$c .= "<td bgcolor=\"$BGCOLOR\"><a href=\"javascript:sortBy('$VERB','ORDER_BILL_NAME');\"><font size=\"2\" face=\"Arial\" color=\"000000\"><b>Customer</a></font></td>";
		$c .= "<td bgcolor=\"$BGCOLOR\"><a href=\"javascript:sortBy('$VERB','ORDER_SHIP_ZONE');\"><font size=\"2\" face=\"Arial\" color=\"000000\"><b>Ship Dest</a></font></td>";
		$c .= "<td bgcolor=\"$BGCOLOR\"><a href=\"javascript:sortBy('$VERB','ORDER_TOTAL');\"><font size=\"2\" face=\"Arial\" color=\"000000\"><b>Amount</a></font></td>";
		$c .= "<td bgcolor=\"$BGCOLOR\"><a href=\"javascript:sortBy('$VERB','REVIEW_STATUS');\"><font size=\"2\" face=\"Arial\" color=\"000000\"><b>Fraud</a></font></td>";
		$c .= "<td bgcolor=\"$BGCOLOR\"><a href=\"javascript:sortBy('$VERB','ORDER_PAYMENT_STATUS');\"><font size=\"2\" face=\"Arial\" color=\"000000\"><b>Pay Status</a></font></td>";
		$c .= "<td bgcolor=\"$BGCOLOR\"><a href=\"javascript:sortBy('$VERB','ORDER_PAYMENT_METHOD');\"><font size=\"2\" face=\"Arial\" color=\"000000\"><b>Pay Type</a></font></td>";
		$c .= "<td bgcolor=\"$BGCOLOR\"><a href=\"javascript:sortBy('$VERB','ITEMS');\"><font size=\"2\" face=\"Arial\" color=\"000000\"><b>Items</a></font></td>";
		$c .= "<td bgcolor=\"$BGCOLOR\"><a href=\"javascript:sortBy('$VERB','FLAGS');\"><font size=\"2\" face=\"Arial\" color=\"000000\"><b>Special</a></font></td>";
		$c .= "<td bgcolor=\"$BGCOLOR\"><a href=\"javascript:sortBy('$VERB','CREATED_GMT');\"><font size=\"2\" face=\"Arial\" color=\"000000\"><b>Created</a></font></a></td>";
		$c .= "</tr>";

		my $ORDERIDS = $ZOOVY::cgiv->{'ORDERIDS'};
		if (not defined $ORDERIDS) { $ORDERIDS = ''; }

		# Now figure out which !@#$% key we need to sort by
		my $SORTBY = uc($ZOOVY::cgiv->{'SORTBY'});
		#if (!defined($SORTBY) || $SORTBY eq '') { $SORTBY = 'ID'; } 
		if (!defined($SORTBY) || $SORTBY eq '') { $SORTBY = 'CREATED_GMT'; } 
		## SORTBY can be ORDER_BILL_NAME ORDER_SHIP_ZONE etc.

		## in order to sort, we need to read in all the appropriate orders
		my %sortthis = ();
		$count = 0;

		foreach my $ref (@{$r}) {
			my $id = $ref->{'ORDERID'};
			next if ($id eq '');	## how bizarre .. sometimes orders are blank
			$count++;
			$ORDERS{$id} = $ref;

			if ($SORTBY eq 'ID') {
				$sortthis{$id} = $id; 
				$sortthis{$id} =~ s/-//g;
				} 
			else {
				$sortthis{$id} = $ref->{$SORTBY};
				} 
			}

		## At this point $sortthis has the sort value in the 
		my $counter = 0;
		my $order_sum = 0;
		my $class = '';
		my ($checked);

		my $style = 'alphabetically';
		if ($SORTBY eq 'ID' || $SORTBY eq 'CREATED_GMT' || $SORTBY eq 'ORDER_TOTAL') {
			$style = 'numerically';
			}

		my @ids = ZTOOLKIT::value_sort(\%sortthis,$style);
		if (($SORTBY eq 'ID') || ($SORTBY eq 'CREATED_GMT') || ($SORTBY eq 'ORDER_TOTAL')) {
			## numnerical sorts always go up down
			@ids = reverse @ids;
			}

		foreach my $id (@ids) {
			if ($counter++ % 2) { $class = "item_on"; } else { $class="item_off"; }
			my $ref = $ORDERS{$id};

			my $order_total = $ref->{'ORDER_TOTAL'};
			if (!defined($order_total)) { $order_total = 0; }
			$total += $order_total;

			$order_total = &ZOOVY::incode($order_total);

			# $id = quotemeta($id);
			my $qtID = quotemeta($id);
			if ($ORDERIDS =~ /$qtID,/) { $checked='checked'; } else { $checked = ''; }
			my $customer_dest = '';

			if (not defined $ref->{'ORDER_SHIP_ZONE'}) {
				$ref->{'ORDER_SHIP_ZONE'} = '';
				}

			$ref->{'ship/country'} = substr($ref->{'ORDER_SHIP_ZONE'},0,2);
			if (not defined $ref->{'ship/country'}) { $ref->{'ship/country'} = ''; }

			if ($ref->{'ship/country'} eq 'US') {
				$ref->{'ship/region'} = substr($ref->{'ORDER_SHIP_ZONE'},2,2); 
				if (length($ref->{'ORDER_SHIP_ZONE'})==9) {
					$ref->{'ship/postal'} = substr($ref->{'ORDER_SHIP_ZONE'},4);		## get rid of USCA (Country/State)
					}
				if (not defined $ref->{'ship/country'}) { $ref->{'ship/country'} = ''; }
				if (not defined $ref->{'ship/region'}) { $ref->{'ship/region'} = ''; }
				if (not defined $ref->{'ship/postal'}) { $ref->{'ship/postal'} = ''; }
	
				$customer_dest = &ZOOVY::incode($ref->{'ship/country'}.", ".$ref->{'ship/region'}." ".$ref->{'ship/postal'})." ";
				} 
			else {
				if (not defined $ref->{'ship/city'})		{ $ref->{'ship/city'} = ''; }
				if (not defined $ref->{'ship/region'})	 { $ref->{'ship/region'} = ''; }
				if (not defined $ref->{'ship/postal'}) { $ref->{'ship/postal'} = ''; }
				$ref->{'ORDER_SHIP_ZONE'} = substr($ref->{'ORDER_SHIP_ZONE'},0,2).' '.substr($ref->{'ORDER_SHIP_ZONE'},2);
				$customer_dest = &ZOOVY::incode($ref->{'ORDER_SHIP_ZONE'});
				}

			if ($ref->{'ORDER_PAYMENT_METHOD'} eq 'CRED') { $ref->{'ORDER_PAYMENT_METHOD'} = 'CREDIT'; }
			elsif ($ref->{'ORDER_PAYMENT_METHOD'} eq 'GOOG') { $ref->{'ORDER_PAYMENT_METHOD'} = 'GOOGLE'; }
			elsif ($ref->{'ORDER_PAYMENT_METHOD'} eq 'PAYP') { $ref->{'ORDER_PAYMENT_METHOD'} = 'PAYPAL'; }
			elsif ($ref->{'ORDER_PAYMENT_METHOD'} eq 'PPEC') { $ref->{'ORDER_PAYMENT_METHOD'} = 'PAYPAL-EC'; }
			elsif ($ref->{'ORDER_PAYMENT_METHOD'} eq 'MIXE') { $ref->{'ORDER_PAYMENT_METHOD'} = 'MIXED'; }
			elsif ($ref->{'ORDER_PAYMENT_METHOD'} eq 'AMAZ') { 
				$ref->{'ORDER_PAYMENT_METHOD'} = 'AMAZON'; 
				# $customer_dest = 'n/a';
				}
		
			$c .= "<tr class=\"$class\">\n";
			$c .= "<td><input type=\"checkbox\" $checked name=\"order-$id\"></td>"; 
			$c .= "<td><a href=\"/biz/orders/view.cgi?ID=$id\">$id</a></td>";
			if ($SHOW_POOL) { $c .= "<td>$ref->{'POOL'}</td>"; }
			if (not defined $ref->{'ORDER_BILL_NAME'}) { $ref->{'ORDER_BILL_NAME'} = ''; }
			$c .= "<td>".$ref->{'ORDER_BILL_NAME'}."&nbsp;</td>";
			$c .= "<td>$customer_dest&nbsp;</td>";
			$c .= "<td>".sprintf("%.2f",$order_total);
			$order_sum += $order_total;
			$c .= "</td>";

			## fraud
			my $rs = substr($ref->{'REVIEW_STATUS'},0,1);
			if ($rs eq '') { $rs = 'n/a'; }
			elsif ($rs eq 'A') { $rs = '<font color="green">ok</font>'; }
			elsif ($rs eq 'R') { $rs = '<font color="yellow">review</font>'; }
			elsif ($rs eq 'E') { $rs = '<font color="red">escalate</font>'; }
			elsif ($rs eq 'D') { $rs = '<font color="red">decline</font>'; }
			elsif ($rs eq 'X') { $rs = '<font color="red">err</font>'; }
		
			$c .= "<td>$rs</td>";
		
			my $status = $ref->{'ORDER_PAYMENT_STATUS'};
			if (not defined $status) { $status = 100; }
	
			# if it's a new payment status
			# if (length($status)==3) { $status = substr($status,0,1); } 
	
			if (substr("$status",0,1) eq '0') { $status = '<font style="color: #3377FF; font-weight: bold;">PAID</font>'; }
			elsif (substr("$status",0,1) eq '1') { $status = '<font color="444444">Pending</font>'; }
			elsif (substr("$status",0,1) eq '2') { $status = '<font color="red">Denied</font>'; }
			elsif (substr("$status",0,1) eq '3') { $status = 'Cancelled ['.$status.']'; }
			elsif (substr("$status",0,1) eq '4') { $status = '<font color="red">Review</font>'; }
			elsif (substr("$status",0,1) eq '5') { $status = '<font color="red">Processing</font>'; }
			else { $status = sprintf('Error(%d)',$status); }
	
			$c .= "<td>$status &nbsp;</td>";
			if (not defined $ref->{'ORDER_PAYMENT_METHOD'}) { $ref->{'ORDER_PAYMENT_METHOD'} = ''; }
			$c .= "<td>$ref->{'ORDER_PAYMENT_METHOD'}&nbsp;</td>";
	
			$c .= "<td>$ref->{'ITEMS'}</td>";

			my @flags = ();
			$ref->{'FLAGS'} = int($ref->{'FLAGS'});
			if ( $ref->{'FLAGS'} & 2 ) { push @flags, 'EXP'; }	# expedited shipping
			if ( $ref->{'FLAGS'} & 4 ) { push @flags, 'RC'; }	 # repeat customer
			if ( $ref->{'FLAGS'} & 24 ) { push @flags, 'SPLIT'; } # split order
			if ( $ref->{'FLAGS'} & 64 ) { push @flags, 'SC'; }	 # supply chain
			if ( $ref->{'FLAGS'} & 128 ) { push @flags, 'MS'; } # multiple shipments
			if ( $ref->{'FLAGS'} & 256 ) { push @flags, 'RTN'; } # returned item
			if ( $ref->{'FLAGS'} & 512 ) { push @flags, 'EDIT'; } # merchant edited.
			$c .= "<td>".join(",",@flags)."</td>";


			$c .= "<td>".&ZTOOLKIT::pretty_date($ref->{'CREATED_GMT'})."</td>\n";
 			$c .= "</tr>\n";
 			}

		$GTOOLS::TAG{'<!-- ORDER_TABLE -->'} = $c;
		# OVERRIDE
		}
	elsif (scalar(@{$r})==0) {
		$GTOOLS::TAG{'<!-- ORDER_TABLE -->'} = "No orders found";
		}
	else {
		## internal error! - should never be reached
		}

	$GTOOLS::TAG{'<!-- ORDER_TOTAL -->'} = sprintf("%.2f",$total);
	$GTOOLS::TAG{'<!-- ORDER_COUNT -->'} = $count;
	if ($count>=$MAX) { 	
		push @MSGS, "WARN|+Maximum order count of $MAX reached. Please use search to find specific orders.";
		}
	$template_file = 'index.shtml';
	}







my $HEADJS = qq~
	<script>
	<!--//
		var tState = false;
		function toggleAll() {
			tState = !tState;
			for (i=0,n=window.document.myForm.elements.length;i<n;i++) {
				if (window.document.myForm.elements[i].name.indexOf("order-") !=-1) {
					window.document.myForm.elements[i].checked = tState;	
				}
			}
		}
		function submitIt(action) {
			window.document.myForm.CMD.value=action;
			window.document.myForm.submit();
		}

		function sortBy(verb,column) {
			myForm.VERB.value=verb;
			myForm.SORTBY.value = column;
			myForm.submit();
		}

	function doCMD() {
		alert("Broken");
		for (var x=0; x < document.forms[0].CMD.length; x++) {
			if (document.forms[0].CMD[x].checked) {
				parent.main.submitIt(document.forms[0].CMD[x].value);
				return false;
			}
		};
		alert("You must select one of choices to submit this request.");
		return false;
	}
	function clickCMD (value) { 
		document.thisFrm.CMD[value].checked=true; return(false); 
		}

	//-->
	</script>
	<style>
		TR.item_on { font-size: 8pt; font-family: arial, helvetica; background-color: #E1E1E1; }
		TR.item_off { font-size: 8pt; font-family: arial, helvetica; background-color: #FFFFFF; }
		TD.item_on { font-size: 8pt; font-family: arial, helvetica; background-color: #E1E1E1; }
		TD.item_off { font-size: 8pt; font-family: arial, helvetica; background-color: #FFFFFF; }
		TD.title { font-size: 10pt; font-family: helvetica, arial; background-color: #000000; font-style: bold; }
		a:visited { color: purple; }		
	a { font-size: 8pt; font-family: Arial, Helvetica, sans-serif; color: #000000; text-decoration: none; }
	a:hover { color: #000000; }
	a:visited { color: #000000; }
	a:active { color: #000000; }
	</style>
~;


my @TABS = ();
push @TABS, { button=>1, name=>'[Create]',link=>'index.cgi?VERB=CREATE', selected=>($VERB eq 'CREATE')?1:0 };
push @TABS, { name=>'Recent',link=>'index.cgi?VERB=SHOW:RECENT', selected=>($VERB eq 'SHOW:RECENT')?1:0 };
push @TABS, { name=>'Review',link=>'index.cgi?VERB=SHOW:REVIEW', selected=>($VERB eq 'SHOW:REVIEW')?1:0 };
push @TABS, { name=>'Hold',link=>'index.cgi?VERB=SHOW:HOLD', selected=>($VERB eq 'SHOW:HOLD')?1:0 };
push @TABS, { name=>'Pending',link=>'index.cgi?VERB=SHOW:PENDING', selected=>($VERB eq 'SHOW:PENDING')?1:0 };
push @TABS, { name=>'Approved',link=>'index.cgi?VERB=SHOW:APPROVED', selected=>($VERB eq 'SHOW:APPROVED')?1:0 };
push @TABS, { name=>'Processing',link=>'index.cgi?VERB=SHOW:PROCESS', selected=>($VERB eq 'SHOW:PROCESS')?1:0 };
push @TABS, { name=>'Completed',link=>'index.cgi?VERB=SHOW:COMPLETED', selected=>($VERB eq 'SHOW:COMPLETED')?1:0 };
push @TABS, { name=>'Cancelled',link=>'index.cgi?VERB=SHOW:CANCELLED', selected=>($VERB eq 'SHOW:CANCELLED')?1:0 };
push @TABS, { name=>'Search',link=>'index.cgi?VERB=SEARCH', selected=>($VERB eq 'SEARCH')?1:0, };


&GTOOLS::output('jquery'=>1,'msgs'=>\@MSGS,'bc'=>\@BC,'tabs'=>\@TABS,'headjs'=>$HEADJS,file=>$template_file,header=>1);


