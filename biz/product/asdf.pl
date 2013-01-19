#!/usr/bin/perl

use Data::Dumper;

$X = {
          'zoovy:profile' => 'DEFAULT',
          'zoovy:base_cost' => '',
          'zoovy:taxable' => 'Y',
          'zoovy:prod_desc' => "TEST PRODUCT   DESCRIPTION -  ! \@ # \$ % ^ & * ( ) _ +  = [ ] 


\x{2211} \x{e2} \x{f1} \x{f5} \x{a5}  \x{a9}  \x{2122}   \x{ae}


This is a test product its a great test product you will want to by 100's

;iou[ pbun[poi ub[poj;


;lkuj np;oiu [pouij
;okub [p9u[0\x{2019}9uj]0 b=98b
\@##^%*(&^(&\$^
?><MI OBIU&Y
;oib u[09yu [
",
          'is:fresh' => 1,
          'zoovy:prod_is_tags' => 'IS_FRESH',
          'zoovy:inv_enable' => 33,
          'zoovy:digest' => '+JtFm9c/soWuSJNbHEx1PQ',
          'zoovy:base_weight' => '',
          'zoovy:prod_is' => 1,
          'zoovy:base_price' => '999.99',
          'amz:ts' => 0,
          'zoovy:prod_name' => 'testing'
        };

use YAML::Syck;
print YAML::Syck::Dump($X);