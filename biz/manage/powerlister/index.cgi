#!/usr/bin/perl

use lib "/httpd/modules";

use Data::Dumper;
use GTOOLS;
use GTOOLS::Table;
use ZOOVY;

my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("/biz/setup",2,'_M&4');
if ($USERNAME eq '') { exit; }

if ($FLAGS !~ /,EBAY,/) {
	## perhaps we ought to deny them.
	}


#mysql> desc EBAY_POWER_QUEUE;
#+------------------------+---------------+------+-----+---------------------+-------+
#| Field                  | Type          | Null | Key | Default             | Extra |
#+------------------------+---------------+------+-----+---------------------+-------+
#| CHANNEL                | int(11)       |      | PRI | 0                   |       |
#| MERCHANT               | varchar(20)   | YES  |     | NULL                |       |
#| PRODUCT                | varchar(45)   |      |     |                     |       |
#| CREATED                | datetime      | YES  |     | NULL                |       |
#| EXPIRES                | datetime      |      | MUL | 0000-00-00 00:00:00 |       |
#| QUANTITY_RESERVED      | int(11)       |      |     | 0                   |       |
#| QUANTITY_SOLD          | int(11)       |      |     | 0                   |       |
#| LISTINGS_ALLOWED       | int(11)       |      |     | 0                   |       |
#| LISTINGS_LAUNCHED      | int(11)       |      |     | 0                   |       |
#| CONCURRENT_LISTINGS    | int(11)       |      |     | 0                   |       |
#| LAST_POLL_GMT          | int(11)       |      |     | 0                   |       |
#| NEXT_POLL_GMT          | int(11)       |      |     | 0                   |       |
#| START_HOUR             | int(11)       | YES  |     | NULL                |       |
#| END_HOUR               | int(11)       | YES  |     | NULL                |       |
#| LAUNCH_DOW             | int(11)       |      |     | 0                   |       |
#| LAUNCH_DELAY           | int(11)       |      |     | 0                   |       |
#| FILL_BIN_ASAP          | enum('Y','N') |      |     | N                   |       |
#| LAST_LAUNCH_GMT        | int(11)       |      |     | 0                   |       |
#| LAST_SALE_GMT          | int(11)       |      |     | 0                   |       |
#| BIN_EVENTS             | int(11)       | YES  |     | NULL                |       |
#| DIRTY                  | int(11)       | YES  | MUL | NULL                |       |
#| TRIGGER_PRICE          | decimal(10,2) |      |     | 0.00                |       |
#| CONCURRENT_LISTING_MAX | int(11)       |      |     | 0                   |       |
#| TITLE                  | varchar(60)   |      |     |                     |       |
#| ERRORS                 | int(11)       |      |     | 0                   |       |
#| LOCKED                 | int(11)       |      | MUL | 0                   |       |
#| LOCK_PID               | int(11)       |      |     | 0                   |       |
#+------------------------+---------------+------+-----+---------------------+-------+
#27 rows in set (0.03 sec)

my $edbh = &DBINFO::db_user_connect($USERNAME);
my $template_file = 'index.shtml';

my @header = ();
push @header, { type=>'moreinfo', width=>13, url=>'/biz/ajax/prototype.pl' };
push @header, { type=>'rowid', title=>'ID', width=>100, };
push @header, { title=>'STATUS', width=>100, };
push @header, { title=>'PID', width=>100, };
push @header, { title=>'Title', width=>350, };
push @header, { title=>'Sold/Qty', width=>80, };
push @header, { title=>'Launches', width=>80, };
push @header, { title=>'SellThru', width=>80, };

my @rows = ();
$pstmt = "select ID,PRODUCT,STATUS,TITLE,QUANTITY_RESERVED,QUANTITY_SOLD,LISTINGS_ALLOWED,LISTINGS_LAUNCHED ";
$pstmt .= " from EBAY_POWER_QUEUE where MID=$MID /* $USERNAME */";

if ($ZOOVY::cgiv->{'VERB'} eq 'SEARCH') {
	$GTOOLS::TAG{'<!-- HEADER -->'} = "Powerlister Manager";
	if ($ZOOVY::cgiv->{'PID'} ne '') {
		$GTOOLS::TAG{'<!-- HEADER -->'} = "Powerlister Manager - Product: $ZOOVY::cgiv->{'PID'}";
		$pstmt .= " and PRODUCT=".$edbh->quote($ZOOVY::cgiv->{'PID'});
		}
	if ($ZOOVY::cgiv->{'ID'} ne '') {
		$GTOOLS::TAG{'<!-- HEADER -->'} = "Powerlister Manager - ID: $ZOOVY::cgiv->{'ID'}";
		$pstmt .= " and ID=".int($ZOOVY::cgiv->{'ID'});
		}
	}

$sth = $edbh->prepare($pstmt);
$sth->execute();
while ( my $hashref = $sth->fetchrow_hashref() ) {
	# print STDERR Dumper($hashref);
	my @row = ();
	push @row, 0;
	push @row, $hashref->{'ID'};
	push @row, $hashref->{'STATUS'};
	push @row, $hashref->{'PRODUCT'};
	push @row, $hashref->{'TITLE'};
	push @row, $hashref->{'QUANTITY_SOLD'}.' of '.$hashref->{'QUANTITY_RESERVED'};
	push @row, $hashref->{'LISTINGS_LAUNCHED'}.' of '.$hashref->{'LISTINGS_ALLOWED'};
	if ($hashref->{'LISTINGS_LAUNCHED'}==0) {
		## avoids a divide by zero issue
		push @row, "n/a";
		}
	else {
		push @row, sprintf("%.1f\%",($hashref->{'QUANTITY_SOLD'} / $hashref->{'LISTINGS_LAUNCHED'}) * 100);
		}
	push @rows, \@row;
	}
$sth->finish();
if (scalar(@rows)==0) {
	$GTOOLS::TAG{'<!-- POWER_TABLE -->'} = "<i>Please create some eBay Powerlisters before attempting to use this interface.</i>";
	}
else {
	$GTOOLS::TAG{'<!-- POWER_TABLE -->'} = &GTOOLS::Table::buildTable(\@header,\@rows,height=>500, rowid=>0, );
	}

&GTOOLS::output(
	'header'=>1, 
	'jquery'=>1,
	'help'=>"#50544", 
	'file'=>$template_file
	);

&DBINFO::db_user_close();


