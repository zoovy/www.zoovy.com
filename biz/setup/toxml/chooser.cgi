#!/usr/bin/perl

no warnings 'once'; # Keeps perl from bitching about variables used only once.

use strict;
use CGI;
use Data::Dumper;

use lib "/httpd/modules";
require TOXML::UTIL;
require TOXML::COMPILE;
require GTOOLS;
require GTOOLS::Table;
require ZOOVY;

&ZOOVY::init();

my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("/biz/setup",2,'_S&2');
if ($USERNAME eq '') { exit; }
$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;

if (index($FLAGS,',WEB,')==-1 ) {
	$GTOOLS::TAG{'<!-- FLAGS -->'} = $FLAGS;
	print "Content-type: text/html\n\n";
	&GTOOLS::print_form('','deny.shtml');
	exit;
	}

my $q = new CGI;
my $ACTION = $q->param('ACTION');
my $FORMAT = $q->param('FORMAT');

my $SUBTYPE = 'P';

$FORMAT = 'WIZARD'; $SUBTYPE = undef;
$GTOOLS::TAG{'<!-- FORMAT -->'} = $FORMAT;

my $template_file = '';
my $header = 1;


my @TABS = ();
push @TABS, { name=>'Help', link=>'index.cgi', };

my @BC = ();
push @BC, 	{ name=>'Setup',link=>'http://www.zoovy.com/biz/setup','target'=>'_top', },
      	 	{ name=>'Custom Page Wizard',link=>'http://www.zoovy.com/biz/setup/toxml','target'=>'_top', };



if ($ACTION eq '') {
	my $c = '';
	my %params = ();
	$params{'DETAIL'} = 1;
	$params{'SUBTYPE'} = $SUBTYPE;
	$params{'SORT'} = 1;
	my $arref = &TOXML::UTIL::listDocs($USERNAME,$FORMAT,%params);
	my $bgcolor = '';
	my @rows = ();

	my $IMAGEpath = '';
	if ($FORMAT eq 'LAYOUT') { $IMAGEpath = &ZOOVY::resolve_userpath($USERNAME).'/TOXML'; }
	if ($FORMAT eq 'WIZARD') { $IMAGEpath = &ZOOVY::resolve_userpath($USERNAME).'/TOXML'; }

	my $rowcount = 0;
	foreach my $inforef (@{$arref}) {
		my $TITLE = $inforef->{'TITLE'};
		my $DOCID = $inforef->{'DOCID'};
		my $SUBTYPE = $inforef->{'SUBTYPE'};
		my $SUBTYPETXT = $TOXML::UTIL::LAYOUT_STYLES->{$SUBTYPE}[0];
		if (not defined $SUBTYPETXT) { $SUBTYPETXT = $SUBTYPE; }
		my $SUMMARY = $inforef->{'SUMMARY'};
		if ($SUMMARY eq '') { $SUMMARY = '<i>No summary provided.</i>'; }
		$SUMMARY =~ s/^[\n\r]+//gs;
		$SUMMARY =~ s/[\n\r]+/<br>\n/gs;

		my $IMAGES = $inforef->{'IMAGES'};
		

		my $image = '/images/blank.gif';
		if ($FORMAT eq 'LAYOUT') {
			if (($inforef->{'MID'}>0) && (-f "$IMAGEpath/$DOCID.gif")) {
				$image = "/biz/setup/builder/flowview.cgi?USER=$USERNAME&IMG=$DOCID";
				}
			elsif ( -f "/httpd/htdocs/images/samples/flows/$DOCID.gif" ) { 
				$image = "/images/samples/flows/$DOCID.gif"; 
				}
			$image = "<a href=\"#\" onClick=\"showDetails('$DOCID');\"><img width=75 height=75 border=0 src='$image'></a>";			
			}
		elsif ($FORMAT eq 'WIZARD') {
			if (($inforef->{'MID'}>0) && (-f "/IMAGES/htmlwiz-$DOCID.gif")) {
				$image = "http://static.zoovy.com/merchant/$USERNAME/htmlwiz-$DOCID.gif";
				}
			elsif (-f "/httpd/htdocs/images/samples/wizards/$DOCID.gif" ) { 
				$image = "/images/samples/wizards/$DOCID.gif"; 
				}
			$image = "<a href=\"#\" onClick=\"showDetails('$DOCID');\"><img width=70 height=50 border=0 src='$image'></a>";			
			}
		else {
			$image = 'Unknown Format';
			}
		
		## remember checkbox
		my $cb = "<input class='$bgcolor' ".($inforef->{'REMEMBER'}?'checked':'')." name='$DOCID' onClick='setCbState(this);' type='checkbox'>";			
		my $about = "<b>$DOCID</b>: $TITLE<br>$SUMMARY";
		my $properties = '';		
		
		my $startxt = '';
		my $STARS = $inforef->{'STARS'};
		if (($STARS>0) && ($STARS<=10)) {
			$startxt = '<table border=0 cellpadding=0 cellspacing=0><tr>';
			foreach (1 .. int($STARS/2)) { $startxt .= "<td><img src='/images/toxmlicons/starfull.gif'></td>"; }
			if ($STARS % 2) {  $startxt .= "<td><img src='/images/toxmlicons/starhalf.gif'></td>"; }
			$startxt .= '<td></tr></table>';
			$about .= $startxt;
			}
		elsif ($STARS>10) {
			$about .= "<table border=0 cellpadding=0 cellspacing=0 width=100%><tr><td>Not Rated (Custom)</td></tr></table>";
			}

		my @icons = ();
		my $PROPERTIES = $inforef->{'PROPERTIES'};
		if ($FORMAT eq 'LAYOUT') {
			if ($PROPERTIES & 1) { push @icons, "dynamicimage.gif"; } # contains at least one dynamic image
			if ($PROPERTIES & 2) { push @icons, "thumbnails.gif"; }	# subcategory has thumbnails 
			if ($PROPERTIES & 4) { push @icons, "images.gif"; }	# contains an image element.
			}
		elsif ($FORMAT eq 'WIZARD') {
			if ($PROPERTIES & 1) { push @icons, "standard.gif"; }
			if ($PROPERTIES & 2) { push @icons, "header.gif"; }
			if ($PROPERTIES & 4) { push @icons, "detaildesc.gif"; }	# 
			if ($PROPERTIES & 8) { push @icons, "flash.gif"; }		# contains flash
			if ($PROPERTIES & 16) { push @icons, "images.gif"; }	
			}
		elsif ($FORMAT eq 'WRAPPER') {
			## from: /httpd/htdocs/biz/setup/themes/body.cgi  line 894
			## 1 = minicart
			## 2 = sidebar
			## 4 = subcats
			## 8 = embed search
			## 16 = embed login
			## 32 = image cats
			}
		elsif ($FORMAT eq 'ZEMAIL') {
			## 
			}

		## common properties.
		if ($PROPERTIES & 256) { push @icons, "wiki.gif"; }	
		if ($PROPERTIES & 512) { push @icons, "web20.gif"; }	


		my $properties = '<table border=0 cellspacing=1 cellpadding=0><tr>';
		foreach my $icon (@icons) {
			$properties .= "<td><img src=\"/images/toxmlicons/$icon\"></td>";
			}
		$properties .= "</tr></table>";
		
		if ((defined $inforef->{'IMAGES'}) && ($inforef->{'IMAGES'}>0)) { 
			$properties .= "<table border=0 cellspacing=1 cellpadding=0><tr><td><img src=\"/images/toxmlicons/image.gif\"> x $inforef->{'IMAGES'}</td></tr></table>";
			}
		# use Data::Dumper; $properties .= Dumper(\@icons);
		$properties .= "<table border=0 cellspacing=0 cellpadding=0><tr><td>$cb</td><td>Favorite</td></tr></table>\n";

		my $class = 'r'.($rowcount++%2); # set to rx for highlight
		if ($inforef->{'REMEMBER'}) { $class .= '; rx'; }

		my $buttons = qq~
		<a href="#" onClick="showDetails('$DOCID');"><img border=0  src="/images/toxmlicons/details.gif"></a>
		<a href="#" onClick="doSelect('$DOCID');"><img border=0  src="/images/toxmlicons/select.gif"></a>
		~;

		push @rows, [ '', $image, $about, $properties, $buttons, $DOCID, $class ];
		}	




	my @header = ();
	push @header, { 'width'=>'5', 'title'=>'' };
	push @header, { 'width'=>'100', 'title'=>'Thumbnail' };
	push @header, { 'width'=>'250', 'title'=>'Description' };
	push @header, { 'width'=>'100', 'title'=>'Properties' };
	push @header, { 'width'=>'100', 'title'=>'' };

	my @icons = ();
	if ($FORMAT eq 'LAYOUT') {
		push @icons, { txt=>'Dynamic Images', img=>'dynamicimage.gif' };
		push @icons, { txt=>'Thumbnails', img=>'thumbnails.gif' };
		push @icons, { txt=>'Images', link=>'', img=>'image.gif' };
		}
	elsif ($FORMAT eq 'WIZARD') {
		push @icons, { txt=>'Standard Fields', img=>'standard.gif' };
		push @icons, { txt=>'Navigation Header', img=>'header.gif' };		
		push @icons, { txt=>'Detail Description', img=>'detaildesc.gif' };
		push @icons, { txt=>'Requires Flash', img=>'flash.gif' };		
		push @icons, { txt=>'Images', link=>'', img=>'image.gif' };
		}
	else {
		push @icons, { txt=>'Logo', link=>'', img=>'logo.gif' };
		push @icons, { txt=>'Search', link=>'', img=>'search.gif' };
		push @icons, { txt=>'HTML Editor', link=>'', img=>'html.gif' };
		push @icons, { txt=>'Text Area', link=>'http://webdoc.zoovy.com/dev/detail/development-beginners.php#TEXT', img=>'text.gif' };
		push @icons, { txt=>'Text Box', link=>'http://webdoc.zoovy.com/dev/detail/development-beginners.php#TEXTBOX', img=>'textbox.gif' };
		push @icons, { txt=>'Image', link=>'', img=>'image.gif' };
		}




	my $legend = '';
	foreach my $ref (@icons) {
		$legend .= qq~<tr><td><img src="/images/toxmlicons/$ref->{'img'}" width=17 height=17></td><td>~;
		if ($ref->{'link'}) { $legend .= qq~<a href="$ref->{'link'}">~; }
		$legend .= $ref->{'txt'};
		if ($ref->{'link'}) { $legend .= "</a>"; }
		$legend .= "</td></tr>\n"; 
		}

	$GTOOLS::TAG{'<!-- OURTABLE -->'} = &GTOOLS::Table::buildTable(\@header,\@rows,rowid=>5,rowclass=>6);
	$GTOOLS::TAG{'<!-- ICONLEGEND -->'} = $legend;

	$template_file = 'chooser.shtml';
	}




&GTOOLS::output(
   'title'=>'Setup : Custom Page Wizard',
   'file'=>$template_file,
   'header'=>$header,
   'help'=>'',
   'tabs'=>\@TABS,
   'bc'=>\@BC,
   );





exit;

