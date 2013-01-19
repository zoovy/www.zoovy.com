#!/usr/bin/perl

use Data::Dumper;
use LWP::UserAgent;
use Net::OAuth;


#  Consumer key
#knlIKwRrYEKhLQvV1TKPKg
# Consumer secret
#rJyKGl1ouhtfKM5AnmYSEUKn0ZaHNV61vTsn9kJmoE
# Request token URL
#http://twitter.com/oauth/request_token
# Access token URL
#http://twitter.com/oauth/access_token
# Authorize URL
#http://twitter.com/oauth/authorize


# message types:
# request token 
# UserAuth

print Dumper(Net::OAuth->request("UserAuth")->required_message_params);


use Net::OAuth;
$Net::OAuth::PROTOCOL_VERSION = Net::OAuth::PROTOCOL_VERSION_1_0A;
use CGI;
my $q = new CGI;

my $request = Net::OAuth->request("userAuth")->from_hash({},
	request_url => 'http://twitter.com/oauth/authorize',
	request_method => 'GET',
	consumer_secret => 'rJyKGl1ouhtfKM5AnmYSEUKn0ZaHNV61vTsn9kJmoE',
	);

print Dumper($request);


die();

$Net::OAuth::PROTOCOL_VERSION = Net::OAuth::PROTOCOL_VERSION_1_0A;
use HTTP::Request::Common;
my $ua = LWP::UserAgent->new;

my $request = Net::OAuth->request("request token")->new(
	consumer_key => 'knlIKwRrYEKhLQvV1TKPKg',
	consumer_secret => 'rJyKGl1ouhtfKM5AnmYSEUKn0ZaHNV61vTsn9kJmoE',
	request_url => 'http://twitter.com/oauth/request_token',
	request_method => 'POST',
	signature_method => 'HMAC-SHA1',
	timestamp => time(),
	nonce => '1234',
	callback => '', # http://webapi.zoovy.com/webapi/oauth/twitter.cgi',
	extra_params => {
		'apple'=>'banana',
		'kiki'=>'pear',	
		}
	);

	$request->sign;
#	print $request->to_url;

my $res = $ua->request(POST $request->to_url); # Post message to the Service Provider

if ($res->is_success) {
	my $response = Net::OAuth->response("request token")->from_post_body($res->content);
	print "Got Request Token ", $response->token, "\n";
  	print "Got Request Token Secret ", $response->token_secret, "\n";
	}
else {
	print Dumper($res);
	die "Something went wrong";
	}


__DATA__

# Service Provider receives Request Token Request

use Net::OAuth;
$Net::OAuth::PROTOCOL_VERSION = Net::OAuth::PROTOCOL_VERSION_1_0A;
use CGI;
my $q = new CGI;

my $request = Net::OAuth->request("request token")->from_hash(
	$q->Vars,
	request_url => 'http://twitter.com/oauth/request_token',
	request_method => $q->request_method,
               consumer_secret => d94hf93k423kf44
           );

           if (!$request->verify) {
               die "Signature verification failed";
           }
           else {
               # Service Provider sends Request Token Response

               my $response = Net::OAuth->response("request token")->new(
                   token => bcdef
                   token_secret => 123456
                   callback_confirmed => rue
               );

               print $response->to_post_body;
           }

