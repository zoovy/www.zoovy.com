#!/usr/bin/perl

use lib "/httpd/modules";
use ZOOVY;
use GTOOLS;
use LUSER;
use CGI;
use PRODUCT;
use utf8;

&ZOOVY::init();
my ($LU) = LUSER->authenticate();
if (not defined $LU) { warn "Auth"; exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT,$RESELLER) = $LU->authinfo();
if ($RESELLER eq '') { $RESELLER = 'ZOOVY'; }
if ($MID<=0) { exit; }

my $PRODUCT = $ZOOVY::cgiv->{'PRODUCT'};

my ($P) = PRODUCT->new($USERNAME,$PRODUCT);

if ($ZOOVY::cgiv->{'ACTION'} eq 'SAVE') {
	$html = $ZOOVY::cgiv->{'ta'};
	
	print STDERR "HTML: [$html]\n";
	
	$html =~ s/\<head\>.*?\<\/head\>//gs;
	$html =~ s/<[\/]?body.*?>//gs;
	$html =~ s/<[\/]?html>//gs;
	$html =~ s/^[\r\n]+//gs;
	$html =~ s/[\r\n]+$//gs;

	if (utf8::is_utf8($html) eq '') {
		## NOTE: this is specifically intended to correct situations where some clients post to us
		##                      in ISO-8859-1 from a UTF8 form field.
		$html = Encode::decode("utf8",$html);
		utf8::decode($html);
		}
	
	# &ZOOVY::saveproduct_attrib($USERNAME,$PRODUCT,'zoovy:prod_desc',$html);
	$P->store('zoovy:prod_desc',$html);
	$P->save();
	print "Location: http://www.zoovy.com/biz/product/edit.cgi?PID=$PRODUCT\n\n";
	exit;
	}

$GTOOLS::TAG{'<!-- PRODUCT -->'} = $PRODUCT;
$GTOOLS::TAG{'<!-- HTMLCONTENT -->'} = $P->fetch('zoovy:prod_desc');
# &ZOOVY::fetchproduct_attrib($USERNAME,$PRODUCT,'zoovy:prod_desc');

&GTOOLS::output('*LU'=>$LU,
	title=>'',
	header=>1,
	file=>'index.shtml',
	);