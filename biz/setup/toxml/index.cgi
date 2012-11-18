#!/usr/bin/perl

no warnings 'once'; # Keeps perl from bitching about variables used only once.

use strict;
use CGI;
use Data::Dumper;

use lib "/httpd/modules";
require TOXML::UTIL;
require TOXML::COMPILE;
require GTOOLS;
require ZOOVY;
require ZWEBSITE;
require LUSER;
require SITE;

my ($LU) = LUSER->authenticate(flags=>'_S&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

$::DENIEDMSG = q~
We're very sorry, however the source code of the file you requested is NOT available for 
download and/or modification.<br>
<br> 
Usually this means the file is classified as a "prototype" or "concept" which contains new functionality 
that is NOT intended for public consumption/usage at this time. Usually this is to specifically limit the 
widespread deployment of the particular technology since we expect it to change.<br>
<br>

Some files may never be exported, simply because the technology which is contained within is so difficult to
support that we do not feel that we will be able to adequately support the resulting "forks" that will
inevitably result if the source code is made public. <br>
<br>

If you would like to have changes made to this particular file it will more than likely be considered as
part of a custom graphic design package. Please contact Zoovy Sales at 877-966-8948 x 2 for more information
on how to get this done.
~;

my @MSGS = ();

push @MSGS, "LEGACY|June 2012 Deprecation Notice: the TOXML format is being sunsetted on or after Jan 1st, 2015


Technical support for this format will cease for this feature in June 2013, and we expect to turn off toxml site hosting in 2015. 
Originally developed for compatibility with HTML 3.0 - the toxml format itself will be over 15 years old (thats 6 years old than CSS is), 
and it's past-due for a fresh clean start. 
We are building sites based on the AnyCommerce jQuery Application Framework, which is a pure CSS3+HTML+Javascript approach for building dynamic websites and mobile applications.
The source code is hosted on github and can quickly be forked, customized, and then an application project can be  in Setup / Projects which automatically updates from the github repository after a commit 
(making updates VERY fast and painless) in addition to giving painless version tracking, and awesome rollback capabilities normally associated
with github.  Zoovy backends are 100% compatible with the AnyCommerce App framework. 
It takes a typical developer about 10 hours to learn the AnyCommerce App Framework.
";

my @TABS = ();
## determine tabs available 
## WEB flag should see layout and wrapper tabs
if (index($FLAGS,',WEB,') > 0 ) {
	push @TABS, { name=>'Wrappers', link=>'/biz/setup/toxml/index.cgi?FORMAT=WRAPPER', },
					{ name=>'Layouts', link=>'/biz/setup/toxml/index.cgi?FORMAT=LAYOUT', },
					{ name=>'Emails', link=>'/biz/setup/toxml/index.cgi?FORMAT=ZEMAIL', },
					{ name=>'Orders', link=>'/biz/setup/toxml/index.cgi?FORMAT=ORDER', },
	}
## EBAY flag should see the wizard tab
if (index($FLAGS,',EBAY,') > 0 ) {
	push @TABS, { name=>'Wizards', link=>'/biz/setup/toxml/index.cgi?FORMAT=WIZARD', };
	}

## API flag should see the definitions and includes tabs
if (index($FLAGS,',API,') > 0 ) {				
	push @TABS, { name=>'Definitions', link=>'/biz/setup/toxml/index.cgi?FORMAT=DEFINITION', },
					{ name=>'Includes', link=>'/biz/setup/toxml/index.cgi?FORMAT=INCLUDE', };
	}

## no authorization to edit TOXML
push @TABS, { name=>'Help', link=>'/biz/setup/toxml/index.cgi?ACTION=HELP', };

my $q = new CGI;
my $ACTION = $ZOOVY::cgiv->{'ACTION'};
print STDERR "ACTION: $ACTION\n";


my $FORMAT = $ZOOVY::cgiv->{'FORMAT'};
if ($ACTION eq 'DOWNLOAD') {}
elsif ($FORMAT eq '') { $ACTION = ''; }	# all other actions require a mode be set

my $DOCID = $ZOOVY::cgiv->{'DOCID'};

#print "Content-type: text/plain\n\n"; print Dumper($ZOOVY::cgiv,$ACTION); die();

## choices from top page
if ($ACTION eq "Edit XML") {	
	&ZWEBSITE::save_website_attrib($USERNAME,'pref_template_fmt',uc($q->param('TYPE')));
	if ($q->param('TYPE') eq "xml") { $ACTION = "EDITXML"; }
	elsif ($q->param('TYPE') eq "html") { $ACTION = "EDITHTML"; }
	# elsif ($q->param('TYPE') eq "plugin") { $ACTION = "EDITPLUGIN"; }
	else { $ACTION = ''; $GTOOLS::TAG{'<!-- MESSAGE -->'} = "Please choose a File Format ".$q->param('TYPE'); } 
	}

$GTOOLS::TAG{'<!-- FORMAT -->'} = $FORMAT;

## link for WEBDOC
my ($helplink, $helphtml) = GTOOLS::help_link('Template Syntax',50251);
$GTOOLS::TAG{'<!-- WEBDOC -->'} = $helphtml;

my $template_file = 'index.shtml';
my $header = 1;


print STDERR "ACTION=$ACTION FORMAT=$FORMAT DOCID=$DOCID\n";


my @BC = ();
push @BC, 	{ name=>'Setup',link=>'/biz/setup','target'=>'_top', },
      	 	{ name=>'Template Manager',link=>'/biz/setup/toxml/index.cgi?ACTION=HELP','target'=>'_top', };
    



if (($ACTION eq 'EDITXML') || ($ACTION eq 'EDITHTML') || ($ACTION eq 'EDITPLUGIN')) {
	$GTOOLS::TAG{'<!-- DOCID -->'} = $DOCID;
		
	$DOCID = '*'.$DOCID;
	my ($toxml) = TOXML->new($FORMAT,$DOCID,USERNAME=>$USERNAME,MID=>$MID);
	my ($cfg) = $toxml->findElements('CONFIG');

	if ($LU->is_zoovy()) { $cfg->{'EXPORT'} = 1; }

	if ((defined $cfg->{'EXPORT'}) && ($cfg->{'EXPORT'}==0)) {
		$GTOOLS::TAG{'<!-- AS_TYPE -->'} = 'forbidden';
		$GTOOLS::TAG{'<!-- CONTENT -->'} = $::DENIEDMSG;
		}
	elsif ($ACTION eq 'EDITXML') {
		$GTOOLS::TAG{'<!-- AS_TYPE -->'} = ' as Strict XML';
		$GTOOLS::TAG{'<!-- CONTENT -->'} = &ZOOVY::incode($toxml->as_xml());
		}
	elsif ($ACTION eq 'EDITHTML') {
		$GTOOLS::TAG{'<!-- AS_TYPE -->'} = ' as HTML';
		$GTOOLS::TAG{'<!-- CONTENT -->'} = &ZOOVY::incode($toxml->as_html());
		}
	elsif ($ACTION eq 'EDITPLUGIN') {
      $GTOOLS::TAG{'<!-- AS_TYPE -->'} = ' as Plugin';
      $GTOOLS::TAG{'<!-- CONTENT -->'} = &ZOOVY::incode($toxml->as_html(1));
      }
	
	$template_file = 'edit.shtml';
	}


if ($ACTION eq 'SAVEAS') {
	## when the user does a raw edit.
	# load the flow style
	my ($CTYPE,$FLAGS,$SHORTNAME,$LONGNAME) = ();

	$DOCID =~ s/[^\w\-\_]+//gs;
	if ($DOCID eq '') { $DOCID = 'unnamed_'.time(); }
	$DOCID = '*'.$DOCID;
	
	my $content = '';
 	if (not defined $q->param('CONTENT')) {
		my $ORIGDOCID = $q->param('ORIGDOCID');
		my ($toxml) = TOXML->new($FORMAT,$ORIGDOCID,USERNAME=>$USERNAME,MID=>$MID);

		if (defined $toxml) { $content = $toxml->as_xml(); }
		else { warn("TOXML Could not load $FORMAT, $DOCID,USERNAME=>$USERNAME,MID=>$MID\n"); }

		my ($cfg) = $toxml->findElements('CONFIG');
		if ((defined $cfg->{'EXPORT'}) && ($cfg->{'EXPORT'}==0)) {
			$content = $::DENIEDMSG;
			}
		}
	else {
		$content = $q->param('CONTENT');
		}
	
	$GTOOLS::TAG{'<!-- DOCID -->'} = $DOCID;

	my ($toxml) = TOXML::COMPILE::fromXML($FORMAT,$DOCID,$content,USERNAME=>$USERNAME,MID=>$MID);
	if (defined $toxml) {
		$LU->log("SETUP.TOXML","Edited TOXML file FORMAT=$FORMAT DOCID=$DOCID","SAVE");
		$toxml->save(LUSER=>$LUSERNAME);
		$DOCID = $toxml->docId();
		print STDERR "saving toxml: $DOCID as a $FORMAT\n";

		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<font color='blue'>successfully saved $DOCID</font>\n";
		}
	else {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<font color='red'>could not save $DOCID</font>\n";
		}
	$ACTION = '';
	}


if ($ACTION eq 'DOWNLOAD') {
	my $DOCID = $q->param('DOCID');
	$GTOOLS::TAG{'<!-- DOCID -->'} = $DOCID;

	my ($toxml) = TOXML->new($FORMAT,$DOCID,USERNAME=>$USERNAME,MID=>$MID);
	my $cfg = undef;
	my ($cfg) = $toxml->findElements('CONFIG');
	my $content = '';
	
	if ((defined $cfg->{'EXPORT'}) && ($cfg->{'EXPORT'}==0)) {
		$content = "<font color='red'>".$::DENIEDMSG.'</font>';
		}
	else {
		$content = &ZOOVY::incode($toxml->as_xml());
		$content =~ s/[\n\r]+/<br>/g;
		$content =~ s/&lt;ELEMENT/<font color='blue'>&lt;ELEMENT/gs;
		$content =~ s/\/ELEMENT&gt;/\/ELEMENT&gt;<\/font>/gs;
		}

	$GTOOLS::TAG{'<!-- CONTENT -->'} = $content;
	$template_file = 'output.shtml';
	}

if ($ACTION eq 'DELETE') {
	my $DOCID = $q->param('DOCID');
	my ($toxml) = TOXML->new($FORMAT,$DOCID,USERNAME=>$USERNAME,MID=>$MID);
	$toxml->nuke();
	$LU->log("SETUP.TOXML","Confirmed deletion of DOCTYPE:$FORMAT DOC:$DOCID","NUKE");
	
	$GTOOLS::TAG{'<!-- MESSAGE -->'} = "Removed $DOCID\n";
	$ACTION = '';
	}


print STDERR "ACTION: $ACTION\n";
#if ($ACTION eq 'UPLOAD') {
#	my $fh = $q->upload("FILENAME");
#	my $BUFFER = "";
#	my $filename = $q->param("FILENAME");
#	if (!defined($filename)) { $filename = time(); }
#	while (<$fh>) { $BUFFER .= $_; }
#	print STDERR "file is: $filename\n";
#
#
#	my $DOCID = $q->param('DOCID');
#	if ($DOCID eq '') { $DOCID = lc($filename); }
#	$DOCID =~ s/[^\w\-\_]+//gs;
#	if (substr($DOCID,0,1) ne '~') { $DOCID = "~$DOCID"; }
#	## Grab the preview image if one exists.
#	my $ERROR = undef;
#
#	if ($BUFFER !~ /CONFIG/) { $ERROR = "Document does not have a valid CONFIG element (this can't possibly work)"; }
#
#	my $toxml = undef; 
#	if (defined $ERROR) {
#		## shit already happened.
#		}
#	elsif (($filename =~ /\.xml$/) || ($filename =~ /\.html/)) {
#		($toxml) = TOXML::COMPILE::fromXML($FORMAT,$DOCID,$BUFFER,USERNAME=>$USERNAME,MID=>$MID);
#		my ($configel) = $toxml->findElements('CONFIG');
#		if ($toxml->{'_HASERRORS'}) {
#			$ERROR = 'page layout contains errors.';
#			}
#		elsif (not defined $configel) {
#			$ERROR = 'could not load config element from compiled toxml document'; 
#			# $ERROR = &ZOOVY::incode(Dumper($toxml));
#			}
#		else {
#			$LU->log("SETUP.TOXML","Uploaded TOXML file FORMAT=$FORMAT DOCID=$DOCID","SAVE");
#			$toxml->save(LUSER=>$LUSERNAME);
#			}
#		}
#	else {
#		$ERROR = "File must end in either .xml or .html extension";
#		}
#
#	if (defined $ERROR) {
#		## shit already happened!
#		}
#	elsif (not defined $toxml) {
#		$ERROR = 'unknown file type - must be .xml, .html, or .flow';
#		}
#	elsif ((defined $toxml) && (ref($toxml) eq 'TOXML')) {
#		my $path = &ZOOVY::resolve_userpath($USERNAME).'/TOXML';
#		my $BUFFER = '';
#		my $fh = $q->upload("IMGFILENAME");
#		my $filename = $q->param("IMGFILENAME");
#		if (!defined($filename)) { $filename = time(); }
#		while (<$fh>) { $BUFFER .= $_; }
#		print STDERR "file is: $filename\n";
#	
#		if ($BUFFER ne '') {
#			open F, ">$path/$DOCID.gif";
#			print F $BUFFER;
#			close F;
#			}
#	
#		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "successfully uploaded type=$FORMAT docid=$DOCID";
#		}
#	else {
#		$ERROR = "Unknown error (but toxml object was definitely not returned from compile)";
#		}
#
#	if (defined $ERROR) {
#		$GTOOLS::TAG{'<!-- MESSAGE -->'} = $ERROR;
#		warn "ERROR: $ERROR\n";
#		}
#	$ACTION = '';
#	}
#

if ($ACTION eq 'ACKDELETE') {
	$GTOOLS::TAG{'<!-- DOCID -->'} = $q->param('DOCID');
	$template_file = 'confirmdelete.shtml';
	}


if ($ACTION eq 'TOP') {
	my $c = '';
	foreach my $k (sort keys %{$TOXML::UTIL::LAYOUT_STYLES}) {
		my $short = $TOXML::UTIL::LAYOUT_STYLES->{$k}[0];
		my $long = $TOXML::UTIL::LAYOUT_STYLES->{$k}[1];
		$c .= "<option value='$k'>$short</option>";
	}
	$GTOOLS::TAG{'<!-- FLOWSTYLE -->'} = $c;

	## Load the custom theme list.
	$c = '';
	my $arref = &TOXML::UTIL::listDocs($USERNAME,$FORMAT,DETAIL=>1);
	foreach my $inforef (@{$arref}) {
		next unless ($inforef->{'MID'}>0); 
		print STDERR Dumper($inforef);

		my $k = $inforef->{'DOCID'};
		my $name = $inforef->{'TITLE'};	

		# only look at userland flows
		$c .= "<a href='/biz/setup/toxml/index.cgi?ACTION=EDITXML&DOCID=".CGI->escape($k)."'>[EDIT XML]</a> ";
		$c .= "<a href='/biz/setup/toxml/index.cgi?ACTION=ACKDELETE&DOCID=".CGI->escape($k)."'>[REMOVE]</a> ($k) $name<br>\n";
		}
	if ($c eq '') { $c = '<i>None</i>'; }
	$GTOOLS::TAG{'<!-- EXISTINGFLOWS -->'} = $c;

	## Load the full theme list for the select boxetemplates
	my $arref = &TOXML::UTIL::listDocs($USERNAME,$FORMAT,DETAIL=>1);
	$c = '';
	foreach my $inforef (reverse @{$arref}) {
		# only look at userland flows
		my $DOCID = $inforef->{'DOCID'};
		my $SUBTYPE = $inforef->{'SUBTYPE'};
		my $SUBTYPETXT = $TOXML::UTIL::LAYOUT_STYLES->{$SUBTYPE}[0];
		$c .= "<option value=\"$DOCID\">[$DOCID] $SUBTYPETXT: $inforef->{'TITLE'}</option>\n";
		}
	undef $arref;
	$GTOOLS::TAG{'<!-- ALLLAYOUTS -->'} = $c;
	
	$template_file = 'top.shtml';
	}

## Display top page for managing each FORMAT
if ($ACTION eq 'HELP') {
	$template_file = 'index.shtml';
	}









##
## saves theme and button settings into the wrapper (by physically modifying the wrapper)
##
if ($ACTION eq 'SAVE-SITEBUTTONS') {
	# Saves the site buttons and theme for a wrapper
	require TOXML::UTIL;

	my ($toxml) = TOXML->new('WRAPPER',$DOCID,USERNAME=>$USERNAME,MID=>$MID);
	my ($configel) = $toxml->findElements('CONFIG');

	my $sbtxt = $ZOOVY::cgiv->{'sitebuttons'};
	if ($sbtxt eq '') { $sbtxt = $ZOOVY::cgiv->{'sitebuttons_txt'}; }	
	if ($sbtxt eq '') { $sbtxt = 'default'; } ## yipes!?!?

	if (index($sbtxt,'|')==-1) {
		## passing an old button reference, lets load it out of info.txt
		$sbtxt =~ s/[^a-z0-9\_]+//gs;	# strip bad characters
		if (open F, "</httpd/static/sitebuttons/$sbtxt/info.txt") {
			$/ = undef; $sbtxt = <F>; $/ = "\n";
			close F;
			}
		}
	$configel->{'SITEBUTTONS'} = $sbtxt;
	$toxml->save(LUSER=>$LUSERNAME);
	$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<center><font face='helvetica, arial' color='red' size='5'><b>Successfully Saved!</b></font></center><br><br>";;

	$ACTION = '';	
	$FORMAT = 'WRAPPER';
	}



##
## Gives the user an editor for the site buttons and theme associated with a wrapper
##
if ($ACTION eq 'SITEBUTTONS') {

	my ($SITE) = SITE->new($USERNAME,'PRT'=>$PRT);

	require TOXML::UTIL;
	my ($toxml) = TOXML->new('WRAPPER',$DOCID,USERNAME=>$USERNAME,MID=>$MID);
	my ($config) = $toxml->initConfig($SITE);
	my ($configel) = $toxml->findElements('CONFIG');

	$GTOOLS::TAG{'<!-- DOCID -->'} = $DOCID;	
	my $out = '';
	my $c = '';

	$GTOOLS::TAG{'<!-- BUTTON_PREVIEW -->'} = "<tr>".
		"<td>".&TOXML::RENDER::RENDER_SITEBUTTON({'TYPE'=>'BUTTON',BUTTON=>'add_to_cart'},$toxml)."</td>".
		"<td>".&TOXML::RENDER::RENDER_SITEBUTTON({'TYPE'=>'BUTTON',BUTTON=>'continue_shopping'},$toxml)."</td>".
		"<td>".&TOXML::RENDER::RENDER_SITEBUTTON({'TYPE'=>'BUTTON',BUTTON=>'update_cart'},$toxml)."</td>".
		"<td>".&TOXML::RENDER::RENDER_SITEBUTTON({'TYPE'=>'BUTTON',BUTTON=>'back'},$toxml)."</td>".
		"</tr><tr>".
		"<td>".&TOXML::RENDER::RENDER_SITEBUTTON({'TYPE'=>'BUTTON',BUTTON=>'cancel'},$toxml)."</td>".
		"<td>".&TOXML::RENDER::RENDER_SITEBUTTON({'TYPE'=>'BUTTON',BUTTON=>'empty_cart'},$toxml)."</td>".
		"<td>".&TOXML::RENDER::RENDER_SITEBUTTON({'TYPE'=>'BUTTON',BUTTON=>'checkout'},$toxml)."</td>".
		"<td>".&TOXML::RENDER::RENDER_SITEBUTTON({'TYPE'=>'BUTTON',BUTTON=>'forward'},$toxml)."</td>".
		"</tr>";
		
	$GTOOLS::TAG{'<!-- SITEBUTTONS_TXT -->'} = $configel->{'SITEBUTTONS'};
	if (open SITEBUTTONS, "</httpd/static/sitebuttons.txt") {
		while (<SITEBUTTONS>) {
			my ($code, $name, $format) = split(/\t/,$_,3);
			if ($name eq '') { $name = $code; }
			if ($format eq '') { $format = 'gif'; }

				$c .= qq~
			<tr>
				<td><input type="radio" name="sitebuttons" value="$code"></td>
				<td>$name</td>
				<td><img src="http://proshop.zoovy.com/graphics/sitebuttons/$code/add_to_cart.$format"></td>
				<td><img src="http://proshop.zoovy.com/graphics/sitebuttons/$code/update_cart.$format"></td>
			</tr>
			~;
			}
		}

	$GTOOLS::TAG{'<!-- BUTTON_LIST -->'} = $c;
	$template_file = 'wrapper-site-buttons.shtml';
	}






if ($ACTION eq '') {
	$template_file = "modes.shtml";

	my $pretty = lc($FORMAT);
	if ($FORMAT eq '') { $pretty = 'templates'; }
	$pretty =~ s/_/ /g;
	$GTOOLS::TAG{'<!-- FORMAT_PRETTY -->'} = ucfirst($pretty);


#	if ($FORMAT ne '') {
#	$GTOOLS::TAG{'<!-- UPLOAD_FORM -->'} = qq~
#<!-- begin upload new-->
#<form action='/biz/setup/toxml/index.cgi' method='POST' enctype='multipart/form-data'>
#<input type='hidden' name='ACTION' value='UPLOAD'>
#<input type='hidden' name='FORMAT' value='$FORMAT'>
#<table width='800' border='0' cellpadding='0' cellspacing='0' class="zoovytable" align='center'>
#<thead>
#<tr>
#	<th class='zoovytableheader'>Add New <!-- FORMAT_PRETTY --></th>
#</tr>
#</thead>
#<tr>
#	<td align="center">
#	<table border='0' cellpadding='5' border='0' cellspacing='0'>
#	<tr>
#		<td align="right"><b>File:</b></td>
#		<td align="left"><input type='file' name='FILENAME'></td>
#	</tr>
#	<tr>
#		<td align="right"><b>Name:</b></td>
#		<td align="left"><input type='textbox' name='DOCID' class='form_text' style='width:200px;'></td>
#	</tr>
#	<tr>
#		<td align="right"><b>Thumbnail Image:</b></td>
#		<td align="left"><input type='file' name='IMGFILENAME'> (optional - GIF format)</td>
#	</tr>
#	<tr>
#		<td colspan='2' align='center'><input type='submit' value='  Upload  ' class='button2'></td>
#	</tr>
#	</table>
#	
#	</td>
#</tr>
#</table>
#</form>
#<!-- end upload new-->
#~;
#	}


	## Load the full theme list.
	my $c = '';
	my $z = '';
	## BLANK LISTS ALL
	my $arref = &TOXML::UTIL::listDocs($USERNAME,$FORMAT,DETAIL=>1);
	my $ctr =0;

	my $c_row = "r0";  #tables.css alternates the class on the row between r0 and r1.
   my $z_row = "r0";

	foreach my $inforef (sort @{$arref}) {
		$ctr++;
		#last if $ctr > 20;
		#print STDERR Dumper($inforef);
		my $TITLE = $inforef->{'TITLE'};
		if ($TITLE eq '') { $TITLE = '<i>Title Not Set</i>'; }
		my $DOCID = $inforef->{'DOCID'};
		my $SUBTYPE = $inforef->{'SUBTYPE'};
		my $SUBTYPETXT = $TOXML::UTIL::LAYOUT_STYLES->{$SUBTYPE}[0];

		#my $configel = TOXML::just_config_please($USERNAME,$FORMAT,$DOCID);		
		my ($MID) = &ZOOVY::resolve_mid($USERNAME);
		my ($t) = TOXML->new($inforef->{'FORMAT'},"$DOCID",USERNAME=>$USERNAME,MID=>$MID);
		my $configel = undef;
		if (defined $t) {
			($configel) = $t->findElements('CONFIG');	# fetch the first CONFIG element out of the document.	
			}

		## CUSTOM TOXML
		if ($inforef->{'MID'}>0) {
			# only look at userland flows

			my $pref_fmt = &ZWEBSITE::fetch_website_attrib($USERNAME,'pref_template_fmt');
			my $html_checked = ($pref_fmt eq 'HTML')?'checked':'';
			my $xml_checked = ($pref_fmt eq 'XML')?'checked':'';
			# my $plugin_checked = ($pref_fmt eq 'PLUGIN')?'checked':'';

			$c .= qq~
					<tr class="$c_row">
						<td>$inforef->{'FORMAT'}.$DOCID
							<a href="/biz/setup/toxml/index.cgi?ACTION=ACKDELETE&FORMAT=$FORMAT&DOCID=$DOCID">
							<font color=red size="-3"><i>(remove)</i></font></a></td>
						<td>$TITLE</td> 
						<td align="right" nowrap>
							<button onClick="navigateTo('/biz/setup/toxml/index.cgi?DOCID=$DOCID&FORMAT=$inforef->{'FORMAT'}&TYPE=xml'); return false;">Edit XML</button>
							~;
## Removed this per JT since its broked and unnecessary - 5/19/10
#			if ($FORMAT eq 'WRAPPER') {
#				$c .= qq~
#					<form action="/biz/setup/toxml/index.cgi" method="GET" style='display:inline;'>
#						<input type=hidden name="DOCID" value="$DOCID">
#						<input type=hidden name="FORMAT" value="$FORMAT">
#						<input type=hidden name="ACTION" value="SITEBUTTONS">
#						<input type=submit class="button" value="Site Buttons">
#					</form>
#					~;
#				}

			$c .= qq~
					</td></tr>~;
			$c_row = ($c_row eq "r1")?"r0":"r1";
			}

		## Zoovy TOXML
		elsif ($DOCID eq '') {
			}
		else {
			$z .= qq~
					<tr class="$z_row">
						<td>$DOCID</td>
						<td>$TITLE</td>
						<td align="right" nowrap>
						<a href="/biz/setup/toxml/index.cgi?ACTION=DOWNLOAD&FORMAT=$inforef->{'FORMAT'}&DOCID=$DOCID">[ View/Copy ]</a></td>
					</tr>~;
			$z_row = ($z_row eq "r1")?"r0":"r1";
			}			
		}

	if ($c eq '') { $c = '<i>None</i>'; }
	if ($z eq '') { $z = '<i>None</i>'; }
	
	$GTOOLS::TAG{'<!-- CUSTOM_TOXML -->'} = $c;
	$GTOOLS::TAG{'<!-- ZOOVY_TOXML -->'} = $z;

	undef $arref;
	}


&GTOOLS::output(
   'title'=>'Setup : TOXML Manager',
   'file'=>$template_file,
   'header'=>1,
	'msgs'=>\@MSGS,
   'help'=>'#50156',
	'*LU'=>$LU,
   'tabs'=>\@TABS,
   'bc'=>\@BC,
   );



