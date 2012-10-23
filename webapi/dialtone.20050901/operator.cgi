#!/usr/bin/perl

use lib "/httpd/modules";
use CGI;
require DIALTONE;
require DBINFO;
use strict;

my $q = CGI->new();
my $dbh = &DBINFO::db_zoovy_connect();

my $MESSAGE = '';
my $CUID = $q->param('CUID');						# tells us which operator from ZUSER_LOGIN to use
my $VERSION = $q->param('VERSION');				# used for version checking. 
my $USERNAME = $q->param('USERNAME');			# just a sanity thing, matched against CUID
$USERNAME =~ s/[^\w]+//gs;
my $METHOD = uc($q->param('METHOD'));			# QUERY, ACK, DONE
my $SESSION = $q->param('SESSION');				# unique call id, created by client - this is only passed on ACK, DONE

##
## validate CUID
##
if ($USERNAME eq '') { $MESSAGE = 'USERNAME variable not set.'; }
elsif ($CUID eq '') { $MESSAGE = 'CUID variable not set.'; }
elsif (not &DIALTONE::validate_cuid($USERNAME,$CUID)) {
	$MESSAGE = 'CUID does not appear to be valid, please register your client.'; 
	}

my %output = ();
$output{'METHOD'} = $METHOD;
if ($MESSAGE ne '') {} 
elsif ($METHOD eq 'ABORT') {
	&DIALTONE::change_call('ABORT',$USERNAME,$CUID,$SESSION);
	}
elsif ($METHOD eq 'DONE') {
	&DIALTONE::change_call('DONE',$USERNAME,$CUID,$SESSION);
	}
elsif ($METHOD eq 'ACK') {
	## acknowledge a call.
	&DIALTONE::change_call('ACK',$USERNAME,$CUID,$SESSION);
	}
elsif ($METHOD eq 'QUERY') {	
	my ($callinfo) = &DIALTONE::get_call($USERNAME,$CUID);
	$output{'COUNT'} = 0;
	if (defined $callinfo) {
		$output{'COUNT'} = 1;
		foreach my $k (keys %{$callinfo}) {
			next if ($k eq 'OP_CUID');
			$output{'CALL_'.uc($k)} = $callinfo->{$k};
			}
		$output{'CALL_URL'} = 'http://www.zoovy.com/'; 
		}
	}

&DBINFO::db_zoovy_close();
if ($MESSAGE ne '') {
	$output{'COUNT'} = -1;
	$output{'ERROR'} = $MESSAGE;
	}

&DIALTONE::output(\%output);

