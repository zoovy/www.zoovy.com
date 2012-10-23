#!/usr/bin/perl

use lib "/httpd/modules"; 
use CGI;
use GTOOLS;
use ZOOVY;
use ZWEBSITE;	
use ZTOOLKIT;
use DBINFO;
# use NAVCAT;
use strict;
# use AMAZON;
use SYNDICATION;

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_M&4');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }



my @BC = ();
push @BC, { name=>'Setup', link=>'http://www.zoovy.com/biz/setup', target=>'_top' };
push @BC, { name=>'Amazon ', link=>'/biz/setup/amazon', target=>'_top' };

my $template_file = 'index.shtml';
#if ($FLAGS !~ /,AMZ,/) {
#	$template_file = 'deny.shtml';
#	}

my $VERB = $ZOOVY::cgiv->{'VERB'};
my ($webdb) = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
my @MSGS = ();

if ($VERB eq 'SIGNUP') {
	my $signup = get_signup_url();
	$GTOOLS::TAG{'<!-- SIGNUP -->'} = $signup;	 

	$template_file = 'signup.shtml';
	push @BC, { 'name'=>'Sign Up' };
	}


if ($VERB eq 'SAVE') {
   $webdb->{'amz_merchantname'} = $ZOOVY::cgiv->{'amz_merchantname'};
	$webdb->{'amz_merchantname'} =~ s/[\s]+$//g;
	$webdb->{'amz_merchantname'} =~ s/^[\s]+//g;
   $webdb->{'amz_userid'} = $ZOOVY::cgiv->{'amz_userid'};
	$webdb->{'amz_userid'} =~ s/[\s]+$//g;
	$webdb->{'amz_userid'} =~ s/^[\s]+//g;
   $webdb->{'amz_password'} = $ZOOVY::cgiv->{'amz_password'};
	$webdb->{'amz_password'} =~ s/[\s]+$//g;
	$webdb->{'amz_password'} =~ s/^[\s]+//g;
   $webdb->{'amz_merchanttoken'} = $ZOOVY::cgiv->{'amz_merchanttoken'};
	$webdb->{'amz_merchanttoken'} =~ s/[\s]+$//g;
	$webdb->{'amz_merchanttoken'} =~ s/^[\s]+//g;
   $webdb->{'amz_merchantid'} = $ZOOVY::cgiv->{'amz_merchantid'};;
	$webdb->{'amz_merchantid'} =~ s/[^A-Z0-9]+//gs;
	$webdb->{'amz_merchantid'} =~ s/[\s]+$//g;
	$webdb->{'amz_merchantid'} =~ s/^[\s]+//g;

	$webdb->{'amz_accesskey'} = $ZOOVY::cgiv->{'amz_accesskey'};
	$webdb->{'amz_accesskey'} =~ s/[\s]+$//g;
	$webdb->{'amz_accesskey'} =~ s/^[\s]+//g;
	$webdb->{'amz_secretkey'} = $ZOOVY::cgiv->{'amz_secretkey'};
	$webdb->{'amz_secretkey'} =~ s/[\s]+$//g;
	$webdb->{'amz_secretkey'} =~ s/^[\s]+//g;

	my ($FEED_PERMS) = 0;
	if ($FLAGS =~ /,AMZ,/) {
		$FEED_PERMS += (defined $ZOOVY::cgiv->{'FEED_PERMS_1'})?1:0;		## products
		}
	$FEED_PERMS += 4;																	## orders, changed to always add 

	if (($FEED_PERMS & 1)==1) {
		my ($gref) = &ZWEBSITE::fetch_globalref($USERNAME);
		if ((not defined $gref->{'amz_prt'}) || ($gref->{'amz_prt'} != $PRT)) {
			push @MSGS, "SUCCESS|Updated send partition to $PRT";
			$LU->log("SETUP.AMAZON","Configured amazon to send products from prt# $PRT");
			$gref->{'amz_prt'} = $PRT;
			&ZWEBSITE::save_globalref($USERNAME,$gref);
			}
		}

	# AMAZON_FEEDS CAN BE REMOVED
	#chanded the code to use cluster specific amazon tables 2010-08-27
	my ($udbh) = &DBINFO::db_user_connect($USERNAME);
	&DBINFO::insert($udbh,'AMAZON_FEEDS',{
		USERNAME=>$USERNAME,PRT=>$PRT,MID=>$MID,FEED_PERMISSIONS=>$FEED_PERMS,UPDATED=>time(),IS_ERROR=>0,
		},key=>['MID','PRT']);
	&DBINFO::db_user_close();
	my ($so) = SYNDICATION->new($USERNAME,"#$PRT","AMZ");
	tie my %s, 'SYNDICATION', THIS=>$so;
	$s{'.feedpermissions'} = $FEED_PERMS;
	$s{'.fbapermissions'} = (defined $ZOOVY::cgiv->{'FBA_PERMS'})?1:0;
	$s{'ERRCOUNT'} = 0;
	$s{'IS_ACTIVE'} = 1;
	$so->save();

	push @MSGS, "SUCCESS|Updated settings";
	$LU->log("SETUP.AMAZON","Tokens updated","SAVE");
	&ZWEBSITE::save_website_dbref($USERNAME,$webdb,$PRT);
	$VERB = '';
	}

## removed ability for merchants to reset their own feeds without using the powertool (if they have enough knowledge
## to use the powertool then it is likely they are doing this for the right reason. no matter how many times some merchnats
## are told, they continue to click this button every time they update a product. this button also causes every product 
## that has ever been sent to amazon to be updated, including ones that have no been removed. at 2010-11-15
#if ($VERB eq 'RESET') {
#	# AMAZON_FEEDS CAN BE REMOVED
#	#chanded the code to use cluster specific amazon tables at 2010-08-27
#	my ($udbh) = &DBINFO::db_user_connect($USERNAME);
#	my $pstmt = "update AMAZON_FEEDS set UPDATED=0 where MID=$MID /* $USERNAME */ and PRT=$PRT";
#	$udbh->do($pstmt);
#	&DBINFO::db_user_close();
#
#	my ($so) = SYNDICATION->new($USERNAME,"#$PRT","AMZ");
#	tie my %s, 'SYNDICATION', THIS=>$so;
#	$s{'PRODUCTS_GMT'} = 0;
#	$s{'IS_ACTIVE'} = 1;
#	$so->save();
#
#	require PRODUCT::BATCH;
#	&PRODUCT::BATCH::updatetss($USERNAME);
#
#	$LU->log("SETUP.AMAZON.RESETFEED","Reset all Product Timestamps from Amazon Configuration");
#
#	$VERB = '';
#	}


if ($VERB eq '') {
	# my ($userref) = &AMAZON::fetch_merchant($USERNAME,$PRT);

	$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;
	$GTOOLS::TAG{'<!-- PRT -->'} = $PRT;
	$GTOOLS::TAG{'<!-- MWSTOKEN_STATUS -->'} = '<font color="red">Not Set</font>';
	if ($webdb->{'amz_token'} ne '') {
		$GTOOLS::TAG{'<!-- MWSTOKEN_STATUS -->'} = "Token: $webdb->{'amz_token'}";
		}

	$GTOOLS::TAG{'<!-- AMZ_MERCHANTNAME -->'} = &ZOOVY::incode($webdb->{'amz_merchantname'});
	$GTOOLS::TAG{'<!-- AMZ_USERID -->'} = &ZOOVY::incode($webdb->{'amz_userid'});
	$GTOOLS::TAG{'<!-- AMZ_PASSWORD -->'} = &ZOOVY::incode($webdb->{'amz_password'});
	$GTOOLS::TAG{'<!-- AMZ_MERCHANTTOKEN -->'} = &ZOOVY::incode($webdb->{'amz_merchanttoken'});
	$GTOOLS::TAG{'<!-- AMZ_MERCHANTID -->'} = &ZOOVY::incode($webdb->{'amz_merchantid'});
	$GTOOLS::TAG{'<!-- AMZ_ACCESSKEY -->'} = &ZOOVY::incode($webdb->{'amz_accesskey'});
	$GTOOLS::TAG{'<!-- AMZ_SECRETKEY -->'} = &ZOOVY::incode($webdb->{'amz_secretkey'});
	my ($so) = SYNDICATION->new($USERNAME,"#$PRT","AMZ");
	my $feedpermissions = $so->get('.feedpermissions');
	$GTOOLS::TAG{'<!-- FEED_PERMS_1 -->'} = ($feedpermissions&1)?'checked':'';
	## FBA Settings, added 2011-06-10 - patti
	## - check if merchant wants us to import FBA Order and Tracking
	##	- Tracking includes orders that originate from Amazon 
	##		and those that are manually put into FBA via the merchant (ie manual FWS)
	my $fbapermissions = $so->get('.fbapermissions');
	$GTOOLS::TAG{'<!-- FBA_PERMS -->'} = ($fbapermissions&1)?'checked':'';
	
	## check to make sure they only have one profile enabled for syndication!
	my ($udbh) = &DBINFO::db_user_connect($USERNAME);
	my $pstmt = "select PROFILE from SYNDICATION where MID=$MID /* $USERNAME */ and DSTCODE='AMZ'";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	my @ACTIVE = ();
	while ( my ($profile) = $sth->fetchrow() ) { 
		my ($so) = SYNDICATION->new($USERNAME,$profile,"AMZ");
		if ( ($so->get('.feedpermissions')&1)>0) {
			push @ACTIVE, $profile; 
			}
		}
	$sth->finish();
	&DBINFO::db_user_close();
	if (scalar(@ACTIVE)>1) {
		push @MSGS, "WARN|You must only have one partition setup to transmit products/inventory currently partitions: ".join(',',@ACTIVE)." have products configured to syndicate.";
		}
	if ($FLAGS !~ /,AMZ,/) {
		push @MSGS, "WARN|You will not be able to send products (only receive orders) without the Amazon bundle.";
		}

	}


&GTOOLS::output(bc=>\@BC,msgs=>\@MSGS,file=>$template_file,header=>1);


sub get_signup_url {
	require Digest;

	my $associates_store_Id = "zoovy2-20";
	my $shared_secret_key = "a29d04860c0a51c6f0bbb9c92f84358b";
	my $promotion_code = "1mosfree";
	## add 7hrs for UTC
	my $time = time()+(7*60*60);
	## expire url in 10 days
	my $expires = $time + (10*86400);
	
	my $url = "http://sellercentral.amazon.com/gp/seller/channel-partner/";
	my $message  = "associatesStoreID=".$associates_store_Id.
						"&uniqueToken=".$MID.
						"&trackingTag=main".
						"&promotionCode=".$promotion_code.
						"&timeGenerated=".$time.
						"&timeExpires=".$expires;

	my $hmac = Digest->HMAC_MD5(pack('H*',$shared_secret_key));
	$hmac->add($message);
	my $hash = $hmac->hexdigest();
	
	my $signup = $url."?".$message."&signedHash=".$hash;

	return($signup);
	}
