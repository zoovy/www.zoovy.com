#!/usr/bin/perl


use LWP::Simple;
use HTTP::Request::Common;
use HTTP::Cookies;
use LWP::UserAgent;
use LWP::Simple;
use Data::Dumper;

my $agent = new LWP::UserAgent;
$agent->cookie_jar(HTTP::Cookies->new(autosave => 1));
$agent->agent('YAM');

$url = "http://www.zoovy.com/webapi/sync.cgi";

$vars{'USERNAME'} = 'brian';
$vars{'PASSWORD'} = 'foobot'; 
$vars{'CONTENT'} = qq~<?xml version="1.0"?>
<Request>
<api CLIENTID="1234" NAME="fullordersync" METHOD="blah">asdf</api>
</Request>
~;

my $result = $agent->request(
	POST $url,
	#  Content_Type => 'form-data',
	Content      => [ %vars ]);

print Dumper($result);