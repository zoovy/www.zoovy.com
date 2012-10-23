#!/usr/bin/perl

use strict;
use lib "/httpd/modules";
use GTOOLS;
use ZOOVY;
use PRODUCT::REVIEWS;

my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = &ZOOVY::authenticate("/biz/utilities",2,'_S&2');
my $VERB = $ZOOVY::cgiv->{'VERB'};
my $RID = int($ZOOVY::cgiv->{'RID'});
my @TABS = ();

if ($FLAGS !~ /,CRM,/) {
	print "Location: /biz/configurator?VERB=VIEW&BUNDLE=CRM\n\n";
	exit;
	}

my $template_file = 'index.shtml';

if ($VERB eq 'APPROVE') {
	&PRODUCT::REVIEWS::update_review($USERNAME,$RID,APPROVED_GMT=>time());	
	$VERB = '';
	}

if ($VERB eq 'DELETE') {
	&PRODUCT::REVIEWS::update_review($USERNAME,$RID,_NUKE_=>1);	
	$VERB = '';
	}


if ($VERB eq 'EDITSAVE') {
	my ($ref) = @{&PRODUCT::REVIEWS::fetch_product_reviews($USERNAME,'',$RID)};
	delete $ref->{'MID'};
	delete $ref->{'ID'};
	my %options = ();
	foreach my $f ('CUSTOMER_NAME','LOCATION','RATING','SUBJECT','MESSAGE','BLOG_URL') {
		$options{$f} = $ZOOVY::cgiv->{$f};
		}

	&PRODUCT::REVIEWS::update_review($USERNAME,$RID,%options);	
	
	$VERB = '';
	}

if ($VERB eq 'EDIT') {
	my ($ref) = @{&PRODUCT::REVIEWS::fetch_product_reviews($USERNAME,'',$RID)};
	$GTOOLS::TAG{'<!-- RID -->'} = $RID;
	foreach my $f (keys %{$ref}) {
		$GTOOLS::TAG{"<!-- $f -->"} = &ZOOVY::incode($ref->{$f});
		}
	foreach my $i (1..10) {
		$GTOOLS::TAG{'<!-- RATING_OPTIONS -->'} .= "<option ".(($ref->{'RATING'}==$i)?'selected':'')." value=\"$i\">$i</option>";
		}

	$template_file = 'edit.shtml';
	}


push @TABS, { link=>"index.cgi?VIEW=", name=>" Recent ",selected=>(($ZOOVY::cgiv->{'VIEW'} eq '')?1:0), };
push @TABS, { link=>"index.cgi?VIEW=UNAPPROVED", name=>" UnApproved ",selected=>(($ZOOVY::cgiv->{'VIEW'} eq 'UNAPPROVED')?1:0), };

if ($VERB eq '') {
	$GTOOLS::TAG{'<!-- VIEW -->'} = $ZOOVY::cgiv->{'VIEW'};
	
	my ($result) = undef;
	if ($ZOOVY::cgiv->{'VIEW'} eq '') {
		$result = &PRODUCT::REVIEWS::fetch_product_reviews($USERNAME,undef,undef);
		}
	elsif ($ZOOVY::cgiv->{'VIEW'} eq 'UNAPPROVED') {
		$result = &PRODUCT::REVIEWS::fetch_product_reviews($USERNAME,undef,-1);
		}

	if ((not defined $result) || (scalar(@{$result})==0)) {
		$GTOOLS::TAG{'<!-- REVIEWS -->'} = "<tr><td>You don't have any reviews yet.</td></tr>";
		}
	else {
		use Data::Dumper;
		my $c = '';
		my $i = 0;
		foreach my $review (@{$result}) {
		my $class = 'r'.(++$i%2);

			foreach my $f (keys %{$review}) {
				## takes care of bad characters. // x-site scripting
				$review->{$f} = &ZOOVY::incode($review->{$f});
				}

		$c .= qq~
<tr>
	<td valign='top' rowspan="2" class="$class">
		<input style="width: 55px;" onClick="
			window.document.thisFrm.VERB.value='EDIT';
			window.document.thisFrm.RID.value='$review->{'ID'}'; 
			window.document.thisFrm.submit();" class="button" type="button" value="Edit" class="Edit"><br>
			~.
	(($review->{'APPROVED_GMT'}==0)?qq~<input style="width: 55px;"  onClick="
         window.document.thisFrm.VERB.value='APPROVE';
         window.document.thisFrm.RID.value='$review->{'ID'}';
         window.document.thisFrm.submit();" class="button" type="button" value="Approve" class="Approve"><br>~:'').
	qq~
		<input style="width: 55px;"  onClick="
         window.document.thisFrm.VERB.value='DELETE';
         window.document.thisFrm.RID.value='$review->{'ID'}';
         window.document.thisFrm.submit();" class="button" type="button" value="Delete" class="Delete"><br>
	</td>
	<td nowrap class="$class">Product: $review->{'PID'}</td>
	<td nowrap class="$class">Rating: $review->{'RATING'} of 10</td>
	<td nowrap class="$class">$review->{'CUSTOMER_NAME'} | $review->{'LOCATION'}</td>
</tr>
<tr>
	<td class="$class" colspan="3">
	<b>$review->{'SUBJECT'}</b><br>
	$review->{'MESSAGE'}<br>
	$review->{'BLOG_URL'}
	</td>
</tr>
~;
#		$c .= '<tr><td>'.Dumper($review).'</td></tr>';
			}
		$GTOOLS::TAG{'<!-- REVIEWS -->'} = $c;
		}

	
	}




&GTOOLS::output( 
		file=>$template_file, 
		tabs=>\@TABS, 
		header=>1, 
		help=>"#50741",
		bc=>[ { name=>"Utilities", link=>"/biz/manage" }, { name=>"Review Manager" }] );
