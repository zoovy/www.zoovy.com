#!/usr/bin/perl

require JSON::XS;
require CGI::Lite;

use lib "/httpd/modules";
require BATCHJOB;


##
## status.pl is a trivial wrapper
##		which returns a json object to the main batch display
##		about the status of a user job..
##

my ($q) = new CGI::Lite;
$form = $q->parse_form_data();

my %result = ();
my ($b) = BATCHJOB->new($form->{'user'},$form->{'job'});
if (not defined $b) {
	$result{'err'} = "Could not load: user=$form->{'user'} job=$form->{'id'}";
	}
elsif ($b->{'err'}) {
	$result{'err'} = $b->{'err'};
	}
else {
	%result = $b->read();
	}

print "Content-type: text/json\n\n";
my $out = JSON::XS::encode_json(\%result);
print $out;
print STDERR $out;

