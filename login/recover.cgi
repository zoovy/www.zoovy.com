#!/usr/bin/perl

use lib "/httpd/modules";
use DBINFO;
use GT;
use CGI;
use ZMAIL;
use ZTOOLKIT;

$q = new CGI;

$lookfor = $q->param('lookfor');

if ($lookfor eq '') { $GT::TAG{'<!-- MESSAGE -->'} = 'no username or email received.'; }

my $dbh = DBI->connect($DBINFO::MYSQL_DSN,$DBINFO::MYSQL_USER,$DBINFO::MYSQL_PASS); 

my $qt_lookfor = $dbh->quote($lookfor);
$pstmt = "select PASSWORD,USERNAME,EMAIL from ZUSERS where USERNAME=$qt_lookfor or EMAIL=$qt_lookfor";

$sth = $dbh->prepare($pstmt);
$rv = $sth->execute();

if ($rv)
{
	while ( ($pass,$username,$email) = $sth->fetchrow() )
	{
		if (&ZTOOLKIT::validate_email_strict($email))
		{
			## This used to have &ZMAIL::sendmail referenced in it but it was looking up user 'zoovy'
			## which didn't exist, so it was failing (it used to work before the merchant.bin change apparently
			## It was easier to just do the same thing here than to try to make ZMAIL handle not having
			## a merchant.  -AK 11/10/2003
			if (open MH, '|/usr/sbin/sendmail -t')
			{
				$GT::TAG{'<!-- MESSAGE -->'} = "Password was mailed to $email";
				print MH "From: support\@zoovy.com\n";
				print MH "To: $email\n";
				print MH "Bcc: logger\@support.zoovy.com\n";
				print MH "Reply-To: support\@zoovy.com\n";
				print MH "Subject: Password Recovery\n";
				print MH "\n";
				print MH "Hi, you or somebody who thinks they're you requested your password for $username.zoovy.com\n";
				print MH "Don't worry, this is the only copy of the password we sent out and you've got it.\n";
				print MH "\n";
				print MH "\n";
				print MH "Your login information is:\n";
				print MH "Username: $username\n";
				print MH "Password: $pass\n";
				print MH "\n";
				print MH "Helpful Hints:\n";
				print MH "\n";
				print MH " * Passwords are case sensitive - which means that you must type the password in either upper\n";
				print MH "     or lower case as shown above.\n";
				print MH " * You must have cookies enabled to login, you can test your cookies by simply trying to add a\n";
				print MH "     product to the shopping cart in any Zoovy store http://shops.zoovy.com - if you receive a\n";
				print MH "     cookie error, then the store will also include instructions to fix the cookie error.\n";
				print MH " * Avoid simple mistakes, for example people often confuse \"trial\" and \"trail\" it helps to\n";
				print MH "     try typing one letter at a time if you think this may be the problem.\n";
				print MH "\n";
				print MH "\n";
				print MH "If you have any questions please contact your support provider.\n";
				close MH;
			}
			else
			{
				$GT::TAG{'<!-- MESSAGE -->'} = "Unable to connect to mail server to send password, please contact Zoovy support support\@zoovy.com";
			}
		}
		else
		{
			$GT::TAG{'<!-- MESSAGE -->'} = "Unable to send password to invalid email address $email, please contact Zoovy support support\@zoovy.com";
		}
	}
}
else
{
	$GT::TAG{"<!-- MESSAGE -->"} = 'Could not find user / email $lookfor.'; 
}

$dbh->disconnect();


&GT::print_form('','thankyou.shtml',1);
