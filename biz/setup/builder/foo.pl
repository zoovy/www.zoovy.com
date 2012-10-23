#!/usr/bin/perl


$VAR1 = {
          'PRETTY:GALLERY_LAST_POLL_GMT' => 'Thu 2-Oct-2008 20:10 PDT',
          'EBAY_TOKEN_EXP' => '2009-09-04 00:57:01',
          'PRETTY:UPI_OLDEST_OPEN_DISPUTE_GMT' => 'Never',
          'GALLERY_NEXT_POLL_GMT' => '1223090184',
          'PRETTY:LAST_TRANSACTIONS_GMT' => 'Tue 6-Jan-2009 7:55 PST',
          'GALLERY_POLL_INTERVAL' => '300',
          'CHKOUT_PROFILE' => 'DEFAULT',
          'HAS_STORE' => '1',
          'EBAY_SUBSCRIPTION' => 'SellerReportsPlus',
          'UPI_OLDEST_OPEN_DISPUTE_GMT' => '0',
          'LAST_POLL_GMT' => 1231279296,
          'NEXT_ACCOUNT_GMT' => '0',
          'MONITOR_LOCK_GMT' => '1231279561',
          'UPI_AUTODISPUTE' => '0',
          'PRETTY:FB_POLLED_GMT' => 'Mon 5-Jan-2009 20:20 PST',
          'FB_MESSAGE' => 'Great Buyer! Always welcome back! A+++++',
          'GALLERY_LAST_POLL_GMT' => '1223003404',
          'PRETTY:NEXT_POLL_GMT' => 'Tue 6-Jan-2009 20:06 PST',
          'FB_MODE' => '2',
          'LAST_ACCOUNT_GMT' => '0',
          'GALLERY_VARS' => 'custom=&items=6&scheme=1&theme=gel',
          'IS_SANDBOX' => '0',
          'ID' => '5523',
          'MERCHANT' => 'designed2bsweet',
          'PRETTY:LAST_POLL_GMT' => 'Tue 6-Jan-2009 14:01 PST',
          'NEXT_POLL_GMT' => '1231301203',
          'GALLERY_STYLE' => '8',
          'PRETTY:MONITOR_LOCK_GMT' => 'Tue 6-Jan-2009 14:06 PST',
          'ERRORS' => 0,
          'PRETTY:LAST_ACCOUNT_GMT' => 'Never',
          'VERIFIED' => '0000-00-00 00:00:00',
          'MID' => '53031',
          'EBAY_FEEDBACKSCORE' => '2105',
          'PRETTY:GALLERY_NEXT_POLL_GMT' => 'Fri 3-Oct-2008 20:16 PDT',
          'CACHED_FLAGS' => '',
          'LAST_TRANSACTIONS_GMT' => '1231257327',
          'MONITOR_LOCK_ATTEMPTS' => '0',
          'UPI_NEXTPOLL_GMT' => '0',
          'PRETTY:UPI_NEXTPOLL_GMT' => 'Never',
          'PRETTY:NEXT_ACCOUNT_GMT' => 'Never',
          'EBAY_TOKEN' => 'AgAAAA**AQAAAA**aAAAAA**3XvYRw**nY+sHZ2PrBmdj6wVnY+sEZ2PrA2dj6wFkoqlAJmFqAudj6x9nY+seQ**CwQAAA**AAMAAA**s+oM8I9OC+qfnm0RZFDVJyPOxU/hA5xOMLWgAkrGVoHxhTY0pVNwW8r2B8Vd2neQgZ/Dyx5bsSk+7/ssG7poeRyrD5Jzc2Lj7cx77pdjPkWalX9onXfCYfm86ZObsO8u9IYIVbdCMp0Qf5Bnmt8RWdZXcdquzY0J8ZtTS+G/H4xTb9Q3Aiz7w128l2MlsxdBiWXxGnvnAFcP3VKPXHywn/MDm1z9wsCZU28HeIShvt0lacIa/Nb9tzx7u9I6KyLY84/exYcmFgA6uV0YcfMmqBLfyqwlCF2LrTCvatZrfE/zDtZWeNkMnznhzWJhcLZE6mfoLZwz+pDWnPb098MUUbyK6mQ03pOa5bg6zxQuvmrIx3vrXv2nrr48NcT07UwFwhAe1jl7uE+K39pQmmeoszDCrdumNFKvGKRckzLEEb8+WBxEpTiK7Z0XJks3oj/A/C+t7zbgV1p5AgtaZPls+MGejvw3J8/VWYGviXNGWuri+nKmo+KuBdO4tZ/Ae79Kd86K8pEjl9m788JgjdN5/7H5ZaCKzgBybLn8ko8fZYkL6uBiGRJrMGHjbFpnZ+NB7r0+hCr00WZrMh4vWNZGnlGYc+TpQBaJugRlEonQ21AzNVW+xtf2ltWMYO08XeWV1Dfbiawaz7/hYUM6+Fm52Bx5zIdIL+LRPCeFxQuxbnxB31NnRka4H3lr0Poes3RdB9MQezZUekhAoM4RTIQqQC38p4WS+YMDZOBi3aI+KcqJuCaoAIaZUXPkmUBD9KPB',
          'EBAY_USERNAME' => 'designed2bsweet',
          'MONITOR_LOCK_ID' => '0',
          'ORDERS_POLLED_GMT' => '0',
          'PRETTY:ORDERS_POLLED_GMT' => 'Never',
          'PRT' => '0',
          'EBAY_EIAS' => 'nY+sHZ2PrBmdj6wVnY+sEZ2PrA2dj6wFkoqlAJmFqAudj6x9nY+seQ==',
          'FB_POLLED_GMT' => '1231215601'
        };


print $VAR1->{'FB_POLLED_GMT'};
exit;


my $txt = qq~1. Cust:  terracotta, #53038 (Muhammad Raaze)
2. Customer: sportstop #21803 (Customer Support)
~;

foreach $line (split(/\n/,$txt)) {
	print "==>$line\n";
	if ($line =~ /Cust(omer)?:[\s]+([a-zA-Z0-9]+)[\s,]+/) {
		print "Customer: $2\n";
		}
	if ($line =~ /\#([\d]+)/) {
		print "MID: $1\n";
		}
	if ($line =~ /^([\d]+)\.\s(.*?)$/) {
		print "\$1: $1\n";
		print "\$2: $2\n";
		} 
	$line =~ s/\(([A-Za-z]+)[\s]+([A-Za-z]+)\)/\($2, $1\)/;
	print "LINE: $line\n";
	}


# print $txt;

