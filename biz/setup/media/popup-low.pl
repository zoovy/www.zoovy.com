#!/usr/bin/perl

use lib "/httpd/modules";
require ZOOVY;
require ZTOOLKIT;
require PRODUCT;
use strict;


##
## parameters:
##
##		attrib=zoovy:property -- set an attrib
##
##

use CGI;
require GTOOLS;

&GTOOLS::init();
&ZOOVY::init();

my $template_file = 'popup-low.shtml';
my $q = new CGI;
my $s = {};
if (not defined $q->param('s')) {
	exit;
	}

# print STDERR "S: ".$q->param('s')."\n";

$s = &ZTOOLKIT::fast_deserialize($q->param('s'),1);
foreach my $p ($q->param()) { 
	next if ($p eq 'USERNAME');
	next if ($p eq 's');
	next if ($p eq 'upfile');
	$s->{$p} = $q->param($p); 
	}

my ($USERNAME,$FLAGS,$MID,$LUSERNAME,$RESELLER,$PRT) = (undef,undef);
if ($s->{'AUTH'} =~ /^(.*?):(.*)$/) {
	$USERNAME = $1; my $MD5PASS = $2;
	require ZAUTH;
	if (&ZAUTH::md5_check($USERNAME,$MD5PASS)>0) { $USERNAME = ''; }
	}
else {
	require LUSER;
	my ($LU) = LUSER->authenticate(flags=>'_S&4|_P&1');
	if (not defined $LU) { exit; }

	($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
	if ($MID<=0) { exit; }
	}

if ($USERNAME eq '') {
	print "Content-type: text/plain\n\n";
	print "Username is not set, or authentication token is invalid.\n";
	}

my $JS = '';
my $img = '';
if (defined $s->{'IMG'}) {

	$GTOOLS::TAG{'<!-- IMAGEURL -->'} = &GTOOLS::imageurl($USERNAME,$s->{'IMG'},100,100,'FFFFFF',undef);
	if ($s->{'mode'} eq 'logo') { 
		require ZWEBSITE;
		require ZOOVY;
		my $url = &GTOOLS::imageurl($USERNAME,$s->{'IMG'},100,100,'FFFFFF',undef);
		&ZOOVY::savemerchantns_attrib($USERNAME,$s->{'profile'},'zoovy:logo_website',$s->{'IMG'});
		$JS = qq~
top.opener.document.logoimg.src='$url'; 
top.close();
~;
		}

	if ($s->{'mode'} eq 'ilogo') { 
		require ZOOVY;

		my ($w,$h) = split(/x/,&ZOOVY::fetchmerchantns_attrib($USERNAME,$s->{'profile'},'zoovy:logo_invoice_xy'));
		if (not defined $w) { $w = 300; }
		if (not defined $h) { $h = 100; }

		my $url = &GTOOLS::imageurl($USERNAME,$s->{'IMG'},$h,$w,'FFFFFF',undef);
		# &ZOOVY::savemerchantns_attrib($USERNAME,$s->{'profile'},'zoovy:logo_website',$s->{'IMG'});
		&ZOOVY::savemerchantns_attrib($USERNAME,$s->{'profile'},'zoovy:logo_invoice',$s->{'IMG'});
		$JS = qq~
top.opener.document.invoiceimg.src='$url'; 
top.close();
~;
		}


	## Speciality Logo
	if ($s->{'mode'} eq 'slogo') { 
		my $panel = $s->{'panel'};
		$JS = qq~top.opener.document.forms['$panel'].SP_LOGO.value='$s->{'IMG'}';  top.close(); ~;
		}


	if ($s->{'mode'} eq 'customerlogo') { 
		require CUSTOMER;
		my ($C) = CUSTOMER->new($USERNAME,CID=>$s->{'CID'},INIT=>16);
		$C->set_attrib('WS.LOGO',$s->{'IMG'});
		$C->save_wholesale(1);
		$C->save();

		my $url = &GTOOLS::imageurl($USERNAME,$s->{'IMG'},70,200,'FFFFFF',undef);
		$JS = qq~
top.opener.document.logoImg.src='$url'; 
top.close();
~;
		}

	if ($s->{'mode'} eq 'prodsku') {
		my ($PID) = &PRODUCT::stid_to_pid($s->{'sku'});
		my ($P) = PRODUCT->new($USERNAME,$PID,'create'=>0);
		#my ($prodref) = &ZOOVY::fetchproduct_as_hashref($USERNAME,$s->{'sku'});
		#my $dref = &ZOOVY::deserialize_skuref($prodref,$s->{'sku'});
		# $dref->{$s->{'attrib'}} = $s->{'IMG'};
		# &ZOOVY::serialize_skuref($prodref,$s->{'sku'},$dref);
		#&ZOOVY::saveproduct_from_hashref($USERNAME,$s->{'sku'},$prodref);
		
		$P->skustore($s->{'sku'},$s->{'attrib'},$s->{'IMG'});
		#print STDERR "STORE: $s->{'sku'},$s->{'attrib'},$s->{'IMG'}\n";
		#use Data::Dumper; print STDERR Dumper($P);
		$P->save();

		my $url = &GTOOLS::imageurl($USERNAME,$s->{'IMG'},50,50,'CCCCCC',undef);
		$GTOOLS::TAG{'<!-- IMAGEURL -->'} = $url;
		$JS = qq~
			top.opener.document.getElementById('$s->{'img'}').src='$url';
			top.close();
			~;
		}
	if ($s->{'mode'} eq 'prod') {
		# &ZOOVY::saveproduct_attrib($USERNAME,$s->{'prod'},lc('zoovy:prod_'.$s->{'img'}),$s->{'IMG'});
		my ($P) = PRODUCT->new($USERNAME,$s->{'prod'}); $P->store(lc('zoovy:prod_'.$s->{'img'}),$s->{'IMG'});	$P->save();
		my $url = &GTOOLS::imageurl($USERNAME,$s->{'IMG'},50,50,'CCCCCC',undef);
		$GTOOLS::TAG{'<!-- IMAGEURL -->'} = $url;
		$JS = qq~
			top.opener.document.forms['images!frm'].$s->{'img'}.src='$url';
			top.close();
			~;
		}

	if ($s->{'mode'} eq 'prodflexedit') {
		# &ZOOVY::saveproduct_attrib($USERNAME,$s->{'product'},$s->{'attrib'},$s->{'IMG'});
		my ($P) = PRODUCT->new($USERNAME,$s->{'product'}); $P->store($s->{'attrib'},$s->{'IMG'});	$P->save();
		my $url = &GTOOLS::imageurl($USERNAME,$s->{'IMG'},50,50,'CCCCCC',undef);
		$GTOOLS::TAG{'<!-- IMAGEURL -->'} = $url;
		my $attrib = $s->{'attrib'};
		$JS = qq~
			top.opener.document.images['$attrib'].src='$url';
			top.close();
			~;
		}

	if ($s->{'mode'} eq 'coupon') {
		require CART::COUPON;
		my $url = &GTOOLS::imageurl($USERNAME,$s->{'IMG'},50,50,'FFFFFF',undef);
		$GTOOLS::TAG{'<!-- THUMBURL -->'} = $url;

		$JS = qq~
			top.opener.document.THUMBURL.src='$url';
			top.opener.document.promo_form.IMAGE.value='$s->{'IMG'}';
			top.close();
			~;
		}

	if ($s->{'mode'} eq 'promo') {
		#print STDERR "in popup-low for promo\n";
		my $url = &GTOOLS::imageurl($USERNAME,$s->{'IMG'},50,50,'FFFFFF',undef);
		$GTOOLS::TAG{'<!-- THUMBURL -->'} = $url;

		$JS = qq~
			top.opener.document.THUMBURL.src='$url';
			top.opener.document.promo_form.IMAGE.value='$s->{'IMG'}';
			top.close();
			~;

		}

	if ($s->{'mode'} eq 'navcat') {
		require NAVCAT;
		my ($NC) = NAVCAT->new($USERNAME,PRT=>$PRT);
		(undef,undef,undef,undef,my $metaref) = $NC->get($s->{'safe'});
		$metaref->{'CAT_THUMB'} = $s->{'IMG'};
		$NC->set($s->{'safe'}, metaref=>$metaref);
		$NC->save();
		# &NAVCAT::save_attrib($USERNAME,$s->{'safe'},'CAT_THUMB',$s->{'IMG'});
		# print STDERR "FOO $USERNAME $s->{'safe'},'CAT_THUMB',$s->{'IMG'}\n";

		my $url = &GTOOLS::imageurl($USERNAME,$s->{'IMG'},21,26,'FFFFFF',undef);
		$GTOOLS::TAG{'<!-- IMAGEURL -->'} = $url;
		$JS = qq~
			// top.opener.document.myForm.$s->{'thumb'}.src='$url';
			top.opener.document.forms['NAVCAT!frm'].$s->{'thumb'}.src='$url';
			top.close();
			~;
		}


	if ($s->{'mode'} eq 'channel') {
		my $url = &GTOOLS::imageurl($USERNAME,$s->{'IMG'},50,50,'FFFFFF',undef);
		$GTOOLS::TAG{'<!-- IMAGEURL -->'} = $url;
		my $val = $s->{'IMG'};
		my $t = time();

		$JS = qq~
			top.setImage('$val','$url',$t);
			top.close();
			~;
		}

	if ($s->{'mode'} eq 'pogchooser') {
		my $url = &GTOOLS::imageurl($USERNAME,$s->{'IMG'},50,50,'FFFFFF',undef);
		$GTOOLS::TAG{'<!-- IMAGEURL -->'} = $url;
		my $val = $s->{'IMG'};
		my $t = time();

		$JS = qq~
			top.setImage('$val','$url',$t);
			top.close();
			~;
		}

	if ($s->{'mode'} eq 'flow') {
		my $BUF = $s->{'IMG'};
		# use Data::Dumper; print STDERR Dumper($s);
		if ($s->{'PROD'} ne '') {
			## we're editing a product
			$JS = "parent.window.location='/biz/product/flow/element.cgi?ACTION=SAVE&IMAGE=$BUF&PROD=$s->{'PROD'}&FL=$s->{'FL'}&EL=$s->{'EL'}&FS=$s->{'FS'}&PG=".CGI->escape($s->{'PG'})."';\n\n";
			}
		else {
			## we're editing a webpage.
			$JS = "parent.window.location='/biz/setup/builder/element.cgi?ACTION=SAVE&IMAGE=$BUF&PROD=$s->{'PROD'}&FL=$s->{'FL'}&EL=$s->{'EL'}&FS=$s->{'FS'}&PG=".CGI->escape($s->{'PG'})."';\n\n";
			}
		
		}

	if ($s->{'mode'} eq 'prodimgmgr') {
		# &ZOOVY::saveproduct_attrib($USERNAME,$s->{'product'},$s->{'attrib'},$s->{'IMG'});
		my ($P) = PRODUCT->new($USERNAME,$s->{'product'}); $P->store($s->{'attrib'},$s->{'IMG'});	$P->save();
		$JS = "parent.window.location='/biz/product/imagemgr/index.cgi?product=$s->{'product'}';\n\n";
		}

	if ($s->{'mode'} eq 'dynimg') {
		my $url = &GTOOLS::imageurl($USERNAME,$s->{'IMG'},75,75,'CCCCCC',undef);
		# print STDERR $url."\n";
		$GTOOLS::TAG{'<!-- IMAGEURL -->'} = $url;
		my $val = $s->{'IMG'};
		my $t = time();

		$JS = qq~
			top.setImage('$val','$url',$t);
			// parent.foo();
			top.close();
			~;
		}

	}

#print STDERR "JS: ".$JS."\n";

$GTOOLS::TAG{'<!-- JAVASCRIPT -->'} = $JS;
&GTOOLS::output( file=>'popup-low.shtml', header=>1 );
