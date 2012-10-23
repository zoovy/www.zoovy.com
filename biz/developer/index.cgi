#!/usr/bin/perl

use lib "/httpd/modules";
use CGI;
use GTOOLS;
use ZOOVY;
use ZWEBSITE;

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

if (!$USERNAME) { exit; }

my @BC = ();
push @BC, { name=>'Setup',link=>'http://www.zoovy.com/biz/setup','target'=>'_top', };
push @BC, { name=>'Site Integrator',link=>'http://www.zoovy.com/biz/developer/','target'=>'_top', };

my $ERROR = '';
my $q = new CGI;
my %webdb = &ZWEBSITE::fetch_website_db($USERNAME);
my $ACTION = $q->param('ACTION');

if ($FLAGS =~ /L1/) {
   if ($FLAGS =~ /DEV/) { $FLAGS .= ',API2,'; }
   }

if ($FLAGS !~ /,API2,/) {
   $template_file = "denied.shtml";
	$ACTION = 'ERROR';
	} 


if ($ACTION eq '') { $ACTION = 'WELCOME'; }

if ($ACTION eq "CONFIG-SAVE") {
	# This is for other stuff
   $url = $q->param('website_url');
   if (length($url)<5) { $url = "http://$USERNAME.zoovy.com"; }
   if ($url !~ /^http:\/\//i)
      { $url = "http://$url"; }
   &ZOOVY::savemerchant_attrib($USERNAME,"zoovy:website_url",$url); 

	if ($q->param('zoovy_dev'))
		{ $webdb{"dev_enabled"} = 1; } else { $webdb{"dev_enabled"} = 0; }

	if ($q->param('dev_softcart'))
		{ $webdb{"dev_softcart"} = 1; } else { $webdb{"dev_softcart"} = 0; }

	if ($q->param('dev_allownegative'))
		{ $webdb{"dev_allownegative"} = 1; } else { $webdb{"dev_allownegative"} = 0; }

	if ($q->param('dev_prod_redir'))
		{ $webdb{"dev_prod_redir"} = 1; } else { $webdb{"dev_prod_redir"} = 0; }

	if ($q->param('dev_nocategories'))
		{ $webdb{"dev_nocategories"} = 1; } else { $webdb{"dev_nocategories"} = 0; }

	if ($q->param('dev_nosubcategories'))
		{ $webdb{"dev_nosubcategories"} = 1; } else { $webdb{"dev_nosubcategories"} = 0; }

	if ($q->param('dev_nocontinue'))
		{ $webdb{"dev_nocontinue"} = 1; } else { $webdb{"dev_nocontinue"} = 0; }

	if ($q->param('dev_noclaimmsg'))
		{ $webdb{"dev_noclaimmsg"} = 1; } else { $webdb{"dev_noclaimmsg"} = 0; }

	if ($q->param('dev_sslonly'))
		{ $webdb{"dev_sslonly"} = 1; } else { $webdb{"dev_sslonly"} = 0; }

	if ($q->param('dev_nocartlink'))
		{ $webdb{"dev_nocartlink"} = 1; } else { $webdb{"dev_nocartlink"} = 0; }

	if ($q->param('dev_getmeta'))
		{ $webdb{"dev_getmeta"} = 1; } else { $webdb{"dev_getmeta"} = 0; }

	if ($q->param('dev_killframes'))
		{ $webdb{"dev_killframes"} = 1; } else { $webdb{"dev_killframes"} = 0; }

	if ($q->param('prodlist_disable_strip'))
		{ $webdb{"prodlist_disable_strip"} = 1; } else { $webdb{"prodlist_disable_strip"} = 0; }

	if ($q->param('dev_dashokay'))
		{ $webdb{"dev_dashokay"} = 1; } else { $webdb{"dev_dashokay"} = 0; }

	$webdb{"branding"} = $q->param('branding');
	$webdb{"dev_homepage"} = $q->param("homepage");
	$webdb{"dev_continue"} = $q->param("shopping");
	$webdb{"dev_search"} = $q->param("search");
	$webdb{"dev_aboutus"} = $q->param("aboutus");
	$webdb{"dev_news"} = $q->param("news");
	$webdb{"dev_returns"} = $q->param("retpolicy");
	$webdb{"dev_privacy"} = $q->param("privacy");
	$webdb{"dev_feedback"} = $q->param("feedback");
	$webdb{"dev_logout"} = $q->param("logout");
	$webdb{'dev_promotion_api'} = $q->param('promotion_api');
	$webdb{"dev_softcart_referers"} = $q->param("dev_softcart_referers");
	$webdb{'dev_chan_inc_attribs'} = $q->param('dev_chan_inc_attribs');
	$webdb{'dev_prod_inc_attribs'} = $q->param('dev_prod_inc_attribs');

	$webdb{'dev_claim_flow'} = $q->param('dev_claim_flow');
	$webdb{"dev_sidebar_html"} = $q->param("sidebar_html");

	if ($q->param('dev_sidebar_issecure'))
		{ $webdb{"dev_sidebar_issecure"} = 1; } else { $webdb{"dev_sidebar_issecure"} = 0; }
   
   if (&ZWEBSITE::save_website_dbref($USERNAME,\%webdb,$PRT)==0)
		{
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "Successfully Saved New Settings";
		} else {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "An error saving occured, the data may not have saved correctly! (data contained herein is not accurate)";
		} 
	$ACTION = 'CONFIG';
}



if ($ACTION eq 'CONFIG') {
	$GTOOLS::TAG{"<!-- WEBSITE_URL -->"} = &ZOOVY::fetchmerchant_attrib($USERNAME,'zoovy:website_url');

	if (!defined($webdb{"branding"})) { $webdb{"branding"} = 0; }
	$GTOOLS::TAG{"<!-- BRANDING_0 -->"} = '';
	$GTOOLS::TAG{"<!-- BRANDING_5 -->"} = '';
	$GTOOLS::TAG{"<!-- BRANDING_9 -->"} = '';
	$GTOOLS::TAG{'<!-- BRANDING_'.$webdb{'branding'}.' -->'} = ' selected ';

	if ($webdb{"dev_killframes"} eq "1") { $c = "CHECKED"; } else { $c = ""; }
	$GTOOLS::TAG{'<!-- DEV_KILLFRAMES -->'} = $c;

	if ($webdb{"dev_softcart"} eq "1") { $c = "CHECKED"; } else { $c = ""; }
	$GTOOLS::TAG{'<!-- DEV_SOFTCART -->'} = $c;

	if ($webdb{"dev_enabled"} eq "1") { $c = "CHECKED"; } else { 
		$c = ""; 
		$GTOOLS::TAG{'<!-- NO_DEV_WARNING -->'} = '<font color="red">WARNING: Developer Not Enabled - none of the settings below will take effect.<br></font>';
		}
	$GTOOLS::TAG{"<!-- DEV_ENABLED -->"} = $c;

	if ($webdb{"dev_nocategories"} eq "1") { $c = "CHECKED"; } else { $c = ""; }
	$GTOOLS::TAG{"<!-- DEV_NOCATEGORIES -->"} = $c;


	if ($webdb{"dev_allownegative"} eq "1") { $c = "CHECKED"; } else { $c = ""; }
	$GTOOLS::TAG{"<!-- DEV_ALLOWNEGATIVE -->"} = $c;


	if ($webdb{"dev_nosubcategories"} eq "1") { $c = "CHECKED"; } else { $c = ""; }
	$GTOOLS::TAG{"<!-- DEV_NOSUBCATEGORIES -->"} = $c;

	if ($webdb{"dev_nocontinue"} eq "1") { $c = "CHECKED"; } else { $c = ""; }
	$GTOOLS::TAG{"<!-- DEV_NOCONTINUE -->"} = $c;

	if ($webdb{"dev_sslonly"} eq "1") { $c = "CHECKED"; } else { $c = ""; }
	$GTOOLS::TAG{"<!-- DEV_SSLONLY -->"} = $c;

	if ($webdb{"dev_prod_redir"} eq "1") { $c = "CHECKED"; } else { $c = ""; }
	$GTOOLS::TAG{"<!-- DEV_PROD_REDIR -->"} = $c;

	if ($webdb{"prodlist_disable_strip"} eq "1") { $c = "CHECKED"; } else { $c = ""; }
	$GTOOLS::TAG{"<!-- PRODLIST_DISABLE_STRIP -->"} = $c;

	if ($webdb{"dev_dashokay"} eq "1") { $c = "CHECKED"; } else { $c = ""; }
	$GTOOLS::TAG{"<!-- DEV_DASHOKAY -->"} = $c;

	if ($webdb{"dev_nocartlink"} eq "1") { $c = "CHECKED"; } else { $c = ""; }
	$GTOOLS::TAG{"<!-- DEV_NOCARTLINK -->"} = $c;

	if ($webdb{"dev_getmeta"} eq "1") { $c = "CHECKED"; } else { $c = ""; }
	$GTOOLS::TAG{"<!-- DEV_GETMETA -->"} = $c;

	$c = $webdb{"dev_homepage"};
	if ((!defined($c)) || ($c eq "")) { $c = "/"; }
	$GTOOLS::TAG{"<!-- DEV_HOMEPAGE -->"} = $c;

	$c = $webdb{"dev_claim_flow"};
	if ((!defined($c)) || ($c eq "")) { $c = ""; }
	$GTOOLS::TAG{"<!-- DEV_CLAIM_FLOW -->"} = $c;

	if ($webdb{"dev_noclaimmsg"} eq "1") { $c = "CHECKED"; } else { $c = ""; }
	$GTOOLS::TAG{"<!-- DEV_NOCLAIMMSG -->"} = $c;

	$c = $webdb{"dev_continue"};
	if ((!defined($c)) || ($c eq "")) { $c = "/"; }
	$GTOOLS::TAG{"<!-- DEV_CONTINUE -->"} = $c;

	$c = $webdb{"dev_search"};
	if ((!defined($c)) || ($c eq "")) { $c = "/search.cgis"; }
	$GTOOLS::TAG{"<!-- DEV_SEARCH -->"} = $c;

	$c = $webdb{"dev_news"};
	if (!defined($c)) {
		if (defined $webdb{"dev_aboutus"} && $webdb{"dev_aboutus"} ne '') { $c = $webdb{"dev_aboutus"}; }
		else { $c = "/news.cgis"; }
	}
	$GTOOLS::TAG{"<!-- DEV_NEWS -->"} = $c;

	$c = $webdb{"dev_aboutus"};
	if ((!defined($c)) || ($c eq "")) { $c = "/company_info.cgis"; }
	$GTOOLS::TAG{"<!-- DEV_ABOUTUS -->"} = $c;

	$c = $webdb{"dev_returns"};
	if ($c eq "") { $c = "/returns.cgis"; }
	$GTOOLS::TAG{"<!-- DEV_RETURNPOLICY -->"} = $c;

	$c = $webdb{"dev_privacy"};
	if ($c eq "") { $c = "/privacy.cgis"; }
	$GTOOLS::TAG{"<!-- DEV_PRIVACYPOLICY -->"} = $c;

	$c = $webdb{"dev_feedback"};
	if ($c eq "") { $c = "/feedback.cgis"; }
	$GTOOLS::TAG{"<!-- DEV_FEEDBACK -->"} = $c;

	$c = $webdb{"dev_logout"};
	if ($c eq "") { $c = "/"; }
	$GTOOLS::TAG{"<!-- DEV_LOGOUT -->"} = $c;

	$c = $webdb{"dev_sidebar_html"};
	if (!defined($c)) { $c = ''; }
	$GTOOLS::TAG{"<!-- DEV_SIDEBAR_HTML -->"} = CGI::escapeHTML($c);

	if ($webdb{"dev_sidebar_issecure"} eq "1") { $c = "CHECKED"; } else { $c = ""; }
	$GTOOLS::TAG{"<!-- DEV_SIDEBAR_ISSECURE -->"} = $c;

	$c = $webdb{"dev_softcart_referers"};
	if (!defined($c)) { $c = ''; }
	$GTOOLS::TAG{"<!-- DEV_SOFTCART_REFERRERS -->"} = CGI::escapeHTML($c);

	$GTOOLS::TAG{'<!-- DEV_CHAN_INC_ATTRIBS -->'} = $webdb{'dev_chan_inc_attribs'};
	$GTOOLS::TAG{'<!-- DEV_PROD_INC_ATTRIBS -->'} = $webdb{'dev_prod_inc_attribs'};

	push @BC,{ name=>'Configuration' };
	$template_file = "config.shtml";
	}


#if ($ACTION eq "WEBAPI-SAVE") {
#	# This is for other stuff
#   $webdb{'dev_promotionapi2_url'} = $q->param('dev_promotionapi_url');
#	if ($webdb{'dev_promotionapi2_url'} eq '') { delete $webdb{'dev_promotionapi2_url'}; }
#
#   $webdb{'dev_promotionapi_attribs'} = $q->param('dev_promotionapi_attribs');
#	if ($webdb{'dev_promotionapi_attribs'} eq '') { delete $webdb{'dev_promotionapi_attribs'}; }
#
#   if (&ZWEBSITE::save_website_dbref($USERNAME,\%webdb,$PRT)==0)
#		{
#		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "Successfully Saved New Settings";
#		} else {
#		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "An error saving occured, the data may not have saved correctly! (data contained herein is not accurate)";
#		} 
#	$ACTION = 'WEBAPI';
#	}

#if ($ACTION eq 'WEBAPI') {
#	$GTOOLS::TAG{'<!-- DEV_PROMOTIONAPI_URL -->'} = $webdb{'dev_promotionapi2_url'};
#	$GTOOLS::TAG{'<!-- DEV_PROMOTIONAPI_ATTRIBS -->'} = $webdb{'dev_promotionapi_attribs'};
#	$template_file = 'api.shtml';
#	push @BC,{ name=>'WebAPIs' };
#	}



if ($ACTION eq 'WRAPPER-DOWNLOAD') {
	if ($cgi->param('TYPE') eq 'NS') {
		$filename = &ZOOVY::resolve_userpath($USERNAME) . '/wrapper.html';
		} 
	else {
		$filename = &ZOOVY::resolve_userpath($USERNAME) . '/swrapper.html';
		}
	open F, "<$filename";
	$/ = undef;
	print <F>;
	$/ = "\n";
	close F;
	exit;
	}

if ($ACTION eq 'WRAPPER-UPLOAD-NORMAL' || $ACTION eq 'WRAPPER-UPLOAD-SECURE') { 
   
	$fh = $cgi->upload('FILENAME');
	$filename = $cgi->param('FILENAME');

	if (not defined $filename || $filename eq '') { $filename = time(); }
	local $/ = undef;
	$BUFFER = <$fh>;;
	$/ = "\n";

	if ($ACTION eq 'UPLOAD-SECURE') { $wrapper = '/swrapper.html'; } else { $wrapper = '/wrapper.html'; }

	# at this point $BUFFER has the contents.
	if (length $BUFFER >= 70000) {
		$ERROR = 'File was too large, must be less than 70,000 bytes.';
	}
	elsif (length $BUFFER > 0) {
		$filename = &ZOOVY::resolve_userpath($USERNAME) . $wrapper;
		if (open WRAP, '>' . $filename) {
			print WRAP $BUFFER;
			close WRAP;
			chmod(0666,$filename);
			&GTOOLS::print_form('','wrapsuccess.shtml');
			exit;
		}
		$ERROR = 'Zoovy internal error, unable to open template file for writing, contact support@zoovy.com';
	}
	else {
		$ERROR = 'Upload had no contents!';
	}
}


if ($ACTION eq 'WRAPPER') {
	if (defined $ERROR && $ERROR) { $GTOOLS::TAG{'<!-- ERROR -->'} = $ERROR; }
	else { $GTOOLS::TAG{'<!-- ERROR -->'} = ''; }
	$template_file = 'wrapupload.shtml';
	push @BC,{ name=>'Wrapper' };
	}


if ($ACTION eq 'WELCOME') {
	$template_file = 'news.shtml';
	push @BC,{ name=>'News' };
	}

&GTOOLS::output(
   'title'=>'Setup : Site Integrator',
   'file'=>$template_file,
   'header'=>'1',
   'help'=>'',
   'tabs'=>[
		{ name=>'News', link=>'index.cgi?ACTION=WELCOME' },
		{ name=>'WebAPI', link=>'index.cgi?ACTION=WEBAPI' },
		{ name=>'Configuration', link=>'index.cgi?ACTION=CONFIG' }
      ],
   'bc'=>\@BC,
   );



