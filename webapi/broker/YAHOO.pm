#!/usr/bin/perl -w

package YAHOO;

use XML::Parser;
use XML::Parser::EasyTree;
use LWP;
use LWP::UserAgent;
use HTTP::Request::Common;
use HTTP::Cookies;
use Data::Dumper;

use lib '/httpd/servers/modules';
use DBINFO;
use ZOOVYLITE;

sub yencode
{
	my ($DATA) = @_;

	# Encoding phase 1, replace %'s
	$DATA =~ s/\%/\%23/gs; 
	# Encoding phase 2, replace all +'s with %29
	$DATA =~ s/\+/\%29/gs;
	# Enconding phase 3, replace allspaces with +'s
	$DATA =~ s/ /\+/gs;

	# now just do the rest of the substitution.
	$DATA =~ s/\!/\%1F/gs;
	$DATA =~ s/\"/\%20/gs;
	$DATA =~ s/\#/\%21/gs;
	$DATA =~ s/\&/\%24/gs;

	$DATA =~ s/\'/\%25/gs;
	$DATA =~ s/\(/\%26/gs;
	$DATA =~ s/\)/\%27/gs;
	$DATA =~ s/\*/\%28/gs;
	$DATA =~ s/\:/\%3a/gs;
	$DATA =~ s/\//\%2f/gs;

	return($DATA);
}


sub yahoo_login {
	my ($USERNAME,$PASSWORD) = @_;

	my $agent = new LWP::UserAgent;
	my $jar = HTTP::Cookies->new;
	$agent->agent('YAM');
	$agent->cookie_jar($jar);
#	print STDERR Dumper($agent);

	my $req = new HTTP::Request('GET',"https://login.yahoo.com/?login=$USERNAME&passwd=$PASSWORD");
#	print STDERR Dumper($req);
	my $results = $agent->request($req);
	$jar->extract_cookies($results);
#	print STDERR Dumper($jar);

#	print STDERR "Login Results:\n";
#	print STDERR Dumper($results->content());

	if ($results->content() =~ m/Invalid/) {
		return;
	}

	return($agent, $jar);
}

sub post_feedback {
  my ($YAHOO_USERNAME, $YAHOO_PASSWORD, $YAHOO_ITEM, $TYPE, $WINNER) = @_;
  return(0);
}

# RETRIEVE_AUCTION
# Accepts: Yahoo username, yahoo password, Yahoo auction ID
# Returns: a hash with the following entries...
#
#	TITLE - Title of the auction
# 	QUANTITY - Number of items being sold
# 	WEIGHT - Weight as extracted from the zoovy codes embedded in the HTML of the auction
# 	FIRSTBID - First bid in dollars
# 	CURRENTLY - Current bid in dollars
# 	BIDCOUNT - Number of bids placed
# 	TIMELEFT - Seconds left until the auction ends (returns a negative number if its already closed)
# 	STARTED - Unix time the auction began (with yahoo this can change, i.e., the auction can be resubmitted)
# 	END - Unix time the auction is planned to end
# 	WINNERS - Comma separated list of space delimited records, "userid email qty price"
# 	ERROR - Desctiption of a problem if one occurred
# 	STATUS - A code for the state of the auction
#		(errors) these only are set in conjunction with a the ERROR field being populated
#			0 = no handler / fallthrough default (internal inconsistency)
#			1 = invalid username/password
#			2 = requestor not the seller
#			3 = invalid item number
#			5 = dumbass didnt' give us a username/password
#			12 = could not get bidder email address
#			13 = auction not in US Dollars
#		(pending)
#			50 = running normal auction no bidders
#			51 = running normal auction w/bidders
#			60 = running dutch auction no bidders
#			61 = running dutch auction w/bidders
#		(completed)
#			99 = closed without winners
#			100 = normal auction (closed)
#			119 = dutch auction without winners
#			120 = dutch auction (closed) (check WINNERS)
sub retrieve_auction {
	my ($USERNAME,$PASSWORD,$ITEM) = @_;

	if (($USERNAME eq '') || ($PASSWORD eq '')) {
		return {
			ERROR => "Username or password was not provided.\n",
			STATUS => 5,
		};
	}

	my $BUFFER = "";

	$ITEM =~ s/\W+//g;
	%RET = ();
	$RET{'STATUS'} = 0;

	my ($agent,$jar) = &yahoo_login($USERNAME,$PASSWORD);
	
	unless (defined($agent) && defined($jar)) {
		return {
			ERROR => "Could not log into YAHOO\n",
			STATUS => 10,
		};
	}

	my $req = new HTTP::Request('GET',"http://partners.auctions.yahoo.com/show/itemxml?aID=$ITEM");
	$jar->add_cookie_header($req);
	$results = $agent->request($req);
	
	$parse = new XML::Parser(Style=>'EasyTree');
	$tree = $parse->parse($results->content());

	my %auction = ();
	my @bidders = ();
	my $auction_found = 0;
	my $bidders_found = 0;
	
	foreach $roottaghash (@{$tree}) {
		$rootname = $roottaghash->{'name'};
		$rootcontent = $roottaghash->{'content'};
		$rootattrib = $roottaghash->{'attrib'};
		if ($rootname eq 'YahooAuctionItemInfo') {
			$root_found = 1;
			$RET{'YAHOO_VERSION'} = $rootattrib->{'Version'};
			$RET{'TIMESTAMP'} = $rootattrib->{'TimeStamp'};
			foreach $auctiontaghash (@{$rootcontent}) {
				my $name = (defined $auctiontaghash->{'name'}) ? $auctiontaghash->{'name'} : '' ;
				my $attrib = $auctiontaghash->{'attrib'};
				if ($name eq 'Summary') {
					$RET{'ID'} = $attrib->{'Aid'};
					if ($attrib->{'SellerID'} ne $USERNAME) {
						return {
							ERROR => "YAHOO auction does not recognize $USERNAME as the authorized seller fo $ITEM.\n",
							STATUS => 2,
						};
					}
					$RET{'USERNAME'} = $attrib->{'SellerID'};
					if ($attrib->{'Currency'} ne "USD") {
						return {
							ERROR => "YAHOO auction must be in US Dollars.\n",
							STATUS => 13,
						};
					}
					$RET{'CURRENTLY'} = $attrib->{'CurrentBidAmount'};
					$RET{'RESERVE'} = $attrib->{'ReservePrice'};
					$RET{'BUYNOW'} = $attrib->{'BuyPrice'};
					$RET{'QUANTITY'} = $attrib->{'Quantity'};
					$RET{'STARTED'} = $attrib->{'StartTime'};
					$RET{'END'} = $attrib->{'EndTime'};
					$RET{'TIMELEFT'} = $RET{'END'} - $RET{'TIMESTAMP'};
				}
				if ($name eq 'Bid') {
					$bidders_found++;
					my %bidder = ();
					$bidder{'username'} = $attrib->{'UserID'};
					$bidder{'bid'} = $attrib->{'BidAmount'};
#					$bidder{'comment'} = $attrib->{'Comment'};
					push @bidders, \%bidder;
				}
				if ($name eq 'Description') {
					$RET{'CONTENTS'} = $auctiontaghash->{'content'}[0]{'content'};#The weird reference to a reference thing is happeing because they're sticking a CDATA inside a tag
				}
			}
		}
		if ($rootname eq 'YahooAuctionAck') {
			return {
				ERROR => "YAHOO could not find auction.\n",
				STATUS => 3,
			};
		}
	}
	
	if ($RET{'CONTENTS'} =~ /<[Zz][Oo][Oo][Vv][Yy]>.*?<!--(.*?)-->.*?<\/[Zz][Oo][Oo][Vv][Yy]>/s) {
		my %ZB = &ZOOVYLITE::safe_attrib_handler($1);
		if ($ZB{'zoovy:prod_name'}) { $RET{'TITLE'} = $ZB{'zoovy:prod_name'}; }
		if ($ZB{'zoovy:base_weight'}) { $RET{'WEIGHT'} = $ZB{'zoovy:base_weight'}; }
		# copy the hash into the RETURN hash!
		foreach $c (keys %ZB) {
			$RET{$c} = $ZB{$c};
		}
	}

	$RET{'BIDCOUNT'} = scalar(@bidders);

	my ($closed) = ($RET{'TIMELEFT'} < 0) ? 1 : 0 ;
	my ($dutch) = ($RET{'QUANTITY'} > 1) ? 1 : 0 ;

	my @winners = ();
	if ($closed) { # Only try to get the winners list if the auction has closed
		$req = new HTTP::Request('GET',"http://page.auctions.yahoo.com/auction/$RET{'ID'}");
		$jar->add_cookie_header($req);
		$results = $agent->request($req);
		foreach $bidder (@bidders) {
			my $userid = $bidder->{'userid'};
			my ($email, $qty);
			if ($results->content() =~ m/$bidder(.*?)[Hh][Rr][Ee][Ff]=\"mailto\:(.+?)\".*?\<[Tt][Dd]\>(\d+)\<\/[Tt][Dd]\><[Tt][Dd]\>\$([\d+\.\,]+)\<\/[Tt][Dd]\>/) {
				$chunk = $1;
				$email = $2;
				$qty = $3;
				$qty =~ s/\,//g;
				$price = $4;
				$price =~ s/\,//g;
				if ($chunk =~ m/Remove/) { #Only auction winners have the Remove from winners list text in them
					push @winners, "$bidder $email $qty $price,";
				}
				else {
					# When we have a list of LOOOO-hoo-hoo-SERRRRRRs, we'll load it up here!
				}
				#$RET{'BIDDEREMAIL'} .= "$email=$qty,";
				#$RET{'BIDDERS'} .= "$bidder=$email,";
			}
			else {
				return {
					%RET,
					ERROR => "Could not fetch bidder email address\n",
					STATUS => 12,
				};
			}
		}
	}

	$RET{'WINNERS'} = '';
	foreach (@winners) {
		$RET{'WINNERS'} .= "$_,";
	}
	chop $RET{'WINNERS'};
	my $num_winners = scalar(@winners);
	my $num_bidders = scalar(@bidders);
	
	if ($closed) {
		if ($num_winners) {
			if ($dutch) { $RET{'STATUS'} = 119; }
			else { $RET{'STATUS'} = 99; }
		}
		else {
			if ($dutch) { $RET{'STATUS'} = 120; }
			else { $RET{'STATUS'} = 100; }
		}
	}
	else {
		if ($num_bidders) { 
			if ($dutch) { $RET{'STATUS'} = 61; }
			else { $RET{'STATUS'} = 51; }
		}
		else {
			if ($dutch) { $RET{'STATUS'} = 60; }
			else { $RET{'STATUS'} = 50; }
		}
	}


	return \%RET;

}

#  This is a function to import external auctions directly into the MONITOR_YAHOO table
sub save_external_auction {
	($ZOOVY_USERNAME,$YAHOO_ID,$YAHOO_USERNAME,$YAHOO_PASSWORD,$TITLE) = @_;
	my $dbh = DBI->connect($DBINFO::MYSQL_DSN,$DBINFO::MYSQL_USER,$DBINFO::MYSQL_PASS); 
	$pstmt = "insert into MONITOR_YAHOO values(0,'$ZOOVY_USERNAME',";
	$pstmt .= $dbh->quote($YAHOO_ID).",";
	$pstmt .= $dbh->quote($YAHOO_USERNAME).",";
	$pstmt .= $dbh->quote($YAHOO_PASSWORD).",";
	$pstmt .= $dbh->quote($TITLE).",";
	$pstmt .= "now(),now(),0,0,'',0,0,0)";
	$sth = $dbh->prepare($pstmt);
	$rv = $sth->execute;
	$dbh->disconnect();
	return (defined($rv) ? 1 : 0 );
}

## parameters: SGML buffer, SSLIFY basically means "PREVIEW"
##             so pass it if you need it.
sub make_pretty {
	($BUFFER,$SSLIFY,$vars) = @_; 
	
	%{$vars} = ZOOVYLITE::buffer_to_hash($BUFFER);
	
	# do a bit of data massaging:
	# apparently yahoo doesn't like https pictures!
	if ($SSLIFY) {
		$vars->{'zoovy:prod_image1'} =~ s/^http/https/i;
		$vars->{'zoovy:prod_image2'} =~ s/^http/https/i;
		$vars->{'zoovy:prod_image3'} =~ s/^http/https/i;
	}
	else {
		$vars->{'zoovy:prod_image1'} =~ s/^https/http/i;
		$vars->{'zoovy:prod_image2'} =~ s/^https/http/i;
		$vars->{'zoovy:prod_image3'} =~ s/^https/http/i;
	}
	
	# build a custom tag of city and state
	$vars->{'zoovy:citystate'} = $vars->{'zoovy:city'}.", ".$vars->{'zoovy:state'};
	#  print "CITYSTATE: ".$vars->{'zoovy:citystate'}."\n";
	
	# do a bit of data validation so we don't accidentially fail
	$vars->{'yahoo:startprice'} += 0;
	if ($vars->{'yahoo:startprice'} <= 0) { $vars->{'yahoo:startprice'} += "0.01"; }
	
	# fit the title into the length!
	$vars->{'yahoo:title'} = substr($vars->{'yahoo:title'},0,45);
	
	# go ahead and make the listing look pretty!
	$pretty = "";
	$pretty .= "<center><table width='630'><tr><td>";
	$pretty .= "<table bgcolor='EFEFEF' width='100%'><tr><td valign='top'>";
	$pretty .= "<font face='Arial'>";
	$pretty .= "<center><font size=3><b>".$vars->{'yahoo:title'}."</b></font></center><br>";
	
	$pretty .= "<center><table width='85%'><Tr><td><font face='Arial'>";
	$pretty .= ZOOVYLITE::text_to_html($vars->{'yahoo:description'}); 
	$pretty .= "</font></td></tr></table>";
	
	if ($vars->{'zoovy:prod_image2'}) { $pretty .= "<center><img src='".$vars->{'zoovy:prod_image2'}."'></center>"; }
	if ($vars->{'zoovy:prod_image2'}) { $pretty .= "<center><img src='".$vars->{'zoovy:prod_image3'}."'></center>"; }
	$pretty .= "</table>";
	
	$pretty .= "<br><br>";
	# begin company logo table!	 
	if ($vars->{'zoovy:company_logo'}) { $pretty .= "<table><tr><td>"; }
	
	$pretty .= "<font face='Arial'>";
	if ($vars->{'zoovy:website_url'}) {
		$pretty .= "<B><a href='".$vars->{'zoovy:website_url'}."'>".$vars->{'zoovy:company_name'}."</a></B>";
	}
	else {
		$pretty .= "<B>".$vars->{'zoovy:company_name'}."</B>";
	}
	$pretty .= "<BR>";	
	$pretty .= $vars->{'zoovy:address1'}."<br>"; 
	if ($vars->{'zoovy:address2'}) {
		$pretty .= $vars->{'zoovy:address2'}."<br>";
	}
	$pretty .= $vars->{'zoovy:citystate'}." ".$vars->{'zoovy:zip'}."<br>"; 
	$pretty .= $vars->{'zoovy:support_email'}."<br>"; 
	$pretty .= "</font>";
	
	# end of company_logo table
	if ($vars->{'zoovy:company_logo'}) {
		$pretty .= "</td><td><img src='".$vars->{'zoovy:company_logo'}."'></td></tr></table>";
	}
	$pretty .= "<br><br>";
	if ($vars->{'zoovy:return_policy'}) {
		$pretty .= "<font face='Arial'><b>RETURN POLICY:</b><br>".$vars->{'zoovy:return_policy'}."<br>";
	}
	
	# Zoovy Co-Brand
	$pretty .= "<br><center><table cellpadding='4'><tr><td colspan='2'><hr></td></tr>";
	$pretty .= "<tr><td><a href='http://www.zoovy.com'>";
	if ($SSLIFY) {
		$pretty .= "<img border='0' src='https://www.zoovy.com/images/poweredby.gif'>";
	}
	else {
		$pretty .= "<img border='0' src='http://www.zoovy.com/images/poweredby.gif'>";
	}
	
	$pretty .= "</a></td><td><font face='Arial' size='2'>";
	$pretty .= "This Auction will be closed using Zoovy Auction processing technology. ";
	$pretty .= "You will be given the opportunity to purchase additional products from ";
	if ($vars->{'zoovy:website_url'}) { $pretty .= "<a href='".$vars->{'zoovy:website_url'}."'>".$vars->{'zoovy:company_name'}."</a>"; }
	else { $pretty .= $vars->{'zoovy:company_name'}; }
	$pretty .= ". Winners of multiple auctions will be able to save shipping. Serious bidders only, automatic positive feedback will be left for all auctions completed within 72 hours of closing, negative feedback will be posted AUTOMATICALLY after 2 weeks.<br></font></td></table></center>";
	
	if (length($vars->{'zoovy:shipping_explanation'})>4) {
		$pretty .= "<center><hr><table width='98%' border='0'><tr><td>";
		$pretty .= "<font face='Arial'><b>Shipping Policy:</b><br>";
		$pretty .= ZOOVYLITE::text_to_html($vars->{'zoovy:shipping_explanation'});
		$pretty .= "</tr></td></table></center>";
	}
	
	if (length($vars->{'zoovy:payment_explanation'})>4) {
		$pretty .= "<center><hr><table border='0' width='98%'><tr><td>";
		$pretty .= "<font face='Arial'><b>Accepted Payment:</b><br>";
		$pretty .= ZOOVYLITE::text_to_html($vars->{'zoovy:payment_explanation'});
		$pretty .= "</tr></td></table></center>";
	} 
	
	$pretty .= "</font></td></tr></table><br>";
	
	# Please visit our website at ..
	if ($vars->{'zoovy:website_url'}) { 
		$pretty .= "<br><font face='Helevetica, Arial' size='4'><center><a href='".$vars->{'zoovy:website_url'}."'>Please visit our website at ".$vars->{'zoovy:website_url'}."</a></center></font><br>";
	}
	
	$pretty .= "</td></tr></table></center>";
	
	return($pretty);
}

######################################################################################################

sub fetch_running_auctions {
	($USERNAME) = @_;

	my @ar = ();
	my $dbh = DBI->connect($DBINFO::MYSQL_DSN,$DBINFO::MYSQL_USER,$DBINFO::MYSQL_PASS); 
	
	$pstmt = "select ID, CREATED, YAHOO_ID, TITLE, NEXTCHECK, SUBSCRIPTION_ID, TRIGGER, HIGHBIDDER, ";
	$pstmt .= " LASTPRICE, REOCCUR from MONITOR_YAHOO where USERNAME=".$dbh->quote($USERNAME);
	$sth = $dbh->prepare($pstmt);
	$sth->execute;
	
	while (@row = $sth->fetchrow()) {
		$title = $row[3];
		$title =~ s/,//s; # commas fuck this shit up!
		push @ar, "$row[0],$row[1],$row[2],$title,$row[4],$row[5],$row[6],$row[7],$row[8],$row[9]";
	}
	
	return(@ar);  
}


1;