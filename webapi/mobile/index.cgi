#!/usr/bin/perl

use Data::Dumper;
use JSON::XS;
use strict;
use lib "/httpd/modules";
use ZOOVY;

$ENV{'REQUEST_METHOD'} =~ tr/a-z/A-Z/;

# Read in text
my $buffer = undef;
if ($ENV{'REQUEST_METHOD'} eq "GET") {
	$buffer = $ENV{'QUERY_STRING'};
	}
elsif ($ENV{'REQUEST_METHOD'} eq "POST") {
	read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
	}

## NOW we need to decide 
# print STDERR 'REQUEST: '.Dumper(\%ENV,{$ENV{'CONTENT_TYPE'}=>$buffer});
print STDERR Dumper(\%ENV);
print STDERR "CONTENT: $ENV{'CONTENT_TYPE'}\n";
print STDERR "BUFFER: $buffer\n";

require LISTING::MSGS;
my $lm = LISTING::MSGS->new();

# Split information into name/value pairs
my @ERRORS = ();

my %VARS = ();
if ($ENV{'CONTENT_TYPE'} =~ /^(text|application)\/json$/) {
	##  myWebRequest.ContentType = 
	## text/json
	## application/json

	print STDERR Dumper(\%ENV);

	$VARS{'USER'} = $ENV{'HTTP_USER'};
	$VARS{'DEVICE'} = $ENV{'HTTP_DEVICE'};
	$VARS{'PIN'} = $ENV{'HTTP_PIN'};
	$VARS{'MD5-SIGNATURE'} = $ENV{'HTTP_MD5_SIGNATURE'};
	$VARS{'REQUEST'} = $buffer;
	$VARS{'%'} = JSON::XS::decode_json($buffer);
	}
elsif ($ENV{'CONTENT_TYPE'} =~ /^application\/x-www-form-urlencoded$/) {
	my @pairs = split(/&/, $buffer);
	foreach my $pair (@pairs) {
		my ($name, $value) = split(/=/, $pair);
		$value =~ tr/+/ /;
		$value =~ s/%(..)/pack("C", hex($1))/eg;
		$VARS{$name} = $value;
		}
	print Dumper(\%VARS);

	my ($success) = eval { $VARS{'%'} = JSON::XS::decode_json($VARS{'REQUEST'}) };
	if (not $success) {
		push @ERRORS, "Malformed JSON passed in REQUEST (could not decode)";
		}	
	}
else {
	print "Content-type: text/html\n\n";
	print "<html>";
	while(<DATA>) { print $_; }
	print "</html>";
	exit;
	}


#[Tue Oct 04 10:28:21 2011] [error] [client 192.168.99.15] $VAR1 = {, referer: http://www.zoovy.com/webapi/mobile/
#[Tue Oct 04 10:28:21 2011] [error] [client 192.168.99.15]           'PIN' => '1234',, referer: http://www.zoovy.com/webapi/mobile/
#[Tue Oct 04 10:28:21 2011] [error] [client 192.168.99.15]           'MD5-SIGNATURE' => 'nrWi25A+TeaDAIx+3b0M0w',, referer: http://www.zoovy.com/webapi/mobile/
#[Tue Oct 04 10:28:21 2011] [error] [client 192.168.99.15]           'TOKEN_NOT_PASSED' => 'xyz',, referer: http://www.zoovy.com/webapi/mobile/
#[Tue Oct 04 10:28:21 2011] [error] [client 192.168.99.15]           'REQUEST' => '{"r":"ping"}',, referer: http://www.zoovy.com/webapi/mobile/
#[Tue Oct 04 10:28:21 2011] [error] [client 192.168.99.15]           'DEVICE' => '1:1:1:1:1:1',, referer: http://www.zoovy.com/webapi/mobile/
#[Tue Oct 04 10:28:21 2011] [error] [client 192.168.99.15]           'USER' => 'brian', referer: http://www.zoovy.com/webapi/mobile/
#[Tue Oct 04 10:28:21 2011] [error] [client 192.168.99.15]         };, referer: http://www.zoovy.com/webapi/mobile/

my $MID = -1;
my $USERNAME = '';
my $LUSER = '';

if (not $lm->can_proceed()) {
	}
elsif (not defined $VARS{'REQUEST'}) {	
	$lm->pooshmsg("ERROR|+REQUEST is required");
	}
elsif (not defined $VARS{'USER'}) {
	$lm->pooshmsg("ERROR|+USER is required");
	}
elsif (not defined $VARS{'PIN'}) {
	$lm->pooshmsg("ERROR|+PIN is required");
	}
elsif (not defined $VARS{'DEVICE'}) {
	$lm->pooshmsg("ERROR|+DEVICE is required");
	}
elsif (defined $VARS{'MD5-SIGNATURE'}) {
	## authenticate MD5
	## eventually we need to replace this with an actual device token lookup.
	my $TOKEN = $VARS{'TOKEN_NOT_PASSED'};
	my $LUSER = '';

	($MID) = &ZOOVY::resolve_mid($VARS{'USER'}); 

	my ($zdbh) = &DBINFO::db_zoovy_connect();
	if (1) {
		my $pstmt = "select TOKEN from ZUSER_DEVICES where MID=$MID and HWADDR=".$zdbh->quote($VARS{'DEVICE'});
		print STDERR "$pstmt\n";
		($TOKEN) = $zdbh->selectrow_array($pstmt);
		}
	
	if (1) {
		my $pstmt = "select USERNAME,LUSER from ZUSER_LOGIN where MID=$MID and WMS_DEVICE_PIN=".$zdbh->quote($VARS{'PIN'});
		print STDERR "$pstmt\n";
		($USERNAME,$LUSER) = $zdbh->selectrow_array($pstmt);	
		}
	&DBINFO::db_zoovy_close();

	require Digest::MD5;
	my $CORRECT_SIGNATURE = Digest::MD5::md5_hex($VARS{'USER'}.$VARS{'PIN'}.$VARS{'DEVICE'}.$TOKEN.$VARS{'REQUEST'});

	if ($VARS{'MD5-SIGNATURE'} eq '') {
		$lm->pooshmsg("ERROR|+MD5-SIGNATURE is required");
		}
	elsif ($CORRECT_SIGNATURE eq $VARS{'MD5-SIGNATURE'}) {
		## yay, the message is authentic.
		## push @ERRORS, "Authentication was successful";
		$lm->pooshmsg("INFO|+MD5-SIGNATURE Authentication was successful");
		}
	else {
		$lm->pooshmsg("ERROR|+The passed MD5-SIGNATURE did not match");
		}
	}
else {
	$lm->pooshmsg("ERROR|+MD5-SIGNATURE or SHA1-SIGNATURE is required");
	}


my %R = ();
if (not $lm->can_proceed()) {
	## already got an error response.
	}
elsif ($VARS{'%'}->{'cmd'} eq '') {
	$lm->pooshmsg("ERROR|+parameter: cmd (command) is required in JSON");
	}
elsif ($VARS{'%'}->{'cmd'} eq 'ping') {
	$R{'pong'} = &ZTOOLKIT::pretty_date(time(),1);
	}
elsif ($VARS{'%'}->{'cmd'} eq 'update') {
	my $txns = $VARS{'%'}->{'@txns'};
	if (ref($txns) ne 'ARRAY') {
		$lm->pooshmsg('ERROR|+@txns must be a valid json array for cmd=update');
		$txns = [];
		}

	my @RESULTS = ();
	foreach my $txn (@{$txns}) {
		push @RESULTS, $txn;
		my %r = ();

		my $code = $txn->{'sku'};
		$code =~ s/^[\s]+//gs;
		$code =~ s/[\s]+$//gs;
		$code =~ s/[\n\r]+//gs;
		$code = uc($code);
		my $SKU = undef;

		if ($code eq '') {
			($r{'err'},$r{'msg'}) = (101,"sku must be passed as a non-blank value");
			}
		if (&ZOOVY::productidexists($USERNAME,$code)) {
			$SKU = $code;
			}
		if (not defined $SKU) {
			($SKU) = @{&PRODUCT::BATCH::list_by_attrib($USERNAME,'zoovy:prod_upc',$code)};
			}	
		if (not defined $SKU) {
			($SKU) = @{&PRODUCT::BATCH::list_by_attrib($USERNAME,'zoovy:prod_mfgid',$code)};
			}	
		if (not defined $SKU) {
			($SKU) = INVENTORY::resolve_sku($USERNAME,'META_UPC',$code);
			}
		if (not defined $SKU) {
			($SKU) = INVENTORY::resolve_sku($USERNAME,'META_MFGID',$code);
			}
		if (not defined $SKU) {
			($r{'err'},$r{'msg'}) = (101,"sku culd not be found.");
			}
		else {
			$r{'sku'} = $SKU;
			}

		## I REALLY CANNOT EXPRESS WHAT A HORRIBLE IDEA THIS IS/WAS AND WHY.. 
		##	at a minimum this should be a separate command
		#	## has inv option or assembly, add children
		#	if ($SKU !~ /:/ && $prodref->{'zoovy:pogs'} =~ /inv\=\"[13]\"/) { 
		#		push @MSGS, "INFO|Found PID with inventorable options";
		#		my (@pogs) = &POGS::text_to_struct($USERNAME,$prodref->{'zoovy:pogs'},1);
      #      my $SKUSref = &POGS::build_sku_list($SKU,\@pogs,1+2);
		#		@skus = keys %{$SKUSref}
		#		}
		
		if (defined $r{'err'}) {
			}
		elsif (($txn->{'verb'} eq 'set') || ($txn->{'verb'} eq 'add')) {

			if ($txn->{'location'}) {
				&INVENTORY::set_location($USERNAME,$SKU,$txn->{'location'});
				}
			if ($txn->{'qty'}>0) {
				my ($TYPE) = '?';
				if ($txn->{'verb'} eq 'set') { $TYPE = 'U'; }
				if ($txn->{'verb'} eq 'add') { $TYPE = 'I'; }
				&INVENTORY::add_incremental($USERNAME,$SKU,$TYPE,$txn->{'qty'},'LUSER'=>$LUSER);
				}
			}
		else {
			($r{'err'},$r{'msg'}) = (100,"Unknown verb in txn");
			}

		if (not defined $r{'err'}) {
			## this line should NEVER be reached.
			%r = %{$txn};	# copy txn in for good measure, hopefully it will give us an idea how we got here.
			($r{'err'},$r{'msg'}) = (1,'Something went horribly wrong, unhandled response');
			}

		if ($r{'err'}>0) {
			$R{'bad'}++; 		## errors
			}
		elsif ($r{'warning'}) {	
			$R{'ugly'}++;		## warnings
			}
		else {
			$R{'good'}++;		## success!
			}
		push @RESULTS, \%r;
		}
	$R{'@txns'} = \@RESULTS;
	}
elsif ($VARS{'%'}->{'cmd'} =~ /^lookup\.(location|sku)$/) {
	##
	##	lookup.location
	##	lookup.sku
	##
	my ($TB) = &INVENTORY::resolve_tb($USERNAME,$MID,'INVENTORY');
	my ($udbh) = &DBINFO::db_user_connect($USERNAME);
	my $pstmt = '';

	if ($VARS{'%'}->{'cmd'} eq 'lookup.location') {
		if (not defined $VARS{'location'}) {
			$lm->pooshmsg("ERROR|+location is a required parameter on cmd=lookup.location");
			}
		else {
			$pstmt = "select SKU,LOCATION,IN_STOCK_QTY from INVENTORY where MID=$MID and LOCATION=".$udbh->quote($VARS{'location'});
			}
		}
	elsif ($VARS{'%'}->{'cmd'} eq 'lookup.sku') {
		if (not defined $VARS{'sku'}) {
			$lm->pooshmsg("ERROR|+sku is a required parameter on cmd=lookup.sku");
			}
		else {
			$pstmt = "select SKU,LOCATION,IN_STOCK_QTY from INVENTORY where MID=$MID and SKU=".$udbh->quote($VARS{'sku'});
			}
		}

	my @RESULTS = ();
	if (scalar(@ERRORS)==0) {
		my $sth = $udbh->prepare($pstmt);
		$sth->execute();
		while ( my ($sku,$location,$qty) = $sth->fetchrow() ) {
			push @RESULTS, { 'sku'=>$sku, 'qty'=>$qty, 'location'=>$location };
			}
		$sth->finish();
		}

	&DBINFO::db_user_close();
	
	$R{'matches'} = scalar(@RESULTS);
	$R{'@result'} = \@RESULTS;
	}
else {	
	$lm->pooshmsg("ERROR|+InValid request cmd, cannot be processed");
	}


if (my $lmref = $lm->had('ERROR')) {
	## this could probably be more elaborate at some point.
	$R{'error'} = $lmref->{'+'};
	}



if ($VARS{'__RESPONSE_PLAINTEXT'}) {
	$R{'test-response-not-actually-valid'}++;
	print "Content-type: text/plain\n\n";
	print "******* PLAINTEXT DEBUG MODE *********\n";
	if ($lm->can_proceed()) {
		print "Congratulations, this command was successful and had no errors\n";
		print Dumper($lm);
		}
	else {
		print "Doh! this command had one or more errors, listed below:\n";
		print 'ERRORS: '.Dumper($lm);
		}
	print "\n\n";
	print 'JSON RESPONSE: '.JSON::XS->new->ascii->pretty->allow_nonref->encode(\%R);
	}
else {
	print "Content-type: application/json\n\n";
	print JSON::XS->new->ascii->pretty->allow_nonref->encode(\%R);
	}



__DATA__
<!--

Zoovy Mobile REST API v1.0
Pass commands on the URI in Entity Encoding and responses are echo'd in the body.

HTTP/200 = success
HTTP/500 = function not available/supported
HTTP/404 = internal error to the application (fault)
HTTP/401 = access denied.

-->

<head>
<link rel="STYLESHEET" type="text/css" href="/biz/standard-20110317.css" />
<script src="md5.js" type="text/javascript"></script>
</head>
<body>
<h1>Zoovy WMS Device API</h1>

<h2>Overview</h2>
<p>
There are two possible methods for making a request, a standard HTTP form post method, 
and a more structured application/json method (preferred). 
Regardless of the incoming request type the output will be an HTTP/200 response of a json object, any non 200 response
is considered an error. The form method below is primarily intended for ease of troubleshooting debugging.
</p>

<form name="DEMO" method="POST" id="DEMO" action="/webapi/mobile/index.cgi">
<h2>Testing/Debugging:</h2>
<p>
Use this form to debug actual requests. 
<center>
<table class="zoovytable" width=400>
<tr>
	<td colspan=2 class="zoovytableheader">Create Request</td>
</tr>
<tr>
	<td valign=top>USER:</td><td valign=top><input id="USER" type="textbox" name="USER"><br><div class='hint'>The zoovy assigned username for the account</div></td>
</tr>
<tr>
	<td valign=top>PIN:</td><td valign=top><input id="PIN" type="textbox" name="PIN"><br><div class='hint'>A 2-10 digit alphanumeric pin # assigned to the user making the request.</div></td>
</tr>
<tr>
	<td valign=top>DEVICE:</td><td valign=top><input id="DEVICE" type="textbox" name="DEVICE"><br><div class='hint'>The hardware address of the device (registered on zoovy.com)</div></td>
</tr>
<tr>
	<td valign=top>REQUEST:</td><td valign=top><textarea id="REQUEST" name="REQUEST"></textarea><br><div class='hint'>The json request (see structure below)</div></td>
</tr>
<tr>
	<td valign=top>TOKEN:</td>
	<td valign=top>
		<input type="textbox" id="TOKEN_NOT_PASSED" name="TOKEN_NOT_PASSED"><br>
		<input type="button" class="minibutton" value=" Calc Hash " onClick="
	// alert(document.DEMO['MD5-SIGNATURE'].value);
	document.DEMO['MD5-SIGNATURE'].value =  hex_md5( 
		document.DEMO['USER'].value + document.DEMO['PIN'].value + 
		document.DEMO['DEVICE'].value + document.DEMO['TOKEN_NOT_PASSED'].value + document.DEMO['REQUEST'].value
		);
">
	<div><div class='hint'>Token is supplied by registering device, it is NOT used to generate the md5 signature, it is not passed in the request</div></div>
	<div><div class='hint'>Formula is: hex_md5(USER+PIN+DEVICE+TOKEN+REQUEST)</div></div>
	</td>
</tr>

<tr>
	<td valign=top>MD5-SIGNATURE:</td><td valign=top>
	<input size="32" type="textbox" id="MD5-SIGNATURE" name="MD5-SIGNATURE">
	</td>
</tr>
<tr>
	<td valign=top colspan=2>
	<input type="checkbox" checked name="__RESPONSE_PLAINTEXT"> Send response in plaintext (debugging only)<br>
	<input type="submit" value=" Submit Test ">
<div class="hint">
Required parameters USER,PIN,DEVICE,MD5-SIGNATURE can be passed as URI Encoded form variables when 
content-type: application/x-www-form-urlencoded is in use, or passed as HTTP Headers when type
application/json is passed.
</div>
	</td>
</tr>
</table>
</center>
</form>
</p>

<h2>Examples:</h2>
<p>
<pre>
EXAMPLE JSON:<br>
Request: {"cmd":"ping"}
Response: {"result":"success"}
</pre>
</p>

<h2>About Device Registration:</h2>
<p>
Users will need to register each device they plan to use. To do this they will need to authorize it.
To do that they will need to go into the application select "Register" it will display
the mac address of the device, the user will go to 
Setup | Mobile Devices 
Put in the mac address and receive a Token (there will be a scannable barcode on the screen)
You will save the token in the device registry.
The signature will be a base64 encoded md5 signature of the parameters, with the token
concatenated and mac address of the device (in he:xa:de:ci:mal notation)
</p>

<h2>Types of API Calls</h2>
<p>
In version 1.0 of this protocol there are only two types of calls "updates" and "lookups".
<li> An UPDATE is any type of add/remove/delete/set/etc. that actually performs a change and is logged each request may pass one or more "txn" lines, which will be applied to the database, 
and each txn will have an individual response.
<li> A LOOKUP request makes no changes to the database and is used to determine status of items, or get waiting data. There are many types of lookups that can be performed and each type has
a similar, but unique response format.
</p>

<hr>
<h2>Example UPDATE</h2>
<pre>
Request:
{
	"cmd":"update",
	"uuid":"very_large_guid_32_characters",	// optional but highly recommended
	"@txns":[
		{ "verb":"set", "zone":"myzone", "id":"upc1", "location":"xyz", "qty":"1" },
		{ "verb":"add", "zone":"myzone", "id":"sku2", "location":"xyz", "qty":"2" },
		]
}

Response:
{
	"good":0,	// # of success
	"bad":0,		// # of errors
	"ugly":0,	// # of success w/warnings
	"uuid":"very_large_guid_32_characters", 	// same value that was passed (if any)
	"@txns":[
		{ "err":0, "msg":"" },
		];
}

in the example above: id is the row # or request id (unique identifier for this request), if ommitted the row # (starting at zero) will be used
</pre>
<hr>
<h2>Example LOOKUP(s)</h2>
<pre>

Request: (lookup details for a sku in a zone)
{
	"cmd":"lookup.sku",
	"sku":"xyz", "zone":"myzone", 
}
Response:
{
	"matches":1,	// number of rows matching.
	"@result":[
		{ "sku":"oursku1", "location":"", "qty":1 },
		{ "sku":"oursku2", "location":"", "qty":2 },
		]
}


Request: (lookup details for a location)
{
	"cmd":"lookup.location",
	"location":""
}
Response:
{
	"matches":1,	// number of rows matching.
	"@result":[
		{ "sku":"oursku1", "qty":1 },
		{ "sku":"oursku2", "qty":2 },
		]
}

</pre>
