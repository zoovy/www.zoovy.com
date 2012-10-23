#!/usr/bin/perl

# 34896-315441310

use LWP::UserAgent; 
 	my $ua = LWP::UserAgent->new; 
 	$ua->timeout(10); 
 	$ua->env_proxy;   

 	require HTTP::Headers;
 	my $h = HTTP::Headers->new;
 	$h->header('Content-Type'=>'text/xml');
 	$h->header('Content-Length'=>length($xml));


	my $xml = qq~
<campaign menuid="34896-850856958" username="zoovy" password="password1" action="0">
<prompts>
	<prompt txt="Testing .. 1.2.3"/></prompts>
<phonenumbers>
<phonenumber number="7604199953" callid="Zoovy, Inc." callerid="7606704798" />
</phonenumbers>
			</campaign>~;

	if (1) {
		my $request = HTTP::Request->new('POST','http://api.voiceshot.com/ivrapi.asp',$h); 
		$request->content($xml);
		my $response = $ua->request($request);
		use Data::Dumper;
		print Dumper($response);
		}

