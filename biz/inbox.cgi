#!/usr/bin/perl

use lib "/httpd/modules";
use ZOOVY;
use DBINFO;
use LUSER;
use PLUGIN::FUSEMAIL;
use GTOOLS;

my ($LU) = LUSER->authenticate();
if (not defined $LU) { warn "Auth"; exit; }

#use Data::Dumper;
#print STDERR Dumper($LU);

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { warn "No auth"; exit; }

my $template_file = '';
my $email = $LU->email();
my $url = '';

# use Data::Dumper;
# print STDERR Dumper($LU);
my $q = new CGI;
my $secure = $q->param('secure');
if (not defined $secure) { $secure = 1; }

if ($LU->{'HAS_EMAIL'} ne 'Y') {

	if ($LU->is_admin()) {
		$GTOOLS::TAG{'<!-- ERROR -->'} = qq~
This account does not have a ZoovyMail (provide by fusemail) inbox associated with it.<br>
<br>
<a href="/biz/configurator/index.cgi?VERB=ADD&BUNDLE=ZM">[ENABLE ZOOVYMAIL]</a><br>
<br>
~;
		}
	else {
		## user doesn't have an integrated mailbox
		$GTOOLS::TAG{'<!-- ERROR -->'} = qq~
This Zoovy User does not have a ZoovyMail (provided by fusemail) inbox associated with it. 
Please have your administrator enable this functionality for your account.<br>
<i>HINT: You may login as the administrative user and click the inbox to enable this.</i>
	~;
		}
	$template_file = 'inbox-sorry.shtml';
	}
elsif (($secure) && ($ENV{'HTTP_USER_AGENT'} =~ /MSIE 7\.0/)) {
	$template_file = 'inbox-sorry.shtml';
	$GTOOLS::TAG{'<!-- ERROR -->'} = qq~
Sorry, but your IE7 browser does not support the GoDaddy SSL certificate which our mail provider "Fusemail"
uses to secures their authentication site webmail.fusemail.com. Please install IE 8 to correct this issue or 
use an alternative browser such as firefox.<br>
<br>
<a href="?secure=0">I don't care, and am willing to assume the risks, please log me in insecurely.</a><br>
<br>
<div class="hint">REMINDER: Logging in insecurely violates PCI/DSS requirements. 
You are solely responsible for any security breach which results as a violation of this. 
Insecure access is logged. 
</div>
<i>User Agent: $ENV{'HTTP_USER_AGENT'}</i><br>
~;
	}
else {

	($url) = &PLUGIN::FUSEMAIL::loginurl($email,$q->param('insecure')?0:1);

	if ($url eq '') {
		$template_file = 'inbox-sorry.shtml';
		$GTOOLS::TAG{'<!-- ERROR -->'} = qq~
Sorry but we could not generate an auto-login url for your linked fusemail account ($email). 
If this problem persists please notify technical support.
~;
		}
	
	}


if ($template_file ne '') {
	&GTOOLS::output(file=>$template_file,header=>1);
	}
else {
	print "Location: $url\n\n";
	$LU->log('PLUGIN::FUSEMAIL',"Auto-login secure:$secure");
	}

# https://webmail.fusemail.com/sq/src/webmail.php?user=brian@zoovy.com&password=labslave&logoutURL=http://www.mailanyone.net/index.html&failURL=http://www.mailanyone.net/index.html&DoLogin=Y&SSL=checked
