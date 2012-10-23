#!/usr/bin/perl

use strict;
use CGI;
use lib "/httpd/modules";
require ZOOVY;
require DBINFO;

#drop table STAT_LISTINGS;
#create table STAT_LISTINGS (
#  ID integer unsigned not null auto_increment,
#  MID mediumint unsigned default 0 not null,
#  PID varchar(20) default '' not null,
#  UUID bigint unsigned default 0 not null,
#  STYLE enum ('CHANNEL','LISTING','UUID'),
#  CNT integer unsigned default 0 not null,
##  LISTING_ID bigint unsigned default 0 not null,
#  UPDATED_GMT integer unsigned default 0 not null,
#
#  unique (MID,PID,LISTING_ID),
#  index(UPDATED_GMT),
#  primary key (ID)
#);



# /counter.cgi?MID=2749&MERCHANT=usfreight&PRODUCT=1398U&UUID=113641908810453&TS=1136419088&CHANNEL=3193767&STYLE=blank 
my $q = new CGI;

my $MERCHANT = $q->param('MERCHANT');
if ( (!defined($MERCHANT)) || ($MERCHANT eq '') ) { $MERCHANT = 'zoovy'; }

my $PID = $q->param('PRODUCT');

#print 'Expires: ' . &CGI::expires('+24h') . "\n";    # Set the expiration time
#print "Content-type: image/gif\n\n";

# print STDERR "PRODUCT: $$ $PID\n";
my $STYLE = $q->param('STYLE'); # aka SERIES

my $MID = $q->param('MID');
my $UUID = $q->param('UUID');
my $PG = $q->param('PG');
my $TS = $q->param('TS');

# now replace all underscores with dashes
if ($MERCHANT) { 
	$MERCHANT =~ s/_/-/g; 
	$MERCHANT =~ s/\W+//g;
	$MERCHANT =~ s/-/_/g; 
	}
## at this point the MERCHANT name is clean.
if ($PID) { $PID =~ s/[\W]+//g; }

if ((not defined $PID) && ($PG)) { $PG =~ s/[^\w\.]+//g; $PID = $PG; }
if (not defined $PID) { $PID = ''; }

my $DEBUG = 0;


## lookup well known referrers
#if ($ENV{'HTTP_REFERER'} =~ /ebay\.com/) {
#	if ($ENV{'HTTP_REFERER'} =~ /item=([\d]+)/) { $AUCTION = $1; }
#	}

##
## /httpd/counters
## /httpd/zoovy/counters
if ($MID<=0) { $MID = &ZOOVY::resolve_mid($MERCHANT); }
if (($MERCHANT eq '') && ($MID>0)) { 
	$MERCHANT = &ZOOVY::resolve_merchant_from_mid($MID);
	warn "resolved MID=$MID to USER:$MERCHANT\n";
	}

if ($MID<=0) {
	print "Content-type: text/plain\n\n";
	print "UNKNOWN MERCHANT/MID\n";
	}


# /counter.pl?MID=2749&MERCHANT=usfreight&PRODUCT=1398U&UUID=113641908810453&TS=1136419088&CHANNEL=3193767&STYLE=blank 
#create table STAT_LISTINGS (
#  ID integer unsigned default 0 not null auto_increment,
#  MID mediumint unsigned default 0 not null,
#  PID varchar(20) default '' not null,
#  STYLE enum ('CHANNEL','LISTING','UUID'),
#  LISTING_ID bigint unsigned default 0 not null,
#  UPDATED_GMT integer unsigned default 0 not null, 
#  
#  unique (MID,PID,LISTING_ID),
#  index(UPDATED_GMT),
#  primary key (ID)
#);

my ($TYPE,$VALUE) = ('',0);

if ($UUID>0) { ($TYPE,$VALUE) = ('UUID',$UUID); }
if ($TYPE eq '') { ($TYPE,$VALUE) = ('OTHER',0); }


##
##
my $count = 0;
if (0) {
	my $udbh = &DBINFO::db_user_connect($MERCHANT);
	$MID = int($MID);
	if (not defined $PID) { $PID = ''; }
	my $qtPID = $udbh->quote($PID);
	my $qtVALUE = $udbh->quote(int($VALUE));
	my $pstmt = "select CNT from STAT_LISTINGS where MID=$MID and PID=$qtPID and UUID=$qtVALUE";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	($count) = $sth->fetchrow();
	$sth->finish();

	my $ts = time();
	if ($count>0) {
		## exists .. update it
		$pstmt = "update STAT_LISTINGS set CNT=CNT+1,UPDATED_GMT=$ts where MID=$MID and PID=$qtPID and UUID=$qtVALUE";
		$count++;
		}
	else {
		my $qtTYPE = $udbh->quote($TYPE);
		$pstmt = "insert into STAT_LISTINGS (MID,PID,STYLE,UUID,UPDATED_GMT,CNT) values ($MID,$qtPID,$qtTYPE,$qtVALUE,$ts,1)";
		$count=1; 
		}
	# print STDERR $pstmt."\n";
	$udbh->do($pstmt);
	&DBINFO::db_user_close();
	}

## always a redirect
my $PROTO = 'http';
if ($ENV{'HTTPS'} eq 'on') { $PROTO = 'https'; }
print "Location: $PROTO://static.zoovy.com/auto/counter/$STYLE/$count.gif\n\n";

