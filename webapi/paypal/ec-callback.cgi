#!/usr/bin/perl

use Data::Dumper;

use lib "/httpd/modules";
use ZSHIP;
use ZPAY::PAYPALEC;
use CART2;
use CGI::Lite;

##
## processes inbound callback requests from paypal express checkout
##
my $q = new CGI;
my %v = ();

foreach my $p ($q->param()) {
   $v{$p} = $q->param($p);
   }

use lib "/httpd/modules";
if ($ENV{'REQUEST_URI'} =~ /\/webapi\/paypal\/ec-callback\.cgi\/USERNAME=([a-zA-Z0-9]+)\/PRT=([\d]+)\/C=(.*?)\/V\=1$/) {
  $v{'_USERNAME'} = $1;
  $v{'_PRT'} = $2;
  $v{'_CART'} = $3;
  }
elsif ($ENV{'REQUEST_URI'} eq '') {
  }
else {
  die("PAYPALEC-CALLBACK UNKNOWN REQUEST-URI: $ENV{'REQUEST_URI'}");
  }


my $METHOD = $v{'METHOD'};
my $CBVERSION = $v{'CALLBACKVERSION'};



#use Data::Dumper;
#open F, ">/tmp/eccallback.txt";
#print F Dumper(\%v);
#close F;
#$VAR1 = {
#          'L_ITEMWEIGHTUNIT2' => 'lbs',
#          'L_NUMBER3' => '',
#          'CALLBACKVERSION' => '57',
#          'L_NAME0' => 'Freedom Basket BreezeArt Garden Flag',
#          'L_DESC3' => 'Freedom Basket MatMate Doormat',
#          'L_ITEMLENGTHUNIT3' => '',
#          'L_NUMBER0' => '',
#          'L_NAME2' => 'Mailwraps Garden Flag Stand - 1 piece',
#          'L_ITEMWIDTHUNIT2' => '',
#          'L_ITEMHEIGHTUNIT0' => '',
#          '_USERNAME' => 'flagsonastick',
#          'L_ITEMWIDTHUNIT3' => '',
#          'L_ITEMHEIGHTUNIT2' => '',
#          'L_ITEMLENGTHVALUE2' => '0',
#          'L_DESC2' => 'Mailwraps Garden Flag Stand - 1 piece',
#          'L_ITEMLENGTHVALUE3' => '0',
#          'L_QTY1' => '1',
#          'L_ITEMHEIGHTVALUE1' => '0',
#          'METHOD' => 'CallbackRequest',
#          'L_DESC0' => 'Freedom Basket BreezeArt Garden Flag',
#          'L_ITEMWEIGHTVALUE1' => '0',
#          'LOCALECODE' => 'en_US',
#          'L_ITEMWIDTHVALUE1' => '0',
#          'L_NUMBER2' => '',
#          'L_ITEMHEIGHTUNIT1' => '',
#          'CURRENCYCODE' => 'USD',
#          '_CART' => 'h3sqDnR1AzONl8IIs60TjGYV3',
#          'L_NAME3' => 'Freedom Basket MatMate Doormat',
#          'L_ITEMHEIGHTUNIT3' => '',
#          'SHIPTOCITY' => 'Moundsville',
#          'L_ITEMWIDTHVALUE3' => '0',
#          'SHIPTOSTREET' => 'R.D.3 Box 23A',
#          'L_ITEMWEIGHTUNIT1' => 'lbs',
#          'L_ITEMLENGTHVALUE1' => '0',
#          'L_NAME1' => 'Garden Flag Stoppers - Set of 4 for $5.00',
#          'L_ITEMHEIGHTVALUE3' => '0',
#          'L_ITEMLENGTHUNIT0' => '',
#          '_PRT' => '0',
#          'SHIPTOSTATE' => 'WV',
#          'L_ITEMLENGTHVALUE0' => '0',
#          'L_ITEMWIDTHVALUE2' => '0',
#          'SHIPTOCOUNTRY' => 'US',
#          'L_ITEMWIDTHUNIT1' => '',
#          'L_AMT0' => '10.99',
#          'L_ITEMWIDTHUNIT0' => '',
#          'L_ITEMWEIGHTVALUE2' => '0',
#          'L_ITEMWIDTHVALUE0' => '0',
#          'L_ITEMHEIGHTVALUE0' => '0',
#          'L_QTY3' => '2',
#          'L_ITEMWEIGHTUNIT0' => 'lbs',
#          'L_AMT1' => '5.00',
#          'SHIPTOZIP' => '26041',
#          'SHIPTOSTREET2' => '',
#          'L_ITEMLENGTHUNIT1' => '',
#          'L_AMT2' => '15.99',
#          'L_DESC1' => 'Garden Flag Stoppers - Set of 4 for $5.00',
#          'L_NUMBER1' => '',
#          'L_QTY0' => '1',
#          'L_ITEMLENGTHUNIT2' => '',
#          'L_ITEMHEIGHTVALUE2' => '0',
#          'L_ITEMWEIGHTVALUE0' => '0',
#          'L_AMT3' => '20.99',
#          'L_QTY2' => '1',
#          'TOKEN' => 'EC-9MR27243LU4916131',
#          'L_ITEMWEIGHTUNIT3' => 'lbs',
#          'L_ITEMWEIGHTVALUE3' => '0'
#        };
#
#
# print "Content-type: text/html\n\n";
print "Content-type: text/plain; charset=utf-8\n\n";
# print "CALLBACKTIMEOUT=6&L_NAME0=tshirt&L_SHIPPINGOPTIONLABEL0=GUESS0&PWD=1238020587&USER=lizm_1238020561_biz_api1.zoovy.com&MAXAMT=5000.00&L_SHIPPINGOPTIONISDEFAULT0=true&CALLBACK=https%3A%2F%2Fwebapi.zoovy.com%2Fwebapi%2Fpaypal%2Fec-callback.cgi%2FUSERNAME%3Dliz%2FPRT%3D0%2FC%3DpuQ9fEJFQI0hTHA4MQnqXBwNg%2FV%3D1&L_AMT0=10.00&METHOD=SetExpressCheckout&CANCELURL=http%3A%2F%2Fliz.zoovy.com%2Fc%3DpuQ9fEJFQI0hTHA4MQnqXBwNg%2Fs%3Dliz.zoovy.com%2Fcart.cgis&L_ITEMWEIGHTUNIT0=lbs&PAYMENTACTION=Authorization&L_DESC0=tshirt&SUBJECT=lizm%40zoovy.com&ITEMAMT=10&SHIPPINGAMT=5.00&SHIPDISCAMT=0&RETURNURL=https%3A%2F%2Fssl.zoovy.com%2Fliz%2Fc%3DpuQ9fEJFQI0hTHA4MQnqXBwNg%2Fs%3Dliz.zoovy.com%2Fpaypal.cgis%3Fmode%3Dexpress-return&L_QTY0=1&INSURANCEOPTIONOFFERED=false&CURRENCYCODE=USD&L_ITEMWEIGHTVALUE0=0.5&AMT=15&L_SHIPPINGOPTIONNAME0=Shipping&INSURANCEAMT=0.00&TAXAMT=0.00&HANDLINGAMT=0.00&VERSION=57&L_SHIPPINGOPTIONAMOUNT0=5.00&ALLOWNOTE=1&SIGNATURE=AVIodDZ7rRKwta0KKUGchfaXwFiXAVtIJJJ0sBssyTdREn.Vy4JtuBZb";

my %r = ();
my ($CART2) = CART2->new_persist($v{'_USERNAME'},$v{'_PRT'},$v{'_CART'});

$CART2->in_set('ship/address',$v{'SHIPTOSTREET'}.' '.$v{'SHIPTOSTREET2'});
$CART2->in_set('ship/city',$v{'SHIPTOCITY'});
$CART2->in_set('ship/postal',$v{'SHIPTOZIP'});
$CART2->in_set('ship/region',$v{'SHIPTOSTATE'});

&ZPAY::PAYPALEC::addShippingToParams($CART2,\%r,'CALLBACK');

$r{'METHOD'} = 'CallbackResponse';
$r{'OFFERINSURANCEOPTION'} = 'false';
if (0) {
	$r{'L_SHIPPINGOPTIONNAME0'} = 'UPS Air';
	$r{'L_SHIPPINGOPTIONLABEL0'}='TEST UPS Next Day Air Freight XYZ';
	$r{'L_SHIPINGPOPTIONLABEL0'} = $r{'L_SHIPPINGOPTIONLABEL0'};	
	$r{'L_SHIPPINGOPTIONAMOUNT0'}='23.00';
	$r{'L_TAXAMT0'}='2.20';
	#$r{'L_TAXAMT0'}='1.00';
	$r{'L_INSURANCEAMOUNT0'}='1.51';
	$r{'L_SHIPPINGOPTIONISDEFAULT0'}='true';
	}
#$r{'L_SHIPPINGOPTIONNAME1'}='UPS Expedited';
#$r{'L_SHIPINGPOPTIONLABEL1'}='TEST UPS Express 2 Days';
#$r{'L_SHIPPINGOPTIONAMOUNT1'}='10.00';
#$r{'L_TAXAMT1'}='2.00';
#$r{'L_INSURANCEAMOUNT1'}='1.35';
#$r{'L_SHIPPINGOPTIONISDEFAULT1'}='true';
#$r{'L_SHIPPINGOPTIONNAME2'}='UPS Ground';
#$r{'L_SHIPINGPOPTIONLABEL2'}='TEST UPS Ground 2 to 7 Days';
#$r{'L_SHIPPINGOPTIONAMOUNT2'}='9.99';
#$r{'L_TAXAMT2'}='1.99';
#$r{'L_INSURANCEAMOUNT2'}='1.28';
#$r{'L_SHIPPINGOPTIONISDEFAULT2'}='false';

print ZTOOLKIT::buildparams(\%r);

#my $ref = &ZTOOLKIT::parseparams('METHOD=CallbackResponse&OFFERINSURANCEOPTION=true&L_SHIPPINGOPTIONNAME0=UPS Air&L_SHIPINGPOPTIONLABEL0=UPS Next Day Air Freight&L_SHIPPINGOPTIONAMOUNT0=20.00&L_TAXAMT0=2.20&L_INSURANCEAMOUNT0=1.51&L_SHIPPINGOPTIONISDEFAULT0=false&L_SHIPPINGOPTIONNAME1=UPS Expedited&L_SHIPINGPOPTIONLABEL1=UPS Express 2 Days&L_SHIPPINGOPTIONAMOUNT1=10.00&L_TAXAMT1=2.00&L_INSURANCEAMOUNT1=1.35&L_SHIPPINGOPTIONISDEFAULT1=true&L_SHIPPINGOPTIONNAME2=UPS Ground&L_SHIPINGPOPTIONLABEL2=UPS Ground 2 to 7 Days&L_SHIPPINGOPTIONAMOUNT2=9.99&L_TAXAMT2=1.99&L_INSURANCEAMOUNT2=1.28&L_SHIPPINGOPTIONISDEFAULT2=false');
#print &ZTOOLKIT::buildparams($ref);


__DATA__

$VAR1 = bless( {
                 '.parameters' => [
                                    'METHOD',
                                    'CALLBACKVERSION',
                                    'TOKEN',
                                    'LOCALECODE',
                                    'CURRENCYCODE',
                                    'L_NAME0',
                                    'L_NUMBER0',
                                    'L_DESC0',
                                    'L_AMT0',
                                    'L_QTY0',
                                    'L_ITEMWEIGHTUNIT0',
                                    'L_ITEMWEIGHTVALUE0',
                                    'L_ITEMHEIGHTUNIT0',
                                    'L_ITEMHEIGHTVALUE0',
                                    'L_ITEMWIDTHUNIT0',
                                    'L_ITEMWIDTHVALUE0',
                                    'L_ITEMLENGTHUNIT0',
                                    'L_ITEMLENGTHVALUE0',
                                    'L_NAME1',
                                    'L_NUMBER1',
                                    'L_DESC1',
                                    'L_AMT1',
                                    'L_QTY1',
                                    'L_ITEMWEIGHTUNIT1',
                                    'L_ITEMWEIGHTVALUE1',
                                    'L_ITEMHEIGHTUNIT1',
                                    'L_ITEMHEIGHTVALUE1',
                                    'L_ITEMWIDTHUNIT1',
                                    'L_ITEMWIDTHVALUE1',
                                    'L_ITEMLENGTHUNIT1',
                                    'L_ITEMLENGTHVALUE1',
                                    'SHIPTOSTREET',
                                    'SHIPTOCITY',
                                    'SHIPTOSTATE',
                                    'SHIPTOCOUNTRY',
                                    'SHIPTOZIP',
                                    'SHIPTOSTREET2'
                                  ],
                 'SHIPTOSTREET' => [
                                     ''
                                   ],
                 'L_ITEMWEIGHTUNIT1' => [
                                          'lbs'
                                        ],
                 'L_ITEMLENGTHVALUE1' => [
                                           '0'
                                         ],
                 'L_NAME1' => [
                                'Coffee Filter bags'
                              ],
                 'L_ITEMLENGTHUNIT0' => [
                                          ''
                                        ],
                 'CALLBACKVERSION' => [
                                        '57.0'
                                      ],
                 'L_NAME0' => [
                                '10% Decaf Kona Blend Coffee'
                              ],
                 'SHIPTOSTATE' => [
                                    'CA'
                                  ],
                 'SHIPTOCOUNTRY' => [
                                      'US'
                                    ],
                 'L_ITEMLENGTHVALUE0' => [
                                           '0'
                                         ],
                 'L_NUMBER0' => [
                                  '623083'
                                ],
                 'escape' => 1,
                 'L_ITEMHEIGHTUNIT0' => [
                                          ''
                                        ],
                 'L_ITEMWIDTHUNIT1' => [
                                         ''
                                       ],
                 'L_AMT0' => [
                               '1.00'
                             ],
                 'L_QTY1' => [
                               '2'
                             ],
                 'L_ITEMWIDTHUNIT0' => [
                                         ''
                                       ],
                 'L_ITEMWIDTHVALUE0' => [
                                          '0'
                                        ],
                 'L_ITEMHEIGHTVALUE1' => [
                                           '0'
                                         ],
                 'L_ITEMHEIGHTVALUE0' => [
                                           '0'
                                         ],
                 'METHOD' => [
                               'CallbackRequest'
                             ],
                 'L_AMT1' => [
                               '2.00'
                             ],
                 'L_ITEMWEIGHTUNIT0' => [
                                          ''
                                        ],
                 'SHIPTOZIP' => [
                                  '92008'
                                ],
                 'SHIPTOSTREET2' => [
                                      ''
                                    ],
                 'L_DESC0' => [
                                'Size: 8.8-oz'
                              ],
                 'L_ITEMLENGTHUNIT1' => [
                                          ''
                                        ],
                 'L_ITEMWEIGHTVALUE1' => [
                                           '0'
                                         ],
                 'LOCALECODE' => [
                                   'en_US'
                                 ],
                 'L_ITEMWIDTHVALUE1' => [
                                          '0'
                                        ],
                 'L_DESC1' => [
                                'Size: Two 24-piece boxes'
                              ],
                 'L_ITEMHEIGHTUNIT1' => [
                                          ''
                                        ],
                 '.fieldnames' => {},
                 'L_QTY0' => [
                               '2'
                             ],
                 'L_NUMBER1' => [
                                  '6230'
                                ],
                 'CURRENCYCODE' => [
                                     'USD'
                                   ],
                 'use_tempfile' => 1,
                 'L_ITEMWEIGHTVALUE0' => [
                                           '0'
                                         ],
                 '.charset' => 'ISO-8859-1',
                 'SHIPTOCITY' => [
                                   'Carlsbad'
                                 ],
                 'TOKEN' => [
                              'EC-8WM21017G50916106'
                            ]
               }, 'CGI' );
