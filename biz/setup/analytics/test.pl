#!/usr/bin/perl

use lib "/httpd/modules";
#use SITE::MSGS;
use ZTOOLKIT::SECUREKEY;
use URI::Escape;

my ($securekey) = &ZTOOLKIT::SECUREKEY::gen_key('cubworld','VR');

$vp = '1%3APROM%3A1245013437%3A10800';
$vp = URI::Escape::uri_unescape($vp);
$try_vpd = '27e18cac76ee5562192f595536429f4189202ab0';

use Digest::HMAC_SHA1;
## $vpd is "Veruta Promotion Digest" which is computed on $vp, using the securekey passed in the "Zoovy" header of
## 	the file, from an architecture standpoint, this should be saved in the persons account someplace.
##		i decided to use the hex version, rather than URI encode this, so that it wouldn't get fubar'd on a 301 redirect
my	$vpd = Digest::HMAC_SHA1::hmac_sha1_hex($vp, $securekey);

print "Vpd: $vpd\n";
print "     $try_vpd\n";

exit;



require Test::Timestamp;
$SITE::pbench = new Test::Timestamp(name=>"website");
	$SITE::pbench->init();

$data =q~
<zoovy:profile>DEFAULT</zoovy:profile>
<zoovy:prod_thumb>1/18_3</zoovy:prod_thumb>
<zoovy:prod_mfg>GUCCI</zoovy:prod_mfg>
<zoovy:prod_mfgid>2754</zoovy:prod_mfgid>
<zoovy:pkg_height>5</zoovy:pkg_height>
<zoovy:prod_upc>354654654</zoovy:prod_upc>
<zoovy:inv_enable>1</zoovy:inv_enable>
<zoovy:base_weight>3</zoovy:base_weight>
<zoovy:ship_int_cost2>2.00</zoovy:ship_int_cost2>
<zoovy:prod_condition>New</zoovy:prod_condition>
<zoovy:prod_name>Gucci 1844 Brown Havana</zoovy:prod_name>
<zoovy:base_cost>54.00</zoovy:base_cost>
<zoovy:taxable>1</zoovy:taxable>
<zoovy:prod_desc>Brand new authentic Gucci 1844/s sunglasses. Colors available are gold, brown, black. They are made in italy and come with Gucci case and Gucci cleaning cloth. </zoovy:prod_desc>
<zoovy:pkg_width>4</zoovy:pkg_width>
<zoovy:ship_can_cost1>24.95</zoovy:ship_can_cost1>
<zoovy:ship_cost1>11.95</zoovy:ship_cost1>
<zoovy:ship_insurance>0.00</zoovy:ship_insurance>
<zoovy:prod_image1>1/18_2</zoovy:prod_image1>
<zoovy:pkg_depth>7</zoovy:pkg_depth>
<zoovy:base_price>119.95</zoovy:base_price>
<zoovy:ship_can_cost2>2.00</zoovy:ship_can_cost2>
<zoovy:ship_cost2>2.00</zoovy:ship_cost2>
<zoovy:ship_int_cost1>29.95</zoovy:ship_int_cost1>
<zoovy:pkg_exclusive>0</zoovy:pkg_exclusive>
~;

$datax =q~
&lt;zoovy:profile&gt;DEFAULT&lt;/zoovy:profile&gt;
&lt;zoovy:prod_thumb&gt;1/18_3&lt;/zoovy:prod_thumb&gt;
&lt;zoovy:prod_mfg&gt;GUCCI&lt;/zoovy:prod_mfg&gt;
&lt;zoovy:prod_mfgid&gt;2754&lt;/zoovy:prod_mfgid&gt;
&lt;zoovy:pkg_height&gt;5&lt;/zoovy:pkg_height&gt;
&lt;zoovy:prod_upc&gt;354654654&lt;/zoovy:prod_upc&gt;
&lt;zoovy:inv_enable&gt;1&lt;/zoovy:inv_enable&gt;
&lt;zoovy:base_weight&gt;3&lt;/zoovy:base_weight&gt;
&lt;zoovy:ship_int_cost2&gt;2.00&lt;/zoovy:ship_int_cost2&gt;
&lt;zoovy:prod_condition&gt;New&lt;/zoovy:prod_condition&gt;
&lt;zoovy:prod_name&gt;Gucci 1844 Brown Havana&lt;/zoovy:prod_name&gt;
&lt;zoovy:base_cost&gt;54.00&lt;/zoovy:base_cost&gt;
&lt;zoovy:taxable&gt;1&lt;/zoovy:taxable&gt;
&lt;zoovy:prod_desc&gt;Brand new authentic Gucci 1844/s sunglasses. Colors available are gold, brown, black. They are made in italy and come with Gucci case and Gucci cleaning cloth. &lt;/zoovy:prod_desc&gt;
&lt;zoovy:pkg_width&gt;4&lt;/zoovy:pkg_width&gt;
&lt;zoovy:ship_can_cost1&gt;24.95&lt;/zoovy:ship_can_cost1&gt;
&lt;zoovy:ship_cost1&gt;11.95&lt;/zoovy:ship_cost1&gt;
&lt;zoovy:ship_insurance&gt;0.00&lt;/zoovy:ship_insurance&gt;
&lt;zoovy:prod_image1&gt;1/18_2&lt;/zoovy:prod_image1&gt;
&lt;zoovy:pkg_depth&gt;7&lt;/zoovy:pkg_depth&gt;
&lt;zoovy:base_price&gt;119.95&lt;/zoovy:base_price&gt;
&lt;zoovy:ship_can_cost2&gt;2.00&lt;/zoovy:ship_can_cost2&gt;
&lt;zoovy:ship_cost2&gt;2.00&lt;/zoovy:ship_cost2&gt;
&lt;zoovy:ship_int_cost1&gt;29.95&lt;/zoovy:ship_int_cost1&gt;
&lt;zoovy:pkg_exclusive&gt;0&lt;/zoovy:pkg_exclusive&gt;
~;


$i = 1;
# my @msgs = keys %SITE::MSGS::DEFAULTS;
use Data::Dumper;
while ($i++ < 1000) {
#foreach my $msg (@msgs) {
	# SITE::MSGS::interpolate_macroref(SITE::MSGS::DEFAULTS->{$msg},\%SITE::EMAIL::CART_MACROS);
	# next if ($SITE::MSGS::DEFAULTS{$msg}->{'msg'} !~ /%/);
	# print "ID: $msg\n";

#	&ZTOOLKIT::decode($data);
	

#	next;
#	my %hash = ();
	&ZTOOLKIT::fast_xmlish_to_hashref($data,'lowercase'   => 1,
		'tag_match'   => qr/\w+\:\w+/,
		'use_hashref' => \%hash);
	
	# print Dumper(\%hash);

	# return(&ZTOOLKIT::xmlish_to_hashref($BUFFER, 'lowercase'=>'1', 'tag_match'=>qr/\w+:\w+/, 'use_hashref'=>$HASHREF));
#	($txt) = SITE::MSGS::safe_interpolate_macroref($SITE::MSGS::DEFAULTS{$msg}->{'msg'},\%SITE::EMAIL::CART_MACROS);
#	($txt1) = SITE::MSGS::fast_interpolate_macroref($SITE::MSGS::DEFAULTS{$msg}->{'msg'},\%SITE::EMAIL::CART_MACROS);
#	if ($txt ne $txt1) {
#		print "ORIG: $SITE::MSGS::DEFAULTS{$msg}->{'msg'}\n";
#		print "TXT1: $txt\n";
#		print "TXT2: $txt1\n";
#		die();
#		}
#	}
	if (($i%100)==0) { $SITE::pbench->stamp("$i"); }
}

#print SITE::MSGS::fast_interpolate_macroref(q~
#%FOO%
#~,\%SITE::EMAIL::CART_MACROS);

$SITE::pbench->stamp("done");

$SITE::pbench->resultAsString();

##
##
##
exit;
use HTML::Mason;

use IO::File;
my $fh = new IO::File ">/tmp/mason.out";

my $foo;

my $interp = HTML::Mason::Interp->new(out_method=>\$foo);
my $comp = $interp->make_component(comp_source=>q~
% print("hello");
~,
);
$interp->exec($comp,out_method => sub { $fh->print($_[0]) });
