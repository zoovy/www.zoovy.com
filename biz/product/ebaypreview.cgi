#!/usr/bin/perl

use strict;

use lib "/httpd/modules";
use CGI;
require ZOOVY;
use Data::Dumper;
use strict;
require ZTOOLKIT;
require TOXML::EDIT;


my $q = new CGI;

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_P&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my ($PID) = $q->param('PID');

## DATA is key=value& and contains _SREF
#my $DATA = $q->param('DATA');
#if ($DATA ne '') {
#	$ZOOVY::cgiv = &ZTOOLKIT::parseparams($DATA);
#	}
#else {
#	&ZOOVY::init();
#	}
#$FLOW::PRODREF = undef;		# initialize this for FLOW::smart_load

## should fix preview issue for komal
my ($P) = undef; 
if ($PID ne '') {
	$P = PRODUCT->new($USERNAME,$PID);
	}
if (not defined $P) {
	$P = PRODUCT->new($USERNAME,'','tmp'=>1);
	}


# our $SREF = ($ZOOVY::cgiv->{'_SREF'})?&ZTOOLKIT::fast_deserialize($ZOOVY::cgiv->{'_SREF'}):{};
#use Data::Dumper;
#open F, ">/tmp/foo";
#print F Dumper($ZOOVY::cgiv);
#close F;

#our $SREF = ($ZOOVY::cgiv->{'_SREF'})?&ZTOOLKIT::parseparams($ZOOVY::cgiv->{'_SREF'},0):{};
#foreach my $var (keys %{$ZOOVY::cgiv}) {
#	next if ($var eq '_SREF');
#	next if ($var eq 'DATA');
#	$SREF->{$var} = $ZOOVY::cgiv->{$var};
#	}

#my $USERNAME = $SREF->{'_USERNAME'};
#my $PRODUCT = $SREF->{'_PRODUCT'};
#my ($MARKET) = split(/\./,$SREF->{'_DOCID'},2);
#my $OPTIONSTR = $SREF->{'_OPTIONSTR'};

require EBAY2::PROFILE;

my $PROFILE = $P->fetch('zoovy:profile');
# my $nsref = &EBAY2::PROFILE::fetch($USERNAME,$PRT,$CODE);;
# &ZOOVY::fetchmerchantns_ref($USERNAME,$PRT,$CODE);
my $ebref = EBAY2::PROFILE::fetch($USERNAME,$PRT,$PROFILE);
my $htmlwiz = $ebref->{'ebay:template'};

#my $SREF = {};
#foreach my $k (keys %{$ebref}) { $SREF->{$k} = $ebref->{$k}; }
#foreach my $k (keys %{$P->prodref()}) { $SREF->{$k} = $P->fetch($k); }
#$SREF->{'_USERNAME'} = $USERNAME;
#$SREF->{'_PRODUCT'} = $PID;
#if ($SREF->{'_PRODUCT'} eq '') {
#	## the we're preview a blank product, so this must be profile edit mode.
#	$FLOW::NSREF = $SREF;
#	}

# print "Content-type: text/plain\n\n"; print Dumper($SREF); exit;

#print STDERR "HTMLWIZ: $htmlwiz\n";
#print STDERR Dumper($TOXML::EDIT::NSREF);


my $html = undef;
if (not defined $htmlwiz) { 
	$html = "<pre>Sorry User[$USERNAME] but Profile[$PROFILE] does not seem to have an HTML Wizard mapped</pre>";
	}
elsif (not defined $P) {
	$html = "<pre>Could not load product $PID</pre>";
	}
#elsif (1) {
#	$html = "<pre>".Dumper($SREF)."</pre>";
#	}
else {
	my ($toxml) = TOXML->new('WIZARD',$htmlwiz,USERNAME=>$USERNAME);
	if (defined $toxml) {
		($html) = $toxml->render(USERNAME=>$USERNAME, SKU=>$PID, PROFILE=>$PROFILE, '*P'=>$P, '%NSREF'=>$ebref);
		}
	}


print "Content-type: text/html\n\n";
print "<html>";
print qq~<!-- 
	USERNAME: $ZOOVY::USERNAME
	PRODUCT: $PID
	PROFILE: $PROFILE
	WIZAZRD: $htmlwiz
	-->~;
print "<body bgcolor='FFFFFF'>";
print "<center><table><tr><td>";

print $html;

print "</td></tr></table>";
print "</body>\n";

exit;
