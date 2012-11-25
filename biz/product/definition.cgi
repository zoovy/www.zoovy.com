#!/usr/bin/perl

use strict;

use File::Slurp;
use Data::Dumper;
use JSON::XS;

use lib "/httpd/modules";
require PRODUCT::FLEXEDIT;
require PRODUCT;

# _PRODUCT
# DOC

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_P&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }


my $VERB = $ZOOVY::cgiv->{'_VERB'};

## note: some apps pass DOCID in uppercase so we need to run lc()
my $DOCID = lc($ZOOVY::cgiv->{'_DOCID'});
$GTOOLS::TAG{'<!-- DOCID -->'} = $DOCID;

print STDERR "VERB: $VERB\n";

my $PRODUCT = $ZOOVY::cgiv->{'_PRODUCT'};
$GTOOLS::TAG{'<!-- PRODUCT -->'} = $PRODUCT;

my $ref = undef;
# my ($prodref) = &ZOOVY::fetchproduct_as_hashref($USERNAME,$PRODUCT);
my ($P) = PRODUCT->new($LU,$PRODUCT);

if ($DOCID =~ /^\~(.*?)$/) {
	$ref = PRODUCT::FLEXEDIT::get_GTOOLS_Form_grp($1);
	}
else {
	$DOCID =~ s/[^a-z0-9\.]+//gs;
	
	my $dir = "/httpd/static/definitions";
	## amazon json files now live in subdir /amz
	if ($DOCID =~ /^amz/) {	
		$dir .= "/amz";
		}

	my $file = lc("$dir/$DOCID.json");
	print STDERR "FILE:$file\n";
	my $json = '';
	if (-f $file) {
		$json = &File::Slurp::read_file($file);
		}

	if ($json ne '') {
		$ref = JSON::XS::decode_json($json);
		}
	else {
		print "Content-type: text/plain\n\n";
		print "MISSING FILE: $file\n"; 
		}
	}

# print STDERR Dumper($ref,$ZOOVY::cgiv);
#print "Content-type: text/plain\n\n";
#print Dumper($ref);


if ($VERB eq 'SAVE') {
	my ($changes) = &PRODUCT::FLEXEDIT::prodsave($P,$ref,$ZOOVY::cgiv);
	if ($changes) {
		$P->save();
		}
	}

#if ($VERB eq 'QUIT') {
#	print "Location: /biz/product/edit.cgi?PID=$PRODUCT\n\n"; exit;
#	}

$GTOOLS::TAG{'<!-- OUTPUT -->'} = &PRODUCT::FLEXEDIT::output_html($P,$ref,form=>"definitionFrm");
$GTOOLS::TAG{'<!-- DOCID -->'} = $DOCID;


&GTOOLS::output(file=>'definition.shtml',header=>1);



