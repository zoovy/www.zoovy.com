#!/usr/bin/perl

use lib "/httpd/modules";
use CGI;
use GTOOLS;
use DBINFO;
use ZUSER;

# this will fetch the username from the environment
($MERCHANT) = ZOOVY::authenticate("/biz");
$GTOOLS::TAG{"<!-- MERCHANT -->"} = $MERCHANT;


$q = new CGI;
print $q->header;

# this will fetch the remote username from the environment
#$REMOTE_USER = $ENV{"REMOTE_USER"};

my $ACTION = $q->param('ACTION');
my $template_file = "changepassword.shtml";

if ($ACTION eq 'SAVE_PASSWORD') {

	# gets the new password for the USER
	$NEWPASSWD = $q->param('NEWPASSWORD');
	$NEWPASSWD2 = $q->param('NEWPASSWORD1');
   #print "NEW1".$NEWPASSWD;
   #print "NEW2".$NEWPASSWD2;

	my ($MERCHANT,$PASSWORD,$ISPORTAL,$ISMERCHANT,$CREATED,$CACHED_FLAGS) = &ZUSER::fetch_user($MERCHANT);
  
	# checks to see if old password matches the one user typed
	# checks to make sure that both new passwords match each other

	if ($NEWPASSWD ne $NEWPASSWD2) {
		# if new passwords does not match display an error
		$GTOOLS::TAG{"<!-- ERRORMESS -->"} = "The new password does not match the other new one<br>";
		} 
	elsif (length($NEWPASSWD)<5) {
		$GTOOLS::TAG{"<!-- ERRORMESS -->"} = "The password you selected is too short. Must be 5 characters or longer.";
		}
	elsif ( (uc($NEWPASSWD) eq 'PASSWORD') || (uc($NEWPASSWD) eq 'TRIAL')) {
		$GTOOLS::TAG{"<!-- ERRORMESS -->"} = "The password you selected is insecure, please choose another.";
		}
	else {
		&ZUSER::update_user_passwd($MERCHANT,$NEWPASSWD);
		$template_file = 'changepassword-success.shtml';
		} # end if matched both new passowrd matche
	}   

&GT::print_form("Change Password",$template_file);
