#!/usr/bin/perl

use lib "/httpd/modules";
use WEBDOC;
use Storable qw (store);

use XML::Parser;
use XML::Parser::EasyTree;
use XML::RSS;
$XML::Parser::Easytree::Noempty=1;
use Data::Dumper;
use strict;
use DBI;
use Storable;
use POSIX;


use WEBDOC::TOPICS;

if (1) {
	open F, "<menu.xml"; $/ = undef;
	my $xml = <F>;
	close F; $/ = "\n";
	&WEBDOC::TOPICS::fromXML($xml);
	}

#if (1) {
#	my $xml = &WEBDOC::TOPICS::toXML(0);
#	print $xml;
#	open F, ">menu.xml";
#	print F $xml;
#	close F;
#	}

exit;


##
##
##

