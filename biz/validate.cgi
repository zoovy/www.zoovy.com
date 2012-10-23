#!/usr/bin/perl

use lib "/httpd/modules";
use ZTOOLKIT::SECUREKEY;
use ZTOOLKIT;
use GTOOLS;
use ZOOVY;
use strict;

my ($USERNAME,$FLAGS,$MID,$LUSER) = ZOOVY::authenticate("/biz",2);
$GTOOLS::TAG{'<!-- MERCHANT -->'} = $USERNAME;
$GTOOLS::TAG{'<!-- USERNAME -->'} = $LUSER;

my $VERB = $ZOOVY::cgiv->{'VERB'};
$GTOOLS::TAG{'<!-- CODE -->'} = $ZOOVY::cgiv->{'KEY'};
$GTOOLS::TAG{'<!-- DATE -->'} = &ZTOOLKIT::pretty_date(time(),1);

if ($VERB eq 'VALIDATE') {
	my $KEY = $ZOOVY::cgiv->{'KEY'};
	my $out;

	$KEY = uc($KEY);
	my $ERROR = '';
	if (length($KEY)!=6) {
		$ERROR = "WARNING: KEY $KEY NOT AUTHENTIC - DOES NOT CONTAIN ENOUGH DIGITS.";
		}
	elsif (not defined $ZTOOLKIT::SECUREKEY::PARTNERS{substr($KEY,0,2)}) {
		$ERROR = "WARNING: KEY $KEY IS NOT AUTHENTIC - INCORRECT/INVALID PARTNER ID.";
		}
	else {
		## okay run a check against it.
		if (&ZTOOLKIT::SECUREKEY::gen_key($USERNAME,$KEY) eq $KEY) {
			$out .= "<br><font color='blue'>Verified Authentic Key!</font><br>";
			$out .= "Issued to: <b>".$ZTOOLKIT::SECUREKEY::PARTNERS{substr($KEY,0,2)}."</b><br>";
			$out .= "<br>The individual and the company they respresent is affiliated with Zoovy.";
			}
		else {
			$ERROR = "CRITICAL ERROR: KEY IS WELL FORMATTED, BUT WAS NOT ISSUED BY ZOOVY.";
			}
		}

	if ($ERROR ne '') {
		$out = qq~
		 <font color='red'>
			<b>THE KEY YOU PROVIDED IS INVALID.</b><br>
			$ERROR<br></b></font><br>
			The person or individual who provided it is *NOT* affiliated with Zoovy in any way.
			Please email legal\@zoovy.com and inform them of this immediately. 
			Do not give your username and password to anybody. 
			Do not allow untrusted vendors access to your store.
		</font>
		~;
		}

	$GTOOLS::TAG{'<!-- OUTPUT -->'} = $out;
	}


&GTOOLS::output(
	title=>'Vendor SecureKeys Validation',
	help=>'#50639',
	file=>'validate.shtml',
	header=>1,
	bc=>[ {name=>'Home' }, {name=>'Validate Security Code'} ],
	);
