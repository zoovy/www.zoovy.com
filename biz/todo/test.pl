#!/usr/bin/perl

use lib "/httpd/modules";
use TODO;
use Data::Dumper;

$USERNAME = 'brian';

$todo = TODO->new($USERNAME);

$todo->add(
	name=>'Enter Company Information',
	detail=>qq~
		Before you get started we ask that you please fill out your account information.
		~,
	link=>'http://www.zoovy.com/biz/setup/account',
	code=>'SETUP:HASPHONE',
	priority=>1,
	);


$todo->add(
	name=>'Select Website Theme', 
	detail=>qq~
		Website themes control the appearance of your site. 
		Choosing a website theme is requiste to getting started.~,
	link=>'http://www.zoovy.com/biz/setup/theme', 
	code=>'SETUP:HASTHEME',
	priority=>1,
	);

$todo->add(
	name=>'Create website categories',
	detail=>qq~
		Website categories should be created before you add products, that way you can put the products onto your website right after you create them.
		~,
	link=>'http://www.zoovy.com/biz/setup/navcat',
	code=>'SETUP:HASNAVCAT',
	priority=>1,
	);

$todo->add(
	name=>'Add a Product',
	detail=>qq~
		Creating products is the first step to getting sales.
		You can add products using a CSV Utility, or the online product manager.
		~,
	code=>'SETUP:HASPRODUCT',
	link=>'http://www.zoovy.com/biz/product/',
	priority=>1,
	);

$todo->add(
	name=>'Configure Shipping',
	detail=>qq~
		You need to configure how Zoovy will calculate shipping for your items.
		~,
	code=>'SETUP:HASSHIPPING',
	link=>'http://www.zoovy.com/biz/setup/shipping',
	priority=>2,
	);

$todo->add(
	name=>'Configure Payment Methods',
	detail=>qq~
		You need to configure how Zoovy will allow people to pay for your items.
		~,
	code=>'SETUP:HASPAYMENT',
	link=>'http://www.zoovy.com/biz/setup/payment',
	priority=>2,
	);

$todo->add(
	name=>'Configure Tax Settings',
	detail=>qq~
		Zoovy can compute the correct amount for both county and state sales tax amounts.
		~,
	code=>'SETUP:HASTAX',
	link=>'http://www.zoovy.com/biz/setup/tax',
	priority=>2,
	);

$todo->add(
	name=>'Setup eBay Account',
	detail=>qq~
		Creating products is the first step to getting sales.
		You can add products using a CSV Utility, or the online product manager.
		~,
	link=>'http://ebayapi.zoovy.net/?ACTION=HANDOFF&username='.$USERNAME,
	priority=>2,
	code=>'SETUP:EBAY',
	);

$todo->add(
	name=>'Configure Syndication',
	detail=>qq~
		Syndication allows you to put your products into Zoovy once, and then let Zoovy automatically
		push them out to a variety of marketplaces.
		~,
	link=>'http://www.zoovy.com/biz/syndication',
	priority=>3,
	code=>'SETUP:SYNDICATION',
	);

$todo->add(
	name=>'Set Company Logo',
	detail=>qq~You should associate your company logo with your account to increase your brand awareness.~,
	link=>'http://www.zoovy.com/biz/setup/logotool/',
	priority=>3,
	code=>'SETUP:COMPANYLOGO',
	);

$todo->add(
	name=>'Launch eBay Auctions',
	detail=>qq~
		You can launch individual products to auction by creating channels. To do this - simply go to the Products tab, select a product, and then select "Create Channels"
		~,
	link=>'http://www.zoovy.com/biz/product/',
	priority=>3,
	code=>'SETUP:HASCHANNELS',
	);

$todo->add(
	name=>'Download Order Manager',
	detail=>qq~
		The Zoovy Order Manager is a desktop client which lets you download orders to your local computer for processing.
		Order Manager delivers compatibility with QuickBooks, UPS Worldship, FedEx, and Endicia (USPS Postage).
		~,
	link=>'http://www.zoovy.com/biz/downloads',
	priority=>3,
	code=>'DOWNLOAD:ZOM',
	);


$todo->save();
print Dumper($todo);