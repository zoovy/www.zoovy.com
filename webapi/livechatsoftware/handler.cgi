#!/usr/bin/perl


use strict;
use Data::Dumper;
use XML::Simple;

use lib "/httpd/modules";
require ZOOVY;
require ZAUTH;
require ZTOOLKIT;

my $xml = '';
if ($ENV{'REQUEST_METHOD'} eq 'POST') {
	$/ = undef; $xml = <STDIN>; $/ = "\n";
	$xml =~ s/[\r]+//gs;
	}

if (1) {
	$xml = q~
<?xml version="1.0"?>
<transcriptNotification>
<header id="securitykey">CCBC:DEFAULT:livechatinc*mariusz:welcome</header>
<header id="license">1234</header>
<header id="plug-version">1.0</header>
<header id="soft-version">1.0</header>
<header id="operator">brian</header>
<!--
please feel free to include any other header= tags you think might be useful,
e.g. ip address, duration, etc. ... the more you include the more I can enhance this
integration without your assistance.
-->
<body>
  <!--
  not sure how you store this, but please the messages here .. format as you wish
  -->
</body>
</transcriptNotification>
~;
	}

my %ERRORS = (
	0=>'',
	1=>'No Body Tag (Did you mean to do this?)',
	100=>'No XML received',
	101=>'Invalid XML',
	200=>'Required Header "securitykey" not found',
	201=>'Required Header "license" not found',
	202=>'Required Header "plug-version" not found',
	203=>'Required Header "soft-version" not found',
	204=>'Required Header "operator" not found',
	300=>'Authentication failure - please check your username or password.',
	);

my $err = 0;
my %results = ();

if (not $err) {	
	## preflight check
	if ($xml eq '') { $err = 100; }
	elsif ($xml !~ /<transcriptNotification>.*<\/transcriptNotification>/s) { $err = 101; }
	}

my $ref = undef;
if (not $err) {
	## xml parsing and required attribute check
	my $xs = new XML::Simple( VarAttr =>'id',ContentKey=>'-content', force_array=>1);
	$ref = $xs->XMLin($xml);
	if ($ref->{'securitykey'} eq '') { $err = 200; }
	elsif ($ref->{'license'} eq '') { $err = 201; }
	elsif ($ref->{'plug-version'} eq '') { $err = 202; }
	elsif ($ref->{'soft-version'} eq '') { $err = 203; }
	elsif ($ref->{'operator'} eq '') { $err = 204; }
	}

if (not $err) {
	## authentication
	my ($xMID,$PROFILE,$USER,$PASS) = split(/:/,$ref->{'securitykey'},4);
	$xMID = hex($xMID);
	if (not int(&ZAUTH::get_user_password($USER,$PASS))) { $err = 300; }	
	}

if (not $err) {
	## cool.. check that we have a body
	if (not defined $ref->{'body'}) { $err = 1; }
	}

if (not $err) {
	$results{'caseid'} = time();
	}





# HTTP BODY:
# 
# <?xml version="1.0"?>
# <transcriptNotification>
# <header id="securitykey">[[securitykey-supplied-by-user]]</header>
# <header id="license">[[livechat license #]]</header>
# <header id="plug-version">[[software version #]]</header>
# <header id="soft-version">[[software version #]]</header>
# <header id="operator">[[operator id#]]</header>
# <!--
# please feel free to include any other header= tags you think might be useful,
# e.g. ip address, duration, etc. ... the more you include the more I can enhance this 
# integration without your assistance.
# -->
# <body>
#   <!--
#   not sure how you store this, but please the messages here .. format as you wish
#   -->
# </body>
# </transcriptNotification>
# 
# 
# SUCCESS RESPONSE:
# 
# Content-type: text/xml
# 
# <?xml version="1.0"?>
# <transcriptResponse>
# <ack>[[unique acknowledgement number]]</ack>
# <result>0</result>
# </transcriptResponse>
# 
# FAILURE RESPONSE:
# 
# Content-type: text/xml
# 
# <?xml version="1.0"?>
# <transcriptResponse>
# <result>[[numeric error code]]</result>
# <errorMsg>[[error message to display to user]]</errorMsg>
# </transcriptResponse>
# 
# FAILURE EXAMPLE:
# 
# <?xml version="1.0"?>
# <transcriptResponse>
# <result>100</result>
# <errorMsg>Invalid Username</errorMsg>
# </transcriptResponse>
# 
# INTENTIONAL FAILURE:
# 
# <?xml version="1.0"?>
# <transcriptResponse>
# <result>1</result>
# <errorMsg>No Body Tag Received</errorMsg>
# </transcriptResponse>
# 
# If you want to make a button in the plugin setup panel to "verify security key" after the user 
# supplies it - then you can send a post with no body tag, and I will respond back with a result of "1"
# which would be a "success" .. meaning that authentication passed, but no body was received
# and then display a success to the user.
# 
print "Content-type: text/xml\n\n";
if ($err) {
	$results{'result'} = $err;
	$results{'errorMsg'} = (defined $ERRORS{$err})?$ERRORS{$err}:"Undefined Error #$err";
	}
else {
	$results{'ack'} = time();
	$results{'result'} = 0;
	}


print qq~<?xml version="1.0"?><transcriptResponse>~;
foreach my $k (sort keys %results) {
	print qq~<$k>~.&ZTOOLKIT::encode($results{$k}).qq~</$k>~;
	}
print qq~</transcriptResponse>~;

print Dumper($ref);