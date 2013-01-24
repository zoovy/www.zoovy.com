#!/usr/bin/perl


use strict;
use lib "/httpd/modules";
require LUSER;
require ZOOVY;
require CUSTOMER;

my ($LU) = LUSER->authenticate();
if (not defined $LU) { warn "Auth"; exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { warn "No auth"; exit; }


if ($USERNAME eq 'brian') {
	$FLAGS = ',BPP,';
	}

my $EMAIL = "$LUSERNAME\@$USERNAME.zoovy.com";


my ($CID) = CUSTOMER::resolve_customer_id("proshop",0,$EMAIL);
my $SCHEDULE = '';
if ($FLAGS =~ /,BPP,/) { $SCHEDULE = 'BPP'; }

my $c = undef;
if ($CID>0) {
	($c) = CUSTOMER->new("proshop",EMAIL=>$EMAIL,INIT=>0xFF,CID=>$CID);
	}
else {
	($c) = CUSTOMER->new("proshop",EMAIL=>$EMAIL,INIT=>0xFF,CREATE=>1);
	$c->set_attrib("INFO.NEWSLETTER",1);
	}
$CID = $c->cid();

my $company = $LU->get('zoovy:company_name');
$company = "user: ".$USERNAME;



$c->set_attrib('INFO.FIRSTNAME', $LU->get('zoovy:firstname'));
$c->set_attrib('INFO.LASTNAME', $LU->get('zoovy:lastname'));
$c->set_attrib('INFO.COMPANY', $company);
$c->set_attrib('INFO.SCHEDULE',$SCHEDULE);


my %bill = ();
$bill{'bill_phone'} = $LU->get('zoovy:phone');
$bill{'bill_company'} = $company;
$bill{'bill_firstname'} = $LU->get('zoovy:firstname');
$bill{'bill_lastname'} = $LU->get('zoovy:lastname');
$bill{'bill_address1'} = $LU->get('zoovy:address1');
$bill{'bill_address2'} = $LU->get('zoovy:address2');
$bill{'bill_city'} = $LU->get('zoovy:city');
$bill{'bill_state'} = $LU->get('zoovy:state');
$bill{'bill_zip'} = $LU->get('zoovy:zip');
$bill{'bill_email'} = $EMAIL;
$c->add_address('BILL',\%bill);

my %ship = ();
foreach my $k (keys %bill) {
	my $d = $k;
	$d =~ s/bill_/ship_/s;
	$ship{$d} = $bill{$k};
	}
$c->add_address('SHIP',\%ship);

$c->save();
my $PASS = $c->fetch_attrib('INFO.PASSWORD');

my $url = "http://proshop.zoovy.com/category/welcome";
if ($ZOOVY::cgiv->{'url'}) { $url = $ZOOVY::cgiv->{'url'}; }

print "Location: https://ssl.zoovy.com/s=proshop.zoovy.com/customer/login?login=$EMAIL&password=$PASS&url=$url\n\n";


##
## SCHEDULE: BPP
## 