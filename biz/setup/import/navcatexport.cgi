#!/usr/bin/perl

use strict;
use lib "/httpd/modules";
use GTOOLS;
use CGI qw/:push -nph/;
use NAVCAT;
use PAGE;
use PAGE::BATCH;

use Text::CSV_XS;

my $csv = Text::CSV_XS->new({binary=>1});          # create a new object

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

#my $USERNAME = 'carpartsdiscount';
my $q = new CGI;
my $ACTION = $q->param('ACTION');

print "Content-type: text/csv\n\n";
print "#TYPE=CATEGORY\n";
print "# -- note: you need to keep the header line in here!\n";
#print "%CATEGORIES\n\n";
print "%SAFE,%PRETTY,%SORT,%PRODUCTS,%METASTR,%LAYOUT";

my ($headers) = $ZOOVY::cgiv->{'headers'};
my @headers = ();
foreach my $h (split(/,/,$headers)) {
	$h =~ s/[\s]+//g; # strip whitespace
	$h = lc($h);
	print ",$h";
	push @headers, $h;
	}
print "\n";

my ($ref) = PAGE::BATCH::fetch_pages($USERNAME,PRT=>$PRT);
#open F, ">/tmp/foo";
#use Data::Dumper; print F Dumper($ref);
#close F;

my $nc = NAVCAT->new($USERNAME,PRT=>$PRT);
my $buf = '';
foreach my $safe (sort $nc->paths()) {
	my ($pretty, $children, $productstr,$sortby,$metaref) = $nc->get($safe);
	my $meta = &NAVCAT::encode_meta($metaref);

	my @cols = ();
	push @cols, $safe;
	push @cols, $pretty;
	push @cols, $sortby;
	push @cols, $productstr;
	push @cols, $meta;	

	my $pg = $safe;
	if ($pg eq '.') { $pg = 'homepage'; }
	if ($pg eq '*cart') { $pg = 'cart'; }

	if (substr($safe,0,1) eq '$') {
		## not a category/page .. no page properties.
		}
	elsif (not defined $ref->{$pg}) {
		## hhmm.. doesn't exist.
		}
	else {
		push @cols, $ref->{$pg}->{'fl'};
		foreach my $h (@headers) {
			push @cols, $ref->{$pg}->{$h};
			}
		}
	
	my $status  = $csv->combine(@cols);  # combine columns into a string
	my $line    = $csv->string();           # get the combined string
	print "$line\n";
	}
undef $nc;

sub csvescape {
	my ($text) = @_;
	$text =~ s/"/\\"/g;
	return('"'.$text.'"');
	}	

