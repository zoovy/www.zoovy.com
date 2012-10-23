#!/usr/bin/perl

use lib "/httpd/modules";
use SUPPORT;

my $USERNAME = 'brian';
my ($TICKET) = SUPPORT::createticket($USERNAME,
	ORIGIN=>'PROJECT',
	DISPOSITION=>'ACTIVE',
	BODY=>qq~
This is a new ticket. Created by brian.
~,
	PUBLIC=>1,
	SUBJECT=>"New Ticket Subject",
	'TECH'=>'lizm',
	);

print "ID: $ID\n";
      &SUPPORT::add_task_to_ticket($USERNAME,$TICKET,'EXP_VERUTA','lizm');
      &SUPPORT::add_task_to_ticket($USERNAME,$TICKET,'CSTM_VERUTA','lizm');
      &SUPPORT::add_task_to_ticket($USERNAME,$TICKET,'BLD_VERUTA','lizm');

