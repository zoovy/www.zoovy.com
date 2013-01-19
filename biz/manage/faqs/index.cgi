#!/usr/bin/perl

use strict;
use Data::Dumper;
use lib "/httpd/modules";
use ZOOVY;
use SITE::FAQS;
use GTOOLS;


# my ($USERNAME,$FLAGS,$MID,$LUSER) = &ZOOVY::authenticate("/biz/utilities",2,'_S&2');
require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $VERB = $ZOOVY::cgiv->{'VERB'};
my $template_file = 'index.shtml';


# print STDERR "FLAGS: $FLAGS\n";

if ($FLAGS !~ /,CRM,/) {
	print "Location: /biz/configurator?VERB=VIEW&BUNDLE=CRM\n\n";
	exit;
	}

my ($faqs) = SITE::FAQS->new($USERNAME,$PRT);

if ($VERB eq 'ADDTOPIC') {
	$faqs->add_topic($ZOOVY::cgiv->{'topic'},10);
	$VERB = '';
	}


if (($VERB eq 'ADDQANDA') || ($VERB eq 'SAVEQANDA')) {
	my $FAQID = 0;
	if ($VERB eq 'SAVEQANDA') { $FAQID = int($ZOOVY::cgiv->{'FAQID'}); }
	$faqs->add_faq($FAQID,$ZOOVY::cgiv->{'topicid'},$ZOOVY::cgiv->{'question'},$ZOOVY::cgiv->{'answer'},$ZOOVY::cgiv->{'keywords'},$ZOOVY::cgiv->{'priority'});
	$VERB = '';
	}

if ($VERB eq 'NUKEQANDA') {
	$faqs->remove_faq($ZOOVY::cgiv->{'DATA'});
	$VERB = ''; 
	}

if ($VERB eq 'SAVETOPIC') {
	$faqs->add_topic($ZOOVY::cgiv->{'topic'},int($ZOOVY::cgiv->{'priority'}),ID=>int($ZOOVY::cgiv->{'TOPICID'}) );
	$VERB = '';
	}

if ($VERB eq 'NUKETOPIC') {
	$faqs->remove_topic($ZOOVY::cgiv->{'DATA'});
	$VERB = '';
	}

if ($VERB eq 'EDITQANDA') {
	$template_file = 'editqanda.shtml';
	$GTOOLS::TAG{'<!-- FAQID -->'} = int($ZOOVY::cgiv->{'DATA'});
	my ($x) = $faqs->get_faq(int($ZOOVY::cgiv->{'DATA'}));
	foreach my $k ('PRIORITY','QUESTION','KEYWORDS','ANSWER') {
		$GTOOLS::TAG{"<!-- $k -->"} = &ZOOVY::incode($x->{$k});
		}

	my $results = $faqs->list_topics();
	my $c = '';
	foreach my $topic (@{$results}) {
		my $selected = ($x->{'TOPIC'} == $topic->{'ID'})?'selected':'';
		$c .= "<option $selected value=\"$topic->{'ID'}\">$topic->{'TITLE'}</option>";
		}
	$GTOOLS::TAG{'<!-- TOPICS -->'} = $c;
	# $GTOOLS::TAG{'<!-- DEBUG -->'} = Dumper($x);
	}

if ($VERB eq 'EDITTOPIC') {
	$template_file = 'edittopic.shtml';
	$GTOOLS::TAG{'<!-- TOPICID -->'} = $ZOOVY::cgiv->{'DATA'};
	my $r = $faqs->get_topic($ZOOVY::cgiv->{'DATA'});
	$GTOOLS::TAG{'<!-- TOPIC -->'} = $r->{'TITLE'};
	$GTOOLS::TAG{'<!-- PRIORITY -->'} = $r->{'PRIORITY'};
	}

my $results = undef;
if ($VERB eq '') {
	$results = $faqs->list_topics();
	}

if (defined $results) {
	my $c = '';
	foreach my $topic (@{$results}) {
		$c .= "<option value=\"$topic->{'ID'}\">$topic->{'TITLE'}</option>";
		}
	$GTOOLS::TAG{'<!-- TOPICS -->'} = $c;

	$c = '';
	foreach my $topic (@{$results}) {
		$c .= qq~
		<tr>
			<td class=\"zoovysub1header\">
			<input type="button" class="button" onClick="
				jQuery('#VERB').attr('value','NUKETOPIC');
				jQuery('#DATA').attr('value','$topic->{'ID'}');
				jQuery('#utilityFaqFrm').submit();
				" value=" DEL ">
			<input type="button" class="button" onClick="
				jQuery('#VERB').attr('value','EDITTOPIC');
				jQuery('#DATA').attr('value','$topic->{'ID'}');
				jQuery('#utilityFaqFrm').submit();
				" value=" EDIT ">
			[$topic->{'ID'}] $topic->{'TITLE'}
			
			</td>	
			<td class=\"zoovysub1header\" width=10% align="right">
			<span style="text-align: right;" class="hint">Priority: $topic->{'PRIORITY'}</span>
			</td>
		</tr>~;

		my ($x) = $faqs->list_faqs($topic->{'ID'});

		my $i = 0;
		foreach my $faq (@{$x}) {
			my $class = "r".(++$i%2);
			$c .= qq~
				<tr>
					<td colspan=2 class="$class">
					<input type="button" class="button" onClick="
						jQuery('#VERB').attr('value','NUKEQANDA');
						jQuery('#DATA').attr('value','$faq->{'ID'}');
						jQuery('#utilityFaqFrm').submit();
						" value=" DEL ">
					<input type="button" class="button" onClick="
						jQuery('#VERB').attr('value','EDITQANDA');
						jQuery('#DATA').attr('value','$faq->{'ID'}');
						jQuery('#utilityFaqFrm').submit();
						" value=" EDIT "> 
					Q: $faq->{'QUESTION'}<br>
					A: $faq->{'ANSWER'}<br>
					KEYS: $faq->{'KEYWORDS'}<br>
					<div class="hint">Priority: $faq->{'PRIORITY'}</div>
					</td>	
				</tr>
				~;
			}
		# $c .= "<tr><td>--</td></tr>";
		}
	$GTOOLS::TAG{'<!-- OUTPUT -->'} = $c;
	}

&GTOOLS::output('*LU'=>$LU,
	file=>$template_file,
	help=>"#50728",
	header=>1);