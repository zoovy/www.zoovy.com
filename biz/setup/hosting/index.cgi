#!/usr/bin/perl

use Data::Dumper;

use strict;

use lib "/httpd/modules";
require GTOOLS;
require LUSER;
require ZWEBSITE;
require ZOOVY;

require TOXML;
require TOXML::UTIL;
require TOXML::RENDER;

my ($LU) = LUSER->authenticate(flags=>'_S&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

# $LU->log('PRODEDIT.NUKEIMG',"[PID:$PID] Nuking image $img ".$prodref->{'zoovy:prod_image'.$img},'INFO');
my $VERB = $ZOOVY::cgiv->{'VERB'};

my ($NS) = &ZWEBSITE::prt_get_profile($USERNAME,$PRT);
my $NSREF = &ZOOVY::fetchmerchantns_ref($USERNAME,$NS);



my ($webdbref) = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
if ($VERB eq 'SAVE') {
	$webdbref->{'dev_enabled'}++;

	my $has_custom_urls = 0;

	## HMMM...
	my %ref = ();
	$ref{'homepage_url'} = $ZOOVY::cgiv->{'homepage'};
	$ref{'home_url'} = $ZOOVY::cgiv->{'homepage'};
	$ref{'aboutus_url'} = $ZOOVY::cgiv->{'aboutus'};
	$ref{'about_us_url'} = $ZOOVY::cgiv->{'aboutus'};
	$ref{'about_url'} = $ZOOVY::cgiv->{'aboutus'};
	$ref{'returns_url'} = $ZOOVY::cgiv->{'returns'};
	$ref{'privacy_url'} = $ZOOVY::cgiv->{'privacy'};
	$ref{'contactus_url'} = $ZOOVY::cgiv->{'contactus'};
	foreach my $url (keys %ref) {
		$ref{$url} =~ s/^\s+//;	# strip leading whitespace
		$ref{$url} =~ s/\s+$//;	# Strip trailing space

		if ($FLAGS =~ /,SITEHOST,/) {
			if ($ref{$url} eq '') { delete $ref{$url}; }		
			}
		}
	if (scalar(keys %ref)>0) { $has_custom_urls++; }
	$webdbref->{'dev.rewrite_urls'} = &ZTOOLKIT::buildparams(\%ref);

	## 
	##	okay this turns on a whole bunch of less secure settings.
	##
	if (($FLAGS =~ /,SITEHOST,/) && (!$has_custom_urls)) {
		## turn on "zoovy to zoovy" feature
		delete $webdbref->{'dev.overrides'};
		}
	else {
		my %dev = (
			'dev.disable_rewrite'=>1,
			'dev.no_continue'=>1,
			'dev.softcart'=>1,
			'dev.no_categories'=>1,
			'dev.no_subcategories'=>1,
			'dev.disable_sessions'=>1,
			'dev.ssl_only'=>0,
			);
		$webdbref->{'dev.overrides'} = &ZTOOLKIT::buildparams(\%dev,1);
		}


	&ZWEBSITE::save_website_dbref($USERNAME,$webdbref,$PRT);
	$LU->log('SETUP.HOSTING',"Configured Hosting Settings","SAVE");	
	}

if ($VERB eq 'SET-THEME') {
	$NSREF->{'zoovy:site_wrapper'} = $ZOOVY::cgiv->{'THEME'};
	$NSREF->{'zoovy:site_rootcat'} = '.';
	delete $NSREF->{'zoovy:site_schedule'};
	$NSREF->{'zoovy:site_partition'} = $PRT;
	&ZOOVY::savemerchantns_ref($USERNAME,$NS,$NSREF);
	$LU->log('SETUP.HOSTING',"Changed Theme","SAVE");
	}

if ($LU->get('todo.setup')) {
	require TODO;
   my $t = TODO->new($USERNAME);
   my ($NEEDREF,$TASKSREF) = $t->setup_tasks('hosting',webdb=>$webdbref,nsref=>$NSREF);
	$GTOOLS::TAG{'<!-- MYTODO -->'} = $t->mytodo_box('hosting',$TASKSREF);
   }



my ($wrapper) = $NSREF->{'zoovy:site_wrapper'};
my $rwurls = &ZTOOLKIT::parseparams($webdbref->{'dev.rewrite_urls'});
$GTOOLS::TAG{'<!-- CURRENT_WRAPPER -->'} = &preview_div($USERNAME,$wrapper,0);
$GTOOLS::TAG{'<!-- HOMEPAGE_URL -->'} = &ZOOVY::incode($rwurls->{'homepage_url'});
$GTOOLS::TAG{'<!-- ABOUTUS_URL -->'} = &ZOOVY::incode($rwurls->{'aboutus_url'});
$GTOOLS::TAG{'<!-- RETURNS_URL -->'} = &ZOOVY::incode($rwurls->{'returns_url'});
$GTOOLS::TAG{'<!-- PRIVACY_URL -->'} = &ZOOVY::incode($rwurls->{'privacy_url'});
$GTOOLS::TAG{'<!-- CONTACTUS_URL -->'} = &ZOOVY::incode($rwurls->{'contactus_url'});

my $c = '';
my @THEMES = ();
push @THEMES, 'blue_angles';
push @THEMES, 'l2_corporatered';
push @THEMES, 'l2_patriotic';
push @THEMES, 'gradefade';
push @THEMES, 'eggs';
push @THEMES, 'allamerican';
push @THEMES, 'l2_tealcraquelure';
push @THEMES, 'swiftunnel4';
push @THEMES, 'sunflare';
foreach my $docid (@THEMES) {
	$c .= &preview_div($USERNAME,$docid,1);
	}
$GTOOLS::TAG{'<!-- BEST_THEMES -->'} = $c;

@THEMES = ();
my $result = &TOXML::UTIL::listDocs($USERNAME,'WRAPPER',SUBTYPE=>'C');
if (defined $result) {
	foreach my $ref (@{$result}) {
		if ($ref->{'MID'}>0) {
			unshift @THEMES, $ref->{'DOCID'};
			}
		else {
			push @THEMES, $ref->{'DOCID'};
			}
		}
	}
$c = '';
foreach my $docid (@THEMES) {
	$c .= &preview_div($USERNAME,$docid,1);
	}
$GTOOLS::TAG{'<!-- ALL_THEMES -->'} = $c;
$GTOOLS::TAG{'<!-- ALL_COUNT -->'} = scalar(@THEMES);

&GTOOLS::output(file=>'index.shtml',header=>1,todo=>1);


##
##
##
sub preview_div {
	my ($USERNAME,$DOCID,$selectable) = @_;

	my ($t) = TOXML->new('WRAPPER',$DOCID,USERNAME=>$USERNAME);
	next if (not defined $t);
	my ($cfg) = $t->findElements('CONFIG');

	my $thumburl = 'http://static.zoovy.com/graphics/wrappers/'.$DOCID.'/preview.jpg';
	if ($t->{'FORMAT'} eq 'ZEMAIL') {
		$thumburl = 'http://static.zoovy.com/graphics/zemails/'.$DOCID.'/preview.jpg';
		}

	if ((substr($DOCID,0,1) eq '~') || ($t->{'MID'} == $MID)) {
		if ($t->{'THUMBNAIL'} eq '') {
			$thumburl = 'http://www.zoovy.com/biz/images/setup/custom_theme.gif'; 	
			}
		else {
			require IMGLIB::Lite;
			$thumburl = &IMGLIB::Lite::url_to_image($USERNAME,$t->{'THUMBNAIL'},140,100,'FFFFFF',0,0);
			}
		}

	$SITE::CONFIG = undef;
	my ($cfg) = $t->initConfig();
#	use Data::Dumper; $c .= Dumper($cfg->{'%SITEBUTTONS'});
	my ($imgtag) = TOXML::RENDER::RENDER_SITEBUTTON({button=>'add_to_cart','%SITEBUTTONS'=>$cfg->{'%SITEBUTTONS'},name=>""},undef,{'_USERNAME'=>$USERNAME});

	if ($cfg->{'TITLE'} eq '') { 
		$cfg->{'TITLE'} = $DOCID.' Untitled'; 
		}

	my $height = 'height: 185px;';
	if (not $selectable) { $height = ''; }

	my $previewhref = '<a>';
	if ($selectable) {
		$previewhref = qq~<a target="_preview" href="http://$USERNAME.zoovy.com/cart.cgis?wrapper=$DOCID">~;
		}
	my $c = qq~<div style='font-size: 8pt; $height float:left; margin-left:8px; margin-bottom:8px; text-align:center;'>
	<div>$previewhref<img src='$thumburl' border=0 alt="preview $cfg->{'TITLE'}" width='140' height='100' alt=''></a></div>
	<div style='width: 180px;'>$cfg->{'TITLE'}</div>
	<div><a href="index.cgi?VERB=SET-THEME&THEME=$DOCID">$imgtag</a></div>
	~;


	if ($selectable) {
		$c .= qq~<div>~;
		$c .= $previewhref.qq~[preview]</a> ~;
		$c .= qq~<a href="index.cgi?VERB=SET-THEME&THEME=$DOCID">[select]</a>~;
		$c .= qq~</div>~;
		}
	$c .= qq~</div>~;
	return($c);
	}