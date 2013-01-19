#!/usr/bin/perl

use strict;

use Data::Dumper;
use lib "/httpd/modules";
use GTOOLS;
use ZOOVY;
use LUSER;
use EBAY2;
use Text::CSV_XS;




my ($LU) = LUSER->authenticate(flags=>'_M&16');
if (not defined $LU) { warn "Auth"; exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { warn "No auth"; exit; }

my $VERB = uc($ZOOVY::cgiv->{'VERB'});
$GTOOLS::TAG{'<!-- BATCHID -->'} = $ZOOVY::cgiv->{'batchid'};


my $PERIOD_GMT = 0;
if ($ZOOVY::cgiv->{'period'} ne '') {
	require ZTOOLKIT::DATE;
	($PERIOD_GMT) = &ZTOOLKIT::DATE::relative_gmt($ZOOVY::cgiv->{'period'});
	}
$GTOOLS::TAG{'<!-- OPT_TODAY -->'} = ($ZOOVY::cgiv->{'period'} eq 'today')?'selected':'';
$GTOOLS::TAG{'<!-- OPT_YESTERDAY -->'} = ($ZOOVY::cgiv->{'period'} eq 'yesterday')?'selected':'';
$GTOOLS::TAG{'<!-- OPT_WEEK -->'} = ($ZOOVY::cgiv->{'period'} eq 'this.week')?'selected':'';
$GTOOLS::TAG{'<!-- OPT_MONTH -->'} = ($ZOOVY::cgiv->{'period'} eq 'this.month')?'selected':'';

my $eb2 = undef;
my @ERRORS = ();
if ($VERB eq 'EXPORT') {
	($eb2) = EBAY2->new($USERNAME,PRT=>$PRT);
	if (not defined $eb2) {
		push @ERRORS, "No eBay Token for this partition";
		}
	if (scalar(@ERRORS)>0) {
		$VERB = 'ERROR';
		}
	}


if ($VERB eq 'EXPORT') {
	my $csv = Text::CSV_XS->new();          # create a new object

	my @HEADERS = ();

	my ($TYPE) = $ZOOVY::cgiv->{'type'};	
	my @rows = ();

	if ($TYPE =~ /^listing\-/) {
		my ($edbh) = $eb2->ebay_db_connect();

		push @HEADERS, "EBAY_ID";
		push @HEADERS, "PRODUCT";
		push @HEADERS, "TYPE";
		push @HEADERS, "TITLE";
		push @HEADERS, "ENDS";
		push @HEADERS, "PROFILE";
		push @HEADERS, "IS_POWERLISTER";
		push @HEADERS, "IS_GTC";
		push @HEADERS, "CLASS";
		push @HEADERS, 'ITEMS_REMAIN';

		my $pstmt = "select EBAY_ID,PRODUCT,TITLE,ENDS_GMT,IS_POWERLISTER,IS_GTC,PROFILE,CLASS,ITEMS_REMAIN from EBAY_LISTINGS where MID=$MID /* $USERNAME */ and PRT=$PRT ";

		if ($TYPE eq 'listing-active') {
			$pstmt .= " and IS_ENDED=0 and EBAY_ID>0";
			}
		elsif ($TYPE eq 'listing-active-fixed') {
			$pstmt .= " and CLASS='FIXED' and IS_ENDED=0 and EBAY_ID>0";
			}
		elsif ($TYPE eq 'listing-active-store') {
			$pstmt .= " and CLASS='STORE' and IS_ENDED=0 and EBAY_ID>0";
			}
		elsif ($TYPE eq 'listing-active-auction') {
			$pstmt .= " and CLASS='AUCTION' and IS_ENDED=0 and EBAY_ID>0";
			}
		elsif ($TYPE eq 'listing-all') {
			$pstmt .= " and EBAY_ID>0";
			}
		elsif ($TYPE eq 'listing-allwattempts') {
			# $pstmt .= "";
			}
		else {
			push @ERRORS, "Unknown TYPE[$TYPE]";
			}


		print STDERR $pstmt."\n";
		my $sth = $edbh->prepare($pstmt);
		$sth->execute();
		while ( my $ref = $sth->fetchrow_hashref() ) {
			my @row = ();
			if ($ref->{'IS_GTC'}) {
				$ref->{'ENDS'} = 'GTC';
				}
			else {
				$ref->{'ENDS'} = &ZTOOLKIT::pretty_date($ref->{'ENDS_GMT'},2);
				}
			
			foreach my $h (@HEADERS) {
				push @row, $ref->{$h};
				}
			push @rows, \@row;
			}
		$eb2->ebay_db_close();
		}
	elsif ($TYPE eq 'power-missing') {

		## get a list of products
		my $zdbh = &DBINFO::db_user_connect($USERNAME);
		my %PIDS = ();
		my @PRODUCTS = &ZOOVY::fetchproduct_list_by_merchant($USERNAME);
		foreach my $p (@PRODUCTS) {
			$PIDS{$p} = 1;
			}

		## remove products which already have powerlisters
		my ($edbh) = $eb2->ebay_db_connect();
		my $pstmt = "select PRODUCT from EBAY_POWER_QUEUE where MID=$MID and STATUS in ('NEW','ACTIVE','PAUSED')";
		if ($PERIOD_GMT>0) { $pstmt .= " and CREATED_GMT>".int($PERIOD_GMT); }

		my $sth = $edbh->prepare($pstmt);
		$sth->execute();
		while ( my ($p) = $sth->fetchrow() ) {
			$PIDS{$p} = 0;
			}
		$sth->finish();
		$eb2->ebay_db_close();

		## a product must have inventory in stock 
		foreach my $p (@{&INVENTORY::all_pids_instock($USERNAME)}) { 
 			$PIDS{$p} |= 2; 
			}

		&DBINFO::db_user_close();

		push @HEADERS, "PRODUCT";
		foreach my $p (sort keys %{PIDS}) {
			next if ($PIDS{$p}<3);
			push @rows, [ $p ]; 
			}
	
		}
	elsif ($TYPE =~ /^power\-/) {
		my ($edbh) = $eb2->ebay_db_connect();
		#  enum('NEW','ACTIVE','PAUSED','ERROR','DONE')
		my $pstmt = "select ID,STATUS,PRODUCT,TITLE,
		QUANTITY_RESERVED,QUANTITY_SOLD,LISTINGS_ALLOWED,LISTINGS_LAUNCHED,CONCURRENT_LISTINGS,START_HOUR,END_HOUR,LAUNCH_DOW,LAUNCH_DELAY,FILL_BIN_ASAP,
		date_format(CREATED_TS,'%Y-%m-%d %H:%i') as CREATED, 
		date_format(EXPIRES_TS,'%Y-%m-%d %H:%i') as EXPIRES, 
		date_format(LAST_LAUNCH_TS,'%Y-%m-%d %H:%i') as LAST_LAUNCH, 
		date_format(LAST_SALE_TS,'%Y-%m-%d %H:%i') as LAST_SALE
		from EBAY_POWER_QUEUE where MID=$MID ";
		if ($TYPE eq 'power-active') {
			$pstmt .= " and STATUS in ('NEW','ACTIVE')";
			}
		elsif ($TYPE eq 'power-paused') {	
			$pstmt .= " and STATUS in ('PAUSED')";
			}
		elsif ($TYPE eq 'power-error') {	
			$pstmt .= " and STATUS in ('ERROR')";
			}
		elsif ($TYPE eq 'power-done') {	
			$pstmt .= " and STATUS in ('DONE')";
			}
		if ($PERIOD_GMT>0) { $pstmt .= " and CREATED>unix_timestamp(".int($PERIOD_GMT).")"; }
		# print STDERR $pstmt."\n";

		push @HEADERS, "ID";
		push @HEADERS, "STATUS";
		push @HEADERS, "PRODUCT";
		push @HEADERS, "TITLE";
		push @HEADERS, "CREATED";
		push @HEADERS, "EXPIRES";
		push @HEADERS, "LAST_LAUNCH";
		push @HEADERS, "LAST_SALE";
		push @HEADERS, "QUANTITY_RESERVED";
		push @HEADERS, "QUANTITY_SOLD";
		push @HEADERS, "LISTINGS_ALLOWED";
		push @HEADERS, "LISTINGS_LAUNCHED";
		push @HEADERS, "CONCURRENT_LISTINGS";
		push @HEADERS, "START_HOUR";
		push @HEADERS, "END_HOUR";
		push @HEADERS, "LAUNCH_DOW";
		push @HEADERS, "LAUNCH_DELAY";
		push @HEADERS, "FILL_BIN_ASAP";

		my $sth = $edbh->prepare($pstmt);
		$sth->execute();
		while ( my $ref = $sth->fetchrow_hashref() ) {
			my @row = ();
			foreach my $h (@HEADERS) {
				push @row, $ref->{$h};
				}
			push @rows, \@row;
			}
		$eb2->ebay_db_close();
		}
	elsif ($TYPE =~ /^event\-/) {
#mysql> desc LISTING_EVENTS;
#+------------------+-------------------------------------------------------------------------------------+------+-----+---------+----------------+
#| Field            | Type                                                                                | Null | Key | Default | Extra          |
#+------------------+-------------------------------------------------------------------------------------+------+-----+---------+----------------+
#| ID               | bigint(20) unsigned                                                                 | NO   | PRI | NULL    | auto_increment |
#| MID              | int(10) unsigned                                                                    | NO   | MUL | 0       |                |
#| PRT              | tinyint(4)                                                                          | NO   |     | 0       |                |
#| USERNAME         | varchar(20)                                                                         | NO   |     | NULL    |                |
#| LUSER            | varchar(10)                                                                         | NO   |     | NULL    |                |
#| PRODUCT          | varchar(20)                                                                         | NO   |     | NULL    |                |
#| SKU              | varchar(35)                                                                         | NO   |     | NULL    |                |
#| QTY              | varchar(10)                                                                         | NO   |     | NULL    |                |
#| CREATED_GMT      | int(10) unsigned                                                                    | NO   |     | 0       |                |
#| LAUNCH_GMT       | int(10) unsigned                                                                    | NO   |     | 0       |                |
#| PROCESSED_GMT    | int(10) unsigned                                                                    | NO   |     | 0       |                |
#| TARGET           | varchar(10)                                                                         | NO   |     | NULL    |                |
#| TARGET_LISTINGID | bigint(20) unsigned                                                                 | YES  |     | NULL    |                |
#| TARGET_UUID      | bigint(20)                                                                          | NO   |     | 0       |                |
#| LOCK_GMT         | int(10) unsigned                                                                    | NO   |     | 0       |                |
#| LOCK_ID          | int(10) unsigned                                                                    | NO   |     | 0       |                |
#| VERB             | enum('INSERT','REMOVE-LISTING','REMOVE-SKU','UPDATE-INVENTORY','UPDATE-LISTING','') | YES  |     | NULL    |                |
#| REQUEST_BATCHID  | varchar(8)                                                                          | NO   |     | NULL    |                |
#| REQUEST_APP      | varchar(4)                                                                          | NO   | MUL | NULL    |                |
#| REQUEST_APP_UUID | bigint(20)                                                                          | YES  |     | NULL    |                |
#| REQUEST_DATA     | mediumtext                                                                          | YES  |     | NULL    |                |
#| RESULT           | enum('PENDING','RUNNING','FAIL-SOFT','FAIL-FATAL','SUCCESS','SUCCESS-WARNING','')   | NO   |     | NULL    |                |
#| RESULT_ERR_SRC   | enum('ZPREFLIGHT','ZLAUNCH','TRANSPORT','MKT','MKT-LISTING','MKT-ACCOUNT')          | YES  |     | NULL    |                |
#| RESULT_ERR_CODE  | int(11)                                                                             | NO   |     | 0       |                |
#| RESULT_ERR_MSG   | tinytext                                                                            | YES  |     | NULL    |                |
#+------------------+-------------------------------------------------------------------------------------+------+-----+---------+----------------+
#25 rows in set (0.01 sec)
	
		push @HEADERS, "ID";
		push @HEADERS, "PRODUCT";
		push @HEADERS, "VERB";
		push @HEADERS, "SKU";
		push @HEADERS, "QTY";
		push @HEADERS, "CREATED";
		push @HEADERS, "TARGET";
		push @HEADERS, "TARGET_LISTINGID";
		push @HEADERS, "REQUEST_APP";
		push @HEADERS, "REQUEST_BATCHID";
		push @HEADERS, "RESULT";
		push @HEADERS, "RESULT_ERR_SRC";
		push @HEADERS, "RESULT_ERR_CODE";
		push @HEADERS, "RESULT_ERR_MSG";
		push @HEADERS, "LUSER";

		my ($udbh) = &DBINFO::db_user_connect($USERNAME);
		my $pstmt = "select ID,VERB,REQUEST_APP,REQUEST_BATCHID,PRODUCT,SKU,QTY,from_unixtime(CREATED_GMT) CREATED,TARGET,TARGET_LISTINGID,RESULT,RESULT_ERR_SRC,RESULT_ERR_CODE,RESULT_ERR_MSG,LUSER from LISTING_EVENTS ";
		$pstmt .= " where MID=$MID /* $USERNAME */ ";
		if ($TYPE eq 'event-error') {
			$pstmt .= " and RESULT in ('FAIL-SOFT','FAIL-FATAL') ";
			}
		elsif ($TYPE eq 'event-warnings') {
			$pstmt .= " and RESULT in ('SUCCESS-WARNING') ";
			}
		elsif ($TYPE eq 'event-success') {
			$pstmt .= " and RESULT in ('SUCCESS','SUCCESS-WARNING') ";
			}
		elsif ($TYPE eq 'event-pending') {
			$pstmt .= " and RESULT in ('PENDING','RUNNING') ";
			}
		elsif ($TYPE eq 'event-target-powr.auction') {
			$pstmt .= " and TARGET='POWR.AUCTION' ";
			}
		elsif ($TYPE eq 'event-target-ebay.auction') {
			$pstmt .= " and TARGET='EBAY.AUCTION' ";
			}
		elsif ($TYPE eq 'event-target-ebay.fixed') {
			$pstmt .= " and TARGET='EBAY.FIXED' ";
			}

		if ($ZOOVY::cgiv->{'batchid'} ne '') {
			$pstmt .= " and REQUEST_BATCHID=".int($ZOOVY::cgiv->{'batchid'});
			}
		if ($PERIOD_GMT>0) { $pstmt .= " and CREATED_GMT>".int($PERIOD_GMT); }

		$pstmt .= " order by ID";

		my $sth = $udbh->prepare($pstmt);
		$sth->execute();
		while ( my $ref = $sth->fetchrow_hashref() ) {
			my @row = ();
			foreach my $h (@HEADERS) {
				push @row, $ref->{$h};
				}
			push @rows, \@row;
			}
		$eb2->ebay_db_close();
		
		&DBINFO::db_user_close();
		}

	if (scalar(@rows)==0) {
		push @ERRORS, "No data/rows found for type:$TYPE";
		}

	if (scalar(@ERRORS)>0) {
		$GTOOLS::TAG{'<!-- MSG -->'} = "<div class='error'>".join("\n",@ERRORS)."</div>";
		$VERB = 'ERROR';
		}
	else {
		print "Content-Type: text/csv\n\n";

		my $status  = $csv->combine(@HEADERS);  # combine columns into a string
		my $line    = $csv->string();           # get the combined string
		print "$line\n";

		foreach my $row (@rows) {
			$status  = $csv->combine(@{$row});  # combine columns into a string
			$line    = $csv->string();           # get the combined string
			print "$line\n";
			}
		}


	}

if ($VERB ne 'EXPORT') {
	$GTOOLS::TAG{'<!-- FILENAME -->'} = "ebay-".time();
	&GTOOLS::output(file=>'index.shtml',header=>1);
	}

