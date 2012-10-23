#!/usr/bin/perl

use strict;

use lib "/httpd/modules";
use LWP::UserAgent;
use Digest::MD5;
use JSON::Syck;
use Data::Dumper;

sub make_call {
	my ($input) = @_;

	my ($ua) = LWP::UserAgent->new();
	$ua->env_proxy;
	my $head = HTTP::Headers->new();
	my $req = HTTP::Request->new("POST","http://www.zoovy.com/webapi/jquery/ie8.cgi/image.gif");
	$req->header('Content_Type' => 'application/json');
	$req->content(JSON::Syck::Dump($input));
	my ($r) = $ua->request($req);
	my $out = JSON::Syck::Load($r->content());
	return($out);
	}


my $t = time();
my $PASSWORD = 'asdf';
my %vars = ();
$vars{'_uuid'} = time();
$vars{'_cmd'} = 'appSessionStart';
$vars{'login'} = 'brian';
$vars{'hashtype'} = 'md5';
$vars{'security'} = 'xyz';
$vars{'ts'} = $t;
$vars{'hashpass'} = Digest::MD5::md5_hex(sprintf("%s%s%s",$PASSWORD,$vars{'security'},$vars{'ts'}));

print Dumper(&make_call(\%vars));




