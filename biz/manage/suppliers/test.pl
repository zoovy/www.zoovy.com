#!/usr/bin/perl

use lib '/httpd/modules';
use SUPPLIER::SUBSCRIPTION;


# http://www.zoovy.com/biz/utilities/suppliers/index.cgi?ACTION=SUBSCRIBE&MID=16804&INDEX=&LOAD=
my ($products) = &SUPPLIER::SUBSCRIPTION::load('http://static.zoovy.com/merchant/ZSMC/testlist1.xml','JEDI?SRCMID%3D16804%26SRCUSER%3DZSMC');




