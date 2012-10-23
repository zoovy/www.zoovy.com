#!/usr/bin/perl 

use strict;
use lib "/httpd/modules"; 
use CGI;
use GTOOLS;
use ZOOVY;
use ZWEBSITE;
use TODO;
use PAGE;

# create persistence
&DBINFO::db_zoovy_connect();

my ($MERCHANT,$FLAGS) = ZOOVY::authenticate("/biz",1);
$FLAGS = ",$FLAGS,";

#my ($LENGTH, $TODAY) = TRIAL::day_of_trial($MERCHANT);
#$GTOOLS::TAG{"<!-- TODAY -->"} = $TODAY;
#$GTOOLS::TAG{"<!-- LENGTH -->"} = $LENGTH;
#$GTOOLS::TAG{"<!-- REMAINING -->"} = $LENGTH - $TODAY;
if (($GTOOLS::TAG{'<!-- REMAINING -->'} > 15) || (index($FLAGS,',RENEW,')>=0)) 
	{
	$GTOOLS::TAG{"<!-- HIDE15_START -->"} = '<!-- ';
	$GTOOLS::TAG{"<!-- HIDE15_END -->"} = ' --> ';
	}

my %webdb = &ZWEBSITE::fetch_website_db($MERCHANT);

my $c = '';
my $todo = TODO->new($MERCHANT);
$todo->verify();
my $htag = '';
foreach my $task (@{$todo->list()}) {
	$htag = '';
	if ($task->{'completed'}>0) { $htag = '<strike><font color="444444">'; }
	$c .= "<tr>";
	if ($task->{'completed'}==0) { $c .= '<td><img src="/biz/images/todo.gif"></td>'; } else { $c .= "<td></td>"; }
	$c .= "<td class='menuitem'><a target=\"_top\" href=\"$task->{'link'}\" class=\"text\">$htag$task->{'name'}</a></td>";
	$c .= "</tr>";
	}
$GTOOLS::TAG{'<!-- TODOLIST -->'} = $c;


if ($FLAGS !~ /TRIAL/)
	{
	$GTOOLS::TAG{"<!-- RETURNTO -->"} = "index.cgi"; 
	} else {
	$GTOOLS::TAG{"<!-- TRIAL -->"} = "trial.cgi";
	}


my (@TIPS);
push @TIPS, "With Zoovy you can use promotions such as discounts and free shipping to increase sales, to configure a promotion visit the SETUP area.";
push @TIPS, "Use Zoovy's Marketing Channels feature to launch auctions on Ebay and Yahoo.";
push @TIPS, "With Zoovy you can use Product Options to create a single product with different sizes, colors, and more.";
push @TIPS, "If you wish you can change your username when you sign up for an account.";
push @TIPS, "Zoovy's Rules Based Shipping let you make special handling rules for special item combinations in an customers shopping cart.";
push @TIPS, "The Zoovy FastTrack service is an affordable way to get your website started ASAP.";
push @TIPS, "Zoovy's can synchronize with popular account packages such as Quickbooks.";
push @TIPS, "Make sure you download and try Zoovy's powerful order manager.";
push @TIPS, "Zoovy supports several different types of customer management for your store, visit the Website Properties in the setup are for more information.";
push @TIPS, "With the Zoovy Order Manager you can easily send targeted newletters for example only email customers who have purchased in the last 3 months";
push @TIPS, "Zoovy Developer makes it easy to integrate Zoovy into any third party website or technology you might need.";
push @TIPS, "Tired of shipping? Zoovy has partnered with several fulfillment vendors who can ship your products for you. Email support\@zoovy.com for more details.";
push @TIPS, "Make sure you download the Windows clients at <a href=\"http://www.zoovy.com/biz/downloads\">http://www.zoovy.com/biz/downloads</a>!";
push @TIPS, "You can manage your Zoovy store directly from the web, or using Zoovy's Windows software.\n";
push @TIPS, "Your Zoovy store can let you offer promotions, visit Setup and then click \"Promotions\" for more information\n";
push @TIPS, "Zoovy provides detailed sales, and traffic reports. Just click the Manage tab along the top of the screen to access them.\n";
push @TIPS, "Using Zoovy's Channels you can effectively market your products and services to a variety of different portals.\n";

#$GTOOLS::TAG{'<!-- TIP -->'} = 'Don\'t run with sharp objects.';
srand(time());
$GTOOLS::TAG{'<!-- TIP -->'} = $TIPS[(rand()*100%scalar(@TIPS))];

my $GOTO = $ZOOVY::cgiv->{'GOTO'};
my $SET = $ZOOVY::cgiv->{'SET'};
my $BACK = $ZOOVY::cgiv->{'BACK'};
$GTOOLS::TAG{"<!-- BACK -->"} = $BACK;

if ($GOTO)
	{
#	print STDERR "Set $SET\n";
#	&TRIAL::setstatus($MERCHANT,$SET,'1');
	print "Location: $GOTO\n\n";
	exit;
	}

my $ACTION = $ZOOVY::cgiv->{'ACTION'};
$GTOOLS::TAG{"<!-- MERCHANT -->"} = $MERCHANT;

##
## GEneric main menu
my ($template_file);
if ($ACTION eq "") {
	# $GTOOLS::TAG{"<!-- PROMO -->"} = "<a target=\"_blank\" href=\"/biz/reward/CSGTOC\">Click Here to Download your edition of the Common Sense Guide to Online Commerce!</a>";
	# $template_file = "trial.shtml";
	}
$template_file = 'trial-todo.shtml';


#if ($FLAGS =~ /,BASIC,/) {
#
#	if ($FLAGS =~ /,PKG=APPAREL,/i) {
#		$template_file = 'trial-pkg-APPAREL.shtml';
#		}
#	elsif ($FLAGS =~ /,PKG=MEDIA,/i) {
#		$template_file = 'trial-pkg-MEDIA.shtml';
#		}
#	elsif ($FLAGS =~ /,PKG=STORE,/i) {
#		$template_file = 'trial-pkg-STORE.shtml';
#		}
#	else {
#		$template_file = 'trial-pkg-EBAY.shtml';
#		}
#	}

my %KEY = ();
my $dbh = &DBINFO::db_zoovy_connect();
my $pstmt = "select SALESPERSON from ZUSERS where USERNAME=".$dbh->quote($MERCHANT);
my $sth = $dbh->prepare($pstmt);
$sth->execute();
my ($OWNER) = $sth->fetchrow();
&DBINFO::db_zoovy_close();
$GTOOLS::TAG{'<!-- OWNER -->'} = ucfirst($OWNER);

&GTOOLS::output(title=>'Welcome Trial User',file=>$template_file,header=>1,help=>'#50727');

# destroy persistence
&DBINFO::db_zoovy_close();

exit;
