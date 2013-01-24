#!/usr/bin/perl

use lib "/httpd/modules";
use ZSHIPRULES;

%cart = ();

# Cart format is: price,qty,weight,taxable,description
$cart{'asdf'} = '1.00,2,10,Y,test item #1';

&ZSHIPRULES::apply_discount_rules('nerdgear',\%cart);