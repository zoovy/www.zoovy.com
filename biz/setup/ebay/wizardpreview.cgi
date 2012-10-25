#!/usr/bin/perl

use lib "/httpd/modules";
require ZOOVY;
use Data::Dumper;
require PRODUCT;
use strict;
require ZTOOLKIT;
require EBAY2::PROFILE;
require TOXML::EDIT;
require SITE;

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_P&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $q = new CGI;

## DATA is key=value& and contains _SREF
my $DATA = $q->param('DATA');
if ($DATA ne '') {
	$ZOOVY::cgiv = &ZTOOLKIT::parseparams($DATA);
	}
else {
	&ZOOVY::init();
	}


# our $SREF = ($ZOOVY::cgiv->{'_SREF'})?&ZTOOLKIT::fast_deserialize($ZOOVY::cgiv->{'_SREF'}):{};
use Data::Dumper;
open F, ">/tmp/foo";
print F Dumper($ZOOVY::cgiv);
close F;

#our $SESSIONREF = ($ZOOVY::cgiv->{'_SREF'})?&ZTOOLKIT::parseparams($ZOOVY::cgiv->{'_SREF'},0):{};

#my %DATA = ();
my %SESSIONREF = ();
foreach my $var (keys %{$ZOOVY::cgiv}) {
	next if ($var eq '_SREF');
	next if ($var eq 'DATA');
	$SESSIONREF{$var} = $ZOOVY::cgiv->{$var};
	}



print STDERR Dumper($ZOOVY::cgiv);


my $SITE = undef;
if (defined $ZOOVY::cgiv->{'_SREF'}) {
	$SITE = SITE::sitedeserialize($USERNAME,$ZOOVY::cgiv->{'_SREF'});
	}
elsif ($ZOOVY::cgiv->{'PID'} ne '') {
	$SITE = SITE->new($USERNAME,'PRT'=>$PRT);
	$SITE->setSTID($ZOOVY::cgiv->{'PID'});
	}

# $USERNAME = $SESSIONREF->{'_USERNAME'};

my ($MARKET) = "ebay";
# my $OPTIONSTR = $SESSIONREF->{'_OPTIONSTR'};

my $PROFILE = $SITE->profile();
my ($P) = PRODUCT->new($SITE->username(),$SITE->pid(),'create'=>0);
if (not defined $P) {
	$P = PRODUCT->new($SITE->username(),$SITE->pid(),'tmp'=>1,'create'=>0);
	}
else {
	$PROFILE = $P->fetch('zoovy:profile'); 
	}


## 
my $epnsref = undef;
if ($PROFILE ne '') {
	$epnsref = EBAY2::PROFILE::fetch_without_prt($USERNAME,$PROFILE);
	foreach my $k (keys %SESSIONREF) {
		$epnsref->{$k} = $SESSIONREF{$k};
		}
	$SITE->layout( $epnsref->{'ebay:template'} );
	$SITE->{'%NSREF'} = $epnsref;
	}

#if ($ZOOVY::cgiv->{'_WIZARD'} ne '') { 
#	$htmlwiz = $ZOOVY::cgiv->{'_WIZARD'}; 
#	foreach my $k (keys %{$epnsref}) { 
#		next if (defined $$SESSIONREF{'DATA'}->{$k}); 
#		$$SESSIONREF{'DATA'}->{$k} = $epnsref->{$k};  
#		}
#	my $ref = $P->prodref(); # &ZOOVY::fetchproduct_as_hashref($USERNAME,$PRODUCT);
#	# foreach my $k (keys %{$ref}) { next if (defined $$SESSIONREF{'DATA'}->{$k}); $$SESSIONREF{'DATA'}->{$k} = $ref->{$k}; }
#	}

#$SITE::SREF = {};
#$SITE::SREF->{'%NSREF'} = $epnsref;

#print STDERR "HTMLWIZ: $htmlwiz\n";
#print STDERR Dumper($TOXML::EDIT::NSREF);

my $html = undef;
if (not defined $SITE->layout()) { 
	$html = "<pre>Sorry User[$USERNAME] but Profile[$PROFILE] does not seem to have an HTML Wizard mapped for Market[$MARKET]</pre>";
	}
else {
#	my ($thisPRT) = &ZOOVY::profile_to_prt($USERNAME,$PROFILE);
#	my ($SITE) = SITE->new($USERNAME,'NS'=>$PROFILE,'PRT'=>$thisPRT,'SKU'=>$PRODUCT,'%EBAYNSREF'=>$epnsref,'*P'=>$P);

	$SITE::CART2 = CART2->new_memory($SITE->username(),$SITE->prt());
	my ($toxml) = TOXML->new('WIZARD',$SITE->layout(),USERNAME=>$USERNAME);
	if (defined $toxml) {
		($html) = $toxml->render('*SITE'=>$SITE);
		}
	else {
		$html = "corrupt toxml\n";
		}
	}

my $PRODUCT = $SITE->pid();
print "Content-type: text/html\n\n";
print "<html>";
print qq~<!-- 
	USERNAME: $USERNAME
	PRODUCT: $PRODUCT
	PROFILE: $PROFILE
	MARKET: $MARKET
	-->~;
print "<body bgcolor='FFFFFF'>";
print "<center><table><tr><td>";

print $html;

print "</td></tr></table>";
print "</body>\n";

#print "<pre>".&ZOOVY::incode(Dumper($epnsref))."</pre>";
#print "<pre>".&ZOOVY::incode($html)."</pre>\n";
exit;
