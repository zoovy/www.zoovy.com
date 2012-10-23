#!/usr/bin/perl

use lib "/httpd/modules";
use DBINFO;

my ($zdbh) = &DBINFO::db_zoovy_connect();

			push @AR, "2010-12-07|html|articles/20101207.html|New Desktop Client Fully Automates Order, Warehouse and Risk Management Functions.";
			push @AR, "2010-11-08|html|articles/20101108.html|Zoovy Offers FedEx SmartPost Shipping to Small to Mid-Sized Retailers";
			push @AR, "2010-09-14|html|articles/20100914.html|Zoovy eCommerce Platform Addresses Online Retailers at the Brink of Growth";
			push @AR, "2010-06-07|html|articles/20100607.html|Zoovy Celebrates Ongoing Growth with Further Expansion at Their San Diego Office";
			push @AR, "2008-05-12|html|articles/20080512.html|Zoovy e-Commerce Technologies Forms Strategic Partnership with U-PIC Insurance Services";
			push @AR, "2008-04-05|html|articles/20080404.html|Zoovy, Inc. Increases Customer Conversion by Partnering With ControlScan";
			push @AR, "2006-06-01|html|articles/20060601.html|Zoovy Inc. Websites are the First to Provide Worry Free Shopping with a Guarantee";
			push @AR, "2006-05-31|html|articles/20060531.html|buySAFE Solves Retail Websites' Number One Problem: Gaining Buyer Confidence";
			push @AR, "2006-04-06|html|articles/20060406.html|Zoovy, Inc.'s New Web 2.0/AJAX Based Software Boosts e-Ccommerce Sales";
			push @AR, "2006-03-14|html|articles/20060314.html|Zoovy, Inc. Releases New Order Manager 6.0";
			push @AR, "2006-02-22|html|articles/20060222.html|Zoovy, Inc. Launches JEDI Supply Chain Integration Function";
			push @AR, "2004-11-08|html|articles/20041108.html|Zoovy, Inc. Signs Strategic Partnership with buySAFE";
			push @AR, "2004-06-23|html|articles/20040623.html|Zoovy Named eBay Star Developer";
			push @AR, "2003-03-10|html|articles/20030310.html|Zoovy, Inc. is First Auction Management and e-Commerce Company to be Approved as UPS OnLine Tools Product Provider";
#			push @AR, "2003-01-13|html|articles/20030113.html|Zoovy, Inc. and AllDropShip.com Announce The Launch of a Revolutionary New eCommerce Marketplace";
			push @AR, "2003-01-07|html|articles/20030107.html|Zoovy, Inc. Integrates Online Business Management Solutions with Endicia Internet Postage";
			push @AR, "2002-12-17|html|articles/20021217.html|Zoovy, Inc. Enters into Strategic Alliance with eBay to Provide Online Merchants with Total Auction and Business Management Solutions";
			push @AR, "2002-12-09|html|articles/20021209.html|Zoovy, Inc. Announces Their Online Business Management Solutions Now Share Data with Intuit's QuickBooks 2003 Products";
#			push @AR, "2002-12-06|html|articles/20021206.html|Zoovy, Inc. and InterShopZone Announce Strategic Agreement";
#			push @AR, "2002-06-12|html|articles/20020612.html|Zoovy, Inc. and uBid Announce Strategic Agreement";
#			push @AR, "2002-02-25|html|articles/20020225.html|Zoovy Partners With ePier To Benefit Auction Community";
			push @AR, "2001-12-07|html|articles/20011207.html|300 Auction Templates Now Available at Zoovy";
#			push @AR, "2001-08-07|html|articles/20010807.html|Zoovy Gains 10,000 Small Business Customers for its E-Commerce System";
#			push @AR, "2001-07-26|html|articles/20010726.html|Zoovy Continues Growth; 10,000 Demos Strong";
			push @AR, "2001-06-06|html|articles/20010606.html|Zoovy Announces Availability Of E-Commerce Software That Enables Fast, Easy Online Sales For Small Businesses";
			push @AR, "2001-04-12|html|articles/20010412.html|The First Auction-Integrated Storefront to Track Inventory";
			push @AR, "2001-03-28|html|articles/20010328.html|Zoovy Integrates Western Union Moneyzap into Online Store and Auction Product";
			push @AR, "2001-01-17|html|articles/20010117.html|Zoovy Receives 1.5 Million in Venture Capital";


#mysql> desc RECENT_NEWS;
#+----------+--------------+------+-----+---------------------+----------------+
#| Field    | Type         | Null | Key | Default             | Extra          |
#+----------+--------------+------+-----+---------------------+----------------+
#| ID       | int(11)      | NO   | PRI | NULL                | auto_increment |
#| RESELLER | varchar(20)  | NO   |     | NULL                |                |
#| CREATED  | datetime     | YES  |     | NULL                |                |
#| EXPIRES  | datetime     | NO   | MUL | 0000-00-00 00:00:00 |                |
#| TITLE    | varchar(255) | NO   |     | NULL                |                |
#| MESSAGE  | mediumtext   | NO   |     | NULL                |                |
#| TOPIC    | varchar(10)  | NO   |     | NULL                |                |
#| TECH     | varchar(10)  | NO   |     | NULL                |                |
#| PUBLIC   | tinyint(4)   | NO   |     | 0                   |                |
#+----------+--------------+------+-----+---------------------+----------------+
#9 rows in set (0.00 sec)

foreach my $x (reverse @AR) {
	my ($date,$type,$file) = split(/\|/,$x);
	open F, "</httpd/htdocs/company/pressreleases/$file";
	$/ = undef;
	($buf) = <F>;
	$/ = "\n";
	close F;

	require ZTOOLKIT;
	$buf = &ZTOOLKIT::stripUnicode($buf);

	$date =~ s/-//gs;
	$date .= '000000';

	$pstmt = &DBINFO::insert($zdbh,'RECENT_NEWS',{
		ID=>0,
		RESELLER=>'PR',
		CREATED=>$date,
		EXPIRES=>$date,
		TITLE=>'IMPORTED PRESS RELEASE',
		MESSAGE=>$buf,
		TOPIC=>'pr',
		TECH=>'IMPORT',
		PUBLIC=>16,
		},sql=>1);
	print $pstmt."\n";
	$zdbh->do($pstmt);
	}

