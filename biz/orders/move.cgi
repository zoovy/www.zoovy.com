#!/usr/bin/perl

use lib "/httpd/modules";
use CGI;
require GTOOLS;
require ZOOVY;
#require ORDER;
require CART2;
require ORDER::BATCH;
require ZTOOLKIT;
require DBINFO;
require ZWEBSITE;
use Date::Calc;
use strict;

&DBINFO::db_zoovy_connect();
&ZOOVY::init();
&GTOOLS::init();

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_O&4');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

# my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("/biz/setup",2,'_O&4');
# if ($USERNAME eq '') { exit; }
# if ($FLAGS =~ /,L3,/) { $FLAGS .= ',API,'; }

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

if ($CMD eq 'PRINT') {
	&GTOOLS::print_form('','print.shtml',1);
	}


my $ORDERIDS = '';
my $template_file = '';

if ($CMD eq 'PAID') {
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

&GTOOLS::output(file=>$template_file,header=>1);

&DBINFO::db_zoovy_close();

exit;


	
