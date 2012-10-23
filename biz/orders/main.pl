#!/usr/bin/perl -w

# use strict;
use strict;
use Data::Dumper;
use lib "/httpd/modules";
require GTOOLS;
require ZOOVY;
require ZTOOLKIT;
require DBINFO;
require ORDER::BATCH;
#require ORDER;
require CART2;
require LUSER;
use Date::Calc;

&ZOOVY::init();
&GTOOLS::init();

&DBINFO::db_zoovy_connect();
my ($LU) = LUSER->authenticate(flags=>'_O&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }
if (index($FLAGS,'BASIC')==-1) { print "Location: /biz\n\n"; exit; }

my $template_file = 'main.shtml';
my $MAX = 1000;

my $CMD = uc($ZOOVY::cgiv->{'CMD'});
my $SHOW_POOL = 0;

if ($CMD eq '') { $CMD = 'RECENT'; }
$GTOOLS::TAG{'<!-- CMD -->'} = $CMD;
$GTOOLS::TAG{'<!-- NEXT -->'} = '';

my ($orderset,$statusref,$createdref,$resultar);

my $buffer = 'internal error';
my $total = 0;
my $count = 0;
my $startts = time()-(86400*180);

my $r = undef;

if ($CMD eq 'RECENT') {
	$GTOOLS::TAG{'<!-- AREA -->'} = 'Recent';	
	($r) = ORDER::BATCH::report($USERNAME,DETAIL=>9,'POOL'=>'RECENT','LIMIT'=>$MAX);
   }
elsif ($CMD eq 'PENDING') {
	$GTOOLS::TAG{'<!-- AREA -->'} = 'Pending';
	($r) = ORDER::BATCH::report($USERNAME,DETAIL=>9,'POOL'=>'PENDING','LIMIT'=>$MAX);
   }
elsif ($CMD eq 'REVIEW') {
	$GTOOLS::TAG{'<!-- AREA -->'} = 'Review';
	($r) = ORDER::BATCH::report($USERNAME,DETAIL=>9,'POOL'=>'REVIEW','LIMIT'=>$MAX);
   }
elsif ($CMD eq 'HOLD') {
	$GTOOLS::TAG{'<!-- AREA -->'} = 'Hold';
	($r) = ORDER::BATCH::report($USERNAME,DETAIL=>9,'POOL'=>'HOLD','LIMIT'=>$MAX);
   }
elsif ($CMD eq 'APPROVED') {
	$GTOOLS::TAG{'<!-- AREA -->'} = 'Approved';
	($r) = ORDER::BATCH::report($USERNAME,DETAIL=>9,'POOL'=>'APPROVED','LIMIT'=>$MAX);
   }
elsif ($CMD eq 'PROCESS') {
	$GTOOLS::TAG{'<!-- AREA -->'} = 'Process';
	($r) = ORDER::BATCH::report($USERNAME,DETAIL=>9,'POOL'=>'PROCESS','LIMIT'=>$MAX);
   }
elsif ($CMD eq 'COMPLETED') {
	$GTOOLS::TAG{'<!-- AREA -->'} = 'Completed';
	my ($CLUSTER) = &ZOOVY::resolve_cluster($USERNAME);
	if (($CLUSTER eq 'SNAP') || ($CLUSTER eq 'DAGOBAH')) {
		$r = [];
		}
	else {
		($r) = ORDER::BATCH::report($USERNAME,DETAIL=>9,'POOL'=>'COMPLETED','SINCE'=>$startts,'LIMIT'=>$MAX);
		}
	# $buffer = '<b>due to system load - this feature has been disabled</b>'; 
	$GTOOLS::TAG{'<!-- MESSAGE -->'} = '<i>Note: orders will only appear in this list for 180 days after being last modified/synced - please search by order # to bring up orders beyond that time.</i>';
   }
elsif ($CMD eq 'CANCELLED') {
	$GTOOLS::TAG{'<!-- AREA -->'} = 'Cancelled';
	($r) = ORDER::BATCH::report($USERNAME,DETAIL=>9,'POOL'=>'DELETED','SINCE'=>$startts,'LIMIT'=>$MAX);
   $GTOOLS::TAG{'<!-- MESSAGE -->'} = '<i>Note: orders will only appear in this list for 180 days after being last modified/synced - please search by order # to bring up orders beyond that time.</i>';
   } 
elsif ($CMD eq 'BACKORDER') {
   $GTOOLS::TAG{'<!-- AREA -->'} = 'Backordered';
   $GTOOLS::TAG{'<!-- NEXT -->'} = '';
	($r) = ORDER::BATCH::report($USERNAME,DETAIL=>9,'POOL'=>'BACKORDER','SINCE'=>$startts,'LIMIT'=>$MAX);
   if ($count==$MAX) {
      $GTOOLS::TAG{'<!-- MESSAGE -->'} = qq~<font color="red">Maximum order count of $MAX reached. Please use search to find specific orders.</font>~;
      }
   }
elsif ($CMD eq 'SEARCH') {
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

#	if (scalar(@ORDERS)==1) {
#		## yay, we found 1 order - lets redirect
#		$template_file = 'redirect-order.shtml';
#		$GTOOLS::TAG{'<!-- ORDERID -->'} = $ORDERS[0];
#		}

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



if (not defined $r) {
	
	}
elsif ((defined $r) && (scalar(@{$r})>0)) {
	#mysql> desc ORDER_POOLS_S;
	#+----------------------+-----------------------------------------------------------------------------------------------+------+-----+---------+----------------+
	#| Field                | Type                                                                                          | Null | Key | Default | Extra          |
	#+----------------------+-----------------------------------------------------------------------------------------------+------+-----+---------+----------------+
	#| ID                   | int(11) unsigned                                                                              | NO   | PRI | NULL    | auto_increment |
	#| MERCHANT             | varchar(20)                                                                                   | NO   | MUL | NULL    |                |
	#| MID                  | int(11) unsigned                                                                              | NO   | MUL | 0       |                |
	#| ORDERID              | varchar(20)                                                                                   | NO   |     | NULL    |                |
	#| BS_SETTLEMENT        | int(10) unsigned                                                                              | NO   |     | 0       |                |
	#| CREATED_GMT          | int(10) unsigned                                                                              | NO   |     | 0       |                |
	#| MODIFIED_GMT         | int(10) unsigned                                                                              | NO   |     | 0       |                |
	#| CUSTOMER             | int(11) unsigned                                                                              | NO   |     | 0       |                |
	#| POOL                 | enum('RECENT','PENDING','APPROVED','PROCESS','COMPLETED','DELETED','BACKORDER','PREORDER','') | NO   |     | NULL    |                |
	#| ORDER_BILL_NAME      | varchar(30)                                                                                   | NO   |     | NULL    |                |
	#| ORDER_BILL_EMAIL     | varchar(30)                                                                                   | NO   |     | NULL    |                |
	#| ORDER_BILL_ZONE      | varchar(9)                                                                                    | NO   |     | NULL    |                |
	#| ORDER_PAYMENT_STATUS | char(3)                                                                                       | NO   |     | NULL    |                |
	#| ORDER_PAYMENT_METHOD | varchar(4)                                                                                    | NO   |     | NULL    |                |
	#| ORDER_TOTAL          | decimal(10,2)                                                                                 | NO   |     | 0.00    |                |
	#| ORDER_SPECIAL        | varchar(40)                                                                                   | NO   |     | NULL    |                |
	#| MKT                  | int(10) unsigned                                                                              | YES  |     | 0       |                |
	#| ITEMS                | tinyint(3) unsigned                                                                           | NO   |     | 0       |                |
	#| PAID_GMT             | int(10) unsigned                                                                              | NO   |     | 0       |                |
	#| PAID_TXN             | varchar(12)                                                                                   | NO   |     | NULL    |                |
	#+----------------------+-----------------------------------------------------------------------------------------------+------+-----+---------+----------------+
	#20 rows in set (0.02 sec)
	my $c = "";

	my %ORDERS = ();


	my $BGCOLOR = "CCCCCC";
	$c .= "<table width=\"100%\" cellpadding=\"3\" cellspacing=\"0\" border=\"0\"><tr>";
	$c .= "<td bgcolor=\"$BGCOLOR\"><a href=\"#\" onClick=\"toggleAll();\"><img border=\"0\" width=\"18\" height=\"18\" src=\"images/green_check.gif\"></a></td>"; 
	$c .= "<td bgcolor=\"$BGCOLOR\"><a href=\"javascript:sortBy('ID');\"><font size=\"2\" face=\"Arial\" color=\"000000\"><b>ID</a></font></td>";
	if ($SHOW_POOL) { 
		$c .= "<td bgcolor=\"$BGCOLOR\"><font size=\"2\" face=\"Arial\" color=\"000000\"><b>STATUS</font></td>"; 
		}
	$c .= "<td bgcolor=\"$BGCOLOR\"><a href=\"javascript:sortBy('ORDER_BILL_NAME');\"><font size=\"2\" face=\"Arial\" color=\"000000\"><b>Customer</a></font></td>";
	$c .= "<td bgcolor=\"$BGCOLOR\"><a href=\"javascript:sortBy('ORDER_SHIP_ZONE');\"><font size=\"2\" face=\"Arial\" color=\"000000\"><b>Ship Dest</a></font></td>";
	$c .= "<td bgcolor=\"$BGCOLOR\"><a href=\"javascript:sortBy('ORDER_TOTAL');\"><font size=\"2\" face=\"Arial\" color=\"000000\"><b>Amount</a></font></td>";
	$c .= "<td bgcolor=\"$BGCOLOR\"><a href=\"javascript:sortBy('REVIEW_STATUS');\"><font size=\"2\" face=\"Arial\" color=\"000000\"><b>Fraud</a></font></td>";
	$c .= "<td bgcolor=\"$BGCOLOR\"><a href=\"javascript:sortBy('ORDER_PAYMENT_STATUS');\"><font size=\"2\" face=\"Arial\" color=\"000000\"><b>Pay Status</a></font></td>";
	$c .= "<td bgcolor=\"$BGCOLOR\"><a href=\"javascript:sortBy('ORDER_PAYMENT_METHOD');\"><font size=\"2\" face=\"Arial\" color=\"000000\"><b>Pay Type</a></font></td>";
	$c .= "<td bgcolor=\"$BGCOLOR\"><a href=\"javascript:sortBy('ITEMS');\"><font size=\"2\" face=\"Arial\" color=\"000000\"><b>Items</a></font></td>";
	$c .= "<td bgcolor=\"$BGCOLOR\"><a href=\"javascript:sortBy('FLAGS');\"><font size=\"2\" face=\"Arial\" color=\"000000\"><b>Special</a></font></td>";
	$c .= "<td bgcolor=\"$BGCOLOR\"><a href=\"javascript:sortBy('CREATED_GMT');\"><font size=\"2\" face=\"Arial\" color=\"000000\"><b>Created</a></font></a></td>";
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
		
		$c .= "<tr class=\"$class\">";
		$c .= "<td><input type=\"checkbox\" $checked name=\"order-$id\"></td>"; 
		$c .= "<td><a target=\"body\" href=\"view.cgi?ID=$id\">$id</a></td>";
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


		$c .= "<td>".&ZTOOLKIT::pretty_date($ref->{'CREATED_GMT'})."</td>";
 		$c .= "</tr>";
 		}
	$c .= "</table>";
	$buffer = $c;
   # OVERRIDE
	}
elsif (scalar(@{$r})==0) {
	$buffer = "No orders found";
	}
else {
	## internal error! - should never be reached
	}

$GTOOLS::TAG{'<!-- ORDER_TOTAL -->'} = sprintf("%.2f",$total);
$GTOOLS::TAG{'<!-- ORDER_TABLE -->'} = $buffer;
$GTOOLS::TAG{'<!-- ORDER_COUNT -->'} = $count;
if ($count>=$MAX) { 	
	$GTOOLS::TAG{'<!-- MESSAGE -->'} = qq~<font color="red">Maximum order count of $MAX reached. Please use search to find specific orders.</font>~;
	}

&GTOOLS::output(file=>$template_file,header=>1);

&DBINFO::db_zoovy_close();

exit;





	
__DATA__

