#!/usr/bin/perl

use Data::Dumper;
use lib "/httpd/modules";
use ZOOVY;
use ZWEBSITE;
use ORDER::BATCH;
use ORDER;
use POSIX; 
use LWP::UserAgent;
use Net::FTP;
use LWP::Simple;
use Data::Dumper;

my $USERNAME = 'zephyrsports';
$USERNAME = $ARGV[0];
if ($USERNAME eq '') { die(); }

my $webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME,0);
my $TMPFILE = "/tmp/$USERNAME.tsv";
open F, ">$TMPFILE\n";

my ($ts) = &ORDER::BATCH::report($USERNAME,'CREATED_GMT'=>time()-(86400*60));
print F "ORDER\tSHIP-DATE\tSUBTOTAL\tCREATED\tCARRIER\tTRACKING\tDECLAREDVAL\n";
foreach my $oidref (@{$ts}) {
	my $oid = $oidref->{'ORDERID'};
	print "OID: $oid\n";
	next if ($oid eq '');
	my ($o) = ORDER->new($USERNAME,$oid);

#$VAR1 = {
#          'cost' => '4.58',
#          'actualwt' => '0',
#          'track' => '518355710166299',
#          'content' => '',
#          'void' => '0',
#          'ins' => '',
#          'carrier' => 'FDXG',
#          'created' => '1209672158',
#          'dv' => '0.00',
#          'notes' => ''
#        };

	my $total = sprintf("%.2f",$o->get_attrib('order_subtotal'));

	foreach my $trk (@{$o->tracking()}) {
		# print Dumper($trk);
		$trk->{'dv'} = sprintf("%.2f",$trk->{'dv'});
		my $shipdate = POSIX::strftime("%Y%m%d%H%M%S",localtime($trk->{'created'}));
		
		print F "$oid\t$shipdate\t$total\t$trk->{'carrier'}\t$trk->{'track'}\t$trk->{'dv'}\n";
		}
	
	}

close F;


if (0) {
  # use MIME::Lite package
  use MIME::Lite;

  # set up email
  my $to = "walt@u-pic.com";
  my $from = "info\@zoovy.com";
  my $subject = "Shipping Report for User: $USERNAME";
  my $message = "any issues contact us at 877-966-8948 x 104";
  
  my $msg = MIME::Lite->new( From => $from, Cc=>'brian@zoovy.com', To => $to, Subject => $subject, Data => $message );
             
  # add the attachment
  # YYYYMMDD_zoovy_data.csv
  my $FILENAME = strftime("%Y%m%d_$USERNAME.csv",localtime());

  $msg->attach( Type => "text/csv", Path => $TMPFILE, Filename => $FILENAME, Disposition => "attachment");
                        
  # MIME::Lite->send('smtp', 'localhost', Timeout => 60);
  MIME::Lite->send("sendmail", "/usr/lib/sendmail -t -oi -oem");
  $msg->send();
  }


if (1) {
  my $ftp = Net::FTP->new("delta.u-pic.com", Debug => 1);
  if (not defined $ftp) {
    my $rc = $ftp->login("zoovy","z0ovY!nc");
    print "RC: $rc\n";

    my $FILENAME = strftime("shiplog-%Y%m%d_$USERNAME.csv",localtime());

    # $ftp->pasv();
    $ftp->binary();
    $ftp->put($TMPFILE,$FILENAME);
    $ftp->quit;
    }
  }
  
print "FINISHED SENDING!\n";
