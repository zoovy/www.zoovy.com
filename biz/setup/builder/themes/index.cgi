#!/usr/bin/perl

use lib "/httpd/modules";
use strict;

require Data::Dumper;
require strict;
require ZOOVY;
require GTOOLS;
require SITE;
require ZWEBSITE;
require TOXML;
require TOXML::UTIL;
require TOXML::COMPILE;
require DOMAIN::TOOLS;



my $dbh = &DBINFO::db_zoovy_connect();

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }



my $NS = $ZOOVY::cgiv->{'NS'};
$GTOOLS::TAG{'<!-- NS -->'} = $NS;
my $SUBTYPE = $ZOOVY::cgiv->{'SUBTYPE'};
## SUBTYPE = "" (wrapper)
## SUBTYPE = "P" (Popup)
## SUBTYPE = "E" (Email)
$GTOOLS::TAG{'<!-- SUBTYPE -->'} = $SUBTYPE;

my $DOCTYPE = 'WRAPPER';
if ($SUBTYPE eq 'E') { $DOCTYPE = 'ZEMAIL'; }

my @TABS = ();

my @BC = ();
push @BC, { name=>"Setup", link=>"/biz/setup" };
push @BC, { name=>"Site Builder", link=>"/biz/setup/builder" };
push @BC, { name=>"Profile [$NS]" };

if ($SUBTYPE eq 'E') {
	push @BC, { name=>"Email Template Chooser" };
	push @TABS, { name=>'Select', link=>"/biz/setup/builder/themes/index.cgi?SUBTYPE=E&NS=$NS", selected=>1 };
	push @TABS, { name=>'Edit', link=>"/biz/setup/builder/emails/index.cgi?VERB=EDIT&NS=$NS", };
	push @TABS, { name=>'Add', link=>"/biz/setup/builder/emails/index.cgi?VERB=ADD&NS=$NS", };
	}
else {
	push @BC, { name=>"Theme Chooser" };
	}

## General Help on Themes
my $help = "#50270";

$GTOOLS::TAG{'<!-- MENUPOS -->'} = 1;
my $webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME);
my $NSREF = &ZOOVY::fetchmerchantns_ref($USERNAME,$NS);
if ($webdbref->{'branding'}>0) {
	delete($WRAPPER::logos->{'thawte'});
	delete($WRAPPER::logos->{'geotrust'});
	}

my $template_file = '';
my $VERB = $ZOOVY::cgiv->{'VERB'};
my @THEMES = ();
if ((defined $ZOOVY::cgiv->{'category'}) || (defined $ZOOVY::cgiv->{'color'})) { $VERB = 'SEARCH'; }

if ($VERB eq '') {
	$VERB = 'MYTHEMES';
	}


my $DOMAIN = DOMAIN::TOOLS::syndication_domain($USERNAME,$NS);


if (1) {
	my $c = '';
	foreach my $cat (sort {$a<=>$b} keys %TOXML::BW_CATEGORIES) {	
		next if ($TOXML::BW_CATEGORIES{$cat} eq '');
		$c .= "<option value=\"$cat\">$TOXML::BW_CATEGORIES{$cat}</option>\n";
		}
	my $CATS = $c;

	$c = '';
	foreach my $color (sort {$a<=>$b} keys %TOXML::BW_COLORS) {
		next if ($TOXML::BW_COLORS{$color} eq '');
		$c .= "<option value=\"$color\">$TOXML::BW_COLORS{$color}</option>\n";
		}

	my $TXT = 'Theme List';
	if ($SUBTYPE eq 'E') { $TXT = 'Email Themes'; }
	if ($SUBTYPE eq 'P') { $TXT = 'Popup Themes'; }
	if ($SUBTYPE eq 'M') { $TXT = 'Mobile Themes'; }

	my $COLORS = $c;
	my $left = qq~

<form name="thisFrm" action="/biz/setup/builder/themes/index.cgi">
<input type="hidden" name="NS" value="$NS">
<input type="hidden" name="SUBTYPE" value="$SUBTYPE">
<table cellspacing="2" cellpadding="0" width="170" border="0"><tr>
	<td width="1%"><img
src="//www.zoovy.com/biz/images/tabs/themes/themes.gif" width="30"
height="30"></td>
	<td width="99%"><h3>$TXT</h3></td>
</tr>
<tr>
	<td colspan="2" align="left">
	<table width="100%" cellspacing=4 cellpadding=0>
	<tr>
		<td width="10"><img width="10" height="10" name="img1" id="img1" src="/images/blank.gif"></td>
		<td align="left"><a href="/biz/setup/builder/themes/index.cgi?VERB=MYTHEMES&SUBTYPE=$SUBTYPE&NS=$NS">My Themes</td>
	</tr>
	<tr>
		<td width="10"><img width="10" height="10" name="img2" id="img2" src="/images/blank.gif"></td>
		<td align="left"><a href="/biz/setup/builder/themes/index.cgi?VERB=FAVORITES&SUBTYPE=$SUBTYPE&NS=$NS">Community Favorites</a></td>
	</tr>
	<tr>
		<td width="10"><img width="10" height="10" name="img3" id="img3" src="/images/blank.gif"></td>
		<td align="left"><a href="/biz/setup/builder/themes/index.cgi?VERB=RECENT&SUBTYPE=$SUBTYPE&NS=$NS">Recently Added</a></td>
	</tr>
	<tr>
		<td width="10"><img width="10" height="10" name="img4" id="img4" src="/images/blank.gif"></td>
		<td align="left"><a href="/biz/setup/builder/themes/index.cgi?VERB=STAFF&SUBTYPE=$SUBTYPE&NS=$NS">Staff Favorites</a></td>
	</tr>
	<tr>
		<td width="10"><img width="10" height="10" name="img5" id="img5" src="/images/blank.gif"></td>
		<td align="left"><a href="/biz/setup/builder/themes/index.cgi?VERB=RANKED&SUBTYPE=$SUBTYPE&NS=$NS">Best Ranked</a></td>
	</tr>
	<tr>
		<td width="10"><img width="10" height="10" name="img5" id="img5" src="/images/blank.gif"></td>
		<td align="left"><a href="/biz/setup/builder/themes/index.cgi?VERB=SHOWALL&SUBTYPE=$SUBTYPE&NS=$NS">Show All</a></td>
	</tr>
~;

$left .= qq~
	</table>
	<br>
	</td>
</tr>
~;

	if ($SUBTYPE eq 'AB') {
		$left .= qq~<tr><td colspan=2><a href="/biz/setup/builder/themes/index.cgi?VERB=SAVE-WRAPPER&NS=$NS&wrapper=&SUBTYPE=AB">DISABLE A/B TEST</a><br><br></td></tr>~;
		}

	if ($SUBTYPE eq 'E') {
		## hmm.. no sitemap, no sidebar/header
		}
	elsif ($SUBTYPE eq 'P') {
		## hmm.. no sitemap, no sidebar/header
		}
	elsif ($SUBTYPE eq 'M') {
		## hmm.. no sitemap, no sidebar/header
		}
	else {
		$left .= qq~
<tr>
	<td><img src="//www.zoovy.com/biz/images/tabs/themes/advanced.gif" width="30" height="30"></td>

	<td><h3>Customize</h3></td>
</tr><tr>
	<td colspan="2"><table width="100%" cellspacing=4 cellpadding=0><tr>
		<td width="10"><img width="10" height="10" name="img6" id="img6" src="/images/blank.gif"></td>
	</tr>

	</table><br></td>
</tr><tr>
	<td>
		<img src="//www.zoovy.com/biz/images/tabs/themes/search.gif" width="30" height="30">
	</td>
	
	<td><h3>Find A Theme</h3></td>
</tr>
	<tr>
	<td colspan="2" align="left"><table><tr>
		<td width="10" rowspan="6"></td>
		<td align="left"><strong>Category:</strong></td>
	</tr><tr>
		<td align="left">
		<select name="category" id="category" class="dropdown">
			<option value=""> - Any - </option>
			$CATS
		</select>
		</td>
	</tr><tr>
		<td><strong>Color:</strong></td>
	</tr><tr>
		<td align="left">
		<select name="color" id="color" class="dropdown">
			<option value="0"> - Any - </option>
			$COLORS 
	 		</select>
	 	</td>
	</tr><tr>
		<td><strong>Features:</strong></td>

	</tr><tr>
		<td>
<input type="checkbox" value="1" name="minicart" id="minicart">&nbsp;Minicart<br>
<input type="checkbox" value="1" name="sidebar" id="sidebar">&nbsp;Sidebar<br>
<input type="checkbox" value="1" name="subcats" id="subcats">&nbsp;Subcats<br>
<input type="checkbox" value="1" name="embed_search" id="embed_search">&nbsp;Embed Search<br>
<input type="checkbox" value="1" name="embed_subscribe" id="embed_subscribe">&nbsp;Embed

Subscribe<br>
<input type="checkbox" value="1" name="embed_login" id="embed_login">&nbsp;Embed Login<br>
<input type="checkbox" value="1" name="imagecats" id="imagecats">&nbsp;Image Navcats<br></td>

	</tr>
<tr>
	<td align="center" colspan="2">
		<input type="button" onClick="thisFrm.submit();" value="Search" class="button">
	</td>
</tr></table></td>
</tr>
	~;
	}

$left .= qq~
	</table>
	</form>
	~;

	$GTOOLS::TAG{'<!-- LEFT -->'} = $left;
	}








########################################################################################################
## 				D E V E L O P E R 	F U N C T I O N S
########################################################################################################


##
## save the wrapper, and return them to the main screen
##		HEY: this is used by both "developer" mode and the regular save-wrapper mode.
##
if (($VERB eq 'SAVE-ZEMAIL') || ($VERB eq 'SAVE-WRAPPER') || ($VERB eq 'SAVE-POPUP') || ($VERB eq 'SAVE-WRAPPERB') || ($VERB eq 'SAVE-MOBILE')) {
	my $wrapper = defined($ZOOVY::cgiv->{'selected'}) ? $ZOOVY::cgiv->{'selected'} : '';
	if ($wrapper eq '') { $wrapper = $ZOOVY::cgiv->{'wrapper'}; }	

	my $TYPE = $ZOOVY::cgiv->{'TYPE'};
	# this is if they choose a default theme from the main menu, we should reset both the category and product
	if ($TYPE eq '') {
		$TYPE = 'SITE';
		}

	my $src = '';
	if (substr($wrapper,0,1) eq '~') {
		$wrapper =~ s/\W//gis;
		$wrapper = '~'.$wrapper;
		$src = 'CUSTOM';
		}
	else {
		$wrapper =~ s/\W//gis;
		}

	## clear out the old values from the legacy system
	if ($SUBTYPE eq '') {
		$NSREF->{'zoovy:site_wrapper'} = $wrapper;
		$LU->log('SETUP.BUILDER.THEME',"Updated site wrapper for profile $NS",'SAVE');
		}
	elsif ($SUBTYPE eq 'AB') {
		$NSREF->{'zoovy:site_wrapperb'} = $wrapper;
		$LU->log('SETUP.BUILDER.THEME',"Updated site wrapper *B* for profile $NS",'SAVE');
		}
	elsif ($SUBTYPE eq 'P') {
		$NSREF->{'zoovy:popup_wrapper'} = $wrapper;
		$LU->log('SETUP.BUILDER.THEME',"Updated popup wrapper for profile $NS",'SAVE');
		}
	elsif ($SUBTYPE eq 'M') {
		$NSREF->{'zoovy:mobile_wrapper'} = $wrapper;
		$LU->log('SETUP.BUILDER.THEME',"Updated mobile wrapper for profile $NS",'SAVE');
		}
	elsif ($SUBTYPE eq 'E') {
		$LU->log('SETUP.BUILDER.THEME',"Updated email wrapper for profile $NS",'SAVE');
		$NSREF->{'email:docid'} = $wrapper;
		}

	&ZOOVY::savemerchantns_ref($USERNAME,$NS,$NSREF);
	$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<center><font face='helvetica, arial' color='red' size='5'><b>Successfully Saved!</b></font></center><br><br>";;


	TOXML::UTIL::remember($USERNAME,'WRAPPER',$wrapper,0);
	$VERB = 'MYTHEMES';
	}





##########################################################################################################
##				T H E M E 	C H O O S E R 		F U N C T I O N S
##########################################################################################################

#mysql> desc THEME_RANKS;
#+-------------+-------------------------+------+-----+---------+----------------+
#| Field       | Type                    | Null | Key | Default | Extra          |
#+-------------+-------------------------+------+-----+---------+----------------+
#| ID          | int(10) unsigned        |      | PRI | NULL    | auto_increment |
#| CREATED_GMT | int(11)                 |      |     | 0       |                |
#| MID         | int(11)                 |      | MUL | 0       |                |
#| MERCHANT    | varchar(20)             |      |     |         |                |
#| WRAPPER     | varchar(30)             |      | MUL |         |                |
#| TYPE        | enum('','DEV','CUSTOM') |      |     |         |                |
#| SELECTED    | tinyint(4)              |      |     | 0       |                |
#+-------------+-------------------------+------+-----+---------+----------------+
#7 rows in set (0.01 sec)




if ($VERB eq 'REMEMBER-WRAPPER') {
	
	my $WRAPPER = $ZOOVY::cgiv->{'wrapper'};
	require TOXML::UTIL;
	&TOXML::UTIL::remember($USERNAME,'WRAPPER',$WRAPPER,1);

	$VERB = 'MYTHEMES';
	}

if ($VERB eq 'FORGET-WRAPPER') {
	
	my $WRAPPER = $ZOOVY::cgiv->{'wrapper'};
	require TOXML::UTIL;
	&TOXML::UTIL::forget($USERNAME,'WRAPPER',$WRAPPER);

	$VERB = 'MYTHEMES';
	}


#mysql> desc THEMES;
#+-----------------+------------------+------+-----+---------+----------------+
#| Field           | Type             | Null | Key | Default | Extra          |
#+-----------------+------------------+------+-----+---------+----------------+
#| ID              | int(11)          |      | PRI | NULL    | auto_increment |
#| NAME            | varchar(30)      |      |     |         |                |
#| CODE            | varchar(15)      |      | UNI |         |                |
#| RANK_POPULARITY | int(10) unsigned |      |     | 0       |                |
#| RANK_REMEMBER   | int(10) unsigned |      |     | 0       |                |
#| CREATED_GMT     | int(11)          |      |     | 0       |                |
#| BW_CATEGORIES   | int(10) unsigned |      |     | 0       |                |
#| BW_COLORS       | int(10) unsigned |      |     | 0       |                |
#| BW_PROPERTIES   | int(10) unsigned |      |     | 0       |                |
#| IS_POPUP        | tinyint(4)       |      |     | 0       |                |
#+-----------------+------------------+------+-----+---------+----------------+

my $pstmt = '';
if ($VERB eq '') { $VERB = 'MYTHEMES'; }
if ($VERB eq 'MYTHEMES') {
	## Show the themes a user has marked as favorite.
	$GTOOLS::TAG{'<!-- MENU_TITLE -->'} = 'My Themes (All Types)';
	$GTOOLS::TAG{'<!-- MENUPOS -->'} = 1;


	# $pstmt = "select TX.* from TOXML TX, TOXML_RANKS TR where TR.MID=$MID and TR.DOCID=TX.DOCID and TR.FORMAT='$DOCTYPE' and TX.CREATED_GMT>0 ";
	$pstmt = "select TX.* from TOXML TX, TOXML_RANKS TR where TR.MID=$MID and TR.DOCID=TX.DOCID and TR.FORMAT='$DOCTYPE' ";
	if ($SUBTYPE eq 'P') { $pstmt .= " and SUBTYPE=".$dbh->quote($SUBTYPE); }
	if ($SUBTYPE eq 'M') { $pstmt .= " and SUBTYPE=".$dbh->quote($SUBTYPE); }

	$pstmt .= " order by TR.ID desc";
	print STDERR $pstmt."\n";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	while ( my $hashref = $sth->fetchrow_hashref() ) {
		push @THEMES, $hashref;
		}

	# my $result = &TOXML::UTIL::listDocs($USERNAME,'WRAPPER',SUBTYPE=>(($SUBTYPE eq '')?undef:$SUBTYPE));
	my $result = &TOXML::UTIL::listDocs($USERNAME,$DOCTYPE);
	if (defined $result) {
		foreach my $ref (@{$result}) {
			next if ($ref->{'MID'}==0);
			$ref->{'WRAPPER_CATEGORIES'} = 1;
			push @THEMES, $ref;
			}
		}

	if (scalar(@THEMES)==0) {
		$template_file = 'body-welcome.shtml';
		}
	else {
		$template_file = 'body-menu.shtml';
		}

	## NOTE: we need pass down MYTHEMES action so we know to add the 'REMOVE' 
	##	$VERB = 'OUTPUT-FAVORITES';
	}

if ($VERB eq 'SEARCH') {
	$GTOOLS::TAG{'<!-- MENU_TITLE -->'} = 'Search Results';
	$GTOOLS::TAG{'<!-- MENUPOS -->'} = 1;
	
	my $PROPERTIES = 0;
	$PROPERTIES += (defined $ZOOVY::cgiv->{'minicart'})?(1<<0):0;
	$PROPERTIES += (defined $ZOOVY::cgiv->{'sidebar'})?(1<<1):0;
	$PROPERTIES += (defined $ZOOVY::cgiv->{'subcats'})?(1<<2):0;
	$PROPERTIES += (defined $ZOOVY::cgiv->{'embed_search'})?(1<<3):0;
	$PROPERTIES += (defined $ZOOVY::cgiv->{'embed_subscribe'})?(1<<4):0;
	$PROPERTIES += (defined $ZOOVY::cgiv->{'embed_login'})?(1<<5):0;
	$PROPERTIES += (defined $ZOOVY::cgiv->{'imagecats'})?(1<<6):0;
	## 1<<9 = wiki text
	## 1<<10 = ajax 

	my $CATEGORIES = int($ZOOVY::cgiv->{'category'});
	my $COLORS = int($ZOOVY::cgiv->{'color'});

	$pstmt = ' FORMAT=\'WRAPPER\' and MID in (0,'.$MID.') ';	
	if ($PROPERTIES>0) { $pstmt .= (($pstmt ne '')?' and ':'')."(PROPERTIES&$PROPERTIES)=$PROPERTIES "; }
	if ($CATEGORIES>0) { $pstmt .= (($pstmt ne '')?' and ':'')."(WRAPPER_CATEGORIES&$CATEGORIES)>0 "; }
	if ($COLORS>0) { $pstmt .= (($pstmt ne '')?' and ':'')."(WRAPPER_COLORS&$COLORS)>0 "; }

	if ($pstmt eq '') {
		## they didn't select anything. FUCKERS!
		}
	else {
		$pstmt = "select * from TOXML where CREATED_GMT>0 and $pstmt";
		}

	print STDERR $pstmt."\n";

	$VERB = 'QUERY';
	}



if ($VERB eq 'FAVORITES') {
	## Show user favorites (rank remember)
	$GTOOLS::TAG{'<!-- MENU_TITLE -->'} = 'Community Favorites (Currently in Use)'; 
	$GTOOLS::TAG{'<!-- MENUPOS -->'} = 2;
	$pstmt = "select * from TOXML where FORMAT='$DOCTYPE' and CREATED_GMT>0 ";
	if ($SUBTYPE eq 'P') { $pstmt .= " and SUBTYPE=".$dbh->quote($SUBTYPE); }
	if ($SUBTYPE eq 'M') { $pstmt .= " and SUBTYPE=".$dbh->quote($SUBTYPE); }
	$pstmt .= " and MID in (0,$MID) order by RANK_SELECTED desc,CREATED_GMT desc limit 0,25";
	$VERB = 'QUERY';
	}

if ($VERB eq 'RECENT') {
	## RECENTLY ADDED
	$GTOOLS::TAG{'<!-- MENU_TITLE -->'} = 'Recently Added'; 
	$GTOOLS::TAG{'<!-- MENUPOS -->'} = 3;
	$pstmt = "select * from TOXML where FORMAT='$DOCTYPE' and CREATED_GMT>0 ";
	if ($SUBTYPE eq 'P') { $pstmt .= " and SUBTYPE=".$dbh->quote($SUBTYPE); }
	if ($SUBTYPE eq 'M') { $pstmt .= " and SUBTYPE=".$dbh->quote($SUBTYPE); }
	$pstmt .= " and MID in (0,$MID) order by CREATED_GMT desc limit 0,25";
	$VERB = 'QUERY';
	}

if ($VERB eq 'STAFF') {
	## Staff Favorites??
	$GTOOLS::TAG{'<!-- MENU_TITLE -->'} = 'Zoovy Favorites'; 
	$GTOOLS::TAG{'<!-- MENUPOS -->'} = 4;
	$pstmt = "select * from TOXML where FORMAT='$DOCTYPE' and CREATED_GMT>0 ";
	if ($SUBTYPE eq 'P') { $pstmt .= " and SUBTYPE=".$dbh->quote($SUBTYPE); }
	if ($SUBTYPE eq 'M') { $pstmt .= " and SUBTYPE=".$dbh->quote($SUBTYPE); }
	$pstmt .= " and MID in (0,$MID) order by CREATED_GMT desc limit 15,25";
	$VERB = 'QUERY';
	}

if ($VERB eq 'SHOWALL') {
	$GTOOLS::TAG{'<!-- MENU_TITLE -->'} = 'All Available'; 
	$GTOOLS::TAG{'<!-- MENUPOS -->'} = 4;
	$pstmt = "select * from TOXML where FORMAT='$DOCTYPE' and CREATED_GMT>0 ";
	if ($SUBTYPE eq 'P') { $pstmt .= " and SUBTYPE=".$dbh->quote($SUBTYPE); }
	if ($SUBTYPE eq 'M') { $pstmt .= " and SUBTYPE=".$dbh->quote($SUBTYPE); }
	$pstmt .= " and MID in (0,$MID) order by CREATED_GMT desc";
	$VERB = 'QUERY';
	}

if ($VERB eq 'RANKED') {
	## RANK REMEMBER
	$GTOOLS::TAG{'<!-- MENU_TITLE -->'} = 'Best Ranked (Most Remembered)'; 
	$GTOOLS::TAG{'<!-- MENUPOS -->'} = 5;
	$pstmt = "select * from TOXML where FORMAT='$DOCTYPE' and CREATED_GMT>0 ";
	if ($SUBTYPE eq 'P') { $pstmt .= " and SUBTYPE=".$dbh->quote($SUBTYPE); }
	if ($SUBTYPE eq 'M') { $pstmt .= " and SUBTYPE=".$dbh->quote($SUBTYPE); }
	$pstmt .= " and MID in (0,$MID) order by RANK_REMEMBER desc,CREATED_GMT desc limit 0,25";
	$VERB = 'QUERY';
	}

if ($VERB eq 'QUERY') {

	print STDERR $pstmt."\n";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	while ( my $hashref = $sth->fetchrow_hashref() ) {
		push @THEMES, $hashref;
		}
	$VERB = 'OUTPUT';
	}


if (($VERB eq 'OUTPUT') || ($VERB eq 'OUTPUT-FAVORITES') || ($VERB eq 'MYTHEMES')) {
	##
	## Build a menu!
	##
	my $out = '';
	my $counter = 0;
	foreach my $t (@THEMES) {
	#	next if (($SUBTYPE ne 'E') && ($t->{'WRAPPER_CATEGORIES'}==0));
		next if (($SUBTYPE eq '') && ($t->{'SUBTYPE'} ne '_') && ($t->{'SUBTYPE'} ne ''));
		next if ($t->{'DOCID'} eq '');
		
		$out .= &format($USERNAME,&lookup_theme($DOCTYPE,$t->{'DOCID'}),$VERB,$counter++,$FLAGS);
		}
	if ($out eq '') { $out = qq~<table><tr><td>Sorry, but no matching themes could be found based on your search parameters.</td></tr></table>~; }

	if (($VERB eq 'OUTPUT-FAVORITES') || ($VERB eq 'MYTHEMES')) {
		## display the currently selected theme.

		my $wrapper = $NSREF->{'zoovy:site_wrapper'};		
		my $popwrapper = $NSREF->{'zoovy:popup_wrapper'};
		my $emailwrapper = $NSREF->{'email:docid'};

		$out = qq~
			<table>
				<tr><td><b>Selected Site Theme:</b><br>
				~.&format($USERNAME,&lookup_theme('WRAPPER',$wrapper),'SELECTED',-1,$FLAGS).qq~</td></tr>				
				~.(($popwrapper ne '')?("<tr><td><b>Selected Popup Theme:</b><br>".&format($USERNAME,&lookup_theme('WRAPPER',$popwrapper),'SELECTED',-1,$FLAGS)."</td></tr>"):'').qq~
				~.(($emailwrapper ne '')?("<tr><td><b>Selected Email Theme:</b><br>".&format($USERNAME,&lookup_theme('EMAIL',$emailwrapper),'SELECTED',-1,$FLAGS)."</td></tr>"):'').qq~
			</table>
			<br><br>

			<b>Remembered $DOCTYPE(s):</b><br>
		~.$out;
		}
	
	$GTOOLS::TAG{'<!-- THEMELIST -->'} = $out; $out = undef;
	$template_file = 'body-menu.shtml';
	## 
	}



###
##
##
##
###
sub lookup_theme {
	my ($doctype,$docid) = @_;
	my $t = {};

	if ($docid eq '') {
		$t->{'TITLE'} = 'Theme Not Set';
		}
	elsif (substr($docid,0,1) eq '~') {
		## Custom Theme
		my ($toxml) = TOXML->new($doctype,$docid,USERNAME=>$USERNAME);
		if (defined $toxml) {
			my ($configel) = $toxml->findElements('CONFIG');	
			## make a copy of the CONFIG element since when $toxml gets deref'd it will call DESTROY and nuke the values
			foreach my $k (keys %{$configel}) {
				$t->{$k} = $configel->{$k};
				}
			}

		if ($t->{'TITLE'} eq '') {
			$t->{'TITLE'} = 'Untitled Custom '.$doctype.': '.$docid;
			}
		$t->{'DOCID'} = $docid;
		$t->{'RANK_SELECTED'} = 100;
		$t->{'RANK_REMEMBER'} = 100;
		$t->{'CREATED_GMT'} = time();
		}
	else {
		my $dbh = &DBINFO::db_zoovy_connect();
		$pstmt = "select * from TOXML where FORMAT='$DOCTYPE' and CREATED_GMT>0 and MID in (0,$MID) and DOCID=".$dbh->quote($docid);
		my $sth = $dbh->prepare($pstmt);
		$sth->execute();
		if ($sth->rows()>0) {
			$t = $sth->fetchrow_hashref();
			}
		else {
			$t->{'TITLE'} = 'Unknown Theme: '.$docid;
			$t->{'DOCID'} = $docid;
			}
		$sth->finish();
		&DBINFO::db_zoovy_connect();
		}

	return($t);
	}



##########################################################################################################
##				G E N E R A L 		F U N C T I O N S
##		(wouldn't these be better suited for WRAPPERS.pm)
##########################################################################################################


sub format {
	my ($USERNAME,$tinfo,$VERB,$counter,$FLAGS) = @_;

	##
	## tinfo - is a copy of the config element in the $toxml file.. but it also has some other
	##		properties we don't find in the config element.
	##

	my $out = '';
	my $thumburl = '//static.zoovy.com/graphics/wrappers/'.$tinfo->{'DOCID'}.'/preview.jpg';
	if ($tinfo->{'FORMAT'} eq 'ZEMAIL') {
		$thumburl = '//static.zoovy.com/graphics/emails/'.$tinfo->{'DOCID'}.'/preview.jpg';
		}

	if ((substr($tinfo->{'DOCID'},0,1) eq '~') || ($tinfo->{'MID'} == $MID)) {
		

		if ($tinfo->{'THUMBNAIL'} eq '') {
			$thumburl = '//www.zoovy.com/biz/images/setup/custom_theme.gif'; 	
			}
		else {
			require IMGLIB::Lite;
			$thumburl = &IMGLIB::Lite::url_to_image($USERNAME,$tinfo->{'THUMBNAIL'},140,100,'FFFFFF',0,0);
			}
		}


#	use Data::Dumper; $out .= "<pre>". Dumper($tinfo). "</pre>";

	my $bgcolor = (($counter%2)?'table_top':'table_head');
	if ($counter==-1) { $bgcolor = 'table_head'; }

	if ($tinfo->{'TITLE'} eq '') { 
		$tinfo->{'TITLE'} = $tinfo->{'DOCID'}.' Untitled'; 
		}
	
	$out .= "<!-- START: $tinfo->{'DOCID'} -->\n";
	$out .= "<table cellspacing=0 cellpadding=0 border=0 width=\"90%\" class=\"$bgcolor\">\n";
	$out .= "<tr><td>\n";
	$out .= "<table cellspacing=1 cellpadding=0 border=0 width=\"100%\"><tr>";	

	$out .= "<td bgcolor=\"#FFFFFF\" valign=\"top\" width=\"1%\">";
	if ($tinfo->{'DOCID'} ne '') {
		$out .= "<img width=140 height=100 src=\"$thumburl\"></td>";
		}
	$out .= "</td>";
	$out .= "<td bgcolor=\"#FFFFFF\" valign=\"top\" width=\"400\" align=\"left\" style=\"padding: 4px;\">";
	$out .= "<strong>$tinfo->{'TITLE'}</strong><br>";

	if ($tinfo->{'DOCID'} ne '') {
		$out .= "Document: $tinfo->{'DOCID'}<br>\n";
		}

	if ($tinfo->{'CREATED'} ne '') {
		$out .= "Created: $tinfo->{'CREATED'}<br>\n";
		}

	if ($tinfo->{'AUTHOR'} ne '') {
		$out .= "Author: $tinfo->{'AUTHOR'}<br>\n";
		}


	if ($tinfo->{'PROJECT'} ne '') {
		$out .= "Project: $tinfo->{'PROJECT'}<br>\n";
		}

	if (($FLAGS =~ /,EBAY,/) && (defined $tinfo->{'BW_PROPERTIES'})) {
		$out .= "Matching Wizard: ".( (($tinfo->{'BW_PROPERTIES'}&(1<<13))>0)?'Yes':'No' )."<br>";
		}

	if (substr($tinfo->{'DOCID'},0,1) eq '~') {}
	elsif ($tinfo->{'RANK_REMEMBER'}>0) { 
		$out .= "Popularity: $tinfo->{'RANK_REMEMBER'}<br>\n"; 
		}


	my $list = '';
	foreach my $i (0..13) { 
		if (($tinfo->{'PROPERTIES'} & (1<<$i))>0) { $list .= ' '.$TOXML::BW_PROPERTIES{1<<$i}.','; } 
		}
	chop($list);
	if ($list eq '') { $list = 'None'; }


	if ($tinfo->{'OVERLOAD'} ne '') {
		$out .= "OverLoads: ";
		my ($ref) = &ZTOOLKIT::parseparams($tinfo->{'OVERLOAD'});
		foreach my $k (keys %{$ref}) {
			my $pretty = $k;
			if ($k eq 'defaultflow.c') { $pretty = "Default Category Layout ($k)"; }
			elsif ($k eq 'defaultflow.p') { $pretty = "Default Product Layout ($k)"; }
			elsif ($k =~ /flow\.(.*?)$/) { $pretty = "Forced $1 ($k)"; }
			$out .= "<div style='margin-left: 10px;'>&#187; $pretty = $ref->{$k}</div>";
			}
		}

	if (substr($tinfo->{'DOCID'},0,1) ne '~') {
		$out .= "Features: $list<br>"; 
		}

	if (($VERB eq 'MYTHEMES') || ($VERB eq 'SELECTED')) {
		if ($tinfo->{'SUBTYPE'} eq 'P') {
			$out .= "<font color='red'>*** THIS IS A POPUP WRAPPER ***<br></font>";
			}
		}

	$list = '';
	foreach my $i (0..15) {	
		if (($tinfo->{'WRAPPER_CATEGORIES'} & (1<<$i))>0) { $list .= ' '.$TOXML::BW_CATEGORIES{1<<$i}.','; } 		
		}
	chop($list);
	if ($list eq '') { $list = 'None'; }
	if (substr($tinfo->{'DOCID'},0,1) ne '~') {
		$out .= "Categories: $list<br>";
		}

	if ($tinfo->{'SITEBUTTONS'} ne '') {
		my $pretty = $tinfo->{'SITEBUTTONS'};
		if (index($tinfo->{'SITEBUTTONS'},'|')<=0) {
			$/ = undef;
			open F, "</httpd/static/graphics/sitebuttons/$tinfo->{'SITEBUTTONS'}/info.txt"; 
			$tinfo->{'SITEBUTTONS'} = <F>; 
			close F;
			$/ = "\n";
			}
		else {
			$pretty = 'Custom Set';
			}
		$out .= "Buttons: $pretty<br>";
		
		$SITE::CONFIG = $tinfo;
		$SITE::CONFIG->{'%SITEBUTTONS'} = &ZTOOLKIT::parseparams($tinfo->{'SITEBUTTONS'});
		my ($SITE) = SITE->new($USERNAME,PRT=>$PRT);

		$out .= "<div>";
		foreach my $b ('add_to_cart','cancel','back','forward','|','empty_cart','checkout','continue_shopping','update_cart') {
			if ($b eq '|') { $out .= "<br>"; }
			next if ($b eq '|');
			$out .= "<!-- $b -->";
			$out .= TOXML::RENDER::RENDER_SITEBUTTON({button=>$b},undef,$SITE);
			$out .= " ";
			}
		$out .= "</div>";
		}
	
	# $out .= "<pre>".Dumper($tinfo)."</pre>";
	$out .= "</td></tr></table>";
	$out .= "</td></tr>\n";

	if ($tinfo->{'DOCID'} ne '') {

		$out .= qq~<tr>
			<td width=99%><table width="100%"><tr>
				<td NOWRAP><span class="light_text">~;

		if ($tinfo->{'FORMAT'} ne 'ZEMAIL') {
			$out .= qq~<a target="_preview" href="http://www.zoovy.com/biz/preview.cgi?url=$DOMAIN/%3Fwrapper=$tinfo->{'DOCID'}" class="light_text">Preview</a>~;
			}

		if ($VERB eq 'MYTHEMES') {
			$out .= qq~
			| <a href="/biz/setup/builder/themes/index.cgi?SUBTYPE=$SUBTYPE&NS=$NS&VERB=FORGET-WRAPPER&wrapper=$tinfo->{'DOCID'}" class="light_text">Forget</a>
			~;
			}

		if ($VERB ne 'SELECTED') {
			## selected is when we are showing a box for a selected theme.
			if ($SUBTYPE eq 'P') {
				$out .= qq~| <a href="/biz/setup/builder/themes/index.cgi?SUBTYPE=$SUBTYPE&NS=$NS&VERB=SAVE-POPUP&wrapper=$tinfo->{'DOCID'}" class="light_text"><strong>Select</strong></a>~;
				}
			elsif ($SUBTYPE eq 'M') {
				$out .= qq~| <a href="/biz/setup/builder/themes/index.cgi?SUBTYPE=$SUBTYPE&NS=$NS&VERB=SAVE-MOBILE&wrapper=$tinfo->{'DOCID'}" class="light_text"><strong>Select</strong></a>~;
				}
			elsif ($SUBTYPE eq 'E') {
				$out .= qq~| <a href="/biz/setup/builder/themes/index.cgi?SUBTYPE=$SUBTYPE&NS=$NS&VERB=SAVE-ZEMAIL&wrapper=$tinfo->{'DOCID'}" class="light_text"><strong>Select Email</strong></a>~;
				}
			else {
				$out .= qq~| <a href="/biz/setup/builder/themes/index.cgi?SUBTYPE=$SUBTYPE&NS=$NS&VERB=SAVE-WRAPPER&wrapper=$tinfo->{'DOCID'}" class="light_text"><strong>Select</strong></a>~;
				}
			}

		if ($VERB eq 'OUTPUT') {
			## don't offer to remember a them when we are already showing remembered themes.
			$out .= qq~
			| <a href="/biz/setup/builder/themes/index.cgi?SUBTYPE=$SUBTYPE&NS=$NS&VERB=REMEMBER-WRAPPER&wrapper=$tinfo->{'DOCID'}" class="light_text">Remember</a>
			~;
			}
	

		$out .= qq~
			</td>
			</tr></table>

</td>
</tr>
</table><br>
			~;	
		}

	return($out);
	}



&GTOOLS::output(
	file=>$template_file,
	header=>1,
	bc=>\@BC,
	tabs=>\@TABS,
	help=>$help,
	title=>"Theme Chooser",
	);
&DBINFO::db_zoovy_close();











sub strip_filename
{
   my ($filename) = @_;

	my $ext = "";
	my $name = "";
	print STDERR "upload.cgi:strip-filename says filename is: $filename\n";
	my $pos = rindex($filename,'.');
	print STDERR "upload.cgi:strip_filename says pos is: $pos\n";
	if ($pos>0)
		{
		$name = substr($filename,0,$pos);
		$ext = substr($filename,$pos+1);
		
		# lets strip name at the first / or \ e.g. C:\program files\zoovy\foo.gif becomes "foo.gif"
		$name =~ s/.*[\/|\\](.*?)$/$1/;
		# allow periods, alphanum, tildes and dashes to pass through, kill any other special characters
		$name =~ s/[^\w\-\.~]+/_/g;
		# now, remove duplicate periods
		$name =~ s/[\.]+/\./g;
		
		} else {
		# very bad filename!! ?? what should we do!
		}

	# we should probably do a bit more sanity on the filename right here

	print STDERR "upload.cgi:strip_filename says name=[$name] extension=[$ext]\n";
	return($name,$ext);
}
