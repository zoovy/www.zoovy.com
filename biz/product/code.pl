#!/usr/bin/perl -w

use lib "/httpd/modules";
require GTOOLS;
require ZOOVY;
require ZWEBSITE;
require CATEGORY;
use strict;

# note this counter should be incremented to represent the number
# of blank menu items
#################################################
my $counter = 4;  		# number of blank menu items

&ZOOVY::init();
&GTOOLS::init();
my ($USERNAME,$FLAGS) = ZOOVY::authenticate("/biz",1);
my $c = '';
my $elements = 1;

if ($FLAGS =~ /,PKG=STARTUP[ABC],/) { $FLAGS .= ',WEB,'; }

$GTOOLS::TAG{'<!-- UPGRADES -->'} = '';
if ($FLAGS =~ /,WEB,/) {
	$counter++;
	$GTOOLS::TAG{'<!-- UPGRADES -->'} .= qq~
menu.addItem("Store Option Groups","/biz/product/options2?product=","text");
MTMIconList.addIcon(new MTMIcon("menu_link_external.gif", "/biz/product/options2", "any"));
~;
	
	}

if (!$USERNAME) {
	print "Content-type: text/html\n\n";	
	print "Access Denied - not logged in.\n\n";
	exit;
	}

my $prods = undef;

my ($gref) = &ZWEBSITE::fetch_globalref($USERNAME);
my $ERROR = '';

if ((defined $gref->{'%tuning'}->{'auto_product_cache'}) && ($gref->{'%tuning'}->{'auto_product_cache'}==0)) {
	$ERROR = "&gt;auto_product_cache is disabled. please use search";
	}
else {
	($prods) = &ZOOVY::fetchproducts_by_nameref($USERNAME);
	}

my $catref = undef;

if ($ERROR) {
	}
elsif (scalar(keys %{$prods})>=10000) {
	$prods = {};
	$ERROR = "&gt;10,000 Products (Please use search)";
	}
else {
	$catref = &CATEGORY::fetchcategories($USERNAME);
	}

if ($ERROR) {
	warn ($ERROR);
	}
elsif (scalar(keys %{$catref})>=1) {
	####
	#### this merchant has categories from the windows client
	#### lets use 'em.
	####

	my $nofolder = $catref->{''};
	delete($catref->{''});

	foreach my $cat (sort %{$catref}) {
		my @result = ();
		if (defined $catref->{$cat}) {
			@result = split /,/, $catref->{$cat};
			}

	 if (scalar(@result)>0) {
      $c .= "menu.MTMAddItem(\"$cat\");\n";
      $c .= "var m$counter = null;\n";
      $c .= "m$counter = new MTMenu();\n";
      foreach my $prod (sort @result) {
			my $prodname = $prods->{$prod};
			$prodname =~ s/[^\w\:\!\. ]+//g;
			&ZOOVY::encode_ref(\$prodname);
			$c .= "m$counter.MTMAddItem(\"$prod: $prodname\", \"edit.cgi?PID=$prod\",\"text\");\n";
			delete $prods->{$prod};	# removes these so we don't look them up later.
			}
		$c .= "menu.makeLastSubmenu(m$counter);\n";
    	$counter++;
		}
	}	

#	my @result = split(',',$nofolder);
#	if (@result>1000) {
#		$c .= "menu.MTMAddItem(\"Max Exceeded - Use Search\",\"search.cgi\",\"text\");\n";
#		}
#	else {
#		foreach my $prod (sort @result) {
#			next if ($prod eq '');
# 		   my $prodname = $hash{$prod};
#			$prodname =~ s/[^\w\:\!\. ]+//g;
#			&ZOOVY::encode_ref(\$prodname);
# 	     	$c .= "menu.MTMAddItem(\"$prod: $prodname\",\"edit.cgi?PID=$prod\",\"text\");\n";
#			}
#		}
	
	}




if (scalar(keys %{$prods})>0) {
	# popular @ar with all the products
	####
	#### this merchant doens't have any categories, probably doesn't
	#### use the windows client, so either use a balanced tree, or just show them all
	####
	my @ar = sort(keys %{$prods});

	if (scalar(@ar)>30) {
		if ( scalar(@ar)>3000 ) { $elements = 30; }		# number of categories
		if ( scalar(@ar)>1000 ) { $elements = 18; }		# number of categories
		elsif ( scalar(@ar)>100 ) { $elements = 10; } 
		else { $elements = 5; }

 	 	# always add $elements-1 to the scalar so we can figure the step properly
	 	my $step = int(( (scalar(@ar)) + ($elements-1) )/$elements);

		while (scalar(@ar)>0) {
			my @result = splice(@ar,0,$step);
			my $text = $result[0]." - ".$result[scalar(@result)-1];
			if (index($text,'"')>=0) { $text =~ s/"//g; }


			$c .= "\n";
			$c .= "menu.addItem(\"$text\");\n";
			$c .= "var m$counter = null;\n";
			$c .= "m$counter = new MTMenu();\n";
	 	   foreach my $prod (@result)
     	  		{
 				my $prodname = $prods->{$prod};
				$prodname =~ s/[^\w\:\!\. ]+//g;
				&ZOOVY::encode_ref(\$prodname);
				$c .= "m$counter.addItem(\"$prod: $prodname\", \"edit.cgi?PID=$prod\",\"text\");\n";
				}
			$c .= "menu.makeLastSubmenu(m$counter);\n";
			$counter++;
			} 

		} 
	elsif (scalar(@ar)>0) {
		# person has less than 10 products, skip the categories.

	   foreach my $prod (@ar) {
 			my $prodname = $prods->{$prod};
			$prodname =~ s/[^\w\:\!\. ]+//g;
			&ZOOVY::encode_ref(\$prodname);
			$prodname = substr($prodname,0,20);

			$c .= "menu.MTMAddItem(\"$prod: $prodname\", \"edit.cgi?PID=$prod\",\"text\");\n";
			}

		} 
	}
elsif ($ERROR ne '') {
	$c .= "menu.MTMAddItem(\"$ERROR\", \"\",\"text\");\n";			
	}
else {
	$c .= "menu.MTMAddItem(\"No Products Defined\", \"\",\"text\");\n";			
	}


if (defined $GTOOLS::TAG{'<!-- MENU -->'}) {};
$GTOOLS::TAG{"<!-- MENU -->"} = $c;
$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;

my $data = qq~

<html>
<head>
<title>Zoovy!</title>
<script type="text/javascript" src="mtmcode-20061226.js">
</script>

<script type="text/javascript">
<!--

// Morten's JavaScript Tree Menu
// version 2.3.3-alpha
// Id: index.html,v 1.1 2003/08/21 19:05:40 nettrom Exp 
// http://www.treemenu.com/

// Copyright (c) 2001-2003, Morten Wang & contributors
// All rights reserved.

// This software is released under the BSD License which should accompany
// it in the file "COPYING".  If you do not have this file you can access
// the license through the WWW at http://www.treemenu.com/license.txt

// Nearly all user-configurable options are set to their default values.
// Have a look at the section "Setting options" in the installation guide
// for description of each option and their possible values.

// var MTMDefaultTarget = "text";

/******************************************************************************

* User-configurable options.                                                  *
******************************************************************************/


// Menu table width, either a pixel-value (number) or a percentage value.
var MTMTableWidth = "100%";

// Name of the frame where the menu is to appear.
var MTMenuFrame = "menu";

// variable for determining whether a sub-menu always gets a plus-sign
// regardless of whether it holds another sub-menu or not
var MTMSubsGetPlus = "Always";

// Directory of menu images/icons
var MTMenuImageDirectory = "menu-images/";

// Variables for controlling colors in the menu document.
// Regular BODY atttributes as in HTML documents.
var MTMBGColor = "#FFFFFF";
var MTMBackground = "";
var MTMTextColor = "#330066";

// color for all menu items
var MTMLinkColor = "#330066";

// Hover color, when the mouse is over a menu link
var MTMAhoverColor = "#0000FF";

// Foreground color for the tracking & clicked submenu item
var MTMTrackColor ="#FF7777";
var MTMSubExpandColor = "#663399";
var MTMSubClosedColor = "#330066";

// All options regarding the root text and it's icon
var MTMRootIcon = "menu_new_root.gif";
var MTMenuText = "Manage Products:";
var MTMRootColor = "3366CC";
var MTMRootFont = "Arial, Helvetica, sans-serif";
var MTMRootCSSize = "84%";
var MTMRootFontSize = "-1";

// Font for menu items.
var MTMenuFont = "Arial, Helvetica, sans-serif";
var MTMenuCSSize = "70%";
var MTMenuFontSize = "1";

// Variables for style sheet usage
// 'true' means use a linked style sheet.
var MTMLinkedSS = true;
var MTMSSHREF = "tree.css";

// Whether you want an open sub-menu to close automagically
// when another sub-menu is opened.  'true' means auto-close
var MTMSubsAutoClose = false;

// This variable controls how long it will take for the menu
// to appear if the tracking code in the content frame has
// failed to display the menu. Number if in tenths of a second
// (1/10) so 10 means "wait 1 second".
var MTMTimeOut = 5;

/******************************************************************************
* User-configurable list of icons.                                            *
******************************************************************************/

var MTMIconList = null;
MTMIconList = new IconList();
MTMIconList.addIcon(new MTMIcon("products.gif", "edit.cgi?VERB=CREATE", "any"));
//MTMIconList.addIcon(new MTMIcon("cogs.gif", "batchwizard", "any"));
MTMIconList.addIcon(new MTMIcon("search.gif", "search.cgi", "any"));
MTMIconList.addIcon(new MTMIcon("menu_link_txt.gif", "listall.cgi?ACTION=LISTALL", "any"));
MTMIconList.addIcon(new MTMIcon("filter.gif", "listall.cgi?ACTION=FILTER", "any"));


/******************************************************************************
* User-configurable menu.                                                     *
******************************************************************************/

// Main menu.
var menu = null;
menu = new MTMenu();

 menu.addItem("New Product","edit.cgi?VERB=CREATE","text");
// menu.addItem("Batch Channel Launcher","channel2/batchwizard.cgi","text");
 menu.addItem("List All Products","listall.cgi?ACTION=LISTALL","text");
 menu.addItem("Filter Products","listall.cgi?ACTION=FILTER","text");

 var fMenu = new MTMenu();
 fMenu.MTMAddItem("Fresh Products","listall.cgi?ACTION=FILTER&is:fresh=1","text");
 fMenu.MTMAddItem("Need Review","listall.cgi?ACTION=FILTER&is:needreview=1","text");
 fMenu.MTMAddItem("Syndication Errors","listall.cgi?ACTION=FILTER&is:haserrors=1","text");
 fMenu.MTMAddItem("Open Box","listall.cgi?ACTION=FILTER&is:openbox=1","text");
 fMenu.MTMAddItem("PreOrder","listall.cgi?ACTION=FILTER&is:preorder=1","text");
 fMenu.MTMAddItem("Discontinued","listall.cgi?ACTION=FILTER&is:discontinued=1","text");
 fMenu.MTMAddItem("Special Order","listall.cgi?ACTION=FILTER&is:specialorder=1","text");
 fMenu.MTMAddItem("Best Seller","listall.cgi?ACTION=FILTER&is:bestseller=1","text");
 fMenu.MTMAddItem("On Sale","listall.cgi?ACTION=FILTER&is:sale=1","text");
 fMenu.MTMAddItem("Can Ship Free","listall.cgi?ACTION=FILTER&is:shipfree=1","text");
 fMenu.MTMAddItem("New Arrival","listall.cgi?ACTION=FILTER&is:newarrival=1","text");
 fMenu.MTMAddItem("Clearance","listall.cgi?ACTION=FILTER&is:clearance=1","text");
 fMenu.MTMAddItem("Refurbished","listall.cgi?ACTION=FILTER&is:refurb=1","text");
 fMenu.MTMAddItem("User Defined 1","listall.cgi?ACTION=FILTER&is:user1=1","text");
 fMenu.MTMAddItem("User Defined 2","listall.cgi?ACTION=FILTER&is:user2=1","text");
 fMenu.MTMAddItem("User Defined 3","listall.cgi?ACTION=FILTER&is:user3=1","text");
 fMenu.MTMAddItem("User Defined 4","listall.cgi?ACTION=FILTER&is:user4=1","text");
 menu.makeLastSubmenu(fMenu);

 menu.addItem("Syndication","listall.cgi?ACTION=MKT","text");
 var sMenu = new MTMenu();
 sMenu.MTMAddItem("eBay Fixed Price","listall.cgi?ACTION=MKT&ebaystores:ts=1","text");
 sMenu.MTMAddItem("Amazon","listall.cgi?ACTION=MKT&amz:ts=1","text");
 sMenu.MTMAddItem("GoogleBase","listall.cgi?ACTION=MKT&gbase:ts=1","text");
 sMenu.MTMAddItem("PriceGrabber","listall.cgi?ACTION=MKT&pricegrabber:ts=1","text");
 sMenu.MTMAddItem("Shopzilla","listall.cgi?ACTION=MKT&bizrate:ts=1","text");
 sMenu.MTMAddItem("Shopping.com","listall.cgi?ACTION=MKT&dealtime:ts=1","text");
 sMenu.MTMAddItem("Overstock","listall.cgi?ACTION=MKT&overstock:ts=1","text");
 sMenu.MTMAddItem("YahooShop","listall.cgi?ACTION=MKT&yshop:ts=1","text");
 sMenu.MTMAddItem("BuySafe","listall.cgi?ACTION=MKT&buysafe:ts=1","text");
 sMenu.MTMAddItem("Bing","listall.cgi?ACTION=MKT&bing:ts=1","text");
 sMenu.MTMAddItem("Buy.com","listall.cgi?ACTION=MKT&buycom:ts=1","text");
 sMenu.MTMAddItem("NextTag","listall.cgi?ACTION=MKT&nextag:ts=1","text");
 sMenu.MTMAddItem("DOBA","listall.cgi?ACTION=MKT&doba:ts=1","text");
 menu.makeLastSubmenu(sMenu);

 menu.addItem("Search for Product","search.cgi","text");
<!-- UPGRADES -->
<!-- MENU -->


//-->
</script>
</head>
<body onload="MTMStartMenu(true);" bgcolor="#FFFFFF" text="#330066" link="#330066" vlink="#330066" alink="red">


</body>
</html>


~;

&GTOOLS::output(title=>"",html=>$data,header=>1);
$c = undef;
