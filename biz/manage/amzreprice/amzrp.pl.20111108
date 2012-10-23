#!/usr/bin/perl

use strict;

use lib "/httpd/modules";
use WATCHER;
use Data::Dumper;

#mysql> desc AMAZON_REPRICE_PRODUCTS;
#+--------------------+------------------+------+-----+---------+----------------+
#| Field              | Type             | Null | Key | Default | Extra          |
#+--------------------+------------------+------+-----+---------+----------------+
#| ID                 | int(10) unsigned | NO   | PRI | NULL    | auto_increment |
#| USERNAME           | varchar(20)      | NO   |     | NULL    |                |
#| MID                | int(10) unsigned | NO   | MUL | 0       |                |
#| CREATED_GMT        | int(10) unsigned | NO   |     | 0       |                |
#| MODIFIED_GMT       | int(10) unsigned | NO   |     | 0       |                |
#| SKU                | varchar(45)      | NO   |     | NULL    |                |
#| ASIN               | varchar(20)      | NO   |     | NULL    |                |
#| IS_SUSPENDED       | tinyint(4)       | NO   |     | 0       |                |
#| STRATEGY_ID        | varchar(10)      | NO   |     | NULL    |                |
#| VAR_MIN_PRICE      | decimal(10,2)    | NO   |     | 0.00    |                |
#| VAR_MIN_SHIP       | decimal(10,2)    | NO   |     | 0.00    |                |
#| VAR_MAX_PRICE      | decimal(10,2)    | YES  |     | 0.00    |                |
#| LAST_PRICE         | decimal(10,2)    | NO   |     | 0.00    |                |
#| LAST_SHIP          | decimal(10,2)    | NO   |     | 0.00    |                |
#| LAST_UPDATE_GMT    | int(10) unsigned | NO   |     | 0       |                |
#| LAST_STATUS        | tinytext         | NO   |     | NULL    |                |
#| CURRENT_PRICE      | decimal(10,2)    | NO   |     | 0.00    |                |
#| CURRENT_SHIP       | decimal(10,2)    | NO   |     | 0.00    |                |
#| LOCK_ID            | int(10) unsigned | YES  |     | 0       |                |
#| LOCK_GMT           | int(10) unsigned | YES  |     | 0       |                |
#| NEEDS_PRICE_UPDATE | tinyint(4)       | NO   |     | 0       |                |
#+--------------------+------------------+------+-----+---------+----------------+
#21 rows in set (0.07 sec)


#alter table AMAZON_PID_UPCS 
# add AMZRP_STRATEGY varchar(10) default '' not null,
# add AMZRP_MIN_SHIP_I integer unsigned default 0 not null,
# add AMZRP_MIN_PRICE_I integer unsigned default 0 not null,
# add AMZRP_MAX_PRICE_I integer unsigned default 0 not null,
# add AMZRP_LAST_PRICE_I integer unsigned default 0 not null,
# add AMZRP_LAST_SHIP_I integer unsigned default 0 not null,
# add AMZRP_LAST_POLL_TS timestamp default 0 not null,
# add AMZRP_POLL_LOCK_ID integer unsigned default 0 not null,
# add AMZRP_CURRENT_PRICE_I integer unsigned default 0 not null,
# add AMZRP_CURRENT_SHIP_I integer unsigned default 0 not null,
# add AMZRP_STATUS smallint unsigned default 0 not null,
# add AMZRP_NEXT_POLL_TS timestamp default 0 not null,
# add index(AMZRP_NEXT_POLL_TS)
#;


my $rdbh = &WATCHER::db_ec2rds_connect();

my $pstmt = "select * from AMAZON_REPRICE_PRODUCTS";
my $sth = $rdbh->prepare($pstmt);
$sth->execute();
while ( my $hashref = $sth->fetchrow_hashref() ) {
	print Dumper($hashref);

	my $USERNAME = $hashref->{'USERNAME'};
	my ($udbh) = &DBINFO::db_user_connect($USERNAME);
	my $pstmt = &DBINFO::insert($udbh,"AMAZON_PID_UPCS",{
			'MID'=>$hashref->{'MID'},
			'SKU'=>$hashref->{'SKU'},
			'AMZRP_STRATEGY'=>$hashref->{'STRATEGY_ID'},
			'AMZRP_MIN_SHIP_I'=>$hashref->{'VAR_MIN_SHIP'}*100,
			'AMZRP_MIN_PRICE_I'=>$hashref->{'VAR_MIN_PRICE'}*100,
			'AMZRP_MAX_PRICE_I'=>$hashref->{'VAR_MAX_PRICE'}*100,
			'*AMZRP_NEXT_POLL_TS'=>time(),
			'AMZRP_STATUS'=>1,
		},key=>['MID','SKU'], update=>2, sql=>1);
	print $pstmt."\n";
	$udbh->do($pstmt);
	&DBINFO::db_user_close();
	
	}
$sth->finish();
&WATCHER::db_ec2rds_close();
