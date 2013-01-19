#!/usr/bin/perl

use lib "/httpd/modules";
use DOBA;
use Data::Dumper;
use CUSTOMER;

my $dobauser = 'richard@zoovy.com';

 my ($C) = CUSTOMER->new('doba',EMAIL=>'admin@hurrywebhosting.zoovy.com',INIT=>0xFF);
# $C->set_attrib('META.foo','asdf');
# $C->save();
#$USERNAME = 'hurrywebhosting';
#      my ($c) = CUSTOMER->new('doba',EMAIL=>'admin@'.$USERNAME.'.zoovy.com',INIT=>0xFF);
#      $c->set_attrib('META.dobauserid',$userid);
#      $c->set_attrib('META.dobacookie',$cookie);
#      $c->set_attrib('META.dobatoken',$token);
#      $c->save();

print Dumper($C);
exit;


if (1) {
	($rref) = DOBA::doRequest('order.drop_user_link',{ username=>$dobauser, user_id=>103608 });
	($rref) = DOBA::doRequest('order.request_user_link',{ username=>$dobauser });
	}



print Dumper($rref);
