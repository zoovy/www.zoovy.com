#!/usr/bin/perl

use lib "/httpd/modules";
use ZWEBSITE;

$USERNAME = 'secondact';

##
## type: 
##		cbr - checkbox required
##	id:
##		unique 12 character id (chkfield_tos)
##	trigger:
##		a trigger rule (??!?!?) .. something we can match against (does the cart match!?!)
##	values:
##		a list of key value separated pairs. e.g. &= ..
##		fixed for cbr, cbo types
## 
#
&ZWEBSITE::checkfield_add($USERNAME,0,{
	'type'=>'cbr',
	'id'=>'chkfield_tos',
	'trigger'=>'*',
	});

