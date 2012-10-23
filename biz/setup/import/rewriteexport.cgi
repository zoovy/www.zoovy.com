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
print "#TYPE=REWRITES\n";
print "# -- username: $USERNAME partition: $PRT\n";
print "# -- note1: you need to keep the header line in here!\n";
print "# -- note2: you cannot rewrite a url that exists. matching rewrites override a 404 page not found only.\n";
print "%DOMAIN,%PATH,%TARGETURL\n";

my $udbh = &DBINFO::db_user_connect($USERNAME);
my $pstmt = "select DUM.DOMAIN,DUM.PATH,DUM.TARGETURL from DOMAINS_URL_MAP DUM,DOMAINS D where D.MID=$MID and D.PRT=$PRT and D.DOMAIN=DUM.DOMAIN and DUM.MID=$MID /* $USERNAME */";
print STDERR $pstmt."\n";
my $sth = $udbh->prepare($pstmt);
$sth->execute();
while ( my (@cols) = $sth->fetchrow() ) {
	my $status  = $csv->combine(@cols);  # combine columns into a string
	my $line    = $csv->string();           # get the combined string
	print "$line\n";	
	}
$sth->finish();
&DBINFO::db_user_close();

