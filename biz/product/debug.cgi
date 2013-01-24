#!/usr/bin/perl

use lib "/httpd/modules";
use ZOOVY;
use PRODUCT::FLEXEDIT;
use DBINFO;
use Data::Dumper;
use ZTOOLKIT;
use GTOOLS;
use INVENTORY;
use EXTERNAL;
use strict;


require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_P&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }


my $PID = $ZOOVY::cgiv->{'product'}; 
$GTOOLS::TAG{'<!-- PRODUCT -->'} = $PID;

if ($ZOOVY::cgiv->{'ACTION'} eq 'OVERRIDE_RESERVE') {
	my ($SKU) = $ZOOVY::cgiv->{'SKU'};
	my ($APPKEY) = $ZOOVY::cgiv->{'APPKEY'};
	my ($LISTINGID) = $ZOOVY::cgiv->{'LISTINGID'};
	&INVENTORY::set_other($USERNAME,$APPKEY,$SKU,0,'expirets'=>time()-1,'uuid'=>$LISTINGID);
	$LU->log("PRODEDIT.DEBUG.RESINVOVERRIDE","Reserve Inventory Override SKU=$SKU APPKEY=$APPKEY LISTINGID=$LISTINGID");
	$ZOOVY::cgiv->{'ACTION'} = 'REFRESH';
	}


if ($ZOOVY::cgiv->{'ACTION'} eq 'REFRESH') {
	&INVENTORY::update_reserve($USERNAME,$PID,1+2+4+8);
	$GTOOLS::TAG{'<!-- MESSAGE -->'} = &GTOOLS::std_box("Refreshed Inventory","Reserve Inventory for product $PID has been updated. <i>NOTE: if this changes any values, it indicates a critical error in the inventory system. Do not use this feature unless instructed by technical support.</i>");
	}


#mysql> desc INVENTORY_UPDATES;
#+-----------+---------------+------+-----+---------+----------------+
#| Field     | Type          | Null | Key | Default | Extra          |
#+-----------+---------------+------+-----+---------+----------------+
#| ID        | int(11)       |      | PRI | NULL    | auto_increment |
#| USERNAME  | varchar(20)   | YES  | MUL | NULL    |                |
#| LUSER     | varchar(20)   |      |     |         |                |
#| TIMESTAMP | datetime      | YES  |     | NULL    |                |
#| TYPE      | enum('U','I') | YES  |     | NULL    |                |
#| PRODUCT   | varchar(20)   |      |     |         |                |
#| SKU       | varchar(35)   |      |     |         |                |
#| QUANTITY  | int(11)       | YES  |     | NULL    |                |
#| APPID     | varchar(10)   |      |     |         |                |
#| ORDERID   | varchar(16)   |      |     |         |                |
#+-----------+---------------+------+-----+---------+----------------+
#10 rows in set (0.02 sec)

my $zdbh = &DBINFO::db_zoovy_connect();
my $udbh = &DBINFO::db_user_connect($USERNAME);
my $c = '';

my $qtPID = $udbh->quote($PID);

## future: show events
## select * from USER_EVENTS where MID='62321' and PID='SCUBA-AS-BEIGE-BLK' order by ID;


## OTHER RESERVE
my $detailref = &INVENTORY::list_other(undef,$USERNAME,$PID,0);
foreach my $iref (@{$detailref}) {
	$c .= "<tr><td>$iref->{'APPKEY'}</td><td>$iref->{'LISTINGID'}</td><td>$iref->{'SKU'}</td><td>$iref->{'QTY'}</td><td>".&ZTOOLKIT::pretty_date($iref->{'EXPIRES_GMT'})."</td>";
	$c .= "<td><a href=\"/biz/product/debug.cgi?product=$PID&ACTION=OVERRIDE_RESERVE&SKU=$iref->{'SKU'}&APPKEY=$iref->{'APPKEY'}&LISTINGID=$iref->{'LISTINGID'}\">[Manual Override]</a></td>";
	$c .= "</tr>";
	}
if ($c eq '') { $c .= "<tr><td><i>None</i></td></tr>"; } else {
	$c = "<tr><td><b>Application</b></td><td><b>Listing</b></td><td><b>SKU</b></td><td><b>QTY</b></td><td><b>Expires</b></td></tr>".$c; 
	}
$GTOOLS::TAG{'<!-- OTHER_RESERVE -->'} = $c;

## INCOMPLETE RESERVE
if (1) {
	$c = '';
	my $udbh = &DBINFO::db_user_connect($USERNAME);
	my $pstmt = "select ID,MKT_LISTINGID,CREATED_GMT from EXTERNAL_ITEMS where MID=$MID and (SKU=".$zdbh->quote($PID)." or SKU like ".$zdbh->quote($PID.':%').") and STAGE in ('A','I','V','W')";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	while ( my ($CLAIM,$MARKETID,$CREATED_GMT) = $sth->fetchrow() ) {
		my $CREATED = &ZTOOLKIT::pretty_date($CREATED_GMT,1);
		$c .= "<tr><td>$CLAIM</td><td>$MARKETID</td><td>$CREATED</td></tr>";
		}
	if ($c eq '') { $c .= "<tr><td><i>None</i></td></tr>"; } else {
		$c = "<tr><td><b>Claim</b></td><td><b>Market Id</b></td><td><b>Created</b></td></tr>".$c;
		}
	$sth->finish();
	$GTOOLS::TAG{'<!-- INCOMPLETE_RESERVE -->'} = $c;
	&DBINFO::db_user_close();
	}



## INVENTORY DEBUG LOG
my $pdbh = &DBINFO::db_user_connect($USERNAME);
my ($LOGTB) = &INVENTORY::resolve_tb($USERNAME,$MID,'INVENTORY_LOG');

$c = '';
#$pstmt = "select * from $LOGTB where MID=$MID and PID=".$pdbh->quote($PID)." and FINALIZED_GMT>".(time()-(86400*14))." order by ID asc";
my $LIMIT = 20;
if ($USERNAME eq 'toynk') { $LIMIT = 100; }
my $pstmt = "select * from $LOGTB where MID=$MID and PID=".$pdbh->quote($PID)." order by ID desc limit 0,$LIMIT";

print STDERR $pstmt."\n";
my $sth = $pdbh->prepare($pstmt);
$sth->execute();

## wanted the 20 latest entries ordered from earliest to latest
#my $logref = ();
#while ( my $hashref = $sth->fetchrow_hashref() ) { 
#	$logref->{$hashref->{'ID'}} = $hashref;
#	}
#foreach my $id (sort keys %{$logref}) {

while ( my $hashref = $sth->fetchrow_hashref() ) { 

	my $APP = $hashref->{'APP'};
	$c .= qq~
	<tr>
		<td style='font-size: 8pt;' valign=top>~.&ZTOOLKIT::pretty_date($hashref->{'POSTED_GMT'},1).qq~</td>
		<td style='font-size: 8pt;' valign=top>$hashref->{'LUSER'}</td>
		<td style='font-size: 8pt;' valign=top>$hashref->{'INV_OPT'}</td>
		<td style='font-size: 8pt;' valign=top align='center'>$hashref->{'WAS'}</td>
		<td style='font-size: 8pt;' valign=top>$hashref->{'COMMENT'}</td>
		<td style='font-size: 8pt;' valign=top align='center'>$hashref->{'NOW'}</td>
		<td style='font-size: 8pt;' valign=top>$APP</td>
		<td style='font-size: 8pt;' valign=top>$hashref->{'DEBUG'}</td>
		<td style='font-size: 8pt;' valign=top>~.&ZTOOLKIT::pretty_date($hashref->{'FINALIZED_GMT'},1).qq~</td>
	</tr>
	~;
	}

## prepend finalization pending records.
$pstmt = "select LUSER,TIMESTAMP,TYPE,PRODUCT,SKU,QUANTITY,APPID,ORDERID from INVENTORY_UPDATES where MID=$MID /* $USERNAME */ and PRODUCT=".$pdbh->quote($PID)." order by ID desc";
print STDERR $pstmt."\n";
$sth = $pdbh->prepare($pstmt);
$sth->execute();
while ( my $hashref = $sth->fetchrow_hashref() ) {
	$c = qq~
	<tr class='rs'>
		<td style='font-size: 8pt;' valign=top>~.&ZTOOLKIT::pretty_date(&ZTOOLKIT::mysql_to_unixtime($hashref->{'TIMESTAMP'}),1).qq~</td>
		<td style='font-size: 8pt;' valign=top>$hashref->{'LUSER'}</td>
		<td style='font-size: 8pt;' valign=top>$hashref->{'SKU'}</td>
		<td style='font-size: 8pt;' valign=top>-</td>
		<td style='font-size: 8pt;' valign=top>$hashref->{'TYPE'}=$hashref->{'QUANTITY'}</td>
		<td style='font-size: 8pt;' valign=top>-</td>
		<td style='font-size: 8pt;' valign=top>$hashref->{'APPID'}</td>
		<td style='font-size: 8pt;' valign=top>$hashref->{'ORDERID'}</td>
		<td style='font-size: 8pt;' valign=top>-- FINALIZATION PENDING --</td>
	</tr>
	~.$c;
	}
$sth->finish();




#+------------------+---------------------+------+-----+---------+----------------+
#| Field            | Type                | Null | Key | Default | Extra          |
#+------------------+---------------------+------+-----+---------+----------------+
#| ID               | int(11)             | NO   | PRI | NULL    | auto_increment |
#| MERCHANT         | varchar(20)         | NO   |     | NULL    |                |
#| MID              | int(10) unsigned    | NO   | MUL | 0       |                |
#| PRODUCT          | varchar(20)         | NO   |     | NULL    |                |
#| SKU              | varchar(35)         | NO   |     | NULL    |                |
#| WHCODE           | tinyint(3) unsigned | NO   |     | 0       |                |
#| IN_STOCK_QTY     | int(11)             | NO   |     | 0       |                |
#| RESERVED_QTY     | int(11)             | NO   |     | 0       |                |
#| TS               | int(11)             | NO   |     | 0       |                |
#| EXTERNAL_QTY     | int(11)             | NO   |     | 0       |                |
#| CHANNEL_QTY      | int(11)             | NO   |     | 0       |                |
#| OTHER_QTY        | int(11)             | NO   |     | 0       |                |
#| LOCATION         | varchar(20)         | NO   |     | NULL    |                |
#| RESERVED_DIRTY   | int(10) unsigned    | NO   |     | 0       |                |
#| LAST_ORDERID     | varchar(16)         | NO   |     | NULL    |                |
#| ONORDER_QTY      | int(11)             | NO   |     | 0       |                |
#| REORDER_QTY      | int(11)             | NO   |     | 0       |                |
#| COST             | decimal(8,2)        | NO   |     | 0.00    |                |
#| TOUCHED          | int(10) unsigned    | NO   |     | 0       |                |
#| COUNTED_GMT      | int(10) unsigned    | NO   |     | 0       |                |
#| AMZ_UPLOADED_GMT | int(10) unsigned    | NO   |     | 0       |                |
#+------------------+---------------------+------+-----+---------+----------------+
#27 rows in set (0.02 sec)


#mysql> desc AMAZON_PID_UPCS;
#+-------------------+----------------------------------------------+------+-----+---------+----------------+
#| Field             | Type                                         | Null | Key | Default | Extra          |
#+-------------------+----------------------------------------------+------+-----+---------+----------------+
#| ID                | int(11)                                      | NO   | PRI | NULL    | auto_increment |
#| MID               | int(11) unsigned                             | NO   | MUL | 0       |                |
#| PID               | varchar(50)                                  | NO   |     | NULL    |                |
#| PRODUCTDB_GMT     | int(10) unsigned                             | NO   |     | 0       |                |
#| UPC               | varchar(15)                                  | YES  | MUL | NULL    |                |
#| ASIN              | varchar(50)                                  | YES  |     | NULL    |                |
#| UPLOADED_GMT      | int(11)                                      | NO   |     | 0       |                |
#| INVENTORY_GMT     | int(11)                                      | YES  |     | 0       |                |
#| FEEDS_DONE        | smallint(5) unsigned                         | NO   |     | 0       |                |
#| FEEDS_TODO        | smallint(5) unsigned                         | NO   |     | 0       |                |
#| FEEDS_ERROR       | smallint(5) unsigned                         | NO   |     | 0       |                |
#| RELATIONSHIP      | varchar(10)                                  | NO   |     | NULL    |                |
#| parent            | varchar(20)                                  | YES  |     | NULL    |                |
#| CATALOG           | varchar(65)                                  | NO   |     | NULL    |                |
#| STATE             | enum('NEW','PROCESS','SUCCESS','ERR','WARN') | YES  |     | NULL    |                |
#| ERROR             | varchar(255)                                 | YES  |     | NULL    |                |
#| LASTDOC_PRODUCTS  | bigint(20) unsigned                          | NO   |     | 0       |                |
#| LASTDOC_INVENTORY | bigint(20) unsigned                          | NO   |     | 0       |                |
#| LASTDOC_PRICES    | bigint(20) unsigned                          | NO   |     | 0       |                |
#| LASTDOC_IMAGES    | bigint(20) unsigned                          | NO   |     | 0       |                |
#| LASTDOC_RELATIONS | bigint(20) unsigned                          | NO   |     | 0       |                |
#| LASTDOC_ACCESSORY | bigint(20) unsigned                          | NO   |     | 0       |                |
#| LASTDOC_SHIPPING  | bigint(20) unsigned                          | NO   |     | 0       |                |
#+-------------------+----------------------------------------------+------+-----+---------+----------------+

## AMAZON SYN data
#my @skus = ();
#if (1) {
#	require AMAZON3;
#	my $qtPID = $udbh->quote($PID);
#	my $c = '';
#	$pstmt = "select * from AMAZON_PID_UPCS where MID=$MID and (PID=$qtPID or PARENT=$qtPID) order by PID";
#	my $sth = $udbh->prepare($pstmt);
#	$sth->execute();
#	while ( my $pref = $sth->fetchrow_hashref() ) {
#
#		my $todo_pretty = &AMAZON3::describe_bw($pref->{'FEEDS_TODO'});
#		if ($todo_pretty eq '') { $todo_pretty = '*nothing-waiting*'; }
#
#		my $done_pretty = &AMAZON3::describe_bw($pref->{'FEEDS_DONE'});
#		if ($done_pretty eq '') { $done_pretty = '*feeds-completed*'; }
#
#		my $error_pretty = &AMAZON3::describe_bw($pref->{'ERROR_DONE'});
#		if ($error_pretty eq '') { $error_pretty = '*none*'; }
#
#		my $uploaded = &ZTOOLKIT::pretty_date($pref->{'UPLOADED_GMT'},1);
#		my $inventory = &ZTOOLKIT::pretty_date($pref->{'INVENTORY_GMT'},1);
#		if ($pref->{'parent'} eq '') { $pref->{'parent'} = 'n/a'; }
#		$c .= qq~
#<tr>
#	<td valign=top>$pref->{'SKU'}</td>
#	<td valign=top>$pref->{'UPC'}<br>UPC_FAKE: $pref->{'UPC_FAKED'}</td>
#	<td valign=top>$pref->{'ASIN'}</td>
#	<td valign=top>
#	Last Sync: $uploaded<br>
#	Last Inventory: $inventory<br>
#	</td>
#	<td valign=top>
#	Relationship: $pref->{'RELATIONSHIP'} (parent=$pref->{'parent'})<br>
#	ProductVersion: $pref->{'PRODUCTDB_GMT'}<br>
#	</td>
#	<td valign=top nowrap>
#	STATE: $pref->{'STATE'}<br>
#	FEEDS_TODO: $pref->{'FEEDS_TODO'}=$todo_pretty<br>
#	FEEDS_DONE: $pref->{'FEEDS_DONE'}=$done_pretty<br>
#	FEEDS_ERROR: $pref->{'FEEDS_ERROR'}=$error_pretty<br>
#	</td>
#	<td valign=top nowrap>
#	TXT: $pref->{'ERROR'}<Br>
#	LASTDOC_PRODUCTS: <a target="amzview" href="/biz/setup/private/index.cgi?VERB=VIEW&FILENAME=amz-$USERNAME-$pref->{'LASTDOC_PRODUCTS'}.xml">$pref->{'LASTDOC_PRODUCTS'}</a><br>
#	LASTDOC_INVENTORY: $pref->{'LASTDOC_INVENTORY'}<br>
#	LASTDOC_PRICES: $pref->{'LASTDOC_PRICES'}<br>
#	LASTDOC_IMAGES: $pref->{'LASTDOC_IMAGES'}<br>
#	LASTDOC_ACCESSORY: $pref->{'LASTDOC_ACCESSORY'}<br>
#	LASTDOC_SHIPPING: $pref->{'LASTDOC_SHIPPING'}<br>
#	</td>
#</tr>
#~;
#		push @skus, $pref->{'PID'};
#		}
#	if ($c eq '') {
#		$c = "<tr><td colspan=5><i>No Amazon Data Found</td></tr>";
#		}
#	$sth->finish();
#	$GTOOLS::TAG{'<!-- AMAZON_DEBUG -->'} = $c;
#	}
#
## AMAZON LOG 
#if (1) {
#	
#	my $c = '';
#
#	foreach my $sku (sort @skus) {
#		my $qtSKU = $zdbh->quote($sku);
#		$pstmt = "select product,from_unixtime(CREATED_GMT),TYPE,MSGTYPE,MESSAGE,DOCID from AMAZON_LOG where MID=$MID and PRODUCT=$qtSKU order by created_gmt desc limit 20";
#		my $sth = $udbh->prepare($pstmt);
#		$sth->execute();
#		while ( my ($product,$created,$type,$msgtype,$message,$docid) = $sth->fetchrow() ) {
#			$c .= qq~
#<tr>
#	<td valign=top>$product</td>
#	<td valign=top>$created</td>
#	<td valign=top>$type</td>
#	<td valign=top>$msgtype</td>
#	<td valign=top>$message</td>
#	<td valign=top>$docid</td>
#</tr>
#~;
#			}
#		}
#	if ($c eq '') {
#		$c = "<tr><td colspan=5><i>No Amazon Data Found</td></tr>";
#		}
#	$sth->finish();
#	$GTOOLS::TAG{'<!-- AMAZON_LOG_DEBUG -->'} = $c;
#	}

#mysql> desc AMAZON_DOCUMENT_CONTENTS;
#+------------+----------------------------------------------------------------------------------------+------+-----+-------------------+-----------------------------+
#| Field      | Type                                                                                   | Null | Key | Default           | Extra                       |
#+------------+----------------------------------------------------------------------------------------+------+-----+-------------------+-----------------------------+
#| MID        | int(10) unsigned                                                                       | NO   | PRI | 0                 |                             |
#| DOCID      | bigint(20)                                                                             | NO   | PRI | 0                 |                             |
#| MSGID      | int(11)                                                                                | NO   | PRI | 0                 |                             |
#| FEED       | enum('init','products','prices','images','inventory','relations','shipping','deleted') | YES  |     | NULL              |                             |
#| SKU        | varchar(35)                                                                            | NO   |     | NULL              |                             |
#| CREATED_TS | timestamp                                                                              | NO   |     | CURRENT_TIMESTAMP | on update CURRENT_TIMESTAMP |
#| DEBUG      | tinytext                                                                               | YES  |     | NULL              |                             |
#| ACK_GMT    | int(10) unsigned                                                                       | NO   |     | 0                 |                             |
#+------------+----------------------------------------------------------------------------------------+------+-----+-------------------+-----------------------------+
#8 rows in set (0.00 sec)
if (1) {
	my $c = '';
	## select a PID or any matching SKU of a PID 
	my $pstmt = "select DOCID,MSGID,FEED,SKU,CREATED_TS,DEBUG,ACK_GMT from AMAZON_DOCUMENT_CONTENTS where MID=$MID and SKU REGEXP concat('^',$qtPID,'(\\:[A-Z0-9\\#]{4,4}){0,3}\$') order by DOCID desc limit 150;";
	# $c .= $pstmt;
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	while ( my ($DOCID,$MSGID,$FEED,$SKU,$CREATED_TS,$DEBUG,$ACK_GMT) = $sth->fetchrow() ) {
		$c .= "<tr>";
		$c .= "<td>".$DOCID."</td>";
		$c .= "<td>".$MSGID."</td>";
		$c .= "<td>".$FEED."</td>";
		$c .= "<td>".$SKU."</td>";
		$c .= "<td>".$CREATED_TS."</td>";
		$c .= "<td>".$DEBUG."</td>";
		$c .= "<td>".$ACK_GMT."</td>";
		$c .= "</tr>";
		}
	$sth->finish();
	$GTOOLS::TAG{'<!-- AMAZON_DOCUMENT_CONTENTS -->'} = $c;
	}


#mysql> desc SKU_LOOKUP_60000;
#+-----------------------------+------------------------------------------------------------------------------------+------+-----+---------------------+----------------+
#| Field                       | Type                                                                               | Null | Key | Default             | Extra          |
#+-----------------------------+------------------------------------------------------------------------------------+------+-----+---------------------+----------------+
#| ID                          | bigint(20) unsigned                                                                | NO   | PRI | NULL                | auto_increment |
#| MID                         | int(10) unsigned                                                                   | NO   | MUL | 0                   |                |
#| PID                         | varchar(30)                                                                        | NO   |     | NULL                |                |
#| INVOPTS                     | varchar(15)                                                                        | NO   |     | NULL                |                |
#| SKU                         | varchar(45)                                                                        | NO   |     | NULL                |                |
#| TITLE                       | varchar(80)                                                                        | NO   |     | 0                   |                |
#| COST                        | decimal(10,2)                                                                      | NO   |     | 0.00                |                |
#| PRICE                       | decimal(10,2)                                                                      | NO   |     | 0.00                |                |
#| UPC                         | varchar(13)                                                                        | NO   |     | NULL                |                |
#| MFGID                       | varchar(25)                                                                        | NO   |     | NULL                |                |
#| SUPPLIERID                  | varchar(25)                                                                        | NO   |     | NULL                |                |
#| PRODASM                     | tinytext                                                                           | YES  |     | NULL                |                |
#| INV_AVAILABLE               | int(10) unsigned                                                                   | NO   |     | 0                   |                |
#| AMZ_PARENT                  | varchar(20)                                                                        | NO   |     | NULL                |                |
#| AMZ_ASIN                    | varchar(15)                                                                        | NO   |     | NULL                |                |
#| AMZ_FEEDS_DONE              | smallint(5) unsigned                                                               | NO   |     | 0                   |                |
#| AMZ_FEEDS_TODO              | smallint(5) unsigned                                                               | NO   |     | 0                   |                |
#| AMZ_FEEDS_SENT              | tinyint(4)                                                                         | NO   |     | 0                   |                |
#| AMZ_FEEDS_WAIT              | tinyint(4)                                                                         | NO   |     | 0                   |                |
#| AMZ_FEEDS_WARN              | smallint(5) unsigned                                                               | NO   |     | 0                   |                |
#| AMZ_FEEDS_ERROR             | smallint(5) unsigned                                                               | NO   |     | 0                   |                |
#| AMZ_RELATIONSHIP            | enum('VPARENT','VCONTAINER','NPARENT','BASE','CHILD','VCCHILD','VCHILD','STUB','') | YES  |     | NULL                |                |
#| AMZ_PRODUCTDB_GMT           | int(10) unsigned                                                                   | NO   |     | 0                   |                |
#| AMZ_STATE                   | enum('NEW','PROCESS','SUCCESS','ERR','WARN','')                                    | NO   |     | NULL                |                |
#| AMZ_ERROR                   | text                                                                               | NO   |     | NULL                |                |
#| AMZ_LASTDOC_PRODUCTS        | bigint(20) unsigned                                                                | NO   |     | 0                   |                |
#| AMZ_LASTDOC_PRODUCTS_MSGID  | smallint(5) unsigned                                                               | NO   |     | 0                   |                |
#| AMZ_LASTDOC_INVENTORY       | bigint(20) unsigned                                                                | NO   |     | 0                   |                |
#| AMZ_LASTDOC_INVENTORY_MSGID | smallint(5) unsigned                                                               | NO   |     | 0                   |                |
#| AMZ_LASTDOC_PRICES          | bigint(20) unsigned                                                                | NO   |     | 0                   |                |
#| AMZ_LASTDOC_PRICES_MSGID    | smallint(5) unsigned                                                               | NO   |     | 0                   |                |
#| AMZ_LASTDOC_IMAGES          | bigint(20) unsigned                                                                | NO   |     | 0                   |                |
#| AMZ_LASTDOC_IMAGES_MSGID    | smallint(5) unsigned                                                               | NO   |     | 0                   |                |
#| AMZ_LASTDOC_RELATIONS       | bigint(20) unsigned                                                                | NO   |     | 0                   |                |
#| AMZ_LASTDOC_RELATIONS_MSGID | smallint(5) unsigned                                                               | NO   |     | 0                   |                |
#| AMZ_LASTDOC_ACCESSORY       | bigint(20) unsigned                                                                | NO   |     | 0                   |                |
#| AMZ_LASTDOC_SHIPPING        | bigint(20) unsigned                                                                | NO   |     | 0                   |                |
#| AMZ_LASTDOC_SHIPPING_MSGID  | smallint(5) unsigned                                                               | NO   |     | 0                   |                |
#| INV_ON_SHELF                | int(10) unsigned                                                                   | NO   |     | 0                   |                |
#| INV_ON_ORDER                | int(10) unsigned                                                                   | NO   |     | 0                   |                |
#| INV_IS_BO                   | int(10) unsigned                                                                   | NO   |     | 0                   |                |
#| INV_IS_RSVP                 | int(10) unsigned                                                                   | NO   |     | 0                   |                |
#| AMZRP_STRATEGY              | varchar(10)                                                                        | NO   |     | NULL                |                |
#| AMZRP_META                  | tinytext                                                                           | YES  |     | NULL                |                |
#| AMZRP_NEXT_POLL_TS          | timestamp                                                                          | NO   |     | 0000-00-00 00:00:00 |                |
#| AMZRP_SET_PRICE_I           | int(10) unsigned                                                                   | NO   |     | 0                   |                |
#| AMZRP_SET_SHIP_I            | int(10) unsigned                                                                   | NO   |     | 0                   |                |
#| AMZRP_IS                    | set('ENABLED','UNLEASHED','PAUSED','UNHAPPY','ANGRY','WINNING','LOSING')           | NO   |     | NULL                |                |
#| BUYRP_STRATEGY              | varchar(10)                                                                        | NO   |     | NULL                |                |
#| BUYRP_META                  | tinytext                                                                           | YES  |     | NULL                |                |
#| BUYRP_NEXT_POLL_TS          | timestamp                                                                          | NO   |     | 0000-00-00 00:00:00 |                |
#| BUYRP_SET_PRICE_I           | int(10) unsigned                                                                   | NO   |     | 0                   |                |
#| BUYRP_SET_SHIP_I            | int(10) unsigned                                                                   | NO   |     | 0                   |                |
#| BUYRP_IS                    | set('ENABLED','UNLEASHED','PAUSED','UNHAPPY','ANGRY','WINNING','LOSING')           | NO   |     | NULL                |                |
#| EBAYRP_STRATEGY             | varchar(10)                                                                        | NO   |     | NULL                |                |
#| EBAYRP_META                 | tinytext                                                                           | YES  |     | NULL                |                |
#| EBAYRP_NEXT_POLL_TS         | timestamp                                                                          | NO   |     | 0000-00-00 00:00:00 |                |
#| EBAYRP_SET_PRICE_I          | int(10) unsigned                                                                   | NO   |     | 0                   |                |
#| EBAYRP_SET_SHIP_I           | int(10) unsigned                                                                   | NO   |     | 0                   |                |
#| EBAYRP_IS                   | set('ENABLED','UNLEASHED','PAUSED','UNHAPPY','ANGRY','WINNING','LOSING')           | NO   |     | NULL                |                |
#| GOORP_STRATEGY              | varchar(10)                                                                        | NO   |     | NULL                |                |
#| GOORP_META                  | tinytext                                                                           | YES  |     | NULL                |                |
#| GOORP_NEXT_POLL_TS          | timestamp                                                                          | NO   |     | 0000-00-00 00:00:00 |                |
#| GOORP_SET_PRICE_I           | int(10) unsigned                                                                   | NO   |     | 0                   |                |
#| GOORP_SET_SHIP_I            | int(10) unsigned                                                                   | NO   |     | 0                   |                |
#| GOORP_IS                    | set('ENABLED','UNLEASHED','PAUSED','UNHAPPY','ANGRY','WINNING','LOSING')           | NO   |     | NULL                |                |
#| USR1RP_STRATEGY             | varchar(10)                                                                        | NO   |     | NULL                |                |
#| USR1RP_META                 | tinytext                                                                           | YES  |     | NULL                |                |
#| USR1RP_NEXT_POLL_TS         | timestamp                                                                          | NO   |     | 0000-00-00 00:00:00 |                |
#| USR1RP_SET_PRICE_I          | int(10) unsigned                                                                   | NO   |     | 0                   |                |
#| USR1RP_SET_SHIP_I           | int(10) unsigned                                                                   | NO   |     | 0                   |                |
#| USR1RP_IS                   | set('ENABLED','UNLEASHED','PAUSED','UNHAPPY','ANGRY','WINNING','LOSING')           | NO   |     | NULL                |                |
#| IS_CONTAINER                | tinyint(4)                                                                         | NO   |     | 0                   |                |
#+-----------------------------+------------------------------------------------------------------------------------+------+-----+---------------------+----------------+
#73 rows in set (0.01 sec)

if (1) {
	my $c = '';
	## select a PID or any matching SKU of a PID 
	my ($TB) = &ZOOVY::resolve_lookup_tb($USERNAME,$MID);
	my $pstmt = "select * from $TB where MID=$MID and PID=$qtPID order by ID desc";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	while ( my $ref = $sth->fetchrow_hashref() ) {
		$c .= "<tr>";
		$c .= "<td>".$ref->{'SKU'}."</td>";
		$c .= "<td>".$ref->{'TITLE'}."</td>";
		$c .= "<td>".$ref->{'PRICE'}."</td>";
		$c .= "<td>".$ref->{'UPC'}."</td>";
		$c .= "<td>".$ref->{'MFGID'}."</td>";
		$c .= "<td>".$ref->{'SUPPLIERID'}."</td>";
		$c .= "<td>".$ref->{'AMZ_ASIN'}."</td>";
		$c .= "<td>".$ref->{'AMZ_FEEDS_TODO'}."</td>";
		$c .= "<td>".$ref->{'AMZ_FEEDS_SENT'}."</td>";
		$c .= "<td>".$ref->{'AMZ_FEEDS_ERROR'}."</td>";
		$c .= "<td>".$ref->{'AMZ_FEEDS_DONE'}."</td>";
		$c .= "<td>".$ref->{'AMZ_PRODUCTDB_GMT'}."</td>";
		$c .= "</tr>";
		}
	$sth->finish();
	$GTOOLS::TAG{'<!-- SKU_LOOKUP -->'} = $c;
	}




#mysql> desc SYNDICATION_QUEUED_EVENTS;
#+---------------+------------------+------+-----+---------+----------------+
#| Field         | Type             | Null | Key | Default | Extra          |
#+---------------+------------------+------+-----+---------+----------------+
#| ID            | int(10) unsigned | NO   | PRI | NULL    | auto_increment |
#| USERNAME      | varchar(20)      | NO   |     | NULL    |                |
#| MID           | int(10) unsigned | NO   | MUL | 0       |                |
#| PRODUCT       | varchar(20)      | NO   |     | NULL    |                |
#| SKU           | varchar(35)      | NO   |     | NULL    |                |
#| CREATED_GMT   | int(10) unsigned | NO   |     | 0       |                |
#| PROCESSED_GMT | int(10) unsigned | NO   |     | 0       |                |
#| DST           | varchar(3)       | NO   |     | NULL    |                |
#| VERB          | varchar(10)      | NO   |     | NULL    |                |
#| ORIGIN_EVENT  | int(10) unsigned | NO   |     | 0       |                |
#---------------+------------------+------+-----+---------+----------------+
#10 rows in set (0.01 sec)
if (1) {
	my $c = '';
	## select a PID or any matching SKU of a PID 
	my $pstmt = "select SKU,CREATED_GMT,PROCESSED_GMT,DST,VERB,ORIGIN_EVENT from SYNDICATION_QUEUED_EVENTS where MID=$MID and PRODUCT=$qtPID order by ID desc";
	# $c .= $pstmt;
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	while ( my ($SKU,$CREATED_GMT,$PROCESSED_GMT,$DST,$VERB,$ORIGIN_EVENT) = $sth->fetchrow() ) {
		$c .= "<tr>";
		$c .= "<td>".$SKU."</td>";
		$c .= "<td>".&ZTOOLKIT::pretty_date($CREATED_GMT,2)."</td>";
		$c .= "<td>".&ZTOOLKIT::pretty_date($PROCESSED_GMT,2)."</td>";
		$c .= "<td>".$DST."</td>";
		$c .= "<td>".$VERB."</td>";
		$c .= "<td>".$ORIGIN_EVENT."</td>";
		$c .= "</tr>";
		}
	$sth->finish();
	$GTOOLS::TAG{'<!-- SYNDICATION_QUEUED_EVENTS -->'} = $c;
	}




if (1) {
	my $c = '';
	my $TB = &INVENTORY::resolve_tb($USERNAME,$MID,'INVENTORY');
	my $qtPID = $udbh->quote($PID);
	my $pstmt = "select * from $TB where MID=$MID /* $USERNAME */ and PRODUCT=$qtPID";
	print STDERR $pstmt."\n";
	my $sth = $pdbh->prepare($pstmt);
	$sth->execute();
	while ( my $hashref = $sth->fetchrow_hashref() ) {
		$c .= "<tr>";
		$c .= "<td valign=top style='font-size: 8pt;'>$hashref->{'PRODUCT'}</td>";
		$c .= "<td valign=top style='font-size: 8pt;'>$hashref->{'SKU'}</td>";
		$c .= "<td valign=top style='font-size: 8pt;'>$hashref->{'IN_STOCK_QTY'}</td>";
		$c .= "<td valign=top style='font-size: 8pt;'>$hashref->{'RESERVED_QTY'}</td>";
		$c .= "<td valign=top style='font-size: 8pt;'>$hashref->{'LOCATION'}</td>";
		$c .= "<td valign=top style='font-size: 8pt;'>$hashref->{'LAST_ORDERID'}</td>";
		$c .= "<td valign=top style='font-size: 8pt;'>$hashref->{'ONORDER_QTY'}</td>";
		$c .= "<td valign=top style='font-size: 8pt;'>$hashref->{'COST'}</td>";
		$c .= "<td valign=top style='font-size: 8pt;'>$hashref->{'META'}</td>";
		$c .= "</tr>";
		}
	$sth->finish();
	$GTOOLS::TAG{'<!-- INVENTORY_RECORDS -->'} = $c;
	}


	
if ($c eq '') { 
	$c .= "<tr><td valign=top><i>No inventory events have been recorded.</i></td></tr>"; 
	}
else {
	$c = "<tr><td valign=top><b>WHEN</td><td valign=top><b>USER</td><td valign=top><b>OPTION</td><td valign=top><b>WAS</b></td><td valign=top><b>COMMENT</b></td><td><b>NOW</b></td><td><b>APP</b></td><td><b>DEBUG</td><td><b>FINALIZED</b></td></tr>".$c; 
	}




#+---------------+-----------------------+------+-----+---------+----------------+
#| Field         | Type                  | Null | Key | Default | Extra          |
#+---------------+-----------------------+------+-----+---------+----------------+
#| ID            | int(10) unsigned      |      | PRI | NULL    | auto_increment |
#| MID           | int(11)               |      | MUL | 0       |                |
#| LUSER         | varchar(20)           |      |     |         |                |
#| POSTED_GMT    | mediumint(8) unsigned |      |     | 0       |                |
#| FINALIZED_GMT | mediumint(8) unsigned |      | MUL | 0       |                |
#| PID           | varchar(20)           |      |     |         |                |
#| INV_OPT       | varchar(15)           |      |     |         |                |
#| COMMENT       | varchar(30)           |      |     |         |                |
#| DEBUG         | varchar(25)           |      |     |         |                |
#| APP           | varchar(10)           |      |     |         |                |
#| WAS           | mediumint(9)          | YES  |     | 0       |                |
#| NOW           | mediumint(9)          |      |     | 0       |                |
#+---------------+-----------------------+------+-----+---------+----------------+

$GTOOLS::TAG{'<!-- INVENTORY_LOG -->'} = $c;


if (1) {
	require NAVCAT;
	$c = '';
	foreach my $prttext (@{&ZWEBSITE::list_partitions($USERNAME)}) {
		my ($prt) = split(/:/,$prttext); 
		my ($nc) = NAVCAT->new($USERNAME,PRT=>$prt);
		my $paths = $nc->paths_by_product($PID);
		foreach my $path (@${paths}) {
			$c .= "<tr><td>$path</td><td>$prttext</td></tr>";
			}
		}
	if ($c eq '') { $c .= "<tr><td><i>Product is not associated with website.</td></tr>"; }
	$GTOOLS::TAG{'<!-- NAVCATS -->'} = $c;
	}




if (1) {
	my $c = '';
	my $P = PRODUCT->new($USERNAME,$PID);

	my $SKUS = $P->list_skus();
	my %VARS = ();

	if (scalar(@{$SKUS})>0) {
		#$c .= "<tr><td>------------ BEGIN SKU SPECIFIC DATA -----------------</td></tr>";
		foreach my $set (@{$SKUS}) {
			my ($sku,$skuref) = @{$set};
			foreach my $k (keys %{$skuref}) {
				$VARS{"$k\~$sku"} = $skuref->{$k};
				#my $val = $ref->{'%SKU'}->{$sku}->{$k};
				#$val = &ZOOVY::incode($val);
				#$c .= "<tr><td>$sku\[$k\]</td><td>$val</td></tr>";
				}
			}
		# $c .= "<tr><td>------------ BEGIN SKU SPECIFIC DATA -----------------</td></tr>";
		}

	foreach my $k (keys %{$P->prodref()}) {
		$VARS{$k} = $P->fetch($k);
		}

	foreach my $skukey (sort keys %VARS) {
		next if ($skukey eq '');

		my $sku = undef;
		my $k = undef;
		if ($skukey =~ /(.*?)\~(.*?)/) { 
			## zoovy:prod_desc<sku:#010>
			$k = $1; $sku = $2;
			}
		else {
			$k = $skukey;
			}

		$c .= "<tr>";
		$c .= "<td valign='top'><b>$skukey</b></td>";
		my $out = '';
		if (ref($VARS{$skukey}) eq '') {
			$out = &ZOOVY::incode($VARS{$skukey});
			}
		elsif (ref($VARS{$skukey}) eq 'HASH') {
			$out = "<pre>".&ZOOVY::incode(Dumper($VARS{$skukey}))."</pre>";
			}
		else {
			$out = '**ERR**';
			}
		$c .= "<td>$out</td>";
		$c .= "</tr>";

		if (($k =~ /(.*?):prod_image[\d]+$/) || ($k =~ /:prod_thumb/)) {
			## REMINDER: make sure we don't match zoovy:prod_image[\d]_alt -- which can have spaces
			if (index($VARS{$skukey},' ')>=0) {
				$c .= "<tr><td colspan='2'><div class='error'>====&gt; WARNING: attribute $skukey contains a space in the data (not valid for images).</div></td></tr>";
				}
			}
		if ($skukey =~ /[\s]+/) {
			$c .= "<tr><td colspan='2'><div class='error'>====&gt; WARNING: attribute $skukey contains a space in the key '$skukey'.</div></td></tr>";
			}
		elsif ($skukey =~ /^[^a-z]+/) {
			$c .= "<tr><td colspan='2'><div class='error'>====&gt; WARNING: attribute $skukey contains an invalid leading character.</div></td></tr>";
			}

		
		my $fieldref = $PRODUCT::FLEXEDIT::fields{$k};
		if ($k =~ /^user:/) {
			## user defined fields.
			}
		elsif (defined $fieldref) {
			## valid field, but we can still perform some global checks.
			if ($fieldref->{'type'} eq 'legacy') {
				$c .= "<tr><td colspan='2'><div class='error'>====&gt; WARNING: attribute $skukey is a legacy field and should probably be removed.</div></td></tr>";
				}
			if ((defined $sku) && (not $fieldref->{'sku'})) {
				$c .= "<tr><td colspan='2'><div class='error'>====&gt; WARNING: attribute $skukey is set at the sku level, but is not considered a sku level field.</div></td></tr>";
				}
			}
		elsif (not &PRODUCT::FLEXEDIT::is_valid($k,$USERNAME)) {
			$c .= "<tr><td colspan='2'><div class='error'>====&gt; WARNING: attribute $k is not valid and should be removed.</div></td></tr>";
			}

		## field specific type checks
		if (not defined $fieldref) {
			}
		elsif ($fieldref->{'type'} eq 'textbox') {
			if (not defined $fieldref->{'minlength'}) { 
				## no minimum length check
				}
			elsif ( length($VARS{$skukey}) < $fieldref->{'minlength'}) {
				$c .= "<tr><td colspan='2'><div class='error'>====&gt; ERROR: attribute $skukey does not meet minimum length requirement of $fieldref->{'minlength'}.</div></td></tr>";
				}

			if (not defined $fieldref->{'maxlength'}) {}
			elsif ( length($VARS{$skukey}) > $fieldref->{'maxlength'}) {
				$c .= "<tr><td colspan='2'><div class='error'>====&gt; ERROR: attribute $skukey is longer than the maximum length requirement of $fieldref->{'maxlength'}.</div></td></tr>";
				}
			}

		## check data
		if ($VARS{$skukey} =~ /^[\s]+/) {
			$c .= "<tr><td colspan='2'><div class='warning'>====&gt; WARNING: attribute $skukey contains one or more leading spaces in data.</div></td></tr>";
			}
		elsif ($VARS{$skukey} =~ /^[\t]+/) {
			$c .= "<tr><td colspan='2'><div class='warning'>====&gt; WARNING: attribute $skukey contains one or more leading TAB characters in data.</div></td></tr>";
			}
		elsif ($VARS{$skukey} =~ /[\s]+$/) {
			$c .= "<tr><td colspan='2'><div class='warning'>====&gt; WARNING: attribute $skukey contains one or more trailing spaces in data.</div></td></tr>";
			}
		elsif ($VARS{$skukey} =~ /[\t]$/) {
			$c .= "<tr><td colspan='2'><div class='warning'>====&gt; WARNING: attribute $skukey contains one or more trailing TAB characters in data.</div></td></tr>";
			}
		}
	$GTOOLS::TAG{'<!-- PROD_DATA -->'} = $c; 
	}


&GTOOLS::output('*LU'=>$LU,'file'=>'debug.shtml',header=>1,popup=>1,head=>qq~
<script name="javascript">
<!--

function openWindow(url) {
	var popupWin = window.open(url,'popupWin','status=yes,resizable=yes,width=638,height=450,menubar=yes,scrollbars=yes')
   popupWin.focus(true);
	}

//-->
</script>
~);


&DBINFO::db_zoovy_close();
&DBINFO::db_user_close();

