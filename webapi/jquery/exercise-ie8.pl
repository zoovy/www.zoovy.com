#!/usr/bin/perl

use strict;

use lib "/httpd/modules";
use LWP::UserAgent;
use Digest::MD5;
use JSON::Syck;
use Data::Dumper;

sub buildparams {	
	my ($hashref,$minimal) = @_;

	if (not defined $minimal) { $minimal = 0; }	
	my $string = '';

	foreach my $k (sort keys %{$hashref}) {
		foreach my $ch (split(//,$k)) {
			# print "ORD: ".ord($ch)."\n";
			if ($ch eq ' ') { $string .= '+'; }
			elsif (((ord($ch)>=48) && (ord($ch)<58)) || ((ord($ch)>64) &&  (ord($ch)<=127))) { $string .= $ch; }
			else { $string .= '%'.sprintf("%02x",ord($ch));  }
			}
		$string .= '=';
		foreach my $ch (split(//,$hashref->{$k})) {
			if ($ch eq ' ') { $string .= '+'; }
			elsif (((ord($ch)>=48) && (ord($ch)<58)) || ((ord($ch)>64) &&  (ord($ch)<=127))) { $string .= $ch; }
			## don't encode <(60) or >(62) /(47)
			elsif (($minimal) && ((ord($ch)==60) || (ord($ch)==62) || (ord($ch)==47))) { $string .= $ch; }
			else { $string .= '%'.sprintf("%02x",ord($ch));  }
			}
		$string .= '&';
		}
	chop($string);
	return($string);
	}



sub make_call {
	my ($input) = @_;

	$input->{'_uuid'} = time();

	my ($ua) = LWP::UserAgent->new();
	$ua->env_proxy;
	my ($params) = &buildparams($input);
	my $head = HTTP::Headers->new();
	# my $req = $ua->get("http://www.zoovy.com/webapi/jquery/index.cgi/ie8.gif?$params");

	my $r = $ua->get("http://www.zoovy.com/webapi/jquery/index.cgi/ie8.js?$params");
	print Dumper($r);
	my $out = $r->content();

	# my $out = JSON::Syck::Load($r->content());

	return(qq~
ie8_run_this($out);
~);
	}


my $t = time();
my $PASSWORD = 'asdf';
my %vars = ();
$vars{'_cmd'} = 'appSessionStart';
$vars{'login'} = 'brian';
$vars{'hashtype'} = 'md5';
$vars{'security'} = 'xyz';
$vars{'ts'} = $t;
$vars{'hashpass'} = Digest::MD5::md5_hex(sprintf("%s%s%s",$PASSWORD,$vars{'security'},$vars{'ts'}));

print &make_call(\%vars)."\n";




