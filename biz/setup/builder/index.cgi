#!/usr/bin/perl

use lib "/httpd/modules";
require GTOOLS;
require ZOOVY;
require SITE;
require ZWEBSITE;
require PAGE;
require ZTOOLKIT;
require NAVCAT;
require TOXML;
require TOXML::RENDER;
require TOXML::CHOOSER;
require LUSER;
require AJAX::PANELS;
require IMGLIB::Lite;
require DOMAIN::TOOLS;
require PRODUCT;
use strict;
use URI::Escape;
use Data::Dumper;
require PRODUCT;

my @MSGS = ();
my @IMG = ();
push @IMG, qq~<img src="/biz/loading.gif" width=120 height=60>~;
$GTOOLS::TAG{'<!-- WAIT_IMG -->'} = $IMG[ time()%scalar(@IMG) ];

my $DEBUG = 0;

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my @TABS = ();
my @BC = ();


##
## generate tabs and breadcrumbs (we must do this after save so $ACTION is set properly)
##
push @BC, { name=>'Setup', link=>'/biz/setup/index.cgi', };
if ($LU->is_level('3')) {
	push @BC, { name=>'Website Builder', link=>'/biz/setup/builder/index.cgi', };
	}



my $webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
my $ACTION = $ZOOVY::cgiv->{'ACTION'};
print STDERR "ACTION:$ACTION\n";


my $template_file = "index.shtml";
$GTOOLS::TAG{"<!-- USERNAME -->"} = $USERNAME;
$GTOOLS::TAG{"<!-- REV -->"} = time();


# print STDERR "ACTION: $ACTION\n";
if ($ACTION eq 'DECALS-SAVE') {

	}

##
##
##
if (($ACTION eq 'DECALS') || ($ACTION eq 'DECALS-SAVE')) {
	my ($CHANGES) = 0;
	push @BC, { link=>"/biz/setup/builder/index.cgi?ACTION=DECALS", name=>"Decals" };

	require PRODUCT::FLEXEDIT;

	my $PROFILE = $ZOOVY::cgiv->{'NS'};
	$GTOOLS::TAG{'<!-- NS -->'} = $PROFILE;

	my ($nsref) = &ZOOVY::fetchmerchantns_ref($USERNAME,$PROFILE);
	my $docid = $nsref->{'zoovy:site_wrapper'};
	my ($tx) = TOXML->new('WRAPPER',$docid,USERNAME=>$USERNAME,MID=>$MID);
	my ($configel) = $tx->findElements('CONFIG');	# fetch the first CONFIG element out of the document.

	my $thumburl = '';
	if (substr($docid,0,1) ne '~') {
		$thumburl = '//static.zoovy.com/graphics/wrappers/'.$docid.'/preview.jpg';
		}
	elsif ($configel->{'THUMBNAIL'} eq '') {
		$thumburl = '//www.zoovy.com/biz/images/setup/custom_theme.gif'; 	
		}
	else {
		require IMGLIB::Lite;
		$thumburl = &IMGLIB::Lite::url_to_image($USERNAME,$configel->{'THUMBNAIL'},140,100,'FFFFFF',0,0);
		}
	$GTOOLS::TAG{'<!-- THUMBURL -->'} = $thumburl;	

	my @DECALS = $tx->findElements('DECAL');
	my @SIDEBARS = $tx->findElements('SIDEBAR');

	my $c = '';
	my %FLEXEDITS = ();
	foreach my $el (@DECALS,@SIDEBARS) {
		my $IS_SSL = 'N/A';
		my $PREVIEW = '';

		my $DATASRC = $el->{'DATA'};
		if (($DATASRC eq '') && ($el->{'TYPE'} eq 'SIDEBAR')) { 
			$DATASRC = 'profile:zoovy:sidebar_logos'; 
			}

		if ($el->{'DECALID'}) {
			## this not considered an error, we don't have a DATA when DECALID is specified
			$DATASRC = '';
			}
		elsif ($DATASRC =~ /profile\:(.*?)$/) { 
			$DATASRC = $1; 
			} 
		elsif ($DATASRC =~ /wrapper\:(.*?)$/) { 
			## currently, wrapper:tag is a global alias to merchant:wrapper:tag
			$DATASRC = "wrapper:$1"; 
			} 
		else { 
			## this is probably an error, we need a data (we'll show this error to the user in a bit)
			$DATASRC = ''; 
			}


		if ($el->{'DECALID'}) {
			## cannot save because decalid is hardcoded
			}
		elsif ($DATASRC eq '') {
			warn "DECAL DATASRC not configured on save for $el->{'ID'}\n";
			}
		elsif ($ACTION eq 'DECALS-SAVE') {
			my @LINES = ();
			my $i = 0;
			while ( defined $ZOOVY::cgiv->{"ELEMENT:$el->{'ID'}.$i"} ) {
				push @LINES, $ZOOVY::cgiv->{"ELEMENT:$el->{'ID'}.$i"};
				$i++;
				}
			$nsref->{$DATASRC} = join("\n",@LINES);
			}

		my $pretty = $el->{'PROMPT'};
		if ($pretty eq '') { $pretty = "$el->{'TYPE'}: $el->{'ID'}"; }

		## header row
		my $width = $el->{'WIDTH'};
		if ($width eq '') { $width = '?'; }
		my $height = $el->{'HEIGHT'};
		if ($height eq '') { $height = '?'; }
		
		if ($el->{'DECALID'}) {
			## hardcoded decal (specified by designer)
			$c .= "<tr class='zoovysub1header'><td>$pretty (not user configurable, decalid: $el->{'DECALID'})</td></tr>";
			}
		else {
			## user configurable decal
			$c .= "<tr class='zoovysub1header'><td>$pretty ($width by $height)</td></tr>";
			}


		my $hint = $el->{'HELP'};
		if ($hint eq '') { $hint = $el->{'HELPER'}; }
		if ($hint ne '') { $hint .= "<br>"; }
		if (($el->{'OUTPUTSKIP'} & 256)>0) { $hint .= "<br>** MULTIVARIANT: Will only be shown on 'B' side **"; }
		if (($el->{'OUTPUTSKIP'} & 512)>0) { $hint .= "<br>** MULTIVARIANT: Will only be shown on 'A' side **"; }

		if ($el->{'DECALID'}) {
			## forced to a decalid (not configurable)
			}
		elsif ($DATASRC eq '') {
			$hint .= "<br><font color='red'>DATA= could not be determined on element. (this decal is broked).</font>";
			}
		elsif ($nsref->{$DATASRC} eq '') {
			$PREVIEW = "<i>Not selected</i>";
			}
		elsif ( ($nsref->{$DATASRC} ne '') && ($el->{'TYPE'} eq 'DECAL')) {
			## lets verify the DECAL actually exists.
			my $Dref = $TOXML::RENDER::DECALS{ $nsref->{$DATASRC} };
			if (not defined $Dref) {
				$hint .= "<br><font color='red'>Decal $el->{'ID'} references a unknown decal id: $nsref->{$DATASRC}</font>";
				}
			else {
				## we've located the currently selected decal id.
				$IS_SSL = ($Dref->{'ssl'})?'Y':'N';		
				foreach my $flexattr (@{$Dref->{'flexedit'}}) {
					## if $FLEXEDITS{$flexattr} > 1 then it means it's already been shown.		
					if (not defined $FLEXEDITS{ $flexattr }) { $FLEXEDITS{ $flexattr } = 1; }
					}
				}
			}
		## hint row
		$c .= qq~<tr><td valign=top><div class="hint">$hint</div></td></tr>~;

		$c .= qq~<tr><td><table>~;


		## DECAL has 1 slot, SIDEBAR has > 0
		my @SLOTS = ($nsref->{$DATASRC});
		if (($el->{'TYPE'} eq 'DECAL') && ($el->{'DECALID'} ne '')) {
			@SLOTS = ( $el->{'DECALID'} );
			}
		elsif ($el->{'TYPE'} eq 'SIDEBAR') {
			my $i = $el->{'SLOTS'};
			if ($i==0) { $i = 10; }
			@SLOTS = split(/[\|\n]/,$nsref->{$DATASRC}); 
			while (--$i>=0) { 
				if (not defined $SLOTS[$i]) { $SLOTS[$i] = ''; }
				}
			}

		# $c .= "<tr><td>".Dumper(\@SLOTS)."</td></tr>";

		my ($domain) = &DOMAIN::TOOLS::domain_for_prt($USERNAME,$PRT);
		my $pos = 0;
		foreach my $slotvar (@SLOTS) {
			## body row
			## @SLOTS is an array of configured DECALID's

			$PREVIEW = '';
			my $options = '';
			foreach my $did (sort keys %TOXML::RENDER::DECALS) {
				my $Dref = $TOXML::RENDER::DECALS{$did};
				## don't display graphics which are too big for the space allocated.
				if ($slotvar eq $did) {
					## if it's selected, we always use / remember it.
					$options .= "<option selected value=\"$did\">$Dref->{'prompt'} (selected)</option>\n";
					$PREVIEW = ($Dref->{'preview'})?$Dref->{'preview'}:$Dref->{'html'};
					if (defined $Dref->{'flexedit'}) {
						foreach my $flexattr (@{$Dref->{'flexedit'}}) {
							if (not defined $FLEXEDITS{ $flexattr }) { $FLEXEDITS{ $flexattr } = 1; }
							}
						#$PREVIEW = "($slotvar==$did) ".Dumper($Dref);
						}
					}
				elsif ((defined $el->{'DECALID'}) && ($did ne $el->{'DECALID'})) {
					$options .= "<!-- $did is not the decal required by the element -->";
					}
				elsif ((defined $Dref->{'height'}) && ($Dref->{'height'}>$el->{'HEIGHT'}) && ($el->{'HEIGHT'}>0)) {
					$options .= "<!-- $did is too tall width=$Dref->{'height'} -->\n";
					}
				elsif ((defined $Dref->{'width'}) && ($Dref->{'width'}>$el->{'WIDTH'}) && ($el->{'WIDTH'}>0)) {
					$options .= "<!-- $did is too wide width=$Dref->{'width'} -->\n";
					}
				else {
					$options .= "<option value=\"$did\">$Dref->{'prompt'}</option>\n";
					}
				}

			## cheap hack to get ssl rewrites working.
			$PREVIEW =~ s/%sdomain%/$domain/gos;
		
			$c .= "<tr>";
			$c .= qq~<td valign=top>~;
			$c .= qq~<select name=\"ELEMENT:$el->{'ID'}.$pos\">$options</select>~;
			$c .= qq~<br><!-- slot=[$pos] --> SSL: $IS_SSL~;
			$c .= qq~</td>~;
			# $PREVIEW = &ZOOVY::incode($PREVIEW);
			if ($PREVIEW =~ /\<script/i) {
				$PREVIEW =~ s/\<script.*?\>.*?\<\/script\>//gs;
				$PREVIEW .= "<div class=\"caution hint\">NOTE: JAVASCRIPT NOT AVAILABLE IN PREVIEW</div>";
				}
	
			$c .= qq~<td valign=top>$PREVIEW</td>~;
			$c .= qq~<td valign="top">~;

			## okay now we'll show any flexedit fields.
			my @FLEXFIELDS = ();
			foreach my $flexid (sort keys %FLEXEDITS) {
				next if ($FLEXEDITS{$flexid}>1);
				$FLEXEDITS{$flexid} = 2;
				$PRODUCT::FLEXEDIT::fields{$flexid}->{'id'} = $flexid;
				push @FLEXFIELDS, $PRODUCT::FLEXEDIT::fields{$flexid};
				}
			if (scalar(@FLEXFIELDS)>0) {
				if ($ACTION eq 'DECALS-SAVE') {
					PRODUCT::FLEXEDIT::prodsave(undef,\@FLEXFIELDS,$ZOOVY::cgiv,'%dataref'=>$nsref);
					}
				$c .= &PRODUCT::FLEXEDIT::output_html(undef,\@FLEXFIELDS,'USERNAME'=>$USERNAME,'PRT'=>$PRT,'%dataref'=>$nsref);
				}
			# $c .= Dumper(\@FLEXFIELDS);
			$c .= "</td></tr>";
			$pos++;
			}

		$c .= "</table>";
		$c .= "</td>";
		$c .= "</tr>";	
		}

	# 	print STDERR 'INDEX DUMP'.Dumper($ZOOVY::cgiv->{'user:decal5'});

	$GTOOLS::TAG{'<!-- POSITIONS -->'} = $c;

	## commit saves to disk.
	if ($ACTION eq 'DECALS-SAVE') {
		&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$nsref);
		$LU->log('SETUP.BUILDER.DECALS',"Updated decals/sidebar for profile $PROFILE","SAVE");
		}
	
	$template_file = 'decals.shtml';
	}



if ($ACTION eq 'EDIT-WRAPPER') {
	$ACTION = 'INITEDIT';
	$ZOOVY::cgiv->{'FORMAT'} = 'WRAPPER';
	}



##
##
##

my $SITEstr = undef;
my $SITE = undef;
if (defined $ZOOVY::cgiv->{'_SREF'}) {
	$SITE = SITE::sitedeserialize($USERNAME,$ZOOVY::cgiv->{'_SREF'});
	}
elsif ($ACTION eq 'INITEDIT') {

	my $NS = $ZOOVY::cgiv->{'NS'};
	if (not defined $NS) { $NS = &ZOOVY::prt_to_profile($USERNAME,$PRT); }
	$SITE = SITE->new($USERNAME,'PRT'=>$PRT,'PROFILE'=>$NS);

	$SITE->sset('_FORMAT',$ZOOVY::cgiv->{'FORMAT'});
	if ($ZOOVY::cgiv->{'SKU'}) {
		$SITE->setSTID($ZOOVY::cgiv->{'SKU'});
		$SITE->sset('_FORMAT','PRODUCT');
		}
	$SITE->sset('_FS',$ZOOVY::cgiv->{'FS'});

	if ($ZOOVY::cgiv->{'FL'}) {
		$SITE->layout( $ZOOVY::cgiv->{'FL'} );
		}
	
	$SITE->{'_is_preview'}++;

	if ($SITE->format() eq 'WRAPPER') {
		## WRAPPER ?? EMAIL?? editing a specific docid w/o page namespace.
		$SITE->pageid( $ZOOVY::cgiv->{'PG'} );
		if ($SITE->layout() eq '') {
			my $nsref = $SITE->nsref();
			$SITE->layout( $nsref->{'zoovy:site_wrapper'} );
			}
		}
	elsif ($SITE->format() eq 'EMAIL') {
		if ($SITE->layout() eq '') {
			$SITE->layout( &ZOOVY::fetchmerchantns_attrib($USERNAME,$SITE->profile(),'email:docid') );
			}
		}
	elsif ($SITE->format() eq 'PRODUCT') {
		$SITE->pageid( $SITE->pid() );
		if ($SITE->layout() eq '') {
			my $P = $SITE->pRODUCT()->fetch('zoovy:fl');
			if ((ref($P) eq 'PRODUCT') && ($P->fetch('zoovy:fl') ne '')) { 
				$SITE->layout( $P->fetch('zoovy:fl') ); 
				}
			}
		}
	elsif ($SITE->format() eq 'PAGE') {
		$SITE->pageid( $ZOOVY::cgiv->{'PG'} );
		if ($SITE->layout() eq '') {
			my $PG = $SITE->pAGE(); 
			$SITE->layout( $PG->docid() );
			}
	#	print STDERR Dumper($SITE);
		}
	#elsif ($SITE->format() eq 'WIZARD') {
	#	$SITE->pageid( $SITE->pid() );
	#	if ($SITE->layout() eq '') {
	#		my $P = $SITE->pRODUCT()->fetch('zoovy:fl');
	#		if ((ref($P) eq 'PRODUCT') && ($P->fetch('zoovy:fl') ne '')) { 
	#			$SITE->layout( $P->fetch('zoovy:fl') ); 
	#			}
	#		}
	#	}
	elsif ($SITE->format() eq 'NEWSLETTER') {
		my $ID = 0;
		$SITE->pageid( $ZOOVY::cgiv->{'PG'} );
		if ($SITE->layout() eq '') {
			my $PG = $SITE->pAGE(); 
			$SITE->layout( $PG->docid() );
			}		
		# if ($SITE->pageid() =~ /^\@CAMPAIGN:([\d]+)$/) { $ID = $1; }
		#$SITE->layout($ZOOVY::cgiv->{'FL'});
		#my ($P) = PAGE->new($USERNAME,$SITE->pageid());
		#$P->set('FL',$ZOOVY::cgiv->{'FL'});
		#$P->save();
		}
	else {
		push @MSGS, "ERROR|+INVALID FORMAT: ".$SITE->format();
		}
	
	
	if (not defined $SITE) {
		$ACTION = 'ERROR';
		}
	elsif ((not defined $SITE->layout()) || ($SITE->layout() eq '')) {
		$ACTION = 'CHOOSER';
		}
	else { 
		$ACTION = 'EDIT'; 
		}

	$SITEstr =  $SITE->siteserialize();
	}

#if (&ZOOVY::is_zoovy_ip()) {
#	push @MSGS, "DEBUG|ZOOVY STAFF ACTION[$ACTION] DEBUG: ".Dumper($SITE);
#	}

if ($ACTION eq 'DIVSELECT') {
	$SITE->{'_DIV'} = $ZOOVY::cgiv->{'DIV'};
	$ACTION = 'EDIT';
	$SITEstr =  $SITE->siteserialize();
	}

##
## Chooser lets us select a new flow.
##
if ($ACTION eq "CHOOSERSAVE") {

	if ($ZOOVY::cgiv->{'FL'}) {
		$SITE->layout($ZOOVY::cgiv->{'FL'});
		}

	if ($SITE->format() eq 'WRAPPER') {	
		die("alas, wrappers are not saved/configured by this tool (only edited)");
		}
	elsif ($SITE->format() eq 'EMAIL') {
	 	&ZOOVY::savemerchantns_attrib($USERNAME,$SITE->profile(),'email:docid',$SITE->docid());
		$LU->log('SETUP.BUILDER.EMAIL',"Saved new layout ".$SITE->docid()." for profile ".$SITE->profile(),"SAVE");
		}
	elsif ($SITE->format() eq 'PRODUCT') {
		my ($P) = PRODUCT->new($LU,$SITE->pid()); 
		$P->store('zoovy:fl',$SITE->layout()); 
		$P->save();
		$LU->log('SETUP.BUILDER.SKU',"Saved new layout ".$SITE->layout()." for SKU ".$SITE->pid(),"SAVE");
		}
	elsif ($SITE->format() eq 'PAGE') {
		# currently this flag tells me to save the FLOW
		my ($P) = PAGE->new($USERNAME, $SITE->pageid(),NS=>$SITE->profile(),PRT=>$SITE->prt());
		$P->set('FL',$SITE->layout());
		&ZOOVY::savemerchantns_attrib($USERNAME,$SITE->profile(),'zoovy:default_flow'.$SITE->fs(),$SITE->layout());
		$LU->log('SETUP.BUILDER.PAGE',"Saved new layout ".$SITE->layout()." for page ".$SITE->fs()." profile ".$SITE->layout(),"SAVE");
		}
	elsif ($SITE->format() eq 'NEWSLETTER') {
		my ($P) = PAGE->new($USERNAME, $SITE->pageid(),NS=>$SITE->profile(),PRT=>$SITE->prt());
		$P->set('FL',$SITE->layout());
		&ZOOVY::savemerchantns_attrib($USERNAME,$SITE->profile(),'zoovy:default_flow'.$SITE->fs(),$SITE->layout());
		$LU->log('SETUP.BUILDER.PAGE',"Saved new layout ".$SITE->layout()." for page ".$SITE->fs()." profile ".$SITE->layout(),"SAVE");
		}
	else {
		die("unsupported toxml->format '".$SITE->format()."' -- never reached!");
		}

	$ACTION = 'EDIT';
	$SITEstr =  $SITE->siteserialize();
	}


##
## Meta properties editor.
##
if ($ACTION eq 'METASAVE') {

	if ($SITE->pid() eq '') {
		my ($P) = PAGE->new($SITE->username(),$SITE->pageid(),NS=>$SITE->profile(),PRT=>$PRT);
		$P->set('page_head',$ZOOVY::cgiv->{'HEAD'});
		$P->set('page_title',$ZOOVY::cgiv->{'PAGE_TITLE'});
		$P->set('head_title',$ZOOVY::cgiv->{'HEAD_TITLE'});
		my $keywords = $ZOOVY::cgiv->{'KEYWORDS'};
		$keywords =~ s/\n/ /gs; # Nuke newlines
		$P->set('meta_keywords',$keywords);
		my $description = $ZOOVY::cgiv->{'DESCRIPTION'};
		$description =~ s/\n/ /gs; # Nuke newlines
		$P->set('meta_description',$description);
		$P->save();
		$LU->log('SETUP.BUILDER.META',"Saved meta properties for ".$SITE->pageid().":".$SITE->profile(),"SAVE");
		}
	else {
		#&ZOOVY::saveproduct_attrib($USERNAME,$SITE->pid(),'zoovy:prod_name',$ZOOVY::cgiv->{'TITLE'});
		#&ZOOVY::saveproduct_attrib($USERNAME,$SITE->pid(),'zoovy:meta_desc',$ZOOVY::cgiv->{'DESCRIPTION'});
		#&ZOOVY::saveproduct_attrib($USERNAME,$SITE->pid(),'zoovy:keywords',$ZOOVY::cgiv->{'KEYWORDS'});
		my ($P) = PRODUCT->new($LU,$SITE->pid()); 
		$P->store('zoovy:prod_name',$ZOOVY::cgiv->{'TITLE'}); 
		$P->store('zoovy:meta_desc',$ZOOVY::cgiv->{'DESCRIPTION'}); 
		$P->store('zoovy:keywords',$ZOOVY::cgiv->{'KEYWORDS'}); 
		$P->save();

		$LU->log('SETUP.BUILDER.META',"Saved meta properties for SKU: ".$SITE->pid(),"SAVE");
		}
	
	$SITEstr =  $SITE->siteserialize();
	$ACTION = 'METAEDIT';
	}


if ($ACTION eq 'TOXMLSAVE') {
	$ACTION = 'EDIT';
	require TOXML::COMPILE;
	
	my $content = $ZOOVY::cgiv->{'CONTENT'};
	my ($toxml) = TOXML::COMPILE::fromXML('LAYOUT',$SITE->layout(),$content,USERNAME=>$USERNAME,MID=>$MID);

	$LU->log('SETUP.BUILDER.TOXMLSAVE',"Save layout: ".$SITE->layout(),"SAVE");
	if (defined $toxml) {
		$toxml->save();
		$SITE->layout( $toxml->docId() );
		push @MSGS, "SUCCESS|successfully saved ".$SITE->format().":".$SITE->layout();
		}
	else {
		push @MSGS, "ERROR|could not save ".$SITE->format().":".$SITE->layout();
		}
	}

##
##
##
if ($ACTION eq 'COMPANYSAVE') {
	my $NS = $ZOOVY::cgiv->{'NS'};
	my $ref = &ZOOVY::fetchmerchantns_ref($USERNAME,$NS);
	my ($gref) = &ZWEBSITE::fetch_globalref($USERNAME);

	$ref->{'zoovy:site_wrapper'} = $ZOOVY::cgiv->{'SP_WRAPPER'};
	$ref->{'zoovy:site_rootcat'} = $ZOOVY::cgiv->{'SP_ROOTCAT'};
	$ref->{'zoovy:site_schedule'} = $ZOOVY::cgiv->{'SP_SCHEDULE'};
	$ref->{'prt:id'} = $ZOOVY::cgiv->{'SP_PARTITION'};
	$ref->{'zoovy:site_partition'} = $ref->{'prt:id'};

	if ($gref->{'%tuning'}->{'allow_default_profile_overrides'}) {
		## this user can override our "SANE" defaults.
		}
	elsif ($NS eq '') {
		$ref->{'zoovy:site_rootcat'} = '.';
		$ref->{'zoovy:site_schedule'} = '';
		$ref->{'zoovy:site_partition'} = 0;
		}

	$ref->{'zoovy:support_phone'} = $ZOOVY::cgiv->{'zoovy:support_phone'};
	$ref->{'zoovy:support_email'} = $ZOOVY::cgiv->{'zoovy:support_email'};
	$ref->{'zoovy:company_name'} = $ZOOVY::cgiv->{'zoovy:company_name'};
	$ref->{'zoovy:seo_title'} = $ZOOVY::cgiv->{'zoovy:seo_title'};
	$ref->{'zoovy:seo_title_append'} = $ZOOVY::cgiv->{'zoovy:seo_title_append'};
	$ref->{'zoovy:firstname'} = $ZOOVY::cgiv->{'zoovy:firstname'};
	$ref->{'zoovy:middlename'} = $ZOOVY::cgiv->{'zoovy:middlename'};
	$ref->{'zoovy:lastname'} = $ZOOVY::cgiv->{'zoovy:lastname'};
	$ref->{'zoovy:address1'} = $ZOOVY::cgiv->{'zoovy:address1'};
	$ref->{'zoovy:address2'} = $ZOOVY::cgiv->{'zoovy:address2'};
	$ref->{'zoovy:city'} = $ZOOVY::cgiv->{'zoovy:city'};
	$ref->{'zoovy:state'} = $ZOOVY::cgiv->{'zoovy:state'};
	$ref->{'zoovy:country'} = $ZOOVY::cgiv->{'zoovy:country'};
	$ref->{'zoovy:zip'} = $ZOOVY::cgiv->{'zoovy:zip'};
	$ref->{'zoovy:phone'} = $ZOOVY::cgiv->{'zoovy:phone'};
	$ref->{'zoovy:facsimile'} = $ZOOVY::cgiv->{'zoovy:facsimile'};
	$ref->{'zoovy:website_url'} = $ZOOVY::cgiv->{'zoovy:website_url'};

	foreach my $k (
		'zoovy:support_phone','zoovy:support_email',
		'zoovy:about','zoovy:contact','zoovy:shipping_policy','zoovy:payment_policy',
		'zoovy:return_policy','zoovy:checkout', 'zoovy:business_description') {
		$ref->{$k} = $ZOOVY::cgiv->{$k};
		}

	$ref->{'zoovy:logo_website_pixelmode'} = (defined $ZOOVY::cgiv->{'logo_website_pixelmode'})?1:0;

	my $width = $ZOOVY::cgiv->{'width'};
	my $height = $ZOOVY::cgiv->{'height'};
	if ((!defined($width)) || ($width>500) || ($width<1)) { $width = 300; }
	if ((!defined($height)) || ($height>300) || ($height<1)) { $height = 100; }
	$ref->{'zoovy:logo_invoice_xy'} = int($width)."x".int($height);

	push @MSGS, "SUCCESS|+Saved settings for profile $NS | prt:$ref->{'prt:id'} root:$ref->{'zoovy:site_rootcat'} wrapper:$ref->{'zoovy:site_wrapper'}";
	$LU->log('SETUP.BUILDER.COMPANY',"Saved settings for profile $NS | prt:$ref->{'prt:id'} root:$ref->{'zoovy:site_rootcat'} wrapper:$ref->{'zoovy:site_wrapper'}","SAVE");
	&ZOOVY::savemerchantns_ref($USERNAME,$NS,$ref);
	$ACTION = 'COMPANYEDIT';
	}




print STDERR "ACTION: $ACTION\n";
$GTOOLS::TAG{'<!-- SREF -->'} = $SITEstr;

if ($ACTION eq 'COMPANYEDIT') {
	push @BC, { name=>'Edit Company Info | PROFILE: '.$ZOOVY::cgiv->{'NS'} }
	}
elsif (not defined $SITE) {
	## the rest of the things require SITE to be populated, it's okay if it's not.
	}
elsif ($SITE->layout() eq '') {
	## hmm.. not sure what this is. ?? perhaps the TOXML chooser?
	## also the main edit page.
	push @BC, { name=>'Select Template' };
	if (($ACTION eq 'INITEDIT') || ($ACTION eq 'EDIT')) {
		## wow.. they've selected either DOCID or WRAPPER as '' (not undef, but actually blank!)
		push @TABS, { name=>'Layout', link=>'/biz/setup/builder/index.cgi?ACTION=CHOOSER&_SREF='.$SITEstr, color=>(($ACTION eq 'CHOOSER')?'orange':undef), };
		}
	push @BC, { name=>"profile:".$SITE->profile()." | format:".$SITE->format()." | pageid:".$SITE->pageid() };
	}
elsif ($SITE->format() eq 'PRODUCT') {
	my $PID = $SITE->pid();
	$GTOOLS::TAG{'<!-- BUTTONS -->'} = qq~
	<center>
		<button class="button2" onClick="navigateTo('/biz/product/edit.cgi?PID=$PID');">Return to Product Editor</button>
	</center>
		~;	

	$SITEstr =  $SITE->siteserialize();
	push @TABS, { name=>'Product Editor', 'jsexec'=>"app.ext.admin_prodEdit.a.showPanelsFor('$PID');", };
	push @TABS, { name=>'Layout', link=>'/biz/setup/builder/index.cgi?ACTION=CHOOSER&_SREF='.$SITEstr, color=>(($ACTION eq 'CHOOSER')?'orange':undef), };
	push @TABS, { name=>'Page Edit', link=>'/biz/setup/builder/index.cgi?ACTION=EDIT&_SREF='.$SITEstr, color=>(($ACTION eq 'EDIT')?'orange':undef), };
	if (($webdbref->{'pref_template_fmt'} ne '') && (index($FLAGS,',WEB,')>=0) && (substr($SITE->{'_FL'},0,1) eq '~')) {
		push @TABS, { name=>'Edit Template', link=>'/biz/setup/builder/index.cgi?ACTION=TOXMLEDIT&_SREF='.$SITEstr, color=>(($ACTION eq 'TOXMLEDIT')?'orange':undef), };
		}
	push @BC, { name=>"Edit profile:".$SITE->profile()." | format:".$SITE->format()." | pageid:".$SITE->pageid()." | layout:".$SITE->layout() };
	}
elsif ($SITE->format() eq 'NEWSLETTER') {
	$GTOOLS::TAG{'<!-- BUTTONS -->'} = qq~
	<center>
		<button class="button2" onClick="navigateTo('/biz/setup/builder/index.cgi');">Exit</button>
	</center>
	~;
	push @TABS, { name=>'Page Edit', link=>'/biz/setup/builder/index.cgi?ACTION=EDIT&_SREF='.$SITEstr, color=>(($ACTION eq 'EDIT')?'orange':undef), };
	push @TABS, { name=>'Layout', link=>'/biz/setup/builder/index.cgi?ACTION=CHOOSER&_SREF='.$SITEstr, color=>(($ACTION eq 'CHOOSER')?'orange':undef), };
	push @TABS, { name=>'Edit Template', link=>'/biz/setup/builder/index.cgi?ACTION=TOXMLEDIT&_SREF='.$SITEstr, color=>(($ACTION eq 'TOXMLEDIT')?'orange':undef), };
	push @BC, { name=>"Edit profile:".$SITE->profile()." format:".$SITE->format()." pageid:".$SITE->pageid()." layout:".$SITE->layout() };
	$template_file = 'edit-newsletter.shtml';
	}
elsif ($SITE->format() eq 'PAGE') {
	$GTOOLS::TAG{'<!-- BUTTONS -->'} = qq~
	<center>
		<button class="button2" onClick="navigateTo('/biz/setup/builder/index.cgi');">Exit</button>
	</center>
	~;
	$SITEstr =  $SITE->siteserialize();
	push @TABS, { name=>'Page Edit', link=>'/biz/setup/builder/index.cgi?ACTION=EDIT&_SREF='.$SITEstr, color=>(($ACTION eq 'EDIT')?'orange':undef), };
	push @TABS, { name=>'Layout', link=>'/biz/setup/builder/index.cgi?ACTION=CHOOSER&_SREF='.$SITEstr, color=>(($ACTION eq 'CHOOSER')?'orange':undef), };
	if (($webdbref->{'pref_template_fmt'} ne '') && (index($FLAGS,',WEB,')>=0) && (substr($SITE->{'_FL'},0,1) eq '~')) {
		push @TABS, { name=>'Edit Template', link=>'/biz/setup/builder/index.cgi?ACTION=TOXMLEDIT&_SREF='.$SITEstr, color=>(($ACTION eq 'TOXMLEDIT')?'orange':undef), };
		}
	if (substr($SITE->pageid(),0,1) eq '*') {
		## no live preview for special pages
		}
	else {
		push @TABS, { name=>'Live Preview', link=>'/biz/setup/builder/index.cgi?ACTION=LIVEPREVIEW&_SREF='.$SITEstr, color=>(($ACTION eq 'LIVEPREVIEW')?'orange':undef), };
		}
	push @TABS, { name=>'Meta Tags', link=>'/biz/setup/builder/index.cgi?ACTION=METAEDIT&_SREF='.$SITEstr, color=>(($ACTION eq 'METAEDIT')?'orange':undef), };
	push @BC, { name=>"Edit profile:".$SITE->profile()." format:".$SITE->format()." pageid:".$SITE->pageid()." layout:".$SITE->layout() };
	}	
elsif ($SITE->format() eq 'WRAPPER') {
	$GTOOLS::TAG{'<!-- BUTTONS -->'} = qq~
	<center>
		<button class="button2" onClick="navigateTo('/biz/setup/builder/index.cgi');">Exit</button>
	</center>
	~;
	push @TABS, { name=>'Page Edit', link=>'/biz/setup/builder/index.cgi?ACTION=EDIT&_SREF='.$SITEstr, color=>(($ACTION eq 'EDIT')?'orange':undef), };
	if (($webdbref->{'pref_template_fmt'} ne '') && (index($FLAGS,',WEB,')>=0) && (substr($SITE->{'_FL'},0,1) eq '~')) {
		push @TABS, { name=>'Edit Template', link=>'/biz/setup/builder/index.cgi?ACTION=TOXMLEDIT&_SREF='.$SITEstr, color=>(($ACTION eq 'TOXMLEDIT')?'orange':undef), };
		}
	push @BC, { name=>"Edit profile:".$SITE->profile()." format:".$SITE->format()." pageid:".$SITE->pageid()." layout:".$SITE->layout() };
	}	
elsif ($SITE->format() ne '') {
	print STDERR Dumper($ZOOVY::cgiv);
	die("Unsupported SITE->format(".$SITE->format().")");
	}

$DEBUG && print STDERR Dumper($SITE);


##
##
##
if ($ACTION eq 'LIVEPREVIEW') {
	my $SRC = '';
	$GTOOLS::TAG{'<!-- FL -->'} = $SITE->{'_FL'};
	$GTOOLS::TAG{'<!-- PG -->'} = $SITE->pageid();
	$GTOOLS::TAG{'<!-- SKU -->'} = $SITE->pid();
	$GTOOLS::TAG{'<!-- TS -->'} = time();

	my $SITE_URL = "http://$USERNAME.zoovy.com";
	if ($LU->prt()>0) {
		$SITE_URL = "http://www.".&DOMAIN::TOOLS::domain_for_prt($USERNAME,$PRT);
		}

	if ($SITE->pid() ne '') {
		$SRC = "$SITE_URL/product/".$SITE->pid();
		}
	elsif ($SITE->pageid() eq '.') {
		$SRC = "$SITE_URL/";		
		}
	elsif (substr($SITE->pageid(),0,1) eq '.') {
		$SRC = "$SITE_URL/category/".substr($SITE->pageid(),1);		
		}
	elsif (index($SITE->pageid(),'.')==-1) {
		my $v = $SITE->pageid();
		if ($SITE->pageid() eq 'contactus') { $v = 'contact_us'; }

		$SRC = "http://$USERNAME.zoovy.com/$v.cgis";
		}
	else {
		$SRC = '#Not Found!';
		}

	$GTOOLS::TAG{'<!-- SRC -->'} = $SRC;
	$template_file = 'livepreview.shtml';
	}


if ($ACTION eq 'SPECIALTYSAVE') {


	}


if ($ACTION eq 'COMPANYEDIT') {
	# handle general parameters.
	my $NS = $ZOOVY::cgiv->{'NS'};
	$GTOOLS::TAG{'<!-- NS -->'} = $NS;
	my $ref = &ZOOVY::fetchmerchantns_ref($USERNAME,$NS);

	if ($LU->get('todo.setup')) {
		require TODO;
		my $t = TODO->new($USERNAME);
		my ($need,$tasks) = $t->setup_tasks('company',webdb=>$webdbref,nsref=>$ref,'LU'=>$LU);
		$GTOOLS::TAG{'<!-- MYTODO -->'} = $t->mytodo_box('company',$tasks);
		}

	$GTOOLS::TAG{"<!-- COMPANY_NAME -->"} = $ref->{'zoovy:company_name'};
	$GTOOLS::TAG{"<!-- SEO_TITLE -->"} = $ref->{'zoovy:seo_title'};
	$GTOOLS::TAG{"<!-- SEO_TITLE_APPEND -->"} = $ref->{'zoovy:seo_title_append'};
	$GTOOLS::TAG{"<!-- ZOOVY_FIRSTNAME -->"} = $ref->{'zoovy:firstname'};
	$GTOOLS::TAG{"<!-- ZOOVY_MI -->"} = $ref->{'zoovy:middlename'};
	$GTOOLS::TAG{"<!-- ZOOVY_LASTNAME -->"} = $ref->{'zoovy:lastname'};
	$GTOOLS::TAG{"<!-- ZOOVY_EMAIL -->"} = $ref->{'zoovy:email'};
	if (not &ZTOOLKIT::validate_email($GTOOLS::TAG{'<!-- ZOOVY_EMAIL -->'})) {
		$GTOOLS::TAG{'<!-- WARN_EMAIL -->'} = "<font color='red'>warning: if you do not have a contact email, you may miss important messages from zoovy.</font>";
		}
	$ref->{'zoovy:phone'} =~ s/[^\d\-]+//g;	# strip non-numeric digits from phone.
	$GTOOLS::TAG{"<!-- ZOOVY_PHONE -->"} = $ref->{'zoovy:phone'};
	$GTOOLS::TAG{"<!-- ZOOVY_ADDRESS1 -->"} = $ref->{'zoovy:address1'};
	$GTOOLS::TAG{"<!-- ZOOVY_ADDRESS2 -->"} = $ref->{'zoovy:address2'};
	$GTOOLS::TAG{"<!-- ZOOVY_CITY -->"} = $ref->{'zoovy:city'};
	$GTOOLS::TAG{"<!-- ZOOVY_STATE -->"} = $ref->{'zoovy:state'};
	$GTOOLS::TAG{"<!-- ZOOVY_COUNTRY -->"} = substr($ref->{'zoovy:country'},0,2);
	$GTOOLS::TAG{"<!-- ZOOVY_ZIP -->"} = $ref->{'zoovy:zip'};
	$GTOOLS::TAG{"<!-- ZOOVY_FAX -->"} = $ref->{'zoovy:facsimile'};
	$GTOOLS::TAG{'<!-- WEBSITE_URL -->'} = $ref->{'zoovy:website_url'};

	foreach my $k ('zoovy:support_phone','zoovy:support_email',
		'zoovy:about','zoovy:contact','zoovy:shipping_policy','zoovy:payment_policy',
		'zoovy:return_policy','zoovy:checkout','zoovy:business_description') {
		$GTOOLS::TAG{"<!-- $k -->"} = $ref->{$k};
		}


## since we moved to SITE::EMAILS this doesn't work anymore
#	require TOXML::EMAIL;
#	my ($errs) = TOXML::EMAIL::check_message($USERNAME,$ref,'*',undef,undef,undef);
#	if (defined $errs) {
#		my $txt = '<font color="red">EMAIL ERRORS:</font> Due to the following errors, we will be unable to send email on your behalf.<br>';
#		foreach my $err (@{$errs}) {
#			$txt .= " &nbsp; $err<br>";
#			}
#		$GTOOLS::TAG{'<!-- EMAIL_ERRORS -->'} = "<tr><td colspan='3'>$txt<hr></td></tr>";
#		}



	if (
		($GTOOLS::TAG{"<!-- zoovy:support_phone -->"} eq '') || 
		($GTOOLS::TAG{"<!-- ZOOVY_ZIP -->"} eq '') ||
		($GTOOLS::TAG{"<!-- ZOOVY_STATE -->"} eq '') ||
		($GTOOLS::TAG{"<!-- ZOOVY_CITY -->"} eq '') ||
		($GTOOLS::TAG{"<!-- ZOOVY_ADDRESS1 -->"} eq '') ||
		($GTOOLS::TAG{"<!-- zoovy:support_email -->"} eq '')) {
		$GTOOLS::TAG{'<!-- BEGIN_WARN -->'} = '<font color="red"><b>';
		$GTOOLS::TAG{'<!-- END_WARN -->'} = '</b></font>';
  		}


	if (not $LU->is_level(5)) {
		$GTOOLS::TAG{'<!-- SITE_CONFIG -->'} = qq~
<b>Company Information</b><hr>
<input type="hidden" name="SP_WRAPPER" value="$ref->{'zoovy:site_wrapper'}">
<input type="hidden" name="SP_ROOTCAT" value="$ref->{'zoovy:site_rootcat'}">
<input type="hidden" name="SP_SCHEDULE" value="$ref->{'zoovy:site_schedule'}">
<input type="hidden" name="SP_PARTITION" value="$ref->{'zoovy:site_partition'}">
~;
		}
	else {
		##
		# $out = "<option value=\"\">Site Theme</option>\n";
		my $THEMES = '';
		if ($ref->{'zoovy:site_wrapper'} ne '') {
			$THEMES = "<option value=\"$ref->{'zoovy:site_wrapper'}\">$ref->{'zoovy:site_wrapper'} (currently selected)</option>\n";
			}
		require TOXML::UTIL;
		foreach my $docref ( @{TOXML::UTIL::listDocs($USERNAME,'WRAPPER',SORT=>1)}) {
			my $wrapper = $docref->{'DOCID'};
			next if ($wrapper eq 'default');
			next unless (($docref->{'REMEMBER'}) || ($docref->{'MID'}>0));
		   $THEMES .= "<option ".(($ref->{'zoovy:site_wrapper'} eq $wrapper)?'selected':'')." value=\"$wrapper\">$wrapper</option>\n";
			}
	
		my $PARTITIONS = '';
		my $globalref = &ZWEBSITE::fetch_globalref($USERNAME);
		my $i = 0;
		foreach my $prt (@{$globalref->{'@partitions'}}) {
			my $selected = ($ref->{'zoovy:site_partition'} eq $i)?'selected':'';
			$PARTITIONS .= "<option $selected value=\"$i\">[$i] $prt->{'name'}</option>";
			$i++;
			}

		my ($gref) = &ZWEBSITE::fetch_globalref($USERNAME);

		my $ROOTS = "<option value=\".\">Homepage</option>\n";
		require NAVCAT;
		my ($NC) = NAVCAT->new($USERNAME,PRT=>$PRT);
		my ($pathar) = $NC->fetch_childnodes('.');
		# my ($pathar,$paths) = &NAVCAT::fetch_children($USERNAME,'.');
		# use Data::Dumper; print STDERR Dumper($pathar, $paths);
		my $FOUND_ROOT = 0;
		foreach my $p ('.',@{$pathar}) {
			my ($pretty) = $NC->get($p);
			if ($ref->{'zoovy:site_rootcat'} eq $p) { $FOUND_ROOT++; }
			$ROOTS .= "<option ".(($ref->{'zoovy:site_rootcat'} eq $p)?'selected':'')." value=\"$p\">[$p] $pretty</option>\n";	
			if ((substr($pretty,0,1) eq '!') || ($gref->{'%tuning'}->{'builder_show_all_navcats'})) {
				my ($pathar) = $NC->fetch_childnodes($p);
				# my ($pathar,$paths) = &NAVCAT::fetch_children($USERNAME,$p);
				foreach my $p (@{$pathar}) {
					my ($pretty) = $NC->get($p);
					$ROOTS .= "<option ".(($ref->{'zoovy:site_rootcat'} eq $p)?'selected':'')." value=\"$p\">[$p] $pretty</option>\n";	
					if ($gref->{'%tuning'}->{'builder_show_all_navcats'}>1) {
						# 3rd level for bamtar
						my ($pathar) = $NC->fetch_childnodes($p);
						foreach my $p (@{$pathar}) {
							my ($pretty) = $NC->get($p);
							$ROOTS .= "<option ".(($ref->{'zoovy:site_rootcat'} eq $p)?'selected':'')." value=\"$p\">[$p] $pretty</option>\n";	
							}
						}
					}
				}
			}
		if ($FOUND_ROOT) {
			}
		elsif ($ref->{'zoovy:site_rootcat'} eq '') {
			$ROOTS .= "<option selected value=\"\">-</option>";
			}
		else {
			$ROOTS .= "<option selected value=\"$ref->{'zoovy:site_rootcat'}\">INVALID CATEGORY: $ref->{'zoovy:site_rootcat'}</option>";
			}

		my $SCHEDULES = '<option value="">None</option>';
		require WHOLESALE;
		my $SCHEDULE = $ref->{'zoovy:site_schedule'};
		if (($SCHEDULE ne '') && (not WHOLESALE::schedule_exists($USERNAME,$SCHEDULE))) {
			$SCHEDULES .= qq~<option selected value="$SCHEDULE">**INVALID SCHEDULE $SCHEDULE**</option>~;
			}

		foreach my $sch (@{&WHOLESALE::list_schedules($USERNAME)}) {
			$SCHEDULES .= "<option ".(($SCHEDULE eq $sch)?'selected':'')." value=\"$sch\">$sch</option>\n";
			if ($gref->{'%tuning'}->{'allow_default_profile_overrides'}) {
				## this user is allowed to change their default behaviors.
				}
			elsif ($NS eq 'DEFAULT') {
				$SCHEDULES = '<option value="">Not Available</option>';
				$ROOTS= '<option value="">Not Available</option>';
				$PARTITIONS = '<option value="0">Not Available</option>';
				}
			##
			}

		$GTOOLS::TAG{'<!-- SITE_CONFIG -->'} = qq~
<h1>Editing Profile Information: <!-- NS --></h1>
<p>Think of a profile as a "version" of your business. You may have as many profiles as you wish.
Profiles may be mapped to one distinct eBay User and/or Overstock User.
Each profile may be mapped to an unlimited number of domains (using speciality site hosting).
Changes you make here will also be made to any auction listings.</p>

<table width="100%" class="zoovytable">
	<tr><td colspan=2 class="zoovytableheader">Speciality Site Settings</td></tr>
	<tr><td width=150>Wrapper:</td><td><select name="SP_WRAPPER">$THEMES</select></td></tr>
	<tr><td>Root Category:</td><td><select name="SP_ROOTCAT">$ROOTS</select></td></tr>
	<tr><td>Pricing Schedule:</td><td><select name="SP_SCHEDULE">$SCHEDULES</select></td></tr>
	<tr><td>Data Partition:</td><td><select name="SP_PARTITION">$PARTITIONS</select></td>
	</tr>
	<!-- PARTITION_CONFIG -->
</table>
	~;
		}


	
	my $logo = $ref->{'zoovy:logo_website'};
	$GTOOLS::TAG{"<!-- LOGO_WEBSITE -->"} = &IMGLIB::Lite::url_to_image($USERNAME,$logo,100,100,'ffffff');
	$GTOOLS::TAG{"<!-- LOGO_WEBSITE_PIXELMODE -->"} = ($ref->{'zoovy:logo_website_pixelmode'})?'CHECKED':'';

	## NOTE:
	## LOGOYES 
	## http://www.cj.com/, u: tom@zoovy.com, p: SLcsaUK 

	my $prt = $ref->{'prt:id'};
	if ($NS eq 'DEFAULT') { 
		$prt = 0; 
		}
	elsif ($prt ne '') {
		## verify we are on the correct profile
		my ($prtinfo) = &ZOOVY::fetchprt($USERNAME,$prt);
		if ($prtinfo->{'profile'} ne $NS) { $prt = ''; }
		}

	if ($prt ne '') {

		## types of logo's:
		# zoovy:logo_invoice : logo at the top of an invoice (for this sdomain)
		# zoovy:logo_website : logo that is used for the wrapper
		# zoovy:logo_market  : logo that will be used for marketplaces (no domain name)
		# zoovy:logo_email	: logo for emails
		# zoovy:logo_mobile	: logo for mobile site

		# zoovy:company_logo_m
		# zoovy:company_logo

		my ($logo_invoice_width,$logo_invoice_height) = split('x',$ref->{'zoovy:logo_invoice_xy'});
		if ((!defined($logo_invoice_width)) || ($logo_invoice_width>500) || ($logo_invoice_width<1)) { $logo_invoice_width = 300; }
		if ((!defined($logo_invoice_height)) || ($logo_invoice_height>500) || ($logo_invoice_height<1)) { $logo_invoice_height = 100; }
		$GTOOLS::TAG{'<!-- LOGO_INVOICE_WIDTH -->'} = $logo_invoice_width;
		$GTOOLS::TAG{'<!-- LOGO_INVOICE_HEIGHT -->'} = $logo_invoice_height;
	
		my $logo = $ref->{'zoovy:logo_invoice'};
		my $invoice_logo_url = &IMGLIB::Lite::url_to_image($USERNAME,$logo,$logo_invoice_width,$logo_invoice_height,'ffffff');

	$GTOOLS::TAG{'<!-- INVOICE_LOGO -->'} = qq~
<table class="zoovytable" cellpadding="2" cellspacing="0" border="0" width='100%'>
<tr>
	<td colspan=2 class="zoovytableheader">Invoice Logo Configuration (Partition #$prt)</td>
</tr>
<tr>
	<td style="padding:5px;">

<!-- BEGIN INVOICE LOGO TABLE -->

	<table class="table_stroke" cellpadding="2" cellspacing="0" border="0" width='100%'>
	<tr>
		<td class="table_head"><span class="header">Invoice Logo @ $logo_invoice_width x $logo_invoice_height:</span></td>
	</tr>
	<tr>
		<td valign="middle" align="center">
		<img name="invoiceimg" src="$invoice_logo_url" width='$logo_invoice_width' height='$logo_invoice_height'>
		<input type="button" class="button" onClick="mediaLibrary($('#invoiceimg'),'mode=ilogo&profile=$NS','Choose Invoice Logo');" value=" Change ">
		</td>
	</tr>
	</table>
<!-- END LOGO GRAPHIC TABLE -->
	</td>

	<Td valign="top" align="left">
	<!-- BEGIN LOGO DETAILS & CHECKBOXES -->
	<table width='100%'>
	<tr>
		<td>
	The logo you select will appear in your checkout, web based printed invoices and more. 
	Zoovy will automatically size your logo to fit within the theme and layout you have chosen.
		</td>
	</tr>
	<tr>
		<td>
		<table>
	<tr>
		<Td>Width:</td>
		<td><input type="textbox" value='$logo_invoice_width' size="3" name="width" class="formed"></td>
		<td>(300 pixels recommended)</td>
	</tr>
	<tr>
		<td>Height:</td>
		<td><input type="textbox" value='$logo_invoice_height' size="3" name="height" class="formed"></td>
		<td>(100 pixels recommended)</td>
	</tr>
	<tr>
		<td colspan='3'>Minimum Size 16x16, Maximum Size: 500x300<br></td>
	</tr>
	</table>
	</td>
</tr>
</table>
	<!-- END INVOICE LOGO TABLE -->
	</td>
</tr>
</table>
	~;
		}

	
	$template_file = 'company.shtml';
	}

##
##
##
if ($ACTION eq 'CHOOSER') {

	my $title = '';
	my $default = '';
	$template_file = 'chooser.shtml';
	if ($SITE->{'_FORMAT'} eq 'EMAIL') {
		$title = "Choose an Email Template";
		$default = &ZOOVY::fetchmerchantns_attrib($USERNAME,$SITE->profile(),'zoovy:email_template');
		$SITE->sset('_FS','');
		}
	elsif ( index($SITE->pageid(), 'CAMPAIGN') > 0){ 
		my (undef, $CAMPAIGN_ID) = split(/:/, $SITE->pageid());
		$title = "Choose a Newsletter Layout";
		$GTOOLS::TAG{"<!-- TITLE -->"} = "Step 2: $title";
		$SITE->sset('_FS','I');
		$default = &ZOOVY::fetchmerchantns_attrib($USERNAME,$SITE->profile(),'zoovy:default_flow'.$SITE->fs());
		}
	else {
		$title = "Choose a Page Layout";
		push @BC, { name=>"Choose Layout: ".$SITE->pageid(), };
		$GTOOLS::TAG{"<!-- TITLE -->"} = $title;
		$default = &ZOOVY::fetchmerchantns_attrib($USERNAME,$SITE->profile(),'zoovy:default_flow'.$SITE->fs());
		}	

	print STDERR "SUBTYPE: ".$SITE->fs()."\n";
	$GTOOLS::TAG{'<!-- FLOW_CHOOSER -->'} = &TOXML::CHOOSER::buildChooser($SITE->username(),$SITE->format(),SREF=>$SITE->siteserialize(),SUBTYPE=>$SITE->fs(),selected=>$SITE->layout(),'*LU'=>$LU);
	}



##
##
##
if ($ACTION eq 'METAEDIT') {
	if (ref($SITE) ne 'SITE') {
		push @MSGS, "ISE|Sorry but we could not deference SITE for ACTION METAEDIT";
		}
	elsif ($SITE->pid() eq '') {
		my ($P) = PAGE->new($USERNAME,$SITE->pageid(),NS=>$SITE->profile(),PRT=>$PRT);
		$GTOOLS::TAG{'<!-- PAGE_TITLE -->'} = $P->get('page_title');
		$GTOOLS::TAG{'<!-- HEAD_TITLE -->'} = $P->get('head_title');
		$GTOOLS::TAG{'<!-- HEAD -->'} = $P->get('page_head');
		$GTOOLS::TAG{'<!-- DESCRIPTION -->'} = $P->get('meta_description');
		$GTOOLS::TAG{'<!-- KEYWORDS -->'} = $P->get('meta_keywords');
		}
	else {
		my ($P) = PRODUCT->new($USERNAME,$SITE->pid());
		$GTOOLS::TAG{'<!-- TITLE -->'} = $P->fetch('zoovy:prod_name'); # &ZOOVY::fetchproduct_attrib($USERNAME,$SITE->pid(),'zoovy:prod_name');
		$GTOOLS::TAG{'<!-- DESCRIPTION -->'} = $P->fetch('zoovy:meta_desc'); # &ZOOVY::fetchproduct_attrib($USERNAME,$SITE->pid(),'zoovy:meta_desc');
		if ($GTOOLS::TAG{'<!-- DESCRIPTION -->'} eq '') {
			$GTOOLS::TAG{'<!-- DESCRIPTION -->'} = &ZTOOLKIT::htmlstrip( $P->fetch('zoovy:prod_desc') ); # &ZOOVY::fetchproduct_attrib($USERNAME,$SITE->pid(),'zoovy:prod_desc'));
			}
		$GTOOLS::TAG{'<!-- KEYWORDS -->'} = $P->fetch('zoovy:keywords'); # &ZOOVY::fetchproduct_attrib($USERNAME,$SITE->pid(),'zoovy:keywords');
		}

	push @BC, { name=>"Page: ".$SITE->pageid(), };
	$template_file = 'meta.shtml';
	$SITEstr = $SITE->siteserialize();
	$GTOOLS::TAG{'<!-- SREF -->'} = $SITEstr;
	}

if ($ACTION eq 'EDIT-NEWSLETTER') {  $ACTION = 'EDIT'; }

##
##
##
if ($ACTION eq 'EDIT') {

	if (ref($SITE) ne 'SITE') {
		push @MSGS, "ISE|Sorry but we could not deference SITE for ACTION $ACTION";
		}

	if ($ZOOVY::cgiv->{'FL'}) { $SITE->layout($ZOOVY::cgiv->{'FL'}); }

	$GTOOLS::TAG{"<!-- USERNAME -->"} = CGI->escape($USERNAME);
	$GTOOLS::TAG{"<!-- FL -->"}       = (defined $SITE->layout())?CGI->escape($SITE->layout()):'';
	$GTOOLS::TAG{"<!-- PG -->"}       = (defined $SITE->pageid())?CGI->escape($SITE->pageid()):'';
	$GTOOLS::TAG{"<!-- PROD -->"}	    = (defined $SITE->pid())?CGI->escape($SITE->pid()):'';
	$GTOOLS::TAG{"<!-- FS -->"}       = (defined $SITE->fs())?CGI->escape($SITE->fs()):'';
	$GTOOLS::TAG{"<!-- TS -->"}       = time();
	$GTOOLS::TAG{"<!-- REV -->"}      = time();

	if (defined $SITE->pageid()) {
		my $NC = NAVCAT->new($USERNAME,PRT=>$PRT); 
		$GTOOLS::TAG{'<!-- PRETTYPG -->'} = $NC->pretty_path($SITE->pageid());
		unless ((defined $GTOOLS::TAG{'<!-- PRETTYPG -->'}) && ($GTOOLS::TAG{'<!-- PRETTYPG -->'} ne '')) {
			$GTOOLS::TAG{'<!-- PRETTYPG -->'} = $SITE->pageid();
			}
		}
	elsif (defined $SITE->docid()) {
		$GTOOLS::TAG{'<!-- PRETTYPG -->'} = $SITE->{'_FORMAT'}.': '.$SITE->docid();
		}

	my $MSG = defined($ZOOVY::cgiv->{'MSG'}) ? $ZOOVY::cgiv->{'MSG'} : '';
	if ($MSG) {
		$GTOOLS::TAG{"<!-- MSG -->"} = "<br><center><table border='1' width='80%'><tr><td><b>$MSG</b></td></tr></table></center><br>";
		}
	## added 08/05/2005 - PM
	## decodes html for new (non-edited) custom page layouts

	my $FORMAT = $SITE->format();

	if ($FORMAT eq 'EMAIL') {
		if ( ($SITE->layout() eq '') && ($ZOOVY::cgiv->{'FL'} ne '') ) {
			$SITE->layout( $ZOOVY::cgiv->{'FL'} );
			}
		push @BC, { name=>sprintf("%s (%s)",$SITE->profile(),$SITE->layout()) }
		}
	elsif ($FORMAT eq 'WRAPPER') {
		}
	elsif ($FORMAT eq 'PAGE') {
		}
	elsif ($FORMAT eq 'LAYOUT') {
		}
	elsif ($FORMAT eq 'PRODUCT') {
		}
	elsif ($FORMAT eq 'NEWSLETTER') {
		}
	else {
		push @MSGS, "ERROR|UNKNOWN FORMAT:$FORMAT";
		}

	print STDERR "FORMAT: '$FORMAT' LAYOUT: '".$SITE->layout()."'\n";

	$GTOOLS::TAG{"<!-- BGCOLOR -->"} = '';
	my ($toxml) = TOXML->new($FORMAT,$SITE->layout(),USERNAME=>$USERNAME,MID=>$MID);

	my $BUF = '';
	if ($FORMAT eq '') {
		push @MSGS, "ERROR|No FORMAT specified, cannot start edit.";
		}
	elsif ($SITE->layout() eq '') {
		push @MSGS, "ERROR|No DOCID specified (FORMAT:$FORMAT), cannot start edit.";
		}
	elsif (defined $toxml) { 
		$toxml->initConfig($SITE);
		my $TH = $SITE::CONFIG->{'%THEME'};

		if (defined($TH->{'content_background_color'})) {
			$GTOOLS::TAG{"<!-- BGCOLOR -->"} = $TH->{'content_background_color'};
			}
		my $divsref = $toxml->divs();
		my $GROUP = '';
		if (defined $divsref) {
			unshift @{$divsref}, { TITLE=>'Page Edit', ID=>'' };
			foreach my $divref (@{$divsref}) {
				next if ($divref->{'TITLE'} eq '');
				my $class = ($divref->{'ID'} eq $SITE->{'_DIV'})?'link_selected':'link';

				if ($GROUP ne $divref->{'GROUP'}) {
					## output a new group header
					$GROUP = $divref->{'GROUP'};
					$BUF .= qq~<tr><td style="padding: 5px 0px 3px 0px;"><h4>$GROUP</h4></td></tr>~;
					}


				# $BUF .= qq~<tr><td><input style="text-align: left; width: 120px; margin-bottom: 3px;" 
				#onClick="document.location='index.cgi?ACTION=DIVSELECT&DIV=$divref->{'ID'}&_SREF=$SITEstr';"
				#type="button" class="$class" value="$divref->{'TITLE'}"></td></tr>~;
				$BUF .= qq~<tr><td class="$class"><a href="/biz/setup/builder/index.cgi?ACTION=DIVSELECT&DIV=$divref->{'ID'}&_SREF=$SITEstr"
class="$class">$divref->{'TITLE'}</a></td></tr>~;
				#onClick="document.location='';"
				#type="button" class="$class" value="$divref->{'TITLE'}"></td></tr>~;
				}
			}
		$GTOOLS::TAG{'<!-- DIVS -->'} = qq~
<td style="padding-right: 5px;" width="120" valign='top'><table cellspacing=0 cellpadding=0 border=0>
$BUF
</table>
</td>~;

		require TOXML::PREVIEW;
		require TOXML::EDIT;
		require SITE;

		($BUF) = $toxml->render('*SITE'=>$SITE,DIV=>$SITE->{'_DIV'});
		}
	else {
		$BUF = qq~
The document your are attempting to use DOCTYPE[$FORMAT] DOCID[~.$SITE->layout().qq~] USER[$USERNAME] is not valid or could not be loaded.
Please select another layout using the Layout tab at the top.
		~;
		}
	
	$GTOOLS::TAG{"<!-- CONTENTS -->"} = $BUF;

	## set EXIT button and TITLE specific for NEWSLETTERS
	## set back to Newsletter Management page if designing flow for CAMPAIGN
	my $title = "Edit Layout Content";

	if( index($SITE->pageid(), 'CAMPAIGN') > 0){
   	$GTOOLS::TAG{"<!-- TITLE -->"} = "Step 3: $title";
	   $GTOOLS::TAG{"<!-- FINISH -->"} = "Step 4: Preview";
	   }
	else{
		$GTOOLS::TAG{"<!-- TITLE -->"} = $title;
		$GTOOLS::TAG{"<!-- FINISH -->"} = "Finish/Save";
 	  	}

	$GTOOLS::TAG{'<!-- SREF -->'} = $SITEstr =  $SITE->siteserialize();
	$template_file = 'edit.shtml';
	if ($SITE->format() eq 'NEWSLETTER') {
		$GTOOLS::TAG{'<!-- MSGS -->'} = &GTOOLS::show_msgs(\@MSGS);
		$template_file = 'edit-newsletter.shtml';
		}
	}


if ($ACTION eq 'TOXMLEDIT') {
	my $toxml = TOXML->new('LAYOUT',$SITE->{'_FL'},USERNAME=>$USERNAME,MID=>$MID);
	
	if ($webdbref->{'pref_template_fmt'} eq 'XML') {
		$GTOOLS::TAG{'<!-- CONTENT -->'} = &ZOOVY::incode($toxml->as_xml());
		}
	elsif ($webdbref->{'pref_template_fmt'} eq 'HTML') {
		$GTOOLS::TAG{'<!-- CONTENT -->'} = &ZOOVY::incode($toxml->as_html(0));
		}
	elsif ($webdbref->{'pref_template_fmt'} eq 'PLUGIN') {
		$GTOOLS::TAG{'<!-- CONTENT -->'} = &ZOOVY::incode($toxml->as_html(1));
		}
	else {
		$GTOOLS::TAG{'<!-- CONTENT -->'} = "Requested template format not supported";
		}
	$GTOOLS::TAG{'<!-- _FL -->'} = $SITE->{'_FL'};

	## Check for stupid designer errors.
	## 	eventually we ought to display warnings when no wiki tags are available
	##		eventually we ought to check and make sure various subs exit
	##		eventually we ought to check parameters of each layout
	##		eventually we ought to put this in it's own function/module
	##
	my @ERRORS = ();
	my %COUNT = ();
	my %SUBS = ();
	foreach my $el (@{$toxml->getElements()}) {
		if ($el->{'SUB'} eq '') { $SUBS{ $el->{'SUB'} }=0; }

		next if ($el->{'TYPE'} eq 'OUTPUT');
		if ($el->{'ID'} eq '') {
			push @ERRORS, "Element $el->{'TYPE'} has no unique ID (how bizarre) - may not render correctly.";
			}
		else {
			$COUNT{ $el->{'ID'} }++;
			}
		}
	foreach my $id (keys %COUNT) {
		if ($COUNT{$id}>1) { 
			push @ERRORS, "ELEMENT ID=$id appears in the document $COUNT{$id} times (should be Unique)"; 
			}
		}

	undef %COUNT;
	if (scalar(@ERRORS)) {
		foreach my $msg (@ERRORS) {
			push @MSGS, "ERROR|$msg";
			}
		}

	$SITEstr =  $SITE->siteserialize();
	$GTOOLS::TAG{'<!-- SREF -->'} = $SITEstr;
	$template_file = 'toxmledit.shtml';
	}





if ($ACTION eq '') {
	require DOMAIN;
	require DOMAIN::QUERY;
	require DOMAIN::PANELS;
	require AJAX::PANELS;

	my ($prtinfo) = &ZOOVY::fetchprt($USERNAME,$PRT);
	my @domainrefs = &DOMAIN::QUERY::domains($USERNAME,PRT=>$PRT,DETAIL=>0);
	# print STDERR Dumper(\@domains,$PRT);

	my $SHOW_PROFILE = '';
	if ($ZOOVY::cgiv->{'PROFILE'}) {
		$SHOW_PROFILE = $ZOOVY::cgiv->{'PROFILE'};
		}

	my $out = '';
	my %DOMAINS = ();
	my %PROFILES = ();
	my @DEBUG = ();
	foreach my $domain (@domainrefs) {
		my $DNSINFO = &DOMAIN::QUERY::lookup("www.$domain",cache=>0,verify=>1,USERNAME=>$USERNAME);
		## skip domains that don't have a profile selected
		my $DISPLAY = 0;
		if (not defined $DNSINFO) {
			push @DEBUG, "WARN|$domain was not shown because it was not properly linked with this account in DNS";
			}
		elsif ($DNSINFO->{'PRT'} != $PRT) {
			push @DEBUG, "WARN|$domain was not shown because of PRT=$DNSINFO->{'PRT'}";
			}
		elsif ($DNSINFO->{'PROFILE'} eq '') {
			push @DEBUG, "WARN|$domain was not shown because of PROFILE is blank";
			}
		elsif ($DNSINFO->{'WWW_HOST_TYPE'} eq 'VSTORE') { 
			$DISPLAY |= 1; 
			}
		elsif ($DNSINFO->{'APP_HOST_TYPE'} eq 'VSTORE') { 
			$DISPLAY |= 2; 
			}
		elsif ($DNSINFO->{'M_HOST_TYPE'} eq 'VSTORE') { 
			$DISPLAY |= 4; 
			}
		elsif ($DNSINFO->{'PROFILE'} eq $SHOW_PROFILE) { 
			$DISPLAY |= 256; 
			} 		
		else {
			push @DEBUG, "WARN|$domain was not shown because WWW=$DNSINFO->{'WWW_HOST_TYPE'} APP=$DNSINFO->{'APP_HOST_TYPE'} M=$DNSINFO->{'M_HOST_TYPE'}";
			}

		if ($DISPLAY) {
			$DOMAINS{$domain} = $DNSINFO;
			push @{$PROFILES{$DNSINFO->{'PROFILE'}}}, $domain;
			}
		}
	@MSGS = @DEBUG;

	my $class = 'r1';
	foreach my $ns (sort keys %PROFILES) {

		## SHOW_PROFILE is a setting that is passed to us from the DOMAINS area
		next if (($SHOW_PROFILE ne '') && ($SHOW_PROFILE ne $ns));
		$class = ($class eq 'r0')?'r1':'r0';

		my $panel = 'BUILDER:'.$ns;

		my ($content,$state) = ('',1);
		#if (($SHOW_PROFILE ne '') && ($SHOW_PROFILE eq $ns)) {
		#	($state)++;
		#	}
		#elsif (defined $LU) { 
		#	($state) = $LU->get('builder.'.$panel,0); 
		#	}
		
		$content = '';
		if ($state) {
			my $nsref = &ZOOVY::fetchmerchantns_ref($USERNAME,$ns);
			$content = &DOMAIN::PANELS::panel_builder($LU,'','LOAD',$nsref,{})
			}
		$out .= &AJAX::PANELS::render_panel($panel,$ns,$state,$content);
		}


	if (($prtinfo->{'p_navcats'}>0) || ($PRT==0)) {
		## only show navcat's on partition 0, or when the partition has it's own navigation.
		my ($content,$state) = ('',1);
		if (defined $LU) { ($state) = $LU->get('builder.navcat',0); }
		$content = ($state)?&DOMAIN::PANELS::panel_navcat($LU,'','LOAD',undef,{}):'';
		$out .= &AJAX::PANELS::render_panel('NAVCAT','Website Navigation Categories',$state,$content);
		}
	
	$GTOOLS::TAG{'<!-- PROFILES -->'} = $out;	
	}





## detect if we are in popup mode (we're editing a product) 
##		note: in popup mode we want to skip headers
my $is_popup = 0;
if ((defined $SITE) && ($SITE->pid() ne '')) { 
	$is_popup = 1; 
	if (scalar(@MSGS)>0) {
		$GTOOLS::TAG{'<!-- MSGS -->'} = &GTOOLS::show_msgs(\@MSGS);
		}
	}

&GTOOLS::output(file=>$template_file,header=>1,
	'js'=>($ACTION eq 'COMPANYEDIT')?1:0,
	help=>"#50361",
	'head'=>($ACTION eq '')?&AJAX::PANELS::header('BUILDEREDIT','','/biz/setup/builder/index.cgi'):'',
	tabs=>\@TABS,
	msgs=>\@MSGS,
	'jquery'=>'1',
	bc=>\@BC,
	popup=>$is_popup,
	'zmvc'=>1,
	todo=>1,
	);



