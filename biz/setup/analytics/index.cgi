#!/usr/bin/perl

use strict;

use lib "/httpd/modules";
use GTOOLS;
use ZOOVY;
use LUSER;
use ZWEBSITE;
use DOMAIN::TOOLS;
use DOMAIN;
use SYNDICATION;
use ZTOOLKIT::SECUREKEY;
use BATCHJOB;
use LISTING::MSGS;

my ($LU) = LUSER->authenticate(flags=>'_S&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }


my $GUID = &BATCHJOB::make_guid();
$GTOOLS::TAG{'<!-- GUID -->'} = $GUID;

$GTOOLS::TAG{'<!-- PRT -->'} = $PRT;
my $template_file = 'index.shtml';

my @TABS = (
	);
my @BC = (
	{ link=>'/biz/setup/', name=>"Setup" },
	{ link=>'/biz/setup/plugin/',  name=>"Analytics &amp; Plugins" },
	);
my @MSGS = ();

my $SO = undef;

my $VERB = $ZOOVY::cgiv->{'VERB'};
my $PROFILE = $ZOOVY::cgiv->{'PROFILE'};
$GTOOLS::TAG{'<!-- PROFILE -->'} = $PROFILE;

$::WARN_INSECURE_FOOTER_REFERENCE = "The string 'http:' appears in the footer javascript. This could be a reference to an insecure image/pixel/iframe. The footer is normally shown on checkout/secure pages and so an insecure reference could cause a security warning with IE 8. Please consider changing from http: to https: if possible.";
$::WARN_INSECURE_CHKOUT_REFERENCE = "The string 'http:' appears in the checkout javascript. This could be a reference to an insecure image/pixel/iframe. The footer is normally shown on checkout/secure pages and so an insecure reference could cause a security warning with IE 8. Please consider changing from http: to https: if possible.";
$::WARN_INSECURE_CHKOUT_REFERENCE = "The string 'http:' appears in the login javascript. This could be a reference to an insecure image/pixel/iframe. The footer is normally shown on checkout/secure pages and so an insecure reference could cause a security warning with IE 8. Please consider changing from http: to https: if possible.";

my @WARNINGS = ();
my $NSREF = undef;
my $WEBDB = undef;
$WEBDB = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
if ($PROFILE ne '') {
	$NSREF = &ZOOVY::fetchmerchantns_ref($USERNAME,$PROFILE);
	}



my $help = '51020';



##
## Google Analytics.
##
if ($VERB eq 'GOOGLETS-SAVE') {
	$NSREF->{'googlets:search_account_id'} = $ZOOVY::cgiv->{'search_account_id'};
	$NSREF->{'googlets:badge_code'} = $ZOOVY::cgiv->{'badge_code'};
	$NSREF->{'googlets:chkout_code'} = $ZOOVY::cgiv->{'chkout_code'};
#	$NSREF->{'analytics:headjs'} = $ZOOVY::cgiv->{'head_code'};
#	$NSREF->{'analytics:syndication'} = (defined $ZOOVY::cgiv->{'syndication'})?'GOOGLE':'';
#	$NSREF->{'analytics:roi'} = 'GOOGLE';
#	$NSREF->{'analytics:linker'} = (defined $ZOOVY::cgiv->{'linker'})?time():'';
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$LU->log("SETUP.PLUGIN","Saved GOOGLE TRUSTED STORES plugin code","SAVE");
	$VERB = 'GOOGLETS';
	}


if ($VERB eq 'GOOGLETS') {
	$GTOOLS::TAG{'<!-- SEARCH_ACCOUNT_ID -->'} = $NSREF->{'googlets:search_account_id'};
	$GTOOLS::TAG{'<!-- BADGE_CODE -->'} = &ZOOVY::incode($NSREF->{'googlets:badge_code'});
	$GTOOLS::TAG{'<!-- CHKOUT_CODE -->'} = &ZOOVY::incode($NSREF->{'googlets:chkout_code'});
#	$GTOOLS::TAG{'<!-- CHK_ROI -->'} = ($NSREF->{'analytics:roi'} eq 'GOOGLE')?'checked':'';
#	$GTOOLS::TAG{'<!-- CHK_SYNDICATION -->'} = ($NSREF->{'analytics:syndication'} eq 'GOOGLE')?'checked':'';
#	$GTOOLS::TAG{'<!-- CHK_LINKER -->'} = ($NSREF->{'analytics:linker'}>0)?'checked':'';
#
#	if ($GTOOLS::TAG{'<!-- HEAD_CODE -->'} =~ /XXXXX/) {
#		$GTOOLS::TAG{'<!-- MESSAGE -->'} = qq~ <div class="error">Zoovy Marketing Services Google Analytics Code has not been customized and will not work.</div>~;
#		}

#	if ($NSREF->{'analytics:headjs'} =~ /urchin/) {
#		push @WARNINGS, "Appears to have older 'urchin' version of the google code. Many zoovy features (such as Google Checkout) will not work.";
#		}

	require DOMAIN::TOOLS;
	my ($DOMAIN) = &DOMAIN::TOOLS::domain_for_profile($USERNAME,$PROFILE);
	my $ztscode = '';
	open F, "<googlets.txt";
	$/ = undef; $ztscode = <F>; $/ = "\n";
	close F;
	require URI::Escape;
	$GTOOLS::TAG{'<!-- ZTSCODE -->'} = ZOOVY::incode($ztscode);

	
	$template_file = 'googlets.shtml';
	push @BC, { name=>'Google Trusted Stores' };
	}





if ($VERB eq 'DECALS') {
	$GTOOLS::TAG{'<!-- WRAPPER -->'} = $NSREF->{'zoovy:site_wrapper'};

	require TOXML;	

	my ($t) = TOXML->new('WRAPPER',$NSREF->{'zoovy:site_wrapper'},USERNAME=>$USERNAME);
	my (@decals) = $t->findElements('DECAL');
	my $c = '';
	foreach my $d (@decals) {
		$c .= "<tr>";
		$c .= "<td width=100% class='zoovysub1header'>$d->{'PROMPT'}</td>";
		$c .= "</tr>";
		$c .= "<tr>";
		$c .= "<td>";
		$c .= "<div class='hint'>Max Height: $d->{'HEIGHT'} &nbsp;  Max Width: $d->{'WIDTH'}</div>";
		$c .= "</td>";
		$c .= "</tr>";
		}
	$GTOOLS::TAG{'<!-- DECALS -->'} = $c;

	$template_file = 'decals.shtml';
	}


if ($VERB eq 'FACEBOOK-APP-SAVE') {
	my ($webdb) = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
	$webdb->{'facebook_appid'} = int($ZOOVY::cgiv->{'facebook_appid'});
	$webdb->{'facebook_secret'} = int($ZOOVY::cgiv->{'facebook_secret'});
	&ZWEBSITE::save_website_dbref($USERNAME,$webdb,$PRT);
	if ($webdb->{'facebook_appid'} ne '') {
		push @MSGS, "SUCCESS|Set Facebook Application ID";
		}
	$VERB = 'FACEBOOK-APP';
	}

if ($VERB eq 'FACEBOOK-APP') {
	my ($webdb) = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
	$GTOOLS::TAG{'<!-- FACEBOOK_APPID -->'} = $webdb->{'facebook_appid'};	
	$GTOOLS::TAG{'<!-- FACEBOOK_SECRET -->'} = $webdb->{'facebook_secret'};	
	$template_file = 'facebook-app.shtml';
	}


##
##
##

if ($VERB eq 'TWITTER-SAVE') {
	my ($webdb) = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);

	$webdb->{'twitter'} = &ZTOOLKIT::buildparams({
		'access_token'=>$ZOOVY::cgiv->{'twitter:access_token'},
		'access_secret'=>$ZOOVY::cgiv->{'twitter:access_secret'},
		'consumer_key'=>$ZOOVY::cgiv->{'twitter:consumer_key'},
		'consumer_secret'=>$ZOOVY::cgiv->{'twitter:consumer_secret'},
		});
	&ZWEBSITE::save_website_dbref($USERNAME,$webdb,$PRT);

	$NSREF->{'twitter:userid'} = $ZOOVY::cgiv->{'twitter:userid'};
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);

	push @MSGS, "SUCCESS|Saved Twitter Settings";
	$VERB = 'TWITTER';
	}

if ($VERB eq 'TWITTER') {
	my ($webdb) = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
	my $twitref = &ZTOOLKIT::parseparams($webdb->{'twitter'});
	$GTOOLS::TAG{'<!-- ACCESS_TOKEN -->'} = &ZOOVY::incode($twitref->{'access_token'});
	$GTOOLS::TAG{'<!-- ACCESS_SECRET -->'} = &ZOOVY::incode($twitref->{'access_secret'});
	$GTOOLS::TAG{'<!-- CONSUMER_KEY -->'} = &ZOOVY::incode($twitref->{'consumer_key'});
	$GTOOLS::TAG{'<!-- CONSUMER_SECRET -->'} = &ZOOVY::incode($twitref->{'consumer_secret'});

	$GTOOLS::TAG{'<!-- TWITTER_USERID -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'twitter:userid'});

	$template_file = 'twitter.shtml';
	}





#if ($VERB eq 'BLINKLOGIC-SAVE') {
#	my %pref = ();
#	$pref{'enable'} = int($ZOOVY::cgiv->{'enable'});
#	$pref{'ftp_user'} = $ZOOVY::cgiv->{'ftp_user'};
#	$pref{'ftp_pass'} = $ZOOVY::cgiv->{'ftp_pass'};
#	$pref{'ftp_server'} = $ZOOVY::cgiv->{'ftp_server'};
#	$WEBDB->{'blinklogic'} = &ZTOOLKIT::buildparams(\%pref);
#	&ZWEBSITE::save_website_dbref($USERNAME,$WEBDB,$PRT);
#	$GTOOLS::TAG{'<!-- MESSAGE -->'} = "Settings saved.";
#	$VERB = 'BLINKLOGIC';
#	}


#if ($VERB eq 'BLINKLOGIC') {
#	my ($pref) = &ZTOOLKIT::parseparams($WEBDB->{'blinklogic'});
#	$GTOOLS::TAG{'<!-- ENABLE_0 -->'} = ($pref->{'enable'}==0)?'selected':'';
#	$GTOOLS::TAG{'<!-- ENABLE_1 -->'} = ($pref->{'enable'}==1)?'selected':'';
#	$GTOOLS::TAG{'<!-- FTP_USER -->'} = &ZOOVY::incode($pref->{'ftp_user'});
#	$GTOOLS::TAG{'<!-- FTP_PASS -->'} = &ZOOVY::incode($pref->{'ftp_pass'});
#	$GTOOLS::TAG{'<!-- FTP_SERVER -->'} = &ZOOVY::incode($pref->{'ftp_server'});
#	$template_file = 'blinklogic.shtml';
#	}

if ($VERB eq 'DEBUG-RUN') {

	my ($lm) = LISTING::MSGS->new($USERNAME);

	#$SITE::merchant_id = $USERNAME;
	#$SITE::SREF->{'%NSREF'} = $NSREF;
	#$SITE::SREF->{'_NS'} = $PROFILE;

	$SITE::CART2 = CART2->new_memory($USERNAME,$PRT);
	$SITE::CART2->in_set('cart/refer',$ZOOVY::cgiv->{'meta'});
	my ($SITE) = SITE->new($USERNAME,'PRT'=>$PRT,'NS'=>$PROFILE,'*CART2'=>$SITE::CART2);

	my @MSGS = ();
	foreach my $i (1..3) {
		my $sku = $ZOOVY::cgiv->{"sku$i"};
		next if ($sku eq '');

		my $STID = $ZOOVY::cgiv->{"sku$i"};;
		next if ($STID eq '');
		my $QTY = 1;

		my ($pid,$claim,$invopts,$noinvopts,$virtual) = PRODUCT::stid_to_pid($STID);
		my ($P) = PRODUCT->new($USERNAME,$pid);
		my ($suggested_variations) = $P->suggest_variations('guess'=>1,'stid'=>$STID);
		foreach my $suggestion (@{$suggested_variations}) {
			if ($suggestion->[4] eq 'guess') {
				$lm->pooshmsg("WARN|+STID:$STID POG:$suggestion->[0] VALUE:$suggestion->[1] was guesssed (reason: not specified or invalid)");
				}
			}
		my $variations = STUFF2::variation_suggestions_to_selections($suggested_variations);
		$SITE::CART2->stuff2()->cram( $STID, $QTY, $variations, '*P'=>$P, '*LM'=>$lm );
		}

	foreach my $msg (@{$lm->msgs()}) {
		my ($ref,$status) = LISTING::MSGS->msg_to_disposition($msg);
		push @MSGS, "$ref->{'_'}|$ref->{'+'}";
		}

	#require SITE::MSGS;
	#$SITE::msgs = SITE::MSGS->new($USERNAME,PRT=>$PRT,CART2=>$SITE::CART2);

	use Data::Dumper;

	$SITE::CART2->in_set('our/orderid','2010-01-123456');
	my $out = $SITE->conversion_trackers($SITE::CART2);
#	my $out = '';

	$GTOOLS::TAG{'<!-- DEBUG_OUT -->'} = '<hr><h1>OUTPUT:</h1><pre>'.&ZOOVY::incode($out).'</pre>';

	$GTOOLS::TAG{'<!-- DEBUG_OUT -->'} .= '<hr><h1>Additional Diagnostic Info:</h1><pre>'.&ZOOVY::incode(Dumper([\@MSGS,$SITE::CART2,$SITE])).'</pre>EOF';
	$VERB = 'DEBUG';
	}


if ($VERB eq 'DEBUG') {
	$GTOOLS::TAG{'<!-- SKU1 -->'} = $ZOOVY::cgiv->{'sku1'};
	$GTOOLS::TAG{'<!-- SKU2 -->'} = $ZOOVY::cgiv->{'sku2'};
	$GTOOLS::TAG{'<!-- SKU3 -->'} = $ZOOVY::cgiv->{'sku3'};
	$GTOOLS::TAG{'<!-- META -->'} = $ZOOVY::cgiv->{'meta'};

   my $profref = &DOMAIN::TOOLS::syndication_profiles($USERNAME,PRT=>$PRT);
	my $c = '';
   foreach my $ns (sort keys %{$profref}) {
		my ($selected) = ($ZOOVY::cgiv->{'PROFILE'} eq $ns)?'selected':'';
		$c .= "<option $selected value=\"$ns\">$profref->{$ns}</option>";
		}
	$GTOOLS::TAG{'<!-- PROFILES -->'} = $c;
	$template_file = 'debug.shtml';
	}



if ($VERB eq 'GOOGAPI-RETURN') {
	if ($ZOOVY::cgiv->{'RESULT'} eq 'SUCCESS') {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<font color='blue'>Successfully setup token</font><br>";
		}
	else {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<font color='red'>Unspecified Error</font><br>";
		}

	$VERB = 'GOOGAPI';
	}
	
if ($VERB eq 'GOOGAPI') {
	my ($webdb) = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
	$GTOOLS::TAG{'<!-- ANALYTICS_TOKEN -->'} = $webdb->{'google_token_analytics'};
	$template_file = 'googapi.shtml';
	}


#if ($VERB eq 'RM-SAVE') {
#	$NSREF->{'razormo:chkoutjs'} = $ZOOVY::cgiv->{'checkout_code'};
#	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
#	$VERB = 'RM';
#	}
#
#if ($VERB eq 'RM') {
#	push @BC, { name=>'RazorMouth' };	
#	$GTOOLS::TAG{'<!-- CHECKOUT_CODE -->'} = &ZOOVY::incode($NSREF->{'razormo:chkoutjs'});
#	if ($NSREF->{'razormo:chkoutjs'} =~ /http:/) {
#		push @WARNINGS, $::WARN_INSECURE_CHKOUT_REFERENCE;
#		}
#	$template_file = 'rm.shtml';
#	push @BC, { name=>'RazorMouth' };	
#	}


##
##
##

if ($VERB eq 'SAS-SAVE') {
	$NSREF->{'sas:chkoutjs'} = $ZOOVY::cgiv->{'checkout_code'};
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$VERB = 'SAS';
	}

if ($VERB eq 'SAS') {
	$GTOOLS::TAG{'<!-- CHECKOUT_CODE -->'} = &ZOOVY::incode($NSREF->{'sas:chkoutjs'});
	if ($NSREF->{'sas:chkoutjs'} =~ /http:/) {
		push @WARNINGS, $::WARN_INSECURE_CHKOUT_REFERENCE;
		}
	$template_file = 'sas.shtml';
	push @BC, { name=>'Share-A-Sale' };	
	}


##
##
##

if ($VERB eq 'LINKSHARE-SAVE') {
	$NSREF->{'linkshare:chkoutjs'} = $ZOOVY::cgiv->{'checkout_code'};
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$VERB = 'LINKSHARE';
	}

if ($VERB eq 'LINKSHARE') {
	$GTOOLS::TAG{'<!-- CHECKOUT_CODE -->'} = &ZOOVY::incode($NSREF->{'linkshare:chkoutjs'});
	if ($NSREF->{'linkshare:chkoutjs'} =~ /http:/) {
		push @WARNINGS, $::WARN_INSECURE_CHKOUT_REFERENCE;
		}
	$template_file = 'linkshare.shtml';
	push @BC, { name=>'LinkShare' };	
	}

##
##
##

if ($VERB eq 'BECOME-SAVE') {
	$NSREF->{'become:chkoutjs'} = $ZOOVY::cgiv->{'checkout_code'};
	$NSREF->{'become:filter'} = int(defined $ZOOVY::cgiv->{'filter'});
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$LU->log("SETUP.PLUGIN","Saved PRONTO plugin code","SAVE");
	$VERB = 'BECOME';
	}


if ($VERB eq 'BECOME') {
	$GTOOLS::TAG{'<!-- CHECKOUT_CODE -->'} = &ZOOVY::incode($NSREF->{'become:chkoutjs'});
	$GTOOLS::TAG{'<!-- CHK_FILTER -->'} = ($NSREF->{'become:filter'})?'checked':'';

	if ($NSREF->{'become:chkoutjs'} =~ /PUT_YOUR_DATA_HERE/) {
		push @WARNINGS, "PUT_YOUR_DATA_HERE is not a valid variable.";
		}
	if ($NSREF->{'become:chkoutjs'} =~ /\%OrderID\%/) {
		push @WARNINGS, "%OrderID% is not a valid Zoovy variable, you probably meant to customize this.";
		}
	if ($NSREF->{'become:chkoutjs'} =~ /http:/) {
		push @WARNINGS, $::WARN_INSECURE_CHKOUT_REFERENCE;
		}
	$template_file = 'become.shtml';
	push @BC, { name=>'Become.com' };
	}


##
if ($VERB eq 'OTHER-SAVE') {
	$NSREF->{'plugin:headjs'} = $ZOOVY::cgiv->{'head_code'};
	$NSREF->{'zoovy:head_nonsecure'} = $ZOOVY::cgiv->{'head_nonsecure_code'};
	$NSREF->{'zoovy:head_secure'} = $ZOOVY::cgiv->{'head_secure_code'};

	$NSREF->{'plugin:footerjs'} = $ZOOVY::cgiv->{'footer_code'};
	$NSREF->{'plugin:loginjs'} = $ZOOVY::cgiv->{'login_code'};
	$NSREF->{'plugin:chkoutjs'} = $ZOOVY::cgiv->{'checkout_code'};
	$NSREF->{'plugin:invoicejs'} = $ZOOVY::cgiv->{'invoice_code'};

	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$LU->log("SETUP.PLUGIN","Saved OTHER plugin code","SAVE");
	$VERB = 'OTHER';
	}


if ($VERB eq 'OTHER') {
	$GTOOLS::TAG{'<!-- HEAD_CODE -->'} = &ZOOVY::incode($NSREF->{'plugin:headjs'});
	$GTOOLS::TAG{'<!-- HEAD_NONSECURE_CODE -->'} = &ZOOVY::incode($NSREF->{'zoovy:head_nonsecure'});
	$GTOOLS::TAG{'<!-- HEAD_SECURE_CODE -->'} = &ZOOVY::incode($NSREF->{'zoovy:head_secure'});
	$GTOOLS::TAG{'<!-- LOGIN_CODE -->'} = &ZOOVY::incode($NSREF->{'plugin:loginjs'});
	$GTOOLS::TAG{'<!-- FOOTER_CODE -->'} = &ZOOVY::incode($NSREF->{'plugin:footerjs'});
	$GTOOLS::TAG{'<!-- CHECKOUT_CODE -->'} = &ZOOVY::incode($NSREF->{'plugin:chkoutjs'});
	$GTOOLS::TAG{'<!-- INVOICE_CODE -->'} = &ZOOVY::incode($NSREF->{'plugin:invoicejs'});
	$template_file = 'other.shtml';

	if ($NSREF->{'zoovy:head_secure'} =~ /favico/) {
		push @WARNINGS, "You should not reference a favico in head_secure - this will cause errors on your site. Please reference webdoc.";
		}
	if ($NSREF->{'zoovy:head_nonsecure'} =~ /favico/) {
		push @WARNINGS, "You should not reference a favico in head_nonsecure - this will cause errors on your site. Please reference webdoc.";
		}
	if ($NSREF->{'plugin:headjs'} =~ /favico/) {
		push @WARNINGS, "You should not reference a favico in headjs - this will cause errors on your site. Please reference webdoc.";
		}

	if ($NSREF->{'plugin:footerjs'} =~ /http\:\/\//) {
		push @WARNINGS, $::WARN_INSECURE_FOOTER_REFERENCE;
		}
	if ($NSREF->{'plugin:chkoutjs'} =~ /http\:\/\//) {
		push @WARNINGS, $::WARN_INSECURE_CHKOUT_REFERENCE;
		}
	if ($NSREF->{'plugin:loginjs'} =~ /http\:\/\//) {
		push @WARNINGS, $::WARN_INSECURE_CHKOUT_REFERENCE;
		}

	push @BC, { name=>'Other' };
	}




if ($VERB eq 'KOUNT-SAVE') {
	require PLUGIN::KOUNT;

#	my $apifile = PLUGIN::KOUNT::pem_file($USERNAME,$PRT,"api");
#	open F, ">$apifile";
#	print F $ZOOVY::cgiv->{'api'};
#	close F;
#	chown 65534,65534, $apifile;

#	my $risfile = PLUGIN::KOUNT::pem_file($USERNAME,$PRT,"ris");
#	open F, ">$risfile";
#	print F $ZOOVY::cgiv->{'ris'};
#	close F;
#	chown 65534,65534, $risfile;
	
	if (($ZOOVY::cgiv->{'RIS-CERT'} ne '') && ($ZOOVY::cgiv->{'RIS-PASS'} ne '')) {
		## if we have a CERT-RIS then save it.
		my ($q) = CGI->new();
		my $fh = $q->param('RIS-CERT');
		$/ = undef; my $out = <$fh>; $/ = "\n";

		my $pass = $ZOOVY::cgiv->{'RIS-PASS'};

		my $tmpfile = "/tmp/kount-$$.p12";	
		open F, ">$tmpfile"; print F $out; close F;
		my $tmpfile2 = "/tmp/kount-$$.pm";	
		my ($cmd) = "/usr/bin/openssl pkcs12 -in $tmpfile -out $tmpfile2 -nodes -passin pass:$pass\n";
		print STDERR $cmd;
		system($cmd);

		open F, "<$tmpfile2"; $/ = undef; my ($pem) = <F>; $/ = "\n"; close F; 

		my ($pk) = PLUGIN::KOUNT->new($USERNAME,prt=>$PRT);
		open F, ">".$pk->pem_file("RIS");
		print F $pem;
		close F;
		}

	my ($cfg) = PLUGIN::KOUNT::load_config($USERNAME);
	$cfg->{'enable'} = int($ZOOVY::cgiv->{'kount_enable'});
	$cfg->{'multisite'} = $ZOOVY::cgiv->{'kount_multisite'};
	$cfg->{'prodtype'} = $ZOOVY::cgiv->{'kount_prodtype'};
	
	PLUGIN::KOUNT::save_config($USERNAME,$cfg);

#	$WEBDB->{'kount'} = int($ZOOVY::cgiv->{'kount_enable'});
#	my ($pref) = &ZTOOLKIT::parseparams($WEBDB->{'kount_config'});
#	$WEBDB->{'kount_config'} = &ZTOOLKIT::buildparams($pref);
#	&ZWEBSITE::save_website_dbref($USERNAME,$WEBDB,$PRT);
	$VERB = 'KOUNT';
	}

if ($VERB eq 'KOUNT') {
	require PLUGIN::KOUNT;
	my ($ID) = &PLUGIN::KOUNT::resolve_kountid($USERNAME,$PRT);
	if ($ID==0) { $VERB = 'KOUNT-REGISTER'; }
	}

if ($VERB eq 'KOUNT-PROVISION') {
	require PLUGIN::KOUNT;

	my ($ID) = 0;
	if ($FLAGS =~ /,TRIAL,/) {
		$ID = -1; 
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<div class='error'>Trial accounts cannot use this feature.</div>";
		}

	if ($ID==0) {
		## we'd still be at $ID 0 if we had no fatal errors.
		($ID) = PLUGIN::KOUNT::provision($USERNAME);
		}

	if ($ID==0) { 
		$VERB = 'KOUNT-REGISTER'; 
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<div class='error'>Unfortunately no new users can be added at this time. Please contact support</div>";
		} 
	else { 
		$VERB = 'KOUNT'; 
		}
	}

if ($VERB eq 'KOUNT-REGISTER') {
	$template_file = 'kount-register.shtml';
	}


if ($VERB eq 'KOUNT') {

#	my $apifile = PLUGIN::KOUNT::pem_file($USERNAME,$PRT,"api");
#	open F, "<$apifile"; $/ = undef; $GTOOLS::TAG{'<!-- API -->'} = &ZOOVY::incode(<F>); $/ = "\n"; close F;
#
#	my $risfile = PLUGIN::KOUNT::pem_file($USERNAME,$PRT,"ris");
#	open F, "<$risfile"; $/ = undef; $GTOOLS::TAG{'<!-- RIS -->'} = &ZOOVY::incode(<F>); $/ = "\n"; close F;

	my ($kcfg) = &PLUGIN::KOUNT::load_config($USERNAME);

	# $WEBDB->{'kount'} = int($WEBDB->{'kount'});
	$GTOOLS::TAG{'<!-- ENABLE_0 -->'} = ($kcfg->{'enable'}==0)?'selected':'';
	$GTOOLS::TAG{'<!-- ENABLE_1 -->'} = ($kcfg->{'enable'}==1)?'selected':'';
	$GTOOLS::TAG{'<!-- ENABLE_2 -->'} = ($kcfg->{'enable'}==2)?'selected':'';

	$GTOOLS::TAG{'<!-- MULTISITE_ -->'} = ($kcfg->{'multisite'} eq '')?'selected':'';
	$GTOOLS::TAG{'<!-- MULTISITE_SDOMAIN -->'} = ($kcfg->{'multisite'} eq 'sdomain')?'selected':'';
	$GTOOLS::TAG{'<!-- MULTISITE_PRT -->'} = ($kcfg->{'multisite'} eq 'prt')?'selected':'';

	$GTOOLS::TAG{'<!-- PRODTYPE_ZOOVY:CATALOG -->'} = ($kcfg->{'prodtype'} eq 'zoovy:catalog')?'selected':'';
	$GTOOLS::TAG{'<!-- PRODTYPE_ZOOVY:PROD_BRAND -->'} = ($kcfg->{'prodtype'} eq 'zoovy:prod_brand')?'selected':'';
	$GTOOLS::TAG{'<!-- PRODTYPE_ZOOVY:PROD_SHIPCLASS -->'} = ($kcfg->{'prodtype'} eq 'zoovy:prod_shipclass')?'selected':'';
	$GTOOLS::TAG{'<!-- PRODTYPE_ZOOVY:PROD_PROMOCLASS -->'} = ($kcfg->{'prodtype'} eq 'zoovy:prod_promoclass')?'selected':'';

	$GTOOLS::TAG{'<!-- MERCHANT -->'} = &ZOOVY::incode($kcfg->{'merchant'});

	require PLUGIN::KOUNT;
	my ($pk) = PLUGIN::KOUNT->new($USERNAME,prt=>$PRT);
#	$GTOOLS::TAG{'<!-- RIS_FILE -->'} = (-f $pk->pem_file('RIS'))?'installed':qq~<b>Not Installed/Required:</b>
#<br>PKCS12 RIS File: <input type="file" name="RIS-CERT"><br>
#PCKS12 Pass: <input type="textbox" name="RIS-PASS"><br>~;
#	$GTOOLS::TAG{'<!-- API_FILE -->'} = (-f $pk->pem_file('API'))?'installed':'not installed';
	$GTOOLS::TAG{'<!-- PASSWORD -->'} = ($LU->is_admin())?$pk->password():'** REQUIRES ADMIN **';

	$template_file = 'kount.shtml';
	}



##
## Google Analytics.
##
if ($VERB eq 'GOOGLEAN-SAVE') {
	$NSREF->{'analytics:headjs'} = $ZOOVY::cgiv->{'head_code'};
	$NSREF->{'analytics:syndication'} = (defined $ZOOVY::cgiv->{'syndication'})?'GOOGLE':'';
	$NSREF->{'analytics:roi'} = 'GOOGLE';
	$NSREF->{'analytics:linker'} = (defined $ZOOVY::cgiv->{'linker'})?time():'';
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$LU->log("SETUP.PLUGIN","Saved GOOGLE plugin code","SAVE");
	$VERB = 'GOOGLEAN';
	}


if ($VERB eq 'GOOGLEAN') {
	$GTOOLS::TAG{'<!-- HEAD_CODE -->'} = &ZOOVY::incode($NSREF->{'analytics:headjs'});
	$GTOOLS::TAG{'<!-- CHK_ROI -->'} = ($NSREF->{'analytics:roi'} eq 'GOOGLE')?'checked':'';
	$GTOOLS::TAG{'<!-- CHK_SYNDICATION -->'} = ($NSREF->{'analytics:syndication'} eq 'GOOGLE')?'checked':'';
	$GTOOLS::TAG{'<!-- CHK_LINKER -->'} = ($NSREF->{'analytics:linker'}>0)?'checked':'';

	if ($GTOOLS::TAG{'<!-- HEAD_CODE -->'} =~ /XXXXX/) {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = qq~ <div class="error">Zoovy Marketing Services Google Analytics Code has not been customized and will not work.</div>~;
		}

	my ($webdb) = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
	if ($webdb->{'google_api_env'}==0) {
		## no google checkout
		}
	elsif ($webdb->{'google_api_analytics'}==0) {
		##
		## analytics/api - 
		##
		$GTOOLS::TAG{'<!-- GOOGLE_CHECKOUT_STATUS -->'} = qq~
<div class="alert">
Google Checkout is currently enabled, but analytics tracking is not. Please go to Setup | Payments | Google Checkout |
and enable "Google Analytics Support" to ensure accurate reporting.
</div>
~;
		}
	elsif ($webdb->{'google_api_analytics'}==1) {
		## 
		$GTOOLS::TAG{'<!-- GOOGLE_CHECKOUT_STATUS -->'} = qq~<div class="success">Google Checkout is currently enabled and configured to use non-Async (pagetracker) Code.</div>~;
		if ($NSREF->{'analytics:headjs'} !~ /pagetracker/i) {
			$GTOOLS::TAG{'<!-- GOOGLE_CHECKOUT_STATUS -->'} = qq~<div class="error">Google Checkout analytics support is currently enabled, but it does not appear to match our analytics code release.</div>~;
			}
		}
	elsif ($webdb->{'google_api_analytics'}==2) {
		## 
		$GTOOLS::TAG{'<!-- GOOGLE_CHECKOUT_STATUS -->'} = qq~<div class="success">Google Checkout is currently enabled and configured to use Async (gaq) Code.</div>~;
		if ($NSREF->{'analytics:headjs'} !~ /_gaq/i) {
			$GTOOLS::TAG{'<!-- GOOGLE_CHECKOUT_STATUS -->'} = qq~<div class="error">Google Checkout analytics support is currently enabled, but it does not appear to match our analytics code release.</div>~;
			}
		}


	if ($NSREF->{'analytics:headjs'} =~ /urchin/) {
		push @WARNINGS, "Appears to have older 'urchin' version of the google code. Many zoovy features (such as Google Checkout) will not work.";
		}


	require DOMAIN::TOOLS;
	my ($DOMAIN) = &DOMAIN::TOOLS::domain_for_profile($USERNAME,$PROFILE);
	my $zmsjs = '';
	open F, "<ga.txt";
	$/ = undef; $zmsjs = <F>; $/ = "\n";
	close F;
	$zmsjs =~ s/%DOMAIN%/$DOMAIN/gs;

	require URI::Escape;
	$GTOOLS::TAG{'<!-- ZMSJS -->'} = ZOOVY::incode($zmsjs);
	
	$template_file = 'googlean.shtml';
	push @BC, { name=>'Google Analytics' };
	}







###############################################################################
##
## Google Webmaster Tools
##
if ($VERB eq 'SAVE-GOOGLEWMT') {
	# Saves changes to the sitemap
	my $ERRORS = 0;

	require DOMAIN::TOOLS;
	require DOMAIN;
	my (@domains) = DOMAIN::TOOLS::domains($USERNAME,PROFILE=>$PROFILE,PRT=>$PRT);

	foreach my $domain ($USERNAME.'.zoovy.com',sort @domains) {
		if (defined($ZOOVY::cgiv->{$domain})) {
			my ($D) = DOMAIN->new($USERNAME,$domain);
			next if (not defined $D);
			$D->set('GOOGLE_SITEMAP',$ZOOVY::cgiv->{$domain});
			$D->save();
			}
		}

	$LU->log('SETUP.GOOGLEWMT',"Updated sitemap settings for profile $PROFILE",'SAVE');

	if ($ERRORS == 0) {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} .= "<center><font face='helvetica, arial' color='red' size='5'><b>Successfully Saved!</b></font></center><br><br>";
		}
	else {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} .= "<center><font face='helvetica, arial' color='red' size='5'><b>Unable to SiteMaps!</b></font></center><br><br>"; 
		}	
	$VERB = 'GOOGLEWMT';
	}


if ($VERB eq 'GOOGLEWMT') {
	$template_file = 'googlewmt.shtml';
	$help = "#50596";

	push @BC, { name=>'Google Webmaster' };	

	$GTOOLS::TAG{'<!-- TS -->'} = time();
	$GTOOLS::TAG{'<!-- NS -->'} = $PROFILE;
	my $out = '';
	require DOMAIN::TOOLS;
	require DOMAIN;
	my (@domains) = DOMAIN::TOOLS::domains($USERNAME, PROFILE=>$PROFILE,PRT=>$PRT);
	my $i = 0;
	foreach my $domain (sort @domains) {
		## get value for webdb.bin
		my $value = '';
		my ($D) = DOMAIN->new($USERNAME,$domain);
	
		$out .= "<tr>";
		$out .= "<td>$domain</td>";
		if ($D->{'HOST_TYPE'} eq 'REDIR') {
			$out .= "<td>-- not compatible with redirects --</td>";
			}
		elsif ($D->{'HOST_TYPE'} eq 'NEWSLETTER') {
			$out .= "<td>-- not compatible with newsletter --</td>";
			}
		else {
			$value = $D->{'GOOGLE_SITEMAP'};
			$value = &ZOOVY::incode($value);
			$out .= qq~<td><input type="text" name="$domain" value="$value" size=80></td>~;
			$i++;
			}
		$out .= "</tr>\n"; 
		}

	if ($out eq '') {
		$out .= "<tr><td><i>You currently have no domains associated with profile $PROFILE</i></td></tr>";
		}

	if ($i>1) {
		$GTOOLS::TAG{'<!-- WARNINGS -->'} = qq~
<tr>
	<td class="rs" colspan=2>
	<b>DUPLICATE CONTENT WARNING</b><br>
	<font class="hint">
	You currently have more than one domain pointing to the same profile/homepage.
	SEO best practices state that you configure all other domains as redirects to your primary domain.
	Example: yourdomain.net, yourdomain.org, yourdomain.us all should redirect to yourdomain.com. 
	You could be inadvertantly hurting your search engine ranking. Go into Setup / Domain Configuration
	to correct this.
	</font>
	</td>
</tr>
~;
		}


	$GTOOLS::TAG{'<!-- DOMAINS -->'} = $out;
	## not used
	## $GTOOLS::TAG{'<!-- HELP_WRAPPER -->'} = &GTOOLS::help_link('Google SiteMap Help','detail/sitemaps.php','dev');
			
	}




##
## YAHOO WEBMASTER TOOLS
##
if ($VERB eq 'SAVE-YAHOOWMT') {
	# Saves changes to the sitemap
	my $ERRORS = 0;

	require DOMAIN::TOOLS;
	require DOMAIN;
	my (@domains) = DOMAIN::TOOLS::domains($USERNAME,PROFILE=>$PROFILE,PRT=>$PRT);

	foreach my $domain ($USERNAME.'.zoovy.com',sort @domains) {
		if (defined($ZOOVY::cgiv->{$domain})) {
			my ($D) = DOMAIN->new($USERNAME,$domain);
			next if (not defined $D);
			$D->set('YAHOO_SITEMAP',$ZOOVY::cgiv->{$domain});
			$D->save();
			}
		}

	$LU->log('SETUP.YAHOOWMT',"Updated yahoo sitemap settings for profile $PROFILE",'SAVE');

	if ($ERRORS == 0) {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} .= "<center><font face='helvetica, arial' color='red' size='5'><b>Successfully Saved!</b></font></center><br><br>";
		}
	else {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} .= "<center><font face='helvetica, arial' color='red' size='5'><b>Unable to SiteMaps!</b></font></center><br><br>"; 
		}	
	$VERB = 'YAHOOWMT';
	}


if ($VERB eq 'YAHOOWMT') {
	$template_file = 'yahoowmt.shtml';
	$help = "#50596";

	push @BC, { name=>'Yahoo Webmaster' };	

	$GTOOLS::TAG{'<!-- TS -->'} = time();
	$GTOOLS::TAG{'<!-- NS -->'} = $PROFILE;
	my $out = '';
	require DOMAIN::TOOLS;
	require DOMAIN;
	my (@domains) = DOMAIN::TOOLS::domains($USERNAME, PROFILE=>$PROFILE,PRT=>$PRT);
	my $i = 0;
	foreach my $domain (sort @domains) {
		## get value for webdb.bin
		my $value = '';
		my ($D) = DOMAIN->new($USERNAME,$domain);
	
		$out .= "<tr>";
		$out .= "<td>$domain</td>";
		if ($D->{'HOST_TYPE'} eq 'REDIR') {
			$out .= "<td>-- not compatible with redirects --</td>";
			}
#		elsif ($D->{'HOST_TYPE'} eq 'SPECIALTY') {
#			$out .= "<td>-- not compatible with specialty --</td>";
#			}
		elsif ($D->{'HOST_TYPE'} eq 'NEWSLETTER') {
			$out .= "<td>-- not compatible with newsletter --</td>";
			}
		else {
			$value = $D->{'YAHOO_SITEMAP'};
			$value = &ZOOVY::incode($value);
			$out .= qq~<td><input type="text" name="$domain" value="$value" size=80></td>~;
			$i++;
			}
		$out .= "</tr>\n"; 
		}

	if ($out eq '') {
		$out .= "<tr><td><i>You currently have no domains associated with profile $PROFILE</i></td></tr>";
		}

	if ($i>1) {
		$GTOOLS::TAG{'<!-- WARNINGS -->'} = qq~
<tr>
	<td class="rs" colspan=2>
	<b>DUPLICATE CONTENT WARNING</b><br>
	<font class="hint">
	You currently have more than one domain pointing to the same profile/homepage.
	SEO best practices state that you configure all other domains as redirects to your primary domain.
	Example: yourdomain.net, yourdomain.org, yourdomain.us all should redirect to yourdomain.com. 
	You could be inadvertantly hurting your search engine ranking. Go into Setup / Domain Configuration
	to correct this.
	</font>
	</td>
</tr>
~;
		}


	$GTOOLS::TAG{'<!-- DOMAINS -->'} = $out;
	## not used
	## $GTOOLS::TAG{'<!-- HELP_WRAPPER -->'} = &GTOOLS::help_link('Google SiteMap Help','detail/sitemaps.php','dev');
			
	}




##
## BING WEBMASTER TOOLS
##
if ($VERB eq 'SAVE-BINGWMT') {
	# Saves changes to the sitemap
	my $ERRORS = 0;

	require DOMAIN::TOOLS;
	require DOMAIN;
	my (@domains) = DOMAIN::TOOLS::domains($USERNAME,PROFILE=>$PROFILE,PRT=>$PRT);

	foreach my $domain ($USERNAME.'.zoovy.com',sort @domains) {
		if (defined($ZOOVY::cgiv->{$domain})) {
			my ($D) = DOMAIN->new($USERNAME,$domain);
			next if (not defined $D);
			$D->set('BING_SITEMAP',$ZOOVY::cgiv->{$domain});
			$D->save();
			}
		}

	$LU->log('SETUP.BINGWMT',"Updated bing sitemap settings for profile $PROFILE",'SAVE');

	if ($ERRORS == 0) {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} .= "<center><font face='helvetica, arial' color='red' size='5'><b>Successfully Saved!</b></font></center><br><br>";
		}
	else {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} .= "<center><font face='helvetica, arial' color='red' size='5'><b>Unable to SiteMaps!</b></font></center><br><br>"; 
		}	
	$VERB = 'BINGWMT';
	}


if ($VERB eq 'BINGWMT') {
	$template_file = 'bingwmt.shtml';
	$help = "#50596";

	$GTOOLS::TAG{'<!-- TS -->'} = time();
	$GTOOLS::TAG{'<!-- NS -->'} = $PROFILE;
	my $out = '';
	require DOMAIN::TOOLS;
	require DOMAIN;
	my (@domains) = DOMAIN::TOOLS::domains($USERNAME, PROFILE=>$PROFILE,PRT=>$PRT);
	my $i = 0;
	foreach my $domain (sort @domains) {
		## get value for webdb.bin
		my $value = '';
		my ($D) = DOMAIN->new($USERNAME,$domain);
	
		$out .= "<tr>";
		$out .= "<td>$domain</td>";
		if ($D->{'HOST_TYPE'} eq 'REDIR') {
			$out .= "<td>-- not compatible with redirects --</td>";
			}
#		elsif ($D->{'HOST_TYPE'} eq 'SPECIALTY') {
#			$out .= "<td>-- not compatible with specialty --</td>";
#			}
		elsif ($D->{'HOST_TYPE'} eq 'NEWSLETTER') {
			$out .= "<td>-- not compatible with newsletter --</td>";
			}
		else {
			$value = $D->{'BING_SITEMAP'};
			$value = &ZOOVY::incode($value);
			$out .= qq~<td><input type="text" name="$domain" value="$value" size=80></td>~;
			$i++;
			}
		$out .= "</tr>\n"; 
		}

	if ($out eq '') {
		$out .= "<tr><td><i>You currently have no domains associated with profile $PROFILE</i></td></tr>";
		}

	if ($i>1) {
		$GTOOLS::TAG{'<!-- WARNINGS -->'} = qq~
<tr>
	<td class="rs" colspan=2>
	<b>DUPLICATE CONTENT WARNING</b><br>
	<font class="hint">
	You currently have more than one domain pointing to the same profile/homepage.
	SEO best practices state that you configure all other domains as redirects to your primary domain.
	Example: yourdomain.net, yourdomain.org, yourdomain.us all should redirect to yourdomain.com. 
	You could be inadvertantly hurting your search engine ranking. Go into Setup / Domain Configuration
	to correct this.
	</font>
	</td>
</tr>
~;
		}


	$GTOOLS::TAG{'<!-- DOMAINS -->'} = $out;
	## not used
	## $GTOOLS::TAG{'<!-- HELP_WRAPPER -->'} = &GTOOLS::help_link('Google SiteMap Help','detail/sitemaps.php','dev');
			
	}




##
##
##
if ($VERB eq 'OMNITURE-SAVE') {	
	$NSREF->{'silverpop:listid'} = $ZOOVY::cgiv->{'silverpop:listid'};
	$NSREF->{'silverpop:enable'} = ($ZOOVY::cgiv->{'silverpop:enable'})?1:0;

	$NSREF->{'omniture:enable'} = (defined $ZOOVY::cgiv->{'enable'})?time():0;
	$NSREF->{'omniture:headjs'} = $ZOOVY::cgiv->{'head_code'};
	$NSREF->{'omniture:footerjs'} = $ZOOVY::cgiv->{'footer_code'};
	$NSREF->{'omniture:checkoutjs'} = $ZOOVY::cgiv->{'checkout_code'};
	$NSREF->{'omniture:cartjs'} = $ZOOVY::cgiv->{'cart_code'};
	$NSREF->{'omniture:categoryjs'} = $ZOOVY::cgiv->{'category_code'};
	$NSREF->{'omniture:productjs'} = $ZOOVY::cgiv->{'product_code'};
	$NSREF->{'omniture:resultjs'} = $ZOOVY::cgiv->{'result_code'};
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$LU->log("SETUP.PLUGIN","Saved OMNITURE plugin code","SAVE");
	$VERB = 'OMNITURE';
	}

if ($VERB eq 'OMNITURE') {
	$GTOOLS::TAG{'<!-- CHK_SILVERPOP -->'} = ($NSREF->{'silverpop:enable'})?'checked':'';
	$GTOOLS::TAG{'<!-- SILVERPOP_LISTID -->'} = &ZOOVY::incode($NSREF->{'silverpop:listid'});

	$GTOOLS::TAG{'<!-- CHK_ENABLE -->'} = ($NSREF->{'omniture:enable'})?'checked':'';
	$GTOOLS::TAG{'<!-- DISABLE_WARNING -->'} = ($NSREF->{'omniture:enable'})?'':'<font color="red">Warning: currently disabled, none of the settings below will be used.</font><br>';

	$GTOOLS::TAG{'<!-- HEAD_CODE -->'} = &ZOOVY::incode($NSREF->{'omniture:headjs'});
	$GTOOLS::TAG{'<!-- FOOTER_CODE -->'} = &ZOOVY::incode($NSREF->{'omniture:footerjs'});
	$GTOOLS::TAG{'<!-- CHECKOUT_CODE -->'} = &ZOOVY::incode($NSREF->{'omniture:checkoutjs'});
	$GTOOLS::TAG{'<!-- CART_CODE -->'} = &ZOOVY::incode($NSREF->{'omniture:cartjs'});
	$GTOOLS::TAG{'<!-- CATEGORY_CODE -->'} = &ZOOVY::incode($NSREF->{'omniture:categoryjs'});
	$GTOOLS::TAG{'<!-- PRODUCT_CODE -->'} = &ZOOVY::incode($NSREF->{'omniture:productjs'});
	$GTOOLS::TAG{'<!-- RESULT_CODE -->'} = &ZOOVY::incode($NSREF->{'omniture:resultjs'});
	$template_file = 'omniture.shtml';
	push @BC, { name=>'Omniture' };
	}


##
##
##
if ($VERB eq 'SHOPCOM-SAVE') {
#	$NSREF->{'shopcom:headjs'} = $ZOOVY::cgiv->{'head_code'};
	$NSREF->{'shopcom:filter'} = int(defined $ZOOVY::cgiv->{'filter'});
	$NSREF->{'shopcom:chkoutjs'} = $ZOOVY::cgiv->{'chkout_code'};
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$LU->log("SETUP.PLUGIN","Saved SHOPCOM plugin code","SAVE");
	$VERB = 'SHOPCOM';
	}

if ($VERB eq 'SHOPCOM') {
#	$GTOOLS::TAG{'<!-- HEAD_CODE -->'} = &ZOOVY::incode($NSREF->{'shopcom:headjs'});
	$GTOOLS::TAG{'<!-- CHKOUT_CODE -->'} = &ZOOVY::incode($NSREF->{'shopcom:chkoutjs'});
	$GTOOLS::TAG{'<!-- CHK_FILTER -->'} = ($NSREF->{'shopcom:filter'})?'checked':'';
	if ($NSREF->{'shopcom:chkoutjs'} =~ /http:/) {
		push @WARNINGS, $::WARN_INSECURE_CHKOUT_REFERENCE;
		}
	$template_file = 'shopcom.shtml';
	push @BC, { name=>'Shopping.com/Dealtime' };
	}


##
##
##
if ($VERB eq 'YAHOO-SAVE') {
	$NSREF->{'yahooshop:headjs'} = $ZOOVY::cgiv->{'head_code'};
	$NSREF->{'yahooshop:filter'} = int(defined $ZOOVY::cgiv->{'filter'});
	$NSREF->{'yahooshop:chkoutjs'} = $ZOOVY::cgiv->{'chkout_code'};
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$LU->log("SETUP.PLUGIN","Saved YAHOO plugin code","SAVE");
	$VERB = 'YAHOO';
	}

if ($VERB eq 'YAHOO') {
	$GTOOLS::TAG{'<!-- HEAD_CODE -->'} = &ZOOVY::incode($NSREF->{'yahooshop:headjs'});
	$GTOOLS::TAG{'<!-- CHKOUT_CODE -->'} = &ZOOVY::incode($NSREF->{'yahooshop:chkoutjs'});
	$GTOOLS::TAG{'<!-- CHK_FILTER -->'} = ($NSREF->{'yahooshop:filter'})?'checked':'';
	if ($NSREF->{'yahooshop:chkoutjs'} =~ /http:/) {
		push @WARNINGS, $::WARN_INSECURE_CHKOUT_REFERENCE;
		}

	if ($NSREF->{'yahooshop:chkoutjs'} =~ /transId=\,currency=\,amount=/) {
		push @WARNINGS, "transId variable not interpolated";
		}

	$template_file = 'yahooshop.shtml';
	push @BC, { name=>'Yahoo' };
	}

##
##
##


if ($VERB eq 'FACEBOOK-SAVE') {
	$NSREF->{'facebook:url'} = $ZOOVY::cgiv->{'facebook:url'};
	$NSREF->{'facebook:chkout'} = (defined $ZOOVY::cgiv->{'facebook:chkout'})?1:0;
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$LU->log("SETUP.PLUGIN","Saved FACEBOOK settings","SAVE");
	$VERB = 'FACEBOOK';
	}

if ($VERB eq 'FACEBOOK') {
	$GTOOLS::TAG{'<!-- FACEBOOK_URL -->'} = &ZOOVY::incode($NSREF->{'facebook:url'});
	$GTOOLS::TAG{'<!-- CHK_FACEBOOK_CHKOUT -->'} = ($NSREF->{'facebook:chkout'})?'checked':'';

	$GTOOLS::TAG{'<!-- SIDEBAR_WARNING -->'} = '';
	if (($NSREF->{'facebook:url'} ne '') && ($NSREF->{'zoovy:sidebar_html'} !~ /facebook/)) {
		$GTOOLS::TAG{'<!-- SIDEBAR_WARNING -->'} = "<font color='red'>Facebook does not appear in sidebar</font>";
		}

	$template_file = 'facebook.shtml';
	}


#if ($VERB eq 'TWITTER-SAVE') {
#	$NSREF->{'twitter:url'} = $ZOOVY::cgiv->{'twitter:url'};
#	$NSREF->{'twitter:chkout'} = (defined $ZOOVY::cgiv->{'twitter:chkout'})?'checked':'';
#
#	$template_file = 'twitter.shtml';
#	push @BC, { name=>'Twitter' };
#	}

##
##
##

if ($VERB eq 'WISHPOT-SAVE') {
	$NSREF->{'wishpot:merchantid'} = $ZOOVY::cgiv->{'wishpot:merchantid'};
	$NSREF->{'wishpot:wishlist'} = (defined $ZOOVY::cgiv->{'wishpot:wishlist'})?1:0;
	$NSREF->{'wishpot:facebook'} = (defined $ZOOVY::cgiv->{'wishpot:facebook'})?1:0;
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$LU->log("SETUP.PLUGIN","Saved WISHPOT settings","SAVE");

	my ($so) = SYNDICATION->new($USERNAME,$PROFILE,'WSH');
	if (($NSREF->{'wishpot:merchantid'} eq '') || ($NSREF->{'wishpot:facebook'}==0)) {
	   $so->nuke();
		}
	else {
		$so->set('IS_ACTIVE',1);
		$so->save();
		}
	

	$VERB = 'WISHPOT';
	}

if ($VERB eq 'WISHPOT') {
	my ($so) = SYNDICATION->new($USERNAME,$PROFILE,'WSH');
	$GTOOLS::TAG{'<!-- FEED_STATUS -->'} = $so->statustxt();

	$GTOOLS::TAG{'<!-- WISHPOT_MERCHANTID -->'} = &ZOOVY::incode($NSREF->{'wishpot:merchantid'});
	$GTOOLS::TAG{'<!-- CHK_WISHLIST -->'} = ($NSREF->{'wishpot:wishlist'})?'checked':'';
	$GTOOLS::TAG{'<!-- CHK_FACEBOOK -->'} = ($NSREF->{'wishpot:facebook'})?'checked':'';

	$template_file = 'wishpot.shtml';
	}


if ($VERB eq 'VERUTA') {
	push @BC, { name=>'Veruta' };	
	$template_file = 'veruta.shtml';
	}


##
##
##
if ($VERB eq 'FETCHBACK-SAVE') {
	$NSREF->{'fetchback:loginjs'} = $ZOOVY::cgiv->{'fetchback:loginjs'};
	$NSREF->{'fetchback:chkoutjs'} = $ZOOVY::cgiv->{'fetchback:chkoutjs'};
	$NSREF->{'fetchback:cartjs'} = $ZOOVY::cgiv->{'fetchback:cartjs'};
	$NSREF->{'fetchback:footerjs'} = $ZOOVY::cgiv->{'fetchback:footerjs'};	
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$LU->log("SETUP.PLUGIN","Saved FETCHBACK plugin code","SAVE");
	$VERB = 'FETCHBACK';	
	}

if ($VERB eq 'FETCHBACK') {
	push @BC, { name=>'Fetchback' };	
	$GTOOLS::TAG{'<!-- LOGINJS -->'} = &ZOOVY::incode($NSREF->{'fetchback:loginjs'});
	$GTOOLS::TAG{'<!-- CHKOUTJS -->'} = &ZOOVY::incode($NSREF->{'fetchback:chkoutjs'});
	$GTOOLS::TAG{'<!-- CARTJS -->'} = &ZOOVY::incode($NSREF->{'fetchback:cartjs'});
	$GTOOLS::TAG{'<!-- FOOTERJS -->'} = &ZOOVY::incode($NSREF->{'fetchback:footerjs'});

	if ($NSREF->{'fetchback:loginjs'} =~ /http\:\/\//) {
		push @WARNINGS, $::WARN_INSECURE_LOGIN_REFERENCE;
		}
	if ($NSREF->{'fetchback:footerjs'} =~ /http\:\/\//) {
		push @WARNINGS, $::WARN_INSECURE_FOOTER_REFERENCE;
		}
	if ($NSREF->{'fetchback:chkoutjs'} =~ /http\:\/\//) {
		push @WARNINGS, $::WARN_INSECURE_CHKOUT_REFERENCE;
		}

	$template_file = 'fetchback.shtml';
	}



##
##
##
if ($VERB eq 'LIVECHAT-SAVE') {
	$NSREF->{'livechat:licenseid'} = $ZOOVY::cgiv->{'licenseid'};
	$NSREF->{'livechat:tracking'} = $ZOOVY::cgiv->{'tracking'};
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$LU->log("SETUP.PLUGIN","Saved LIVECHAT plugin code","SAVE");
	$VERB = 'LIVECHAT';
	}

if ($VERB eq 'LIVECHAT') {
	## LIVECHAT security key:
	$GTOOLS::TAG{'<!-- SECURITY_KEY -->'} = sprintf("%X:%s",$MID,$PROFILE);
	$GTOOLS::TAG{'<!-- LICENSEID -->'} = &ZOOVY::incode($NSREF->{'livechat:licenseid'});
	$GTOOLS::TAG{'<!-- TRACKING -->'} = &ZOOVY::incode($NSREF->{'livechat:tracking'});

	$template_file = 'livechat.shtml';
	push @BC, { name=>'LiveChat' };
	}


##
##
##

if ($VERB eq 'OLARK-SAVE') {
	$NSREF->{'olark:html'} = $ZOOVY::cgiv->{'html'};
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$LU->log("SETUP.PLUGIN","Saved OLARK plugin code","SAVE");
	$VERB = 'OLARK';
	}

if ($VERB eq 'OLARK') {
	## LIVECHAT security key:
	$GTOOLS::TAG{'<!-- HTML -->'} = &ZOOVY::incode($NSREF->{'olark:html'});

	$template_file = 'olark.shtml';
	push @BC, { name=>'OLark' };
	}



##
##
##

if ($VERB eq 'PROVIDESUPPORT-SAVE') {
	$NSREF->{'pschat:html'} = $ZOOVY::cgiv->{'html'};
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$LU->log("SETUP.PLUGIN","Saved PROVIDESUPPORT plugin code","SAVE");
	$VERB = 'PROVIDESUPPORT';
	}

if ($VERB eq 'PROVIDESUPPORT') {
	## LIVECHAT security key:
	$GTOOLS::TAG{'<!-- HTML -->'} = &ZOOVY::incode($NSREF->{'pschat:html'});

	$template_file = 'providesupport.shtml';
	push @BC, { name=>'ProvideSupport' };
	}



# UPSELLIT
#
if ($VERB eq 'UPSELLIT-SAVE') {
	$NSREF->{'upsellit:footerjs'} = $ZOOVY::cgiv->{'footerjs'};
	$NSREF->{'upsellit:chkoutjs'} = $ZOOVY::cgiv->{'chkoutjs'};
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$LU->log("SETUP.PLUGIN","Saved UPSELLIT code","SAVE");
	$VERB = 'UPSELLIT';
	}

if ($VERB eq 'UPSELLIT') {
	$GTOOLS::TAG{'<!-- FOOTERJS -->'} = &ZOOVY::incode($NSREF->{'upsellit:footerjs'});
	$GTOOLS::TAG{'<!-- CHKOUTJS -->'} = &ZOOVY::incode($NSREF->{'upsellit:chkoutjs'});
	if ($NSREF->{'upsellit:chkoutjs'} =~ /http:/) {
		push @WARNINGS, $::WARN_INSECURE_CHKOUT_REFERENCE;
		}
	$template_file = 'upsellit.shtml';
	push @BC, { name=>'UpSellIt' };
	}




##
##
##
if ($VERB eq 'POWERREVIEWS-SAVE') {
	$NSREF->{'powerreviews:merchantid'} = $ZOOVY::cgiv->{'merchantid'};
	$NSREF->{'powerreviews:enable'} = (defined $ZOOVY::cgiv->{'enable'})?1:0;
	$NSREF->{'powerreviews:groupid'} = $ZOOVY::cgiv->{'groupid'};
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$LU->log("SETUP.PLUGIN","Saved POWERREVIEWS code","SAVE");


## Product page:
## <script type="text/javascript">
# var pr_style_sheet="http://cdn.powerreviews.com/aux/10942/2953/css/powerreviews_express.css";
# </script>
# <script type="text/javascript" src="http://cdn.powerreviews.com/repos/10942/pr/pwr/engine/js/full.js"></script>
##
##
# 
#Review this
# <div class="pr_snippet_product">
# <script type="text/javascript">POWERREVIEWS.display.snippet(document, { pr_page_id : "PAGE_ID" });</script>
# </div>
#
#Review Javascript:
# <div class="pr_review_summary">
# <script type="text/javascript">POWERREVIEWS.display.engine(document, { pr_page_id : "PAGE_ID" });</script>
# </div>
#

# Category Page (header)
#<script type="text/javascript">
#var pr_style_sheet="http://cdn.powerreviews.com/aux/10942/2953/css/powerreviews_express.css";
#</script>
#<script type="text/javascript" src="http://cdn.powerreviews.com/repos/10942/pr/pwr/engine/js/full.js"></script>

# Category Page (review spot)
#<div class="pr_snippet_category">
#<script type="text/javascript">
#var pr_snippet_min_reviews=0;
#POWERREVIEWS.display.snippet(document, { pr_page_id : "PAGE_ID" });
#</script>
#</div>

	$VERB = 'POWERREVIEWS';
	}


if (($VERB eq 'POWERREVIEWS') && ($FLAGS =~ /,PR,/)) {
	
	}

if ($VERB eq 'POWERREVIEWS') {
	## POWERREVIEWS security key:
	require ZTOOLKIT::SECUREKEY;
	my ($KEY) = &ZTOOLKIT::SECUREKEY::gen_key($USERNAME,'PR');
	$KEY = sprintf("%s:%s:%s:%s",uc($USERNAME),uc($PRT),$KEY,$PROFILE);
	my ($so) = SYNDICATION->new($USERNAME,$PROFILE,'PRV');
	my ($LASTRUN_GMT) = $so->get('PRODUCTS_LASTRUN_GMT');

	if ($LASTRUN_GMT>0) {
		$GTOOLS::TAG{'<!-- FILE_STATUS -->'} = qq~<a href="http://webapi.zoovy.com/webapi/powerreviews?key=$KEY">
	http://webapi.zoovy.com/webapi/powerreviews?key=$KEY
	</a><br>Last Generated: ~.&ZTOOLKIT::pretty_date($LASTRUN_GMT);
		}
	else {
		$GTOOLS::TAG{'<!-- FILE_STATUS -->'} = qq~-- please generate file --~;
		}

	$GTOOLS::TAG{'<!-- KEY -->'} = $KEY;
	$GTOOLS::TAG{'<!-- PRT -->'} = $PRT;
	$GTOOLS::TAG{'<!-- ENABLE -->'} = ($NSREF->{'powerreviews:enable'})?'checked':'';
	$GTOOLS::TAG{'<!-- MERCHANTID -->'} = &ZOOVY::incode($NSREF->{'powerreviews:merchantid'});
	$GTOOLS::TAG{'<!-- GROUPID -->'} = &ZOOVY::incode($NSREF->{'powerreviews:groupid'});

	$template_file = 'powerreviews.shtml';
	push @BC, { name=>'PowerReviews' };
	}

##
##
##
if ($VERB eq 'MSNADCENTER-SAVE') {
	$NSREF->{'msnad:filter'} = int(defined $ZOOVY::cgiv->{'filter'});
	$NSREF->{'msnad:chkoutjs'} = $ZOOVY::cgiv->{'head_code'};
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$LU->log("SETUP.PLUGIN","Saved MSNADCENTER plugin code","SAVE");
	$VERB = 'MSNADCENTER';
	}

if ($VERB eq 'MSNADCENTER') {
	$GTOOLS::TAG{'<!-- HEAD_CODE -->'} = &ZOOVY::incode($NSREF->{'msnad:chkoutjs'});
	if ($NSREF->{'msnad:chkoutjs'} =~ /http:/) {
		push @WARNINGS, $::WARN_INSECURE_CHKOUT_REFERENCE;
		}
	$GTOOLS::TAG{'<!-- CHK_FILTER -->'} = ($NSREF->{'msnad:filter'})?'checked':'';
	$template_file = 'msnadcenter.shtml';
	push @BC, { name=>'MSN' };
	}

##
##
##
if ($VERB eq 'NEXTAG-SAVE') {
	$NSREF->{'nextag:chkoutjs'} = $ZOOVY::cgiv->{'checkout_code'};
	$NSREF->{'nextag:filter'} = int(defined $ZOOVY::cgiv->{'filter'});
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$LU->log("SETUP.PLUGIN","Saved NEXTAG plugin code","SAVE");
	$VERB = 'NEXTAG';
	}

if ($VERB eq 'NEXTAG') {
	$GTOOLS::TAG{'<!-- CHECKOUT_CODE -->'} = &ZOOVY::incode($NSREF->{'nextag:chkoutjs'});
	$GTOOLS::TAG{'<!-- CHK_FILTER -->'} = ($NSREF->{'nextag:filter'})?'checked':'';

	if ($NSREF->{'nextag:chkoutjs'} =~ /\<\%order_total\%\>/) {
		push @WARNINGS, "Default variable: \<\%order_total\%\>";
		}
	if ($NSREF->{'nextag:chkoutjs'} =~ /http:/) {
		push @WARNINGS, $::WARN_INSECURE_CHKOUT_REFERENCE;
		}

	$template_file = 'nextag.shtml';
	push @BC, { name=>'NexTag' };
	}


##
##
##
if ($VERB eq 'PRICEGRABBER-SAVE') {
	$NSREF->{'pgrabber:chkoutjs'} = $ZOOVY::cgiv->{'checkout_code'};
	$NSREF->{'pgrabber:filter'} = int(defined $ZOOVY::cgiv->{'filter'});
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$LU->log("SETUP.PLUGIN","Saved PRICEGRABBER plugin code","SAVE");
	$VERB = 'PRICEGRABBER';
	}

if ($VERB eq 'PRICEGRABBER') {
	$GTOOLS::TAG{'<!-- CHECKOUT_CODE -->'} = &ZOOVY::incode($NSREF->{'pgrabber:chkoutjs'});
	$GTOOLS::TAG{'<!-- CHK_FILTER -->'} = ($NSREF->{'pgrabber:filter'})?'checked':'';
	if ($NSREF->{'pgrabber:chkoutjs'} =~ /a\|b\|c\|d\|e\|f/) {
		push @WARNINGS, "a|b|c|d|e|f are examples intended for use by programmers.";
		}
	if ($NSREF->{'pgrabber:chkoutjs'} =~ /http:/) {
		push @WARNINGS, $::WARN_INSECURE_CHKOUT_REFERENCE;
		}
	$template_file = 'pricegrabber.shtml';
	push @BC, { name=>'PriceGrabber' };	
	}

##
## 
##
if ($VERB eq 'CJ-SAVE') {
	$NSREF->{'cj:chkoutjs'} = $ZOOVY::cgiv->{'checkout_code'};
	$NSREF->{'cj:filter'} = int(defined $ZOOVY::cgiv->{'filter'});
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$LU->log("SETUP.PLUGIN","Saved CJ plugin code","SAVE");
	$VERB = 'CJ';
	}

if ($VERB eq 'CJ') {

	push @BC, { name=>'Commission Junction' };	
	$GTOOLS::TAG{'<!-- CHECKOUT_CODE -->'} = &ZOOVY::incode($NSREF->{'cj:chkoutjs'});
	if ($NSREF->{'cj:chkoutjs'} =~ /http:/) {
		push @WARNINGS, $::WARN_INSECURE_CHKOUT_REFERENCE;
		}
	$GTOOLS::TAG{'<!-- CHK_FILTER -->'} = ($NSREF->{'cj:filter'})?'checked':'';
	$template_file = 'cj.shtml';
	}


##
## 
##
if ($VERB eq 'OMNISTAR-SAVE') {
	$NSREF->{'omnistar:chkoutjs'} = $ZOOVY::cgiv->{'checkout_code'};
	$NSREF->{'omnistar:filter'} = int(defined $ZOOVY::cgiv->{'filter'});
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$LU->log("SETUP.PLUGIN","Saved OMNISTAR plugin code","SAVE");
	$VERB = 'OMNISTAR';
	}

if ($VERB eq 'OMNISTAR') {

	push @BC, { name=>'Omnistar' };	
	$GTOOLS::TAG{'<!-- CHECKOUT_CODE -->'} = &ZOOVY::incode($NSREF->{'omnistar:chkoutjs'});
	if ($NSREF->{'omnistar:chkoutjs'} =~ /http:/) {
		push @WARNINGS, $::WARN_INSECURE_CHKOUT_REFERENCE;
		}
	$GTOOLS::TAG{'<!-- CHK_FILTER -->'} = ($NSREF->{'omnistar:filter'})?'checked':'';
	$template_file = 'omnistar.shtml';
	}



##
## 
##
if ($VERB eq 'KOWABUNGA-SAVE') {
	$NSREF->{'kowabunga:chkoutjs'} = $ZOOVY::cgiv->{'checkout_code'};
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$LU->log("SETUP.PLUGIN","Saved KOWABUNGA plugin code","SAVE");
	$VERB = 'KOWABUNGA';
	}

if ($VERB eq 'KOWABUNGA') {
	$GTOOLS::TAG{'<!-- CHECKOUT_CODE -->'} = &ZOOVY::incode($NSREF->{'kowabunga:chkoutjs'});
	if ($NSREF->{'kowabunga:chkoutjs'} =~ /http:/) {
		push @WARNINGS, $::WARN_INSECURE_CHKOUT_REFERENCE;
		}
	$template_file = 'kowabunga.shtml';
	push @BC, { name=>'Kowabunga' };
	}

##
## 
##
if ($VERB eq 'BIZRATE-SAVE') {
	$NSREF->{'bizrate:chkoutjs'} = $ZOOVY::cgiv->{'checkout_code'};
	$NSREF->{'bizrate:filter'} = int(defined $ZOOVY::cgiv->{'filter'});
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$LU->log("SETUP.PLUGIN","Saved BIZRATE plugin code","SAVE");
	$VERB = 'BIZRATE';
	}

if ($VERB eq 'BIZRATE') {
	$GTOOLS::TAG{'<!-- CHECKOUT_CODE -->'} = &ZOOVY::incode($NSREF->{'bizrate:chkoutjs'});
	$GTOOLS::TAG{'<!-- CHK_FILTER -->'} = ($NSREF->{'bizrate:filter'})?'checked':'';

	if ($NSREF->{'bizrate:chkoutjs'} =~ /PUT_YOUR_DATA_HERE/) {
		push @WARNINGS, "PUT_YOUR_DATA_HERE is not a valid variable.";
		}
	if ($NSREF->{'bizrate:chkoutjs'} =~ /\%OrderID\%/) {
		push @WARNINGS, "%OrderID% is not a valid Zoovy variable, you probably meant to customize this.";
		}
	if ($NSREF->{'bizrate:chkoutjs'} =~ /http:/) {
		push @WARNINGS, $::WARN_INSECURE_CHKOUT_REFERENCE;
		}
	$template_file = 'bizrate.shtml';
	push @BC, { name=>'BizRate' };
	}



##
## 
##
if ($VERB eq 'PRONTO-SAVE') {
	$NSREF->{'pronto:chkoutjs'} = $ZOOVY::cgiv->{'checkout_code'};
	$NSREF->{'pronto:filter'} = int(defined $ZOOVY::cgiv->{'filter'});
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$LU->log("SETUP.PLUGIN","Saved PRONTO plugin code","SAVE");
	$VERB = 'PRONTO';
	}

if ($VERB eq 'PRONTO') {
	$GTOOLS::TAG{'<!-- CHECKOUT_CODE -->'} = &ZOOVY::incode($NSREF->{'pronto:chkoutjs'});
	$GTOOLS::TAG{'<!-- CHK_FILTER -->'} = ($NSREF->{'pronto:filter'})?'checked':'';

	if ($NSREF->{'pronto:chkoutjs'} =~ /PUT_YOUR_DATA_HERE/) {
		push @WARNINGS, "PUT_YOUR_DATA_HERE is not a valid variable.";
		}
	if ($NSREF->{'pronto:chkoutjs'} =~ /\<\%ORDERID\%\>/i) {
		push @WARNINGS, "&lt;%ORDERID%&gt; is not a valid Zoovy variable, you probably meant to customize this.";
		}
	if ($NSREF->{'pronto:chkoutjs'} =~ /\<\%SUBTOTAL\%\>/i) {
		push @WARNINGS, "&lt;%SUBTOTAL%&gt; is not a valid Zoovy variable, you probably meant to customize this.";
		}


	if ($NSREF->{'pronto:chkoutjs'} =~ /http:/) {
		push @WARNINGS, $::WARN_INSECURE_CHKOUT_REFERENCE;
		}
	$template_file = 'pronto.shtml';
	push @BC, { name=>'Pronto' };
	}



##
##
##
if ($VERB eq 'GOOGLEAW-SAVE') {
	$NSREF->{'googleaw:chkoutjs'} = $ZOOVY::cgiv->{'head_code'};
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);
	$LU->log("SETUP.PLUGIN","Saved GOOGLEAW plugin code","SAVE");
	$VERB = 'GOOGLEAW';
	}

if ($VERB eq 'GOOGLEAW') {
	if ($NSREF->{'googleaw:chkoutjs'} =~ /http:/) {
		push @WARNINGS, $::WARN_INSECURE_CHKOUT_REFERENCE;
		}
	$GTOOLS::TAG{'<!-- HEAD_CODE -->'} = &ZOOVY::incode($NSREF->{'googleaw:chkoutjs'});
	$template_file = 'googleaw.shtml';
	$help = 50595;
	push @BC, { name=>'GoogleAdwords' };
	}




##
##
##
if ($VERB eq 'UPIC-SAVE') {
	$VERB = 'UPIC';

	## Syndication isn't setup to support PRTs yet
	#my ($so) = SYNDICATION->new($USERNAME,"#$PRT","UPI");
	#my ($so) = SYNDICATION->new($USERNAME,"DEFAULT","UPI");
	#tie my %s, 'SYNDICATION', THIS=>$so;
	#$s{'.userid'} =  $ZOOVY::cgiv->{'userid'};
	## $s{'.pass'} =  $ZOOVY::cgiv->{'pass'};
	#$s{'IS_ACTIVE'} = int($ZOOVY::cgiv->{'enable'});

	my ($webdb) = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
	$webdb->{'upic'} = int($ZOOVY::cgiv->{'enable'});
	$webdb->{'upic_userid'} = $ZOOVY::cgiv->{'userid'};
	&ZWEBSITE::save_website_dbref($USERNAME,$webdb,$PRT);

	#untie %s;
	#$so->save();
	$LU->log("SETUP.PLUGIN","Saved UPIC plugin code ($webdb->{'upic'})","SAVE");
	}

if ($VERB eq 'UPIC') {
	$template_file = 'upic.shtml';
	## NOTE: at this point upic is NOT partition aware.

	my ($webdb) = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
	## Syndication isn't setup to support PRTs yet
	#my ($so) = SYNDICATION->new($USERNAME,"#$PRT","UPI");
	#my ($so) = SYNDICATION->new($USERNAME,"DEFAULT","UPI");
	#tie my %s, 'SYNDICATION', THIS=>$so;

	$GTOOLS::TAG{'<!-- CHK_ENABLE_0 -->'} = ($webdb->{'upic'}==0)?'checked':'';
	$GTOOLS::TAG{'<!-- CHK_ENABLE_1 -->'} = ($webdb->{'upic'}==1)?'checked':'';
	$GTOOLS::TAG{'<!-- USERID -->'} = (defined $webdb->{'upic_userid'})?$webdb->{'upic_userid'}:'';
	# $GTOOLS::TAG{'<!-- USERID -->'} = (defined $s{'.userid'})?$s{'.userid'}:'';
	# $GTOOLS::TAG{'<!-- PASS -->'} = (defined $s{'.pass'})?$s{'.pass'}:'';
	#$GTOOLS::TAG{'<!-- STATUS -->'} = $so->statustxt();
	
	if ($webdb->{'upic'}==0) {
		push @MSGS, "WARN|UPIC is disabled";
		}
	elsif ($webdb->{'upic_userid'} eq '') {
		push @MSGS, "WARN|No UPIC userid specified";
		}
	else {
		push @MSGS, "SUCCESS|UPIC is enabled, UPIC may download your order history.";
		}

	push @BC, { name=>'UPIC Insurance' };
	}





##
##
##

if (($VERB eq 'BUYSAFE-SAVE') || ($VERB eq 'BUYSAFE-REFRESH')) {

	require PLUGIN::BUYSAFE;

	my $webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
	$webdbref->{'buysafe_mode'} = $ZOOVY::cgiv->{'buysafe_mode'};
	$webdbref->{'buysafe_token'} = $ZOOVY::cgiv->{'buysafe_token'};
	$webdbref->{'buysafe_sealhtml'} = $ZOOVY::cgiv->{'buysafe_sealhtml'};
	&ZWEBSITE::save_website_dbref($USERNAME,$webdbref,$PRT);

	if ($VERB eq 'BUYSAFE-REFRESH') {
		## 
		}

	my $errcount = 0;
	my @domains = DOMAIN::TOOLS::domains($USERNAME,PRT=>$PRT);
	foreach my $name (@domains) {
		my ($changed) = 0;
		my ($d) = DOMAIN->new($USERNAME,$name);

		if (($d->{'BUYSAFE_TOKEN'} eq '') && ($VERB eq 'BUYSAFE-REFRESH')) {
			## they want us to get new tokens
			($d->{'BUYSAFE_TOKEN'},my $err) = &PLUGIN::BUYSAFE::AddStore($USERNAME,$PRT,$name);
			if ($err) {
				push @MSGS, "ERROR|BUYSAFE API ERROR [$name] token:".$d->{'BUYSAFE_TOKEN'}." Error: $err";
				$errcount++;
				}
			else {
				$changed++;
				}
			}
		elsif ($d->{'BUYSAFE_TOKEN'} ne $ZOOVY::cgiv->{$name}) {
			$d->{'BUYSAFE_TOKEN'} = $ZOOVY::cgiv->{$name};
			$changed++;
			}
	
		if ($changed) {
			$d->save();
			}
		}

	my @domainrefs = &DOMAIN::TOOLS::domains($USERNAME,PRT=>$PRT,DETAIL=>1);
	foreach my $domain (@domainrefs) {
		my $profile = $domain->{'PROFILE'};
		if ($profile eq '') { $profile = 'DEFAULT'; }
		next if not (defined $ZOOVY::cgiv->{"profile:$profile"});
		my ($ref) = &ZOOVY::fetchmerchantns_ref($USERNAME,$profile);
		$ref->{'zoovy:buysafe_sealhtml'} = $ZOOVY::cgiv->{"profile:$profile"};
		&ZOOVY::savemerchantns_ref($USERNAME,$profile,$ref);
		}

	if ($errcount==0) {
		push @MSGS, "SUCCESS|Saved settings";
		}
	
	$LU->log("SETUP.PLUGIN","Saved BUYSAFE plugin code","SAVE");
	$VERB = 'BUYSAFE';
	}


#my $tokensref = &BUYSAFE::loadTokens($USERNAME);
#if ((not defined $tokensref) || (scalar keys %{$tokensref}==0)) {
#	## Hmm.. they need to authenticate.
#	

#	$template_file = 'securekey.shtml';	
#	}



if ($VERB eq 'BUYSAFE-AUTO') {
	## check to see if we need to do "BUYSAFE-NEW" or "BUYSAFE"
	$VERB = 'BUYSAFE';
	# my $webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
	# if ($webdbref->{'buysafe_token'} eq '') { $VERB = 'BUYSAFE-NEW'; }
	}

#if ($VERB eq 'BUYSAFE-CREATE') {
#	## 
#	## Create a new buysafe user.
#	##
#	require BUYSAFE;
#	my ($err) = &PLUGIN::BUYSAFE::AddAccount($USERNAME,$PRT);
#	if ($err ne '') {
#		$GTOOLS::TAG{'<!-- ERROR -->'} = "<font color='red'>ERROR:".&ZOOVY::incode($err)."</font><br><br>";
#		$VERB = 'BUYSAFE-NEW';
#		}
#	else {
#		$VERB = 'BUYSAFE';
#		}
#	}

#if ($VERB eq 'BUYSAFE-NEW') {
#	## prompt the user to create an account.
#	$template_file = 'buysafe-new.shtml';
#	}



if (($VERB eq 'BUYSAFE') || ($VERB eq 'BUYSAFE-MANUAL')) {
	## let the user configure an existing account.
	my $webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
	my $buysafe_mode = $webdbref->{'buysafe_mode'};
	$GTOOLS::TAG{'<!-- BM_0 -->'} = ($buysafe_mode==0)?'selected':'';
	$GTOOLS::TAG{'<!-- BM_1 -->'} = ($buysafe_mode==1)?'selected':'';
	$GTOOLS::TAG{'<!-- BM_2 -->'} = ($buysafe_mode==2)?'selected':'';
	$GTOOLS::TAG{'<!-- BM_3 -->'} = ($buysafe_mode==3)?'selected':'';
	$GTOOLS::TAG{'<!-- BM_4 -->'} = ($buysafe_mode==4)?'selected':'';

	$GTOOLS::TAG{'<!-- TOKEN -->'} = $webdbref->{'buysafe_token'};
	my @domains = DOMAIN::TOOLS::domains($USERNAME,PRT=>$PRT);
	my $c = '';
	foreach my $name (sort @domains) {
		my ($d) = DOMAIN->new($USERNAME,$name);
		$c .= "<tr>";
		$c .= "<td>$name</td>";
		if ($d->{'BUYSAFE_TOKEN'} eq '') {
			## no buysafe token
			$c .= "<td><i>No Token Set</i></td>";
			push @MSGS, "WARN|No token set for domain: $name (hint: use 'Update Tokens' button to correct.)";
			}
		else {
			$c .= "<td><input size=\"80\" type=\"textbox\" value=\"$d->{'BUYSAFE_TOKEN'}\" name=\"$name\"></td>";
			}
		$c .= "</tr>";
		}
	$GTOOLS::TAG{'<!-- DOMAINS -->'} = $c;

	$c = '';
	my @domainrefs = &DOMAIN::TOOLS::domains($USERNAME,PRT=>$PRT);
	foreach my $domain (@domainrefs) {
		my ($D) = DOMAIN->new($USERNAME,$domain);
		my $profile = $D->{'PROFILE'};
		if ($profile eq '') { $profile = 'DEFAULT'; }
		my ($ref) = &ZOOVY::fetchmerchantns_ref($USERNAME,$profile);
		$c .= "<tr>";
		$c .= "<td valign=top><b>DOMAIN: $D->{'DOMAIN'}<br>PROFILE: $profile</b></td>";
		$c .= "<td valign=top><textarea cols=70 rows=3 name=\"profile:$profile\">";
		$c .= &ZOOVY::incode($ref->{'zoovy:buysafe_sealhtml'})."</textarea><br>";

		if (($buysafe_mode == 0) && ($ref->{'zoovy:sidebar_html'} =~ /buysafe/)) {
			## has buysafe in sidebar
			$c .= "<font color='red'>BUYSAFE IS CURRENTLY ADDED TO THEME SIDEBAR, BUT ZOOVY CART FUNCTIONALITY APPEARS TO BE DISABLED (THIS PROBABLY ISN'T WHAT YOU WANT).</font>";
			}
		elsif (($buysafe_mode>1) && ($ref->{'zoovy:sidebar_html'} =~ /buysafe/i)) {
			## has buysafe in sidebar
			my ($color) = ($ref->{'zoovy:buysafe_sealhtml'} eq '')?'red':'blue';
			$c .= "<font color='$color'>BUYSAFE IS ENABLED, AND CURRENTLY ADDED TO THEME SIDEBAR.</font>";
			}
		else {
			## no buysafe in sidebar
			my ($color) = ($ref->{'zoovy:buysafe_sealhtml'} eq '')?'red':'blue';
			if (($color eq 'blue') && ($buysafe_mode == 2)) { $color = 'red'; }
			$c .= "<font color='$color'>BUYSAFE HAS NOT BEEN ADDED TO THEME SIDEBAR.</font>";
			}

		$c .= "</td>";
		$c .= "</tr>";
		}
	$GTOOLS::TAG{'<!-- PROFILES -->'} = $c;

	my ($SECUREKEY) = &ZTOOLKIT::SECUREKEY::gen_key($USERNAME,'BS');
	$GTOOLS::TAG{'<!-- SECUREKEY -->'} = $SECUREKEY;

	push @BC, { name=>'buySAFE Website Bonding' };
	$template_file = 'buysafe.shtml';
	}



if ($VERB eq '') {

	$GTOOLS::TAG{'<!-- CHKOUT_ROI_DISPLAY_HINT -->'} = ($WEBDB->{'chkout_roi_display'})?'Always (even on failure)':'Only on successful/pending payments';

   my $profref = &DOMAIN::TOOLS::syndication_profiles($USERNAME,PRT=>$PRT);
   my $c = '';
   my $cnt = 0;
   foreach my $ns (sort keys %{$profref}) {
		my ($NSREF) = &ZOOVY::fetchmerchantns_ref($USERNAME,$ns);
      my $class = ($cnt++%2)?'r0':'r1';
      $c .= "<tr><td class=\"zoovysub1header\" colspan=4 valign=top class=\"$class\">$ns =&gt; $profref->{$ns}</td></tr>";
		$c .= "<tr><td width=20 class=\"$class\">&nbsp;</td>";
		$c .= "<td width=260 valign=top class=\"$class\">";
		$c .= "<br><b>Trust &amp; Seals:</b><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=GOOGLETS&PROFILE=$ns\">Google Trusted Stores</a><br>";
		$c .= "<br><b>SiteMap/Analytics:</b><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=GOOGLEAN&PROFILE=$ns\">Google Analytics</a><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=GOOGLEWMT&PROFILE=$ns\">Google Webmaster/SiteMap</a><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=BINGWMT&PROFILE=$ns\">Bing Webmaster/SiteMap</a><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=YAHOOWMT&PROFILE=$ns\">Yahoo Site Explorer</a><br>";
		$c .= "<br><b>Affiliate Programs:</b><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=SAS&PROFILE=$ns\">Share-A-Sale</a><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=OMNISTAR&PROFILE=$ns\">Omnistar</a><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=CJ&PROFILE=$ns\">Commission Junction</a><br>";
		# $c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=RM&PROFILE=$ns\">RazorMouth</a><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=KOWABUNGA&PROFILE=$ns\">MyAffiliateProgram/MyAP/KowaBunga!</a><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=LINKSHARE&PROFILE=$ns\">Linkshare.com</a><br>";

		$c .= "<br></td><td width=260 valign=top class=\"$class\">";
		$c .= "<br><b>Remarketing:</b><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=VERUTA&PROFILE=$ns\">Veruta</a><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=FETCHBACK&PROFILE=$ns\">FetchBack</a><br>";
		$c .= "<br><b>ROI Tracking:</b><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=GOOGLEAW&PROFILE=$ns\">Google Adwords</a><br>";
		# $c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=YAHOO&PROFILE=$ns\">Yahoo Shopping / CPC</a><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=SHOPCOM&PROFILE=$ns\">Shopping.com</a><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=BIZRATE&PROFILE=$ns\">Shopzilla/BizRate</a><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=PRONTO&PROFILE=$ns\">Pronto</a><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=MSNADCENTER&PROFILE=$ns\">MSN AdCenter</a><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=NEXTAG&PROFILE=$ns\">NexTag</a><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=PRICEGRABBER&PROFILE=$ns\">Pricegrabber</a><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=BECOME&PROFILE=$ns\">Become.com</a><br>";

		$c .= "<br></td><td width=260 valign=top class=\"$class\">";
		$c .= "<br><b>Customer Service/Relations:</b><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=FACEBOOK&PROFILE=$ns\">Facebook</a><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=TWITTER&PROFILE=$ns\">Twitter</a><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=POWERREVIEWS&PROFILE=$ns\">PowerReviews</a><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=PROVIDESUPPORT&PROFILE=$ns\">ProvideSupport Chat</a><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=OLARK&PROFILE=$ns\">OLark Chat</a><br>";
		if ($NSREF->{'livechat:tracking'} ne '') {
			$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=LIVECHAT&PROFILE=$ns\">LIVECHAT Software</a> (Deprecated)<br>";
			}
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=WISHPOT&PROFILE=$ns\">Wishpot (Social Shopping &amp; Wishlist)</a><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=UPSELLIT&PROFILE=$ns\">Upsellit</a><br>";
		$c .= "<br><b>Other/Non Supported:</b><br>";
#		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=DECALS&PROFILE=$ns\">Website Decals</a><br>";
		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=OTHER&PROFILE=$ns\">Other: Non Supported Application</a><br>";
#		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=OMNITURE&PROFILE=$ns\">Omniture SiteCatalyst / SilverPop</a><br>";
#		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=GOOGLE&PROFILE=$ns\">LivePerson</a><br>";
#		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=GOOGLE&PROFILE=$ns\">Kowabunga</a><br>";
#		$c .= "- <a href=\"/biz/setup/analytics/index.cgi?VERB=GOOGLE&PROFILE=$ns\">SecondBite</a><br>";

		$c .= "<Br>";
		$c .= "</td></tr>";
      }
   $GTOOLS::TAG{'<!-- PROFILES -->'} = $c;
   $template_file = 'index.shtml';
	}

$GTOOLS::TAG{'<!-- DISCLAIMER -->'} = qq~
<div>
<table style="border:1px dotted #e4de7b; margin:10px 0; background:#FFFEED;  text-align:left;" width=600>
<tr>
	<td><b>SUPPORT POLICY:</b></td>
</tr>
<tr>
	<td>
<div class="hint">

Access to this area is provided as a convenience to our clients.
Zoovy does not provide standard implementation or technical support for javascript hosted by other companies per our 
<a target="webdoc" href="http://www.zoovy.com/webdoc/index.cgi?VERB=DOC&DOCID=51375">3rd Party Javascript Policy</a>.

Support Requests will be routed to our 
<a target="webdoc" href="http://www.zoovy.com/webdoc/index.cgi?VERB=DOC&DOCID=51356">Marketing Services department</a>
and will have a billable project created. 

Programmers who plan to integrate services without assistance will most likely find the 
<a target="webdoc" href="http://www.zoovy.com/webdoc/index.cgi?VERB=DOC&DOCID=51020">Analytics/ROI Javascript Developer Documentation</a>
invaluable.  

By choosing to deploy code into this area you agree that you have been informed it is both possible, and easy to 
break your site in a variety of colorful and non-obvious ways, and that on higher traffic sites it can also impact our 
servers - therefore you also accept that any resources necessary to identify and correct associated problems 
will be charged back to your account. 

Clients who participate in our 
<a target="webdoc" href="http://www.zoovy.com/webdoc/index.cgi?VERB=DOC&DOCID=50849">Best Partner Practices</a>
program are required to utilize Zoovy marketing services.

	</td>
</tr>
</table>
</div>
~;
foreach my $warning (@WARNINGS) {
	$GTOOLS::TAG{'<!-- DISCLAIMER -->'} .= qq~
<table width=600><tr><td><div class="warning">
<b>WARNING:</b> $warning<br>
</div>
</td></tr></table>
~;	
	}
$GTOOLS::TAG{'<!-- DISCLAIMER -->'} .= '<br>';


##
##
&GTOOLS::output('*LU'=>$LU,
	title=>"Analytics and Plugins",
	file=>$template_file,
	js=>2+4,
	help=>$help,
	bc=>\@BC,
	msgs=>\@MSGS,
	tabs=>\@TABS,
	header=>1
	);
