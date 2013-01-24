#!/usr/bin/perl


my ($USERNAME) = "brian";

use lib '/httpd/modules';
use TICKET;

   require Net::POP3;
   require FUSEMAIL;

   ## GO GO GADGET IMAP
 #   my ($pop) = Net::POP3->new("pop.fusemail.net", Timeout => 15);

   my $username = "admin\@$USERNAME.zoovy.com";
   my ($password) = &FUSEMAIL::getpassword($username);

	print "PASS: $password\n";

   if ($pop->login($username, $password) > 0) {
      my $msgnums = $pop->list; # hashref of msgnum => size
      foreach my $msgnum (keys %$msgnums) {
         my $msg = $pop->get($msgnum);
         print @$msg;
         # $pop->delete($msgnum);
         }
      }
   $pop->quit;

   ## STOP GADGET IMAP STOP!
