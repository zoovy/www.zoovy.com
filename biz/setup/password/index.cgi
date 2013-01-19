#!/usr/bin/perl

use strict;
use lib "/httpd/modules";
use CGI;
require GTOOLS;
require DBINFO;
require LUSER;

# this will fetch the username from the environment

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_ADMIN');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSER,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $ACTION = $ZOOVY::cgiv->{'ACTION'};

# set the username
$GTOOLS::TAG{"<!-- USERNAME -->"} = $USERNAME;
$GTOOLS::TAG{'<!-- LUSER -->'} = ($LUSER ne '')?'*'.$LUSER:'';

# loads the template 
my $template_file = "index.shtml";

if ($ACTION eq 'SAVE_PASSWORD') {
	# gets the username 
	my $OLDPASSWD = $ZOOVY::cgiv->{'OLDPASSWORD'};
	my $LOGIN = $USERNAME . (($LUSER eq '')?'':'*'.$LUSER);

	# gets the new password for the USER
	my $NEWPASSWD = $ZOOVY::cgiv->{'NEWPASSWORD'};
	my $NEWPASSWD2 = $ZOOVY::cgiv->{'NEWPASSWORD1'};

	my ($LU) = LUSER->new($USERNAME,$LUSER);
	my $ERROR = undef;
	if (not $LU->passmatches($OLDPASSWD)) {
		#if there is any error displayed the error message
		$ERROR = "Old password does not match the one in our database.<br>";
		} 
	elsif (my $REASON = &ZTOOLKIT::is_bad_password($NEWPASSWD)) {
		$ERROR = "Please choose another password: $REASON"; 
		}
	elsif ($NEWPASSWD ne $NEWPASSWD2) {
		# checks to make sure that both new passwords match each other
		# if new passwords does not match display an error
		$ERROR = "The new password does not match the other new one<br>";
		} 
	else {
		# if it has passed both possible errors update their password
		$LU->set_password($NEWPASSWD);
		# load success page saying that password has been sucessful updated.
		} 
	
	if (defined $ERROR) {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<div class='error'>$ERROR</div>";
		}
	else {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<div class='success'>Successfull changed password</div>";
		}

	$LU = undef;
	}   

  


&GTOOLS::output('*LU'=>$LU,
   'title'=>'Setup : Change Password',
   'file'=>$template_file,
   'header'=>'1',
   'help'=>'#50677',
   'tabs'=>[
      ],
   'bc'=>[
      { name=>'Setup',link=>'http://www.zoovy.com/biz/setup','target'=>'_top', },
      { name=>'Change Password',link=>'http://www.zoovy.com/biz/setup/password','target'=>'_top', },
      ],
   );

