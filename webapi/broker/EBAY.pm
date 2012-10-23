package EBAY;

use lib "/httpd/servers/modules";
use DBINFO;
use Data::Dumper;
use LWP;
use HTTP::Request::Common;
use HTTP::Cookies;
use LWP::UserAgent;
use lib "/httpd/modules";
use ZTOOLKIT;
use GT;
use Date::Calc;
use Time::ParseDate;

$REALLYCHECKAUCTIONS = "1";


## purpose pass an auction id, get a URL to the auction
sub lookup_url
{
	my ($id) = @_;
	return('http://cgi.ebay.com/aw-cgi/eBayISAPI.dll?MfcISAPICommand=ViewItem&item='.$id);
}



##
## resolve_username
## turns an ebay_id into an email
## returns: undef on error
sub resolve_username
{
  my ($REQUESTOR, $REQUESTOR_PASS, $REQUESTEE, $ID) = @_;


## fetch user URL:
## http://contact.ebay.com/aw-cgi/eBayISAPI.dll?ReturnUserEmail&requested=phdockmaster@aol.com&iid=1115361687&userid=drollens@optonline.net&pass=2962

	my $agent = new LWP::UserAgent;
	$agent->agent('Groovy/1.0');
	my $jar = HTTP::Cookies->new;
	$agent->cookie_jar($jar);
	
	# we need to fetch the original auction page for the following reasons:
	# Check and see if its a DUTCH or NORMAL auction so we can make the right results request
	# Download any and all Auction Info that is related to the auction.
	# Get the title (its easier to get it here!)
	$contact_url = "http://contact.ebay.com/aw-cgi/eBayISAPI.dll?ReturnUserEmail&requested=$REQUESTEE&iid=$ID&userid=$REQUESTOR&pass=$REQUESTOR_PASS";
	$result = $agent->request(GET $contact_url);
	$jar->extract_cookies($result);

	$content = $result->content;

	if ($content =~ /<h2>This functionality is currently unavailable<\/h2>/)
		{
		print "$content\n\n";
		print "Ebay reports that the resolve_username is currently unavailable. So i'm pretty much stuck.\n";
		print "Try: $contact_url\n";
		exit(0);
		}

	open F, ">/tmp/ebay.resolve.output";
	print F $content;
	close F;

	my $email = undef;

	if ($content =~ /mailto:(.*?)"/) 
		{ 
		print "Found email in stage1: $1\n";
		$email = $1; 
		}
	
	# ?? 
	if (!defined($email))
		{
		# should never be reached?? older style code
		print "Could not determine winning bidder email address!\n";
		exit;
		# <tr><th>User ID History</th><th>Effective Date</th><th>End Date</th></tr><TR>
		# <td>phdockmaster@aol.com</td><td>Sunday, Aug 13, 2000</td><td>Present</td></TR>
		$chunk = &ZTOOLKIT::getafter(\$content,"<th>End Date</th></tr>",50,1);
		if ($DEBUG) { print "resolve chunk is---> $chunk\n"; }
		if ($chunk =~ /<td>(.*?)<\/td>/) { $email = $1; }
		}

  return($email);
}


#<form method="post" action="http://cgi2.ebay.com/aw-cgi/eBayISAPI.dll">
#<input type="hidden" name="MfcISAPICommand" value="LeaveFeedback">
#<input type="text" name="userid" size="30" value="">
#<input type="password" name="pass" size="30">
#<input type="text" name="otheruserid" size="40">
#<input type="text" name="itemno" size="40">
#<input type="radio" name="which" value="positive">positive
#<input type="radio" name="which" value="negative">negative
#<input type="radio" name="which" value="neutral">neutral
#<input type="text" name="comment" size="80" maxlength="80"><br>
#<input type="submit" value="leave comment">
#</form>	

sub post_feedback {
  my ($EBAY_USERNAME, $EBAY_PASSWORD, $EBAY_ITEM, $TYPE, $WINNER) = @_;
  return(0);	
}

# RETRIEVE_AUCTION
# Accepts: Ebay username, ebay password, ebay auction ID
# Returns: a hash with the following entries...
#
#	 TITLE - Title of the auction
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
#	ZOOVY - the contents of the <ZOOVY><!--(.*?)--!></ZOOVY> tag
#
#		(errors) these only are set in conjunction with a the ERROR field being populated
#			0 = no handler / fallthrough default (internal inconsistency)
#			1 = invalid username/password
#			2 = requestor not the seller
#			3 = invalid item number
#			4 = could not obtain title
#			5 = dumbass didnt' give us a username/password
#			6 = Ebay says invalid item (stage1)
#			7 = Ebay says invalid item (stage2)
#			8 = internal error stage 1
#			9 = internal error stage 2
#			10 = could not obtain the title (stage 1)
#			12 = could not get bidder email address
#			13 = auction not in US Dollars
#			14 = internal error, dutch/non-dutch auction determination
#			15 = ebay down?? (they reported an internal server error)
#			16 = ebay returned no contents
#			17 = ebay down for maintenance
#			18 = ebay current down (tech support notified)
#			19 = cannot support eBay stores
#		(pending)
#			50 = running normal auction no bidders
#			51 = running normal auction w/bidders
#			60 = running dutch auction no bidders
#			61 = running dutch auction w/bidders
#		(completed)
#			98	= closed did not meet reserve
#			99 = closed without winners
#			100 = normal auction (closed)
#			119 = dutch auction without winners
#			120 = dutch auction (closed)
#		(critical error)
#			255 = could not verify adult
sub retrieve_auction 
	{

	my ($USERNAME,$PASSWORD,$ITEM) = @_;
	print "Attempting to retrieve_auction $USERNAME $PASSWORD $ITEM\n";
	%RET = ();
	$RET{'STATUS'} = 0;
	
	if ($USERNAME eq "") 
		{ return (STATUS=>1,ERROR=>"Username was not submitted, EBAY requires a valid username and password\n"); }

	# to submit this form:
	#<form method="POST" action="http://cgi3.ebay.com/aw-cgi/eBayISAPI.dll">
	#<input type="hidden" name="MfcISAPICommand" value="ViewBidderWithEmails">
	#<input type="hidden" name="item" value="1209285704">
	#<input type="hidden" name="acceptcookie" value="1">
	#<input type="hidden" name="ed" value="0"> NOTE: DO NOT FUCK WITH ED. no clue what it is, but it breaks things.
	#<input type="text" name="userid" size="30">
	#<input type="password" name="pass" size="30">
	#<input type="submit" value="Submit">
	#</form>
	
	$debug = 0;
	my $BUFFER = "";
	
	$ITEM =~ s/\W+//g;
	
	my $agent = new LWP::UserAgent;
	$agent->agent('Zoovy-is-Groovy/1.0');
	$agent->cookie_jar(HTTP::Cookies->new(autosave => 1));
	
	# we need to fetch the original auction page for the following reasons:
	# Check and see if its a DUTCH or NORMAL auction so we can make the right results request
	# Download any and all Auction Info that is related to the auction.
	# Get the title (its easier to get it here!)
	print "FETCHING: http://cgi.ebay.com/aw-cgi/eBayISAPI.dll?ViewItem&item=$ITEM\n";
	$result = $agent->request(GET "http://cgi.ebay.com/aw-cgi/eBayISAPI.dll?ViewItem&item=$ITEM");

	$RET{'STAGE1'} = $result->content;
	open F, ">/tmp/ebay.monitor.stage1";
	print F $RET{'STAGE1'};
	close F;

	if ($RET{'STAGE1'} =~ /This function is currently unavailable/)
		{
		return (STATUS=>18,ERROR=>"Ebay is currently down (This function currently unavailable)");
		}

	if (substr($RET{'STAGE1'},0,200) =~ /AdultLoginShow/)
		{
		$agent = new LWP::UserAgent;
		$agent->agent('Mozilla/4.76 [en] (Win98; U)');
		my $jar = HTTP::Cookies->new;
		$jar->extract_cookies($result);
		$agent->cookie_jar($jar);

#		open F, ">step1.adult";
#		print F Dumper($result);
#		close F;


#		$result = $agent->request(GET 'http://cgi6.ebay.com/aw-cgi/eBayISAPI.dll?ViewBids&item='.$ITEM);
#		$jar->extract_cookies($result);
#		$agent->cookie_jar($jar);
#		open F, ">step1";
#		print F Dumper($result);
#		close F;

#		$result = $agent->request(GET 'http://cgi3.ebay.com/aw-cgi/eBayISAPI.dll?SignIn&pUserId=&pNextPage='.$mfccommand.'&pageType=271&pa1=off&i1='.$ITEM.'&i2=0&i3=0&i4=0');
#		$jar->extract_cookies($result);
#		$agent->cookie_jar($jar);
#		open F, ">step2";
#		print F Dumper($result);
#		close F;

		$result = $agent->request(POST "http://cgi.ebay.com/aw-cgi/eBayISAPI.dll",
			Referer=>'http://cgi3.ebay.com/aw-cgi/eBayISAPI.dll?SignIn&pUserID=&pNextPage=AdultLoginShow&pageType=271&pa1=off&i1='.$ITEM.'&i2=0&i3=0&i4=0',
			Content_Type   => 'application/x-www-urlencoded',
			Content =>[ 
		'MfcISAPICommand'=>'SignInWelcome',
		'siteid'=>'0',
		'co_partnerId'=>'2',
		'UsingSSL'=>'0',
		'ru'=>'',
		'pp'=>'',
		'pa1'=>'off',
		'pa2'=>'',
		'pa3'=>'',
		'pa4'=>'',
		'pa5'=>'',
		'pa6'=>'',
		'pa7'=>'',
		'pa8'=>'',
		'pa9'=>'',
		'pa10'=>'',
		'i1'=>$ITEM, 
		'i2'=>'0', 
		'i3'=>'0', 
		'i4'=>'0', 
		'i5'=>'-1', 
		'i6'=>'-1', 
		'i7'=>'-1', 
		'i8'=>'-1', 
		'i9'=>'-1', 
		'i10'=>'-1', 
		'i11'=>'-1', 
		'pNextPage'=>'AdultLoginShow', 
		'pageType'=>'271',
		'userid'=>$USERNAME,
		'pass'=>$PASSWORD,
		'keepMeSignInOption'=>'1',
	]);

#	print Dumper($result);
#	print "at that point..\n";
#	exit;


	if ($result->as_string() =~ /Location: (.*?)\n/)
		{
		$thisurl = $1;
		$result = $agent->request(GET $thisurl);
		$jar->extract_cookies($result);
		$agent->cookie_jar($jar);

		use lib "/httpd/servers/modules";
		use ZFORMHACK;
		%hash = &ZFORMHACK::ripform($result->content());
		$jar->set_cookie(1,'keepmesignin','in','/','.ebay.com','80',0,0,100,0);
		$jar->set_cookie(1,'ebaysignin','in','/','.ebay.com','80',0,0,100,0);
		$result = $agent->request(GET 'http://cgi3.ebay.com/aw-cgi/eBayISAPI.dll?MfcISAPICommand='.$hash{'MfcISAPICommand'}.'&userid='.$hash{'userid'}.'&pass='.$hash{'pass'}.'&de=off&item='.$hash{'item'}.'&acceptcookie=0&ed=0&xml=0');

#		print Dumper($result);		
#		print "done dumping..\n";
#		exit;
		$RET{'STAGE1'} = $result->content();

	
		} else {
			die("Missed Cookie Redirect!! (those bastards!)\n");
		}

		} ### END OF ADULT LOGIN
	

#	# catch an adult login
#	if (substr($RET{'STAGE1'},0,60) =~ /<HTML><HEAD><TITLE>eBay Adult Login<\/TITLE><\/HEAD>/)
#		{
#		print "Found adult!\n";
#		$result = $agent->request(GET "http://cgi4.ebay.com/aw-cgi/eBayISAPI.dll?MfcISAPICommand=AdultLogin\&userid=$USERNAME\&password=$PASSWORD");
#		# print $result->content();
#
#		$result = $agent->request(GET "http://cgi.ebay.com/aw-cgi/eBayISAPI.dll?ViewItem&item=$ITEM");	
#		open F, ">/tmp/ebay.adult.error.".time();
#		print F $result->content();
#		close F;
#		$RET{'STAGE1'} = $result->content;
#		} else {
#
#			# only do an eBay stores check if we don't have an adult item.
#			# Note: eBay store check looks for the word "currently" to be missing which is pretty lame but I can't
#			# find a better way.
#			if ($RET{'STAGE1'} !~ /Currently/) 
#				{
#				print "Found eBay store.\n";
#				return(STATUS=>19,ERROR=>"Cannot support eBay stores.");
#				} else {
#				print "Probably not an eBay stores.\n";
#				}
#		}
#
#
#	if (substr($RET{'STAGE1'},0,60) =~ /<HTML><HEAD><TITLE>eBay Adult Login<\/TITLE><\/HEAD>/)
#		{ 
#		die("i think i'll die before I return 255 error [should this have happened??]"); 
#		return (STATUS=>255,ERROR=>'Could not login as an adult. Critical Error.'); 
#		}

	if ($RET{'STAGE1'} =~ /\<TITLE\>eBay Input Error\<\/TITLE\>/s) 
		{ return (STATUS=>8,ERROR=>"Ebay says INPUT ERROR?? (something really bad happened in stage1!)"); }

	if ($RET{'STAGE1'} =~ /\<TITLE\>(.*?)\<\/TITLE\>/si) {
		$RET{"TITLE"} = $1;
		$RET{"TITLE"} =~ s/.*?\(.*?\) - (.*?)/$1/is;
		$RET{'TITLE'} =~ s/\n//g;
	}
	else {
		return(STATUS=>10,ERROR=>"Could not obtain title of Auction in stage1 processing!\n");
	}

	if ($RET{'STAGE1'} =~ /\<font color\=\"red\"\>Auction has ended.\<\/font\>/)
		{
		$ISOVER = 1;
		} else {
		$ISOVER = 0;
		}

	# Now lets check for a custom Zoovy buffer!
	# Human readable <zoovy><!--(.*)--></zoovy>
	if ($RET{'STAGE1'} =~ /<[Zz][Oo][Oo][Vv][Yy]>[\s]*<!--(.*?)-->[\s]*<\/[Zz][Oo][Oo][Vv][Yy]>/s) {
		$RET{'ZOOVY'} = $1; 
		my %ZB = &attrib_handler($RET{'ZOOVY'});
		# Special Cases!
		if ($ZB{'zoovy:prod_name'}) { $RET{'TITLE'} = $ZB{'zoovy:prod_name'}; }
		if ($ZB{'zoovy:base_weight'}) { $RET{'WEIGHT'} = $ZB{'zoovy:base_weight'}; }
		# copy the hash into the RETURN hash!
		foreach $c (keys %ZB) { $RET{$c} = $ZB{$c}; }
	}

	if (&ZTOOLKIT::getafter(\$RET{'STAGE1'},'Quantity',75) =~ /<b>(\d+)<\/b></s) {
		$RET{"QUANTITY"} = $1;
	} else {
		print $RET{'STAGE1'}."\n";
		if ($RET{'STAGE1'} =~ /Invalid Item/)
			{
			return(STATUS=>3,ERROR=>"EBAY reports $ITEM as an invalid auction\n");
			}
		die ("Missed Quantity for sale???");
	}
	if ($RET{"QUANTITY"}>1) { $mfccommand = 'ViewBidDutchHighBidderEmails'; }
	else { $mfccommand = 'ViewBidderWithEmails'; }
		

#	if ($ISOVER == 0) { return(STATUS=>50); }

	## Phase two: at this point the $mfccommand should be set to either ViewBidderWithEmails or ViewBidDutchHighBidderEmails
#	print "Attempting:\nhttp://cgi3.ebay.com/aw-cgi/eBayISAPI.dll?MfcISAPICommand=$mfccommand&item=$ITEM&acceptcookie=1&ed=0&userid=$USERNAME&password=$PASSWORD&de=on\n";
#	$result = $agent->request(POST "http://cgi3.ebay.com/aw-cgi/eBayISAPI.dll",
#	Content_Type   => 'application/x-www-urlencoded',
#	Content =>[ 'MfcISAPICommand'=>$mfccommand, 'item'=>$ITEM, 'acceptcookie'=>'1', 'ed'=>'0', 'userid'=>$USERNAME, 'password'=>$PASSWORD, 'de'=>'on']);

$agent = new LWP::UserAgent;
$agent->agent('Mozilla/4.76 [en] (Win98; U)');
my $jar = HTTP::Cookies->new;
$agent->cookie_jar($jar);

$result = $agent->request(GET 'http://cgi6.ebay.com/aw-cgi/eBayISAPI.dll?ViewBids&item='.$ITEM);
$jar->extract_cookies($result);
$agent->cookie_jar($jar);
open F, ">step1";
print F Dumper($result);
close F;

$result = $agent->request(GET 'http://cgi3.ebay.com/aw-cgi/eBayISAPI.dll?SignIn&pUserId=&pNextPage='.$mfccommand.'&pageType=271&pa1=off&i1='.$ITEM.'&i2=0&i3=0&i4=0');
$jar->extract_cookies($result);
$agent->cookie_jar($jar);
open F, ">step2";
print F Dumper($result);
close F;

$result = $agent->request(POST "http://cgi.ebay.com/aw-cgi/eBayISAPI.dll",
	Referer=>'http://cgi3.ebay.com/aw-cgi/eBayISAPI.dll?SignIn&pUserID=&pNextPage='.$mfccommand.'&pageType=271&pa1=off&i1='.$ITEM.'&i2=0&i3=0&i4=0',
	Content_Type   => 'application/x-www-urlencoded',
	Content =>[ 
		'MfcISAPICommand'=>'SignInWelcome',
		'siteid'=>'0',
		'co_partnerId'=>'2',
		'UsingSSL'=>'0',
		'ru'=>'',
		'pp'=>'',
		'pa1'=>'off',
		'pa2'=>'',
		'pa3'=>'',
		'pa4'=>'',
		'pa5'=>'',
		'pa6'=>'',
		'pa7'=>'',
		'pa8'=>'',
		'pa9'=>'',
		'pa10'=>'',
		'i1'=>$ITEM, 
		'i2'=>'0', 
		'i3'=>'0', 
		'i4'=>'0', 
		'i5'=>'-1', 
		'i6'=>'-1', 
		'i7'=>'-1', 
		'i8'=>'-1', 
		'i9'=>'-1', 
		'i10'=>'-1', 
		'i11'=>'-1', 
		'pNextPage'=>$mfccommand, 
		'pageType'=>'271',
		'userid'=>$USERNAME,
		'pass'=>$PASSWORD,
		'keepMeSignInOption'=>'1',
	]);


if ($result->as_string() =~ /Location: (.*?)\n/)
	{
	$thisurl = $1;
	$result = $agent->request(GET $thisurl);
	$jar->extract_cookies($result);
	$agent->cookie_jar($jar);

	use lib "/httpd/servers/modules";
	use ZFORMHACK;
	%hash = &ZFORMHACK::ripform($result->content());
	$jar->set_cookie(1,'keepmesignin','in','/','.ebay.com','80',0,0,100,0);
	$jar->set_cookie(1,'ebaysignin','in','/','.ebay.com','80',0,0,100,0);
	$result = $agent->request(GET 'http://cgi3.ebay.com/aw-cgi/eBayISAPI.dll?MfcISAPICommand='.$hash{'MfcISAPICommand'}.'&userid='.$hash{'userid'}.'&pass='.$hash{'pass'}.'&de=off&item='.$hash{'item'}.'&acceptcookie=0&ed=0&xml=0');

	} else {
		die("Missed Cookie Redirect!! (those bastards!)\n");
	}



	
	$RET{'CONTENTS'} = $result->content;
	print $RET{'CONTENTS'};

	## For Debug!
	open F, ">/tmp/ebay.monitor.contents";
	print F $RET{'CONTENTS'}."\n";
	close F;

	if ($RET{'CONTENTS'} eq '') { return(STATUS=>16,ERROR => "Ebay returned no contents. [check /tmp/ebay.monitor.contents]\n"); }
	if ($RET{'CONTENTS'} =~ /\<h2\>An Internal Error has occurred\<\/h2\>/) { return(STATUS=>15,ERROR => "Ebay reports an Internal Error has occured! [check /tmp/ebay.monitor.contents]\n"); }


	$RET{'EBAY_ID'} = $ITEM;
	if ($RET{'CONTENTS'} =~ /User ID<\/a> or Password invalid/) 
		{ return(STATUS=>1,ERROR => "EBAY reports unable to log in as $USERNAME with a password of $PASSWORD\n"); }
	
	if ($RET{'CONTENTS'} =~ /Error: Requestor not the seller/) 
		{ return(STATUS=>2,ERROR=>"EBAY does not recognize $USERNAME as the authorized seller of $ITEM\n"); }

		if ($RET{'CONTENTS'} =~ /\<h2\>Unknown Item\<\/h2\>/) 
			{ return(STATUS=>3,ERROR=>"EBAY reports $ITEM as an invalid auction\n"); }

		if ($RET{'CONTENTS'} =~ /eBay '.*?' - Invalid Item/) 
			{ return(STATUS=>6,ERROR =>"EBAY reports $ITEM as an invalid auction\n"); }

		if ($RET{'CONTENTS'} =~ /\<TITLE\>eBay Input Error\<\/TITLE\>/)
			{ return(STATUS=>7,ERROR=>"EBAY reports an input error [check /tmp/ebay.monitor.contents]\n"); }

		if ($RET{'CONTENTS'} =~ /pages\.ebay\.com\/unavailable\/site\.html/)
			{ return(STATUS=>17,ERROR=>"EBAY is down [must be friday am]\n"); }


		# at this point we've determined that we're probably looking at the right page  (no errors!)
		my $firstbid = &ZTOOLKIT::getafter(\$RET{'CONTENTS'},'>First bid<',75);
		if (!defined($firstbid)) { $firstbid = ''; }
		if ($firstbid =~ />\$([\d\.]+)</s) {
			$RET{"FIRSTBID"} = $1;
		}

# Broken on 6/7/01
#	if (&ZTOOLKIT::getafter(\$RET{'CONTENTS'},'>Currently<',75) =~ />\$([\d\.]+)</s) 
#		{
#		$RET{"CURRENTLY"} = $1;
#		} else {
#		print "ERROR: Could not determine current price.\n";
#		exit;
#		}

	if ($RET{'CONTENTS'} =~ /\<font size\=\"2\"\>[\n]?Currently[\n]?\<\/font\>.*?\>\$(.*?)\<\//s)
		{
		print ("Currently is: $1"); 
		$RET{'CURRENTLY'} = $1;
		} else {

		# Fucking eBay started inserting comments which make the line lengths variable
		$RET{'CONTENTS'} =~ s/(\<\!\-\-.*?\-\-\>)//sg;

		$c = &ZTOOLKIT::getafter(\$RET{'CONTENTS'},'Currently',75)."\n";
		print "CURRENTLY: ".$c;
		# print $RET{'CONTENTS'};
		# Lets try again [what can it break??]
		if ($c =~ /\<b\>\$(.*?)\<\/b\>/s)
			{		
			$RET{'CURRENTLY'} = $1;
			} else {
			print "Dumping: $RET{'CONTENTS'}\n";
			die ("Could not determine Current price [$1] - tried twice");
			}
		}

	if (&ZTOOLKIT::getafter(\$RET{'CONTENTS'},'Quantity',75) =~ />(\d+)</s) {
		$RET{"QUANTITY"} = $1;
		} else {
		die ("Could not determine quantity");
		}

	if (&ZTOOLKIT::getafter(\$RET{'CONTENTS'},'# of bids',75) =~ />(\d+)</s) {
		$RET{"BIDCOUNT"} = $1;
	}

	# Longest version of Time left is: Auction ended with buy it now (ack!)
	# Human readable <b>(.*)</b>

	if (&ZTOOLKIT::getafter(\$RET{'CONTENTS'},'Time left',250) =~ /<[Bb]>(.*?)<\/[Bb]>/s) 
		{ $RET{"TIMELEFT"} = $1; }

	# Human readable <font size=3>(.*)</font>
	# Human readable <td colspan="4">Jul-19-01 08:47:16 PDT</td>
	if (&ZTOOLKIT::getafter(\$RET{'CONTENTS'},"Started",125) =~ /\<td colspan\=\"4\"\>(.*?)\<\/td\>/s) {
		$RET{"STARTED"} = $1;
	} else {
		if (&ZTOOLKIT::getafter(\$RET{'CONTENTS'},"Started",125) =~ /\<font size=3>(.*?)\<\/font\>/s)
			{
			$RET{'STARTED'} = $1;
			} else {
			die ("Missed STARTED field");
			}
	}

#### SAMPLE:
##<tr><td width="3%">&nbsp;</td>
##<td width="15%"><font size=2>Ends</font></td>
##<td colspan=4><font size=3>Apr-24-01 21:07:08 PDT</font>
##

	# look for the ends in the title.
	# print &ZTOOLKIT::getafter(\$RET{'STAGE1'},'(Ends ',25);


	if (&ZTOOLKIT::getafter(\$RET{'STAGE1'},'(Ends ',30) =~ /(.*?)\)/s)
		{
		$RET{'ENDS'} = $1;
		$RET{'ENDS'} =~ s/([A-Z0-9 ]+)/$1/gs; # remove their carriage returns
		$RET{'ENDS'} =~ s/[\n\r]+//g;
		print "FOUND ENDING: ".$RET{'ENDS'}."\n";
		} else {	
		if (&ZTOOLKIT::getafter(\$RET{'STAGE1'},'Ends',100) =~ /<td colspan=\"4\">(.*?)<\/td>/s)
			{
			$RET{'ENDS'} = $1;
			$RET{'ENDS'} =~ s/([A-Z0-9 ]+)/$1/gs; # remove their carriage returns
			$RET{'ENDS'} =~ s/[\n\r]+//g;
			print "FOUND ANOTHER ENDING: ".$RET{'ENDS'}."\n";
			}
		}

#	if (&ZTOOLKIT::getafter(\$RET{'CONTENTS'},'>Ends</font>',150) =~ /<td colspan="4">(.*?)<\/td>/) { $RET{"ENDS"} = $1; }
#	$RET{"ENDS"} =~ s/.*\<font size\=3\>(.*?)\<\/font\>.*/$1/s;
#	if (!defined($RET{"ENDS"}))
#		{
#		# Ends</font> t
#		if (&ZTOOLKIT::getafter(\$RET{'CONTENTS'},'>Ends</font>',150) =~ /\<td colspan\=4\>\<font size\=3\>(.*?)<\/font>/) { $RET{"ENDS"} = $1; }
#		print ZTOOLKIT::getafter(\$RET{'CONTENTS'},'>Ends</font>',150)."\n";
#		}
#
	if (!defined($RET{"ENDS"})) { die "No ending time!\n"; }

#	print "Bleh.. [$RET{'CONTENTS'}]";

	my $dutch;
	my @winners = ();

	## worked July 7th 2001
	## if ($RET{'CONTENTS'} =~ /eBay Dutch Auction High Bidders/) { # DUTCH auction processing

	## Worked July 25th 2001
	## if ($RET{'CONTENTS'} =~ /All bids in this Dutch Auction/) { # DUTCH auction processing
	if ($RET{'CONTENTS'} =~ /Dutch Auction/) { # DUTCH auction processing
		print "This road looks Dutch to me..\n";
		$dutch = 1;
		my $qty = $RET{"QUANTITY"};
		$high_bidders = $RET{'CONTENTS'};
		# Human readable <a name=dutch>(.*)<!--footer-->

		if (&ZTOOLKIT::getafter(\$RET{'CONTENTS'},'# of bids',75) =~ /<b>(.*?)<\/b>/)
			{
			$RET{"BIDCOUNT"} = $1;
			} else { die "Could not determine bid count on dutch auction!!!\n"; }

		if ($RET{"BIDCOUNT"}>0)
			{
			# Worked as of July 25th
			# $BUFFER = &ZTOOLKIT::getafter(\$RET{'CONTENTS'},'All bids in this Dutch Auction',32000);
			

			$DUTCHROAD = 0;
			$BUFFER = $RET{'CONTENTS'};
			if (index($BUFFER,'<A name=dutch>')>=0) {	
				$DUTCHROAD=1;
				$BUFFER = substr($BUFFER,0,index($BUFFER,'<SCRIPT SRC="http://include.ebay.com/aw/pics/js/stats/ss.js">'));
				} 
			elsif (index($BUFFER,'<a name="dutch">')>=0) {
				$DUTCHROAD=2;
				$BUFFER = substr($BUFFER,0,index($BUFFER,'<a name="dutch">'));
				} 
			else {
				# print $BUFFER."\n";
				die ("Could not determine the end of the DUTCH field");
				}

		
			if ($DUTCHROAD == 1)
				{

				foreach $row (split /<\/TABLE\>/,$BUFFER)
					{
					next unless ($row =~ /eBayISAPI\.dll\?ReturnUserEmail/);
					# print $row."\n";
					if ($row =~ m/<[Aa] [Hh][Rr][Ee][Ff]\=[\"\']?[Mm][Aa][Ii][Ll][Tt][Oo]:(.*?)[\"\']?>[\(]?(.*?)[\)]?<.*?>\$([\d\.]+)<.*?>(\d+)</s) 
						{
						# userid, email, qty, price
						$win_nick = $2;
						$win_email = $1;
						$win_qty = $4;
						$win_bid = $RET{'CURRENTLY'};
						print "EMAIL=[$win_email] WINNER=[$win_nick] PRICE=[$win_bid] QUANTITY=[$win_qty]\n";
	
						# decrement the quantity available.
						if ($win_qty<=$qty) 
							{ 
							$qty = $qty - $win_qty; 
							$win_bid = $win_bid;
						 	} else { 
							$win_bid=$win_bid; 
							$win_qty = $qty; 
							$qty=0; 
							}

						## Sanity check
						# print "ROW=[$row]\n";
						if ($win_email eq '' || $win_nick eq '' || $qty eq '') { die "Problem with DUTCH [$win_nick][$win_bid][$qty]\n"; }

						# unless we have a quantity, don't bother tracking the winner
						if ($win_qty>0) { push @winners, "$win_nick $win_email $win_qty $win_bid"; }
						}
					}
				} ## END OF DUTCHROAD == 1

			if ($DUTCHROAD == 2)
				{

			open F, ">/tmp/foo";
			print F "-=----------------------------\n".$BUFFER."\n";
			close F;

				foreach $row (split /\<\/table\>/,$BUFFER)
					{
#					print "----------> $row\n\n";
					# make this this is a table we want
					next unless ($row =~ /eBayISAPI\.dll\?ReturnUserEmail/);
					next unless ($row !~ /$USERNAME/);
					print "----------> $row\n\n";
	
					$win_nick = '';
					$win_bid = '';
					$win_qty = 0;
					$win_email = '';
					if ($row =~ /ViewFeedback\&amp;userid\=(.*?)\">/) { $win_nick = $1; }

					print "!!!!!!!!!!!!! WIN NICK: $win_nick\n";
		
					# if we don't have any more qty available, then skip this user.
					if ($qty == 0) { $win_nick = ''; }	
	
					if ($win_nick ne '')
						{
						@items = split("\<\/td\>",$row);
#						$counter = 0; foreach $k (@items) { print "[".$counter++."] $k\n"; }
						if ($items[0] =~ /\<a href\=\"mailto\:(.*?)\"\>/) { $win_email = $1; }
						if ($items[1] =~ /\>(.*?)$/) { $win_bid = $1; }
						print "ITEMS [1] is: $items[1]\n";
						if ($items[2] =~ /\>(.*?)$/) { $win_qty = $1; }
						
						print "EMAIL=[$win_email] WINNER=[$win_nick] PRICE=[$win_bid] QUANTITY=[$win_qty]\n";
	
						# decrement the quantity available.
						if ($win_qty<=$qty) 
							{ 
							$qty = $qty - $win_qty; 
							$win_bid = $win_bid;
						 	} else { 
							$win_bid=$win_bid; 
							$win_qty = $qty; 
							$qty=0; 
							}

						## Sanity check
						print "ROW=[$row]\n";
						if ($win_email eq '' || $win_nick eq '' || $win_bid eq '' || $qty eq '') { die "Problem with DUTCH [$win_nick][$win_bid][$qty]\n"; }

						# unless we have a quantity, don't bother tracking the winner
						if ($win_qty>0) { push @winners, "$win_nick $win_email $win_qty $win_bid"; }
						}
					}
			} # End of DUTCHROAD == 1

			foreach $row (@winners)
				{
				print "WINNER: [$row]\n";
				}		

#			print $BUFFER;
	
#			print "\n\n***********************************> DUTCH IS BROKEN [DUTCHROAD=$DUTCHROAD] !!!!!!!\n";
#  		   exit;

#			foreach $row (split /<\/[Tt][Rr]>/,$high_bidders) 
#				{
#				# Human readable <a href=mailto:(.*)>(.*)<.*>$(\d\.+)<.*>(\d+)<
#				if ($row =~ m/<[Aa] [Hh][Rr][Ee][Ff]\=[\"\']?[Mm][Aa][Ii][Ll][Tt][Oo]:(.*?)[\"\']?>[\(]?(.*?)[\)]?<.*?>\$([\d\.]+)<.*?>(\d+)</s) 
#					{
#					# userid, email, qty, price
#					$win_nick = $2;
#					$win_email = $1;
#					$win_qty = $4;
#					}
#				}	# end of foreach winner
#			}

			} else {
			print "This dutch auction doesn't seem to have any bids!\n";
#			die;
			}

	} # end of DUTCH auction processing
	elsif ($RET{'CONTENTS'} =~ /eBay Bid History for/) { # NON-DUTCH (normal)
		$dutch = 0;
		print "This road is NOT dutch..\n";

		# this finds the chunk with the winners
		if ($RET{'CONTENTS'} =~ /\<a name\=\"bids"\>(.*?)\<a name\=\"dutch\"\>/s)
			{
			$after_date = $1;
			}

#		my $after_date = &ZTOOLKIT::getafter(\$RET{'CONTENTS'},'<a name="bids">',1000);
#		print $RET{'CONTENTS'};
#		exit;

	## Do a quick IF to make sure we're still SANE
	if (length($after_date)>0)
		{

		if ($after_date =~ /userid=(.*?)">/)
			{
			$win_userid = $1;
			print $win_userid."\n";

			$win_email = undef;
			if ($after_date =~ /mailto\:(.*?)\"\>/s)
				{
				$win_email = $1;
				}
			print "WIN EMAIL: [$win_email]\n";
			# BROKEN May 16th 2001 BH - now reports no longer in transaction
			# $win_email = &resolve_username($USERNAME,$PASSWORD,$win_userid,$ITEM);

			if (!$win_email) { die("Could not determine winning bidders email address."); }

			# userid, email, qty, price
			push @winners, "$win_userid $win_email 1 $RET{'CURRENTLY'}";

			} else {
				print $after_date."\n";
				if ($after_date !~ /There were no earlier bidders/s)
					{
					die ("Ebay page appears to have changed, normally we will wait to wait to resolve email addresses till the auction is over..\n");
					}
			}

		} else {
		die "\$after_date is blank [length of zero], dammit.\n";
		}
	
		print "here.. ".scalar(@winners)." winners\n";	
		
# CODE Broken: Mar 2nd, 2001
#		Ebay decided to stop including mailtos
#		# Human readable <a href=mailto:(.*)>(.*)<
#		if ($after_date =~ /.*?<[Aa] [Hh][Rr][Ee][Ff]\=[\"\']?[Mm][Aa][Ii][Ll][Tt][Oo]:(.*?)[\"\']?>[\(]?(.*?)[\)]?</s) {
#			# userid, email, qty, price
#			push @winners, "$2 $1 1 $RET{'CURRENTLY'}";
#		}


	}
	else { # Neither DUTCH nor NON-DUTCH, in other words, FUBAR
		print $RET{'CONTENTS'};
		return(STATUS=>14,ERROR=>"Internal error, Could not determine if EBAY auction was dutch or not\n");
	}

	$RET{'WINNERS'} = '';
	foreach (@winners) { $RET{'WINNERS'} .= "$_,"; }
	if (length($RET{'WINNERS'})>0) { chop $RET{'WINNERS'}; }

	my $num_winners = scalar(@winners);
	my $num_bidders = $RET{'BIDCOUNT'};
	
	print "num_winners=[$num_winners] num_bidders=[$num_bidders]\n";

	if ($RET{"TIMELEFT"} =~ /Auction has ended./) 
		{

		
		if ($RET{'STAGE1'} =~ /\(reserve not yet met\)/i)
			{
			$RET{'STATUS'} = 98;  
			} else {

			if ($num_winners<=0) 
				{
				if ($dutch) 
					{ $RET{'STATUS'} = 119; } 
					else { $RET{'STATUS'} = 99; }
				} else {
				if ($dutch) 
					{ $RET{'STATUS'} = 120; } 
					else { $RET{'STATUS'} = 100; }
				}
			}

	} else {
		if ($num_bidders) { 
			if ($dutch) { $RET{'STATUS'} = 61; }
			else { $RET{'STATUS'} = 51; }
		}
		else {
			if ($dutch) { $RET{'STATUS'} = 60; }
			else { $RET{'STATUS'} = 50; }
		}
	}

	return %RET;
}

##
##  This is a function to import external auctions directly into the MONITOR_EBAY table
##
##
##
sub save_external_auction
{
  ($ZOOVY_USERNAME,$EBAY_ID,$EBAY_USERNAME,$EBAY_PASSWORD,$TITLE) = @_;

  my $dbh = DBI->connect($DBINFO::MYSQL_DSN,$DBINFO::MYSQL_USER,$DBINFO::MYSQL_PASS); 
  $pstmt = "insert into MONITOR_EBAY values(0,'$ZOOVY_USERNAME',";
  $pstmt .= $dbh->quote($EBAY_ID).",";
  $pstmt .= $dbh->quote($EBAY_USERNAME).",";
  $pstmt .= $dbh->quote($EBAY_PASSWORD).",";
  $pstmt .= $dbh->quote($TITLE).",";
  $pstmt .= "now(),now(),0,0,'',0,0,0)";

  $sth = $dbh->prepare($pstmt);
  $rv = $sth->execute;
  if (defined($rv))
    {
    $result = 1;    
    } else {
    $result = 0;
    }
  $dbh->disconnect();
#  print $pstmt."<br>";
#  print "RESULT IS: $result<br>\n";
  return($result);
}



##
## parameters: SGML buffer, SSLIFY basically means "PREVIEW"
##             so pass it if you need it.
##
##

sub make_pretty
{
  ($BUFFER,$SSLIFY,$vars,$MERCHANT,$CHANNEL) = @_; 

	if (!defined($CHANNEL)) { $CHANNEL = 0; }
	$MERCHANT = lc($MERCHANT);
  %{$vars} = &safe_attrib_handler($BUFFER);

  # do a bit of data massaging:

	$bgcolor = $$vars{'ebay:bgcolor'};
	if ($bgcolor eq "") { $bgcolor = "FFFFFF"; }

	$fullimg1 = &GT::imageurl($MERCHANT,$$vars{'zoovy:prod_image1'},0,0,'FFFFFF',0);
	$fullimg2 = &GT::imageurl($MERCHANT,$$vars{'zoovy:prod_image2'},0,0,'FFFFFF',0);
	$fullimg3 = &GT::imageurl($MERCHANT,$$vars{'zoovy:prod_image3'},0,0,'FFFFFF',0);

	$$vars{'zoovy:prod_image1'} = &GT::imageurl($MERCHANT,$$vars{'zoovy:prod_image1'},300,300,$bgcolor,0);
	$$vars{'zoovy:prod_image2'} = &GT::imageurl($MERCHANT,$$vars{'zoovy:prod_image2'},300,300,$bgcolor,0);
	$$vars{'zoovy:prod_image3'} = &GT::imageurl($MERCHANT,$$vars{'zoovy:prod_image3'},300,300,$bgcolor,0);
	$$vars{'ebay:logo'} = &GT::imageurl($MERCHANT,$$vars{'ebay:logo'},100,100,'FFFFFF',$SSLIFY);

  # build a custom tag of city and state
  $$vars{'zoovy:citystate'} = $$vars{'zoovy:city'}.", ".$$vars{'zoovy:state'};
#  print "CITYSTATE: ".$$vars{'zoovy:citystate'}."\n";

  # do a bit of data validation so we don't accidentially fail
  $$vars{'ebay:startprice'} += 0;
  if ($$vars{'ebay:startprice'} <= 0) { $$vars{'ebay:startprice'} += "0.01"; }

   # fit the title into the length!
# STOP this breaks if the title is incoded.
#  $$vars{'ebay:title'} = substr($$vars{'ebay:title'},0,45);

   # go ahead and make the listing look pretty!
   $pretty = "";

#$pretty .= "<script language=\"JavaScript\">\n";
#$pretty .= "<!--// \n";
#$pretty .= "	function zoom(img) { \n";
#$pretty .= "		popupWin = window.open('','zoom_picture','status=0,directories=0,toolbar=0,menubar=0,resizable=1,scrollbars=1');\n";
#$pretty .= "		popupWin = window.open('','zoom_picture','');\n";
#$pretty .= "		popupWin.document.write('<html><head><title>Picture Zoom</title></head><body><center>\\n');\n";
#$pretty .= "		popupWin.document.write('<img src=\"' + img + '\"><br>\\n');\n";

#$pretty .= "		popupWin.document.write('<form><input type=\"button\" value=\"Close Window\" onClick=\"self.close(true)\"></form>\\n');\n";

#$pretty .= "		popupWin.document.write('</center></body></html>\\n');\n";
#$pretty .= "		popupWin.focus(true);\n";
#$pretty .= "		return false;\n";
#$pretty .= "	}\n";
#$pretty .= "//-->\n";
#$pretty .= "</script>\n\n";

   $pretty .= "<center><table width='630'><tr><td>";
   $pretty .= "<table bgcolor=$bgcolor width='100%'><tr><td valign='top'>";
   $pretty .= "<font face='Arial'><center>";

	if ($vars->{'ebay:linklocation'} eq 'TOP') { $pretty .= "<a href='http://$MERCHANT.zoovy.com/counter.cgis?channel=$CHANNEL'>".$vars->{'ebay:linktext'}.'</a><br><br>'; }

   $pretty .= "<font size=+1><b>".$$vars{'ebay:title'}."</b></font></center><br>";

   $pretty .= "<center><table width='85%'><Tr><td><font face='Arial'>";
   $pretty .= &text_to_html($$vars{'ebay:description'}); 
# for debugging
#   foreach (keys %{$vars}) { $pretty .= "$_<br>"; }
   $pretty .= "</font></td></tr></table>";
 
   if ($$vars{'zoovy:prod_image1'}) 
		{ 
		$pretty .= "<center>";
#		$pretty .= "<a href=\"#\" onClick=\"return zoom('".$fullimg1."')\">";
		$pretty .= "<img border='0' src='".$$vars{'zoovy:prod_image1'}."'>";
#		$pretty .= "</a>";
		$pretty .= "</center>"; 
		}
   if ($$vars{'zoovy:prod_image2'}) 
		{ 
		$pretty .= "<center>";
#		$pretty .= "<a href=\"#\" onClick=\"return zoom('".$fullimg2."')\">";
		$pretty .= "<img border='0' src='".$$vars{'zoovy:prod_image2'}."'>";
#		$pretty .= "</a>";
		$pretty .= "</center>"; 
		}
   if ($$vars{'zoovy:prod_image3'}) 
		{ 
		$pretty .= "<center>";
#		$pretty .= "<a href=\"#\" onClick=\"return zoom('".$fullimg3."')\">";
		$pretty .= "<img border='0' src='".$$vars{'zoovy:prod_image3'}."'>";
#		$pretty .= "</a>";
		$pretty .= "</center>"; 
		}
   $pretty .= "</table>";

	if ($vars->{'ebay:linklocation'} eq 'BODY') { $pretty .= "<a href='http://$MERCHANT.zoovy.com/counter.cgis?channel=$CHANNEL'>".$vars->{'ebay:linktext'}.'</a><br><br>'; }

   $pretty .= "<br><br>";
   # begin company logo table!	 

   if ($$vars{'ebay:logo'} && ($$vars{'ebay:use_logo'} eq 'Y')) 
      { $pretty .= "<table><tr><td>"; }
 
   $pretty .= "<font face='Arial'>";
	$pretty .= "<B>".$$vars{'zoovy:company_name'}."</B>"; 
   $pretty .= "<BR>";	
   $pretty .= $$vars{'zoovy:address1'}."<br>"; 
   if ($$vars{'zoovy:address2'}) { $pretty .= $$vars{'zoovy:address2'}."<br>"; }
   $pretty .= $$vars{'zoovy:citystate'}." ".$$vars{'zoovy:zip'}."<br>"; 
   $pretty .= $$vars{'zoovy:support_email'}."<br>"; 
   $pretty .= "</font>";

# end of company_logo table
   if ($$vars{'ebay:logo'} && ($$vars{'ebay:use_logo'} eq 'Y')) 
      { 
		$pretty .= "</td><td><img src='".$$vars{'ebay:logo'}."'></td></tr></table>"; 
		}

   $pretty .= "<br><br>";
   if ($$vars{'zoovy:return_policy'}) {  $pretty .= "<font face='Arial'><b>RETURN POLICY:</b><br>".$$vars{'zoovy:return_policy'}."<br>"; }

	# Zoovy Co-Brand
	$pretty .= "<br><center><table cellpadding='4'><tr><td colspan='2'><hr></td></tr>";
   $pretty .= "<tr><td><a href='http://www.zoovy.com/track.cgi?P=$MERCHANT'>";

	$pretty .= "<img border='0' src='http://www.zoovy.com/images/poweredby.gif'>";
	$pretty .= "</a></td><td><font face='Arial' size='2'>";
	$pretty .= "This Auction will be closed using Zoovy Auction processing technology. ";
	$pretty .= "Winners of multiple auctions will be able to save shipping. Serious bidders only.";

	if (int($vars->{'feedback_policy'})>0) { $pretty .= " Automatic positive feedback will be left for all auctions completed within 72 hours of closing."; }
	if (int($vars->{'feedback_policy'})>1) { $pretty .= " Non-Paying Bidders Beware: Negative feedback will be posted AUTOMATICALLY after 2 weeks."; }

	$pretty .= "<br></font></td></table></center>";

    if (length($$vars{'zoovy:shipping_explanation'})>4)
        {
	$pretty .= "<center><hr><table width='98%' border='0'><tr><td>";
	$pretty .= "<font face='Arial'><b>Shipping Policy:</b><br>";
        $pretty .= &text_to_html($$vars{'zoovy:shipping_explanation'});
	$pretty .= "</tr></td></table></center>";
        }

    if (length($$vars{'zoovy:payment_explanation'})>4)
        {
	$pretty .= "<center><hr><table border='0' width='98%'><tr><td>";
	$pretty .= "<font face='Arial'><b>Accepted Payment:</b><br>";
        $pretty .= &text_to_html($$vars{'zoovy:payment_explanation'});
	$pretty .= "</tr></td></table></center>";
	} 
	
        $pretty .= "</font></td></tr></table><br>";

	# Please visit our website at ..

	if ($$vars{'ebay:counter'} ne '')
		{
		$pretty .= "<center>";
		$pretty .= "<a href='http://$MERCHANT.zoovy.com/counter.cgis?channel=$CHANNEL'>";
		if (($vars->{'ebay:counter'} eq 'blank') || ($vars->{'ebay:counter'} eq 'hidden')) { $BORDER = 0; } else { $BORDER = 1; }
		$pretty .= "<br><img border=$BORDER src='http://track.zoovy.com/counter.cgi?MERCHANT=$MERCHANT&CHANNEL=$CHANNEL&STYLE=".$vars->{'ebay:counter'}."'><br>";
		$pretty .= "</a>";
		}

	if ($vars->{'ebay:linklocation'} eq 'BOTTOM') { $pretty .= "<a href='http://$MERCHANT.zoovy.com/counter.cgis?channel=$CHANNEL'>".$vars->{'ebay:linktext'}.'</a>'; }
	$pretty .= "</center><br><br>";
	$pretty .= "</td></tr></table></center>";

	if ($$vars{'ebay:pog_policy'}>0)
		{
		$c .= "\n<ZOOVY><!--\n";
		$c .= "<".lc($MERCHANT).":pogs>".$$vars{lc($MERCHANT).":pogs"}."</".lc($MERCHANT).":pogs>\n";
		foreach $pog (split(',',$$vars{lc($MERCHANT).":pogs"}))
			{
			$key = $MERCHANT.":pog_$pog";
			if ($$vars{$key})
				{
				$c .= "<$key>\n";
				my $data = $$vars{$key};
				# strip blank price modifiers
				$data =~ s/price=\"\"//ig;
				# strip black weight modifiers
				$data =~ s/wt=\"\"//ig;
				# strip extra spaces to make it all look pretty!
				$data =~ s/[ ]+>/>/g;

				if ($$vars{'ebay:pog_policy'}<=1) # <2 means nuke the price modifier
					{
					$data =~ s/price=\"(.*?)\"//g;
					}

				# we have to encode BEFORE we sample out the <br>
				$c .= "$data\n";
				$c .= "</$key>\n";
				}
			}
	$c .= "--></ZOOVY>\n";
	$pretty .= $c;
		}

	open F, ">/httpd/htdocs/pretty.shtml";
	print F "<body bgcolor='FFFFFF'>$pretty</body>";
	close F;

    return($pretty);
}




sub fetch_running_auctions
{
  ($USERNAME) = @_;

  my @ar = ();
  my $dbh = DBI->connect($DBINFO::MYSQL_DSN,$DBINFO::MYSQL_USER,$DBINFO::MYSQL_PASS); 
  
  $pstmt = "select ID, CREATED, EBAY_ID, TITLE, NEXTCHECK, SUBSCRIPTION_ID, TRIGGER, HIGHBIDDER, ";
  $pstmt .= " LASTPRICE, REOCCUR from MONITOR_EBAY where USERNAME=".$dbh->quote($USERNAME);
#  print $pstmt."\n";
  $sth = $dbh->prepare($pstmt);
  $sth->execute;

  while (@row = $sth->fetchrow())
    {
     $title = $row[3];
# commas fuck this shit up!
     $title =~ s/,//s; 
     push @ar, "$row[0],$row[1],$row[2],$title,$row[4],$row[5],$row[6],$row[7],$row[8],$row[9]";
    }
  
 return(@ar);  
}

######################################################################################################

# Found this redefined subroutine through perl -w, renamed to 2
sub fetch_running_auctions2
{
  ($USERNAME) = @_;

  my @ar = ();
  my $dbh = DBI->connect($DBINFO::MYSQL_DSN,$DBINFO::MYSQL_USER,$DBINFO::MYSQL_PASS); 
  
  $pstmt = "select ID, CREATED, EBAY_ID, TITLE, NEXTCHECK, SUBSCRIPTION_ID, TRIGGER, HIGHBIDDER, ";
  $pstmt .= " LASTPRICE, REOCCUR from MONITOR_EBAY where USERNAME=".$dbh->quote($USERNAME);
#  print $pstmt."\n";
  $sth = $dbh->prepare($pstmt);
  $sth->execute;

  while (@row = $sth->fetchrow())
    {
     $title = $row[3];
# commas fuck this shit up!
     $title =~ s/,//s; 
     push @ar, "$row[0],$row[1],$row[2],$title,$row[4],$row[5],$row[6],$row[7],$row[8],$row[9]";
    }
  
 return(@ar);  
}


sub fix_ebay_time
{
	my ($ebaydate) = @_;

	# FORMAT: Apr-08-01 21:26:11 PDT
	($front,$remainder) = split('-',$ebaydate,2);
	if ($remainder eq '') { return 0; }

	# $front now contains Apr
	# $remainder contains the rest	

	print "EBAYDATE: $ebaydate\n";

	$c = sprintf("%2d-%s",Date::Calc::Decode_Month($front),$remainder); 
	$c= parsedate($c);

	print "--->". $c."\n";
	
	($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($c); $year+=1900;	$mon+=1;
	print "I THINK IT EXPIRES ON: $mon/$mday/$year $hour:$min:$sec\n";

#	$c = time();		# DEBUG: set the expirations to right now

	return($c);
}



##############################
## 
## sub: attrib_handler
##
## PURPOSE: converts strings from the format <merchant.tag>data</tag> to 
##          a usable hash
##
## returns: HASH with key=merchant.tag and value=data
##
###############################
sub attrib_handler
{
	my ($BUFFER) = @_;
	if ((not defined($BUFFER)) || ($BUFFER eq '')) { return; }
	# first match all the merchant:tag combinations (note this will NOT
	# match </merchant:attrib>
	$BUFFER .= "\n";
	study($BUFFER);
	my %HASH = ();

	# split on the end tags.
	my @ar = split (/.*?\<\/([\w|:]+)\>.*?/s, $BUFFER);

	foreach my $KEY (@ar)
	{
		# find the data which matches the KEY
		# print STDERR "\n\nKEY IS:".$KEY;
		if ($KEY ne "")
		{
			if ($BUFFER =~ /\<$KEY\>(.*?)\<\/$KEY\>/s) { $HASH{$KEY} = &dcode("$1"); }
		}
	}

	return (%HASH);
} ## end sub attrib_handler


#
#
# sub text_to_html
#
sub text_to_html
{
 ($BUFFER) = @_;
 if ($BUFFER !~ /<br>/is)
    {
    # replace all carriage returns with \n's
    $BUFFER =~ s/\n/<br>/igs;

    # replace all double spaces with real spaces.
    $BUFFER =~ s/  /\&nbsp;\&nbsp;/igs;
    } else {

    }
 return($BUFFER);
}





1;