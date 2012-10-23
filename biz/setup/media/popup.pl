#!/usr/bin/perl


##
## parameters:
##
## 	mode=logo			(popup)
##			-> sets zoovy:company_logo
##			-> sets webdb - company_logo
##
## 	mode=slogo			(popup - logo chooser for speciality domains)
##			-> sets thisFrm.SLOGO
##
##		mode=ilogo			(popup)
##			-> sets zoovy:invoice_logo
##
##		mode=customerlogo	(popup)	(myForm.logoImg)
##			-> sets CUSTOMER->{'WS'}->{'LOGO'} property!
##			-> this is passed CID (customer id) 
##
##		mode=prodimgmgr (myForm)
##			-> product=PRODUCT
##			-> attrib=zoovy:prod_image1,zoovy:prod_image2
##
##		mode=prodflexedit (myForm)
##			-> product=PRODUCT
##			-> attrib=zoovy:prod_image1,zoovy:prod_image2
##
##		mode=prod						(myForm.Thumb)
##			-> prod=PRODUCT
##			-> img=Thumb,Image1,Image2,..
##
##		mode=navcat						(myForm.imgX)
##			-> safe=category safename
##			-> img=image name
##			-> thumb= where to save the image preview
##
##		mode=channel		(popup)
##			-> SERIAL=serialized hash	(use fast_deserialize)
##					-> ATTRIB
##					-> SRC
##					-> DIV (default to DIV)
##					-> IMAGENAME
##					-> PROMPT
##			->	t=time
##
##		mode=flow			(embedded)
##			-> FL=flow #
##			->	EL=element
##			-> FS=flow style (optional)
##			->	PG=page (if not product)
##			->	PROD=productid (if not page)
##
##		mode=dynimg			(popup)
##			-> SERIAL=serialized
##
##		mode=pogchooser (popup + windows client) -- [NOTE: same parameters as channel]
##			-> SERIAL=serialized hash (use fast_deserialize)
##				-> ATTRIB=>'img'
##				-> SRC=>'',
##				-> PROMPT=>'Select List Image',
##				-> DIV=>'thisFrm',
##				-> AUTH=>auth token
##
##		mode=promo
##			-> promo=PROMO_ID
##
##		mode=coupon
##			-> promot=COUPON_ID
##			
## note: to add a new handler simply do the following
##		in popup-top.pl set the CANCELLINK javascript (to cancel any changes)
##		in popup-top.pl set the CLEARLINK javascript (to initialize the image)
##		in popup-low.pl set the SAVE code
use CGI;

use lib "/httpd/modules";
require ZTOOLKIT;
require ZOOVY;
require LUSER;
require PRODUCT;

&ZOOVY::init();
my ($USERNAME,$FLAGS,$MID,$LUSERNAME,$RESELLER,$PRT) = (undef,undef);
use strict;

## we pass the URI parameters through
my $q = new CGI;
my $SERIAL = undef;

## 
## MD5 Authentication is used by pogchooser mode -- but might be used elsewhere later.
##
if ($q->param('SERIAL')) {
	$SERIAL = &ZTOOLKIT::fast_deserialize($q->param('SERIAL'),1);	
	if ($SERIAL->{'AUTH'} =~ /^(.*?):(.*)$/) {
		$USERNAME = $1; my $MD5PASS = $2;
		require ZAUTH;
		if (&ZAUTH::md5_check($USERNAME,$MD5PASS)>0) { $USERNAME = undef; }
		}
	}

## username will not be defined unless MD5 Auth was not run or failed!
if (not defined $USERNAME) {
	require LUSER;
	my ($LU) = LUSER->authenticate(flags=>'_S&4|_P&1');
	if (not defined $LU) { exit; }

	($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
	if ($MID<=0) { exit; }
	}

my $s = {};
foreach my $p ($q->param()) {
	$s->{$p} = $q->param($p); 
	}

if ($s->{'mode'} eq 'logo') {
	my $profile = $s->{'profile'};
	$s->{'IMG'} = &ZOOVY::fetchmerchantns_attrib($USERNAME,$profile,'zoovy:logo_website');
	}
elsif ($s->{'mode'} eq 'ilogo') {
	my $profile = $s->{'profile'};
	$s->{'IMG'} = &ZOOVY::fetchmerchantns_attrib($USERNAME,$profile,'zoovy:logo_invoice');
	}
elsif ($s->{'mode'} eq 'slogo') {
	$s->{'IMG'} = $s->{'img'};
	}
elsif ($s->{'mode'} eq 'prodsku') {
	## image panel, sku specific image
	my ($PID) = &PRODUCT::stid_to_pid($s->{'sku'});
	my ($P) = PRODUCT->new($USERNAME,$PID);
	my $skuref = $P->skuref($s->{'sku'});
	# &ZOOVY::fetchsku_as_hashref($USERNAME,$s->{'sku'});
	my $attrib = $s->{'img'};  $attrib =~ s/^(.*?):.*$/$1/; $attrib = lc("zoovy:prod_$attrib");
	$s->{'attrib'} = $attrib;
	$s->{'IMG'} = $skuref->{$attrib};
	}
elsif ($s->{'mode'} eq 'prod') {
	my ($P) = PRODUCT->new($USERNAME,$s->{'prod'},'create'=>0);
	if (defined $P) { $s->{'IMG'} = $P->fetch( lc('zoovy:prod_'.$s->{'img'}) ); }
	# $s->{'IMG'} = &ZOOVY::fetchproduct_attrib($USERNAME,$s->{'prod'},lc('zoovy:prod_'.$s->{'img'}));
	}
elsif ($s->{'mode'} eq 'promo') {
	require ZSHIP;
	my @rules = &ZSHIP::RULES::fetch_rules($USERNAME,$PRT,'PROMO');
   my %hash = %{$rules[$s->{'promo'}]};
	$s->{'IMG'} = &ZOOVY::incode($hash{'IMAGE'});
	} 
elsif ($s->{'mode'} eq 'coupon') {
	require CART::COUPON;
	my ($cpnref) = &CART::COUPON::load($USERNAME,$PRT,$s->{'coupon'});
	$s->{'IMG'} = &ZOOVY::incode($cpnref->{'image'});
#	my @rules = &ZSHIP::RULES::fetch_rules($USERNAME,'PROMO');
#   my %hash = %{$rules[$s->{'promo'}]};
#	$s->{'IMG'} = &ZOOVY::incode($hash{'IMAGE'});
	} 
elsif ($s->{'mode'} eq 'prodimgmgr') {
	my ($P) = PRODUCT->new($USERNAME,$s->{'prod'},'create'=>0);
	if (defined $P) { $s->{'IMG'} = $P->fetch( lc($s->{'attrib'}) ); }
	# $s->{'IMG'} = &ZOOVY::fetchproduct_attrib($USERNAME,$s->{'product'},lc($s->{'attrib'}));
	}
elsif ($s->{'mode'} eq 'prodflexedit') {
	## inside the flex editor.
	my $PID = $s->{'prod'};
	if ($PID eq '') { $PID = $s->{'product'} };	# used by html listing panel (that recycles flexedit)

	my ($P) = PRODUCT->new($USERNAME,$PID,'create'=>0);
	if (defined $P) { $s->{'IMG'} = $P->fetch( lc($s->{'attrib'}) ); } 
	print STDERR "prodflexedit USER:$USERNAME prod:$s->{'prod'} IMG: $s->{'IMG'}\n";
	# $s->{'IMG'} = &ZOOVY::fetchproduct_attrib($USERNAME,$s->{'product'},lc($s->{'attrib'}));
	}
elsif ($s->{'mode'} eq 'channel') {
	$s->{'IMG'} = $SERIAL->{'VALUE'};
	}
elsif ($s->{'mode'} eq 'pogchooser') {
	$s->{'IMG'} = $SERIAL->{'VALUE'};
	}
elsif ($s->{'mode'} eq 'navcat') {
	require NAVCAT;
	my ($NC) = NAVCAT->new($USERNAME,PRT=>$PRT);
	(undef,undef,undef,undef,my $metaref) = $NC->get($s->{'safe'});
	$s->{'IMG'} = $metaref->{'CAT_THUMB'};
	undef $NC;
	# $s->{'IMG'} = &NAVCAT::fetch_attrib($USERNAME,$s->{'safe'},'CAT_THUMB');
	}
elsif ($s->{'mode'} eq 'customerlogo') {
	require CUSTOMER;
	my ($C) = CUSTOMER->new($USERNAME,CID=>$s->{'CID'});
	$s->{'IMG'} = $C->fetch_attrib('WS.LOGO');

	require MEDIA;
	&MEDIA::mkfolder($USERNAME,'protected');
	$s->{'PWD'} = 'protected';
	}

$s->{'USERNAME'} = $USERNAME;

if ($s->{'IMG'} ne '') {
	$GTOOLS::TAG{'<!-- IMGNAME -->'} = $s->{'IMG'};
	require MEDIA;
	my ($inforef) = MEDIA::getinfo($USERNAME,$s->{'IMG'});
	my ($pwd,$file,$ext) = MEDIA::parse_filename($s->{'IMG'});
	$s->{'PWD'} = $pwd;

	if (&MEDIA::resolve_fid($USERNAME,$pwd)<=0) {
		$s->{'PWD'} = '';
		$s->{'IMG'} = '';
		$GTOOLS::TAG{'<!-- IMGNAME -->'} = '** INVALID **';
		$GTOOLS::TAG{'<!-- IMGSIZE -->'} = '0k'; 
		}

#	require IMGLIB;
#	my $inforef = &IMGLIB::load_collection_info($USERNAME,$s->{'IMG'});
#	use Data::Dumper;
#	$GTOOLS::TAG{'<!-- IMGSIZE -->'} = Dumper($inforef);
	}
else {
	$GTOOLS::TAG{'<!-- IMGNAME -->'} = '* Not Set *';
	$GTOOLS::TAG{'<!-- IMGSIZE -->'} = '0k';
	}


my $S = &ZTOOLKIT::fast_serialize($s,1);

print "Content-type: text/html\n\n";
print "<html>\n<script>\n<!--//\n";

### BEGIN CHANNEL SPECIFIC JAVASCRIPT
if ($q->param('mode') eq 'channel' || $q->param('mode') eq 'pogchooser' || $q->param('mode') eq 'banner') {
	my $SERIAL = &ZTOOLKIT::fast_deserialize($q->param('SERIAL'),1);
	my $ATTRIB = $SERIAL->{'ATTRIB'};
	my $ID = $SERIAL->{'ID'};
	my $DIV = ($SERIAL->{'DIV'})?$SERIAL->{'DIV'}:'DIV';
print qq~
// used for Channels

function setImage(attrib,url,time) {
// alert('test: $ATTRIB');

if ('$ATTRIB'!='') {
	var thisFrm = opener.document.forms['thisFrm-$ID'];
	if (!thisFrm) { thisFrm = opener.document.forms['thisFrm']; }

 // alert(opener.document.thisFrm['${ATTRIB}img'].src);
	thisFrm['${ATTRIB}img'].src=url;
 // alert(opener.document.thisFrm['${ATTRIB}img'].src);
 // opener.document.thisFrm['${ATTRIB}img'].blur();
 	thisFrm['$ATTRIB'].value = attrib;
 this.close();
 // opener.document.focus();
 } 
else {
 alert('Could not save image, please contact support\@zoovy.com');
 }
}
~;

	}
### END OF CHANNEL SPECIFIC JAVASCRIPT


### BEGIN DYNIMAGE SPECIFIC JAVASCRIPT
if ($q->param('mode') eq 'dynimg') {
	my $SERIAL = &ZTOOLKIT::fast_deserialize($q->param('SERIAL'),1);
	my $ATTRIB = $SERIAL->{'ATTRIB'};
	my $ID = $SERIAL->{'ID'};
	my $DIV = ($SERIAL->{'DIV'})?$SERIAL->{'DIV'}:'DIV';
print qq~
function setImage(attrib,url,time) {
 if ('${ATTRIB}'!='') {
	var thisFrm = opener.document.forms['thisFrm-$ID'];
	if (!thisFrm) { thisFrm = opener.document.forms['thisFrm']; }
	// alert("${ATTRIB}");
 	thisFrm.${ATTRIB}img.src=url;
 	thisFrm.${ATTRIB}.value = attrib;
	
  } else {
 alert('Could not save image, please contact support\@zoovy.com');
 }
}
~;

	}
### END OF CHANNEL SPECIFIC JAVASCRIPT


print qq~

function foo() {	
	alert('foo!');
	}

var topInitialized = false;
//-->
</script>

<frameset frameborder=0 framespacing=0 border=1 cols="*" rows="150,200,200">
	<frame marginwidth=0 marginheight=0 src="/biz/setup/media/popup-top.cgi?s=$S" name="TopFrame" noresize scrolling="no">
	<frame marginwidth=0 marginheight=0 src="/biz/setup/media/popup-mid.cgi?s=$S" name="MidFrame" scrolling="yes">
	<frame marginwidth=0 marginheight=0 src="/biz/setup/media/popup-wait.shtml" name="LowFrame" scrolling="yes">
</frameset>
</html>
~;
