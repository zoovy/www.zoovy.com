#!/usr/bin/perl

use lib "/httpd/modules";
use ACCOUNT;
use ZOOVY;

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_ADMIN');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my @MSGS = ();
my @BC = ();

my $VERB = $ZOOVY::cgiv->{'VERB'};
if (not $LU->is_admin()) {
	$VERB = 'DENY';
	}

my $template_file = '';
if ($VERB eq '') { $VERB = 'ACCOUNT'; }


my ($ACCT) = undef;

##
##
##
if ($VERB eq 'ACCOUNT-SAVE') {
	if (not defined $ACCT) { ($ACCT) = ACCOUNT->new($USERNAME,$LUSERNAME); }

	my $ERRORS = 0;
	foreach my $k (keys %{$ZOOVY::cgiv}) {
		my $ERROR = undef;
		next if ($k eq 'VERB');
		if (not defined $ACCOUNT::VALID_FIELDS{$k}) {
			$ERROR = "Field $k is unknown/invalid";
			}
		elsif ($ZOOVY::cgiv->{$k} =~ /[<>\"]+/) {
			$ERROR = "Field $k attempted to store one or more disallowed characters";
			}

		if (not defined $ERROR) {
			$ACCT->set($k,$ZOOVY::cgiv->{$k});
			}
		else {
			$ERRORS++;
			push @MSGS, "ERROR|$ERROR";
			}
		}

	if (not $ERRORS) {
		push @MSGS, "SUCCESS|Successfully updated account information";
		$ACCT->save();
		}
		
	$VERB = 'ACCOUNT';
	}

if ($VERB eq 'ACCOUNT') {
	if (not defined $ACCT) { ($ACCT) = ACCOUNT->new($USERNAME,$LUSERNAME); }
	foreach my $k (keys %ACCOUNT::VALID_FIELDS) {
		$GTOOLS::TAG{"<!-- $k -->"} = &ZOOVY::incode($ACCT->get($k));
		}
	$template_file = 'account.shtml';
	}

&GTOOLS::output('*LU'=>$LU,file=>$template_file,header=>1,msgs=>\@MSGS,bc=>\@BC);