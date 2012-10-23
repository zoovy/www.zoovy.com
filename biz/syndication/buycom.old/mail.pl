#!/usr/bin/perl

use lib "/httpd/modules";
use MIME::Entity;

           ### Create an entity:
           my $top = MIME::Entity->build(From    => 'brian@zoovy.com',
                                      To      => 'brian@zoovy.com',
                                      Subject => "CSV File",
                                      Data    => \@my_message);

           ### Attach stuff to it:
           $top->attach(Path     => '/tmp/877myjuicer.xls',
                        Type     => "application/ms-excel",
                        Encoding => "base64");

           ### Output it:

open MH, "|/usr/sbin/sendmail -t ";
$top->print(\*MH);
close MH;
