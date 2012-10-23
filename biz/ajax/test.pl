#!/usr/bin/perl

use lib "/httpd/modules";
use AUTH;



@TESTS = (
	[ 'brian','asdf','1.2.3.4','mypad' ],
	[ 'brian*pinhead','zoovy','1.2.3.4','mypad' ],
	);

foreach my $set (@TESTS) {
	exercise(@{$set});
	}

sub exercise {
	my ($LOGIN,$PASSWORD,$IP,$DEVICE) = @_;


	my @ERRORS = ();
	my ($USERNAME,$LUSER) = AUTH::parse_login($LOGIN);

	my ($zdbh) = &DBINFO::db_zoovy_connect();
	my ($udbh) = &DBINFO::db_user_connect($USERNAME);

	if (not $USERNAME) {
		push @ERRORS, "$USERNAME is not defined";
		}

	my $token = undef;
	if (scalar(@ERRORS)==0) {
		($token) = AUTH::create_session($USERNAME,$LUSER,$IP,$DEVICE);
		print "TOKEN: $token\n";
		}

	use Digest::MD5;
	my ($tryhash) = Digest::MD5::md5_hex($PASSWORD.'*'.$token);
	my ($ERROR) = AUTH::verify_credentials($USERNAME,$LUSER,$token,"MD5",$tryhash);
	if ($ERROR) {
		print "ERROR: $ERROR\n";
		}
	elsif (not defined $ERROR) {
		&AUTH::authorize_session($USERNAME,$LUSER,$token);
		}

	&DBINFO::db_user_close();
	&DBINFO::db_zoovy_close();
	}

