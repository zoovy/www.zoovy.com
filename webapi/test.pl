#!/usr/bin/perl

open F, "<content"; while(<F>) { $buf .= $_; } close F;
eval($buf);

my $in = $VAR1->{'_request'}->{'_content'};

use Mail::Box::Message;
#print "$in\n";
my ($mbm) = Mail::Message->read($in, strip_status_fields=>1);
my ($TO) = $mbm->get('X-Original-To'); $TO =~ s/[\n\r]+//gs;
my $BODY = $mbm->decoded();

print $BODY;


exit;

use lib "/httpd/modules";
use WEBAPI;

$XAPI = 'FULLORDERSYNC/SINCE/0';
$DATA = '';

($pickup,$XML) = &WEBAPI::fullOrderSync('brian',$XAPI,time(),$DATA);

print "PICKUP: $pickup\n";
print "XML:\n$XML\n";