package ORDER;

use LWP;
use Data::Dumper;
use XML::Parser;
use XML::Parser::EasyTree;

##
## takes a BUFFER which is formatted <ORDER ...>...</ORDER>
## returns three things:
##    orderref = contains a reference to a hash that contains all keys in order
##		productref = contains a reference to a hash keyed by product id where the value is a hashref 
##						contains a list of contents for the product (note: 'contents' is the the product name)
## 	eventref = contains a reference to an array, all fields are present ('event' is the contents of the event)
##
## Bugs: contents in product is assumed not to be an attribute, also event in event, 
##			(if they are they will overwrite, which probably isn't critical) - this breaks spec but simplifies everything considerably
##
sub parse_order {
	my ($BUFFER) = @_;

	print STDERR "parse_order BUFFER IS: ".length($BUFFER)." bytes\n";

	if ($DEBUG) {
		open F, ">>/tmp/parseorder.txt.".time();
		print F $BUFFER;
		close F;
		}

	my %ORDERINFO = ();
	my %CONTENTS = ();
	my %VIRTUALMAPS = ();
	my @EVENTS = ();

	$XML::Parser::Easytree::Noempty=1;
	my $p=new XML::Parser(Style=>'EasyTree');
	
	my $tree=$p->parse($BUFFER);	

	my $ORDERID = $tree->[0]->{'attrib'}->{'ID'};
	print "ORDERID is: $ORDERID\n";

	foreach $node (@{$tree->[0]->{'content'}}) {
		next if ($node->{'type'} ne 'e');
		if ($DEBUG) { print STDERR Dumper($node); }

		if ($node->{'name'} eq 'CONTENTS') {
			foreach $product (@{$node->{'content'}}) {
				next if ($product->{'type'} ne 'e');
				next if ($product->{'name'} ne 'product');
				
				$productid = $product->{'attrib'}->{'id'};
				delete $product->{'attrib'}->{'id'};
				$product->{'attrib'}->{'contents'} = $product->{'content'}->[0]->{'content'};
				$CONTENTS{$productid} = $product->{'attrib'};
				}
			}
		elsif ($node->{'name'} eq 'VIRTUALMAPS') {
			foreach $product (@{$node->{'content'}}) {
				## <map product="@ALIENVID" url="http://www.alldropship.com/zoovy/order.cgi/SID=21/SELLER=brian/SKU=ALIENVID"/>
				next if ($product->{'type'} ne 'e');
				next if ($product->{'name'} ne 'map');
				
				$productid = $product->{'attrib'}->{'product'};
				$VIRTUALMAPS{$productid} = $product->{'attrib'}->{'url'};
				}
			}
		elsif ($node->{'name'} eq 'contents') {
			die("ORDER::parse_order does not support encoded products.");
			}
		elsif ($node->{'name'} eq 'events') {
			# Lower case events are encoded inside the data, uppercase EVENTS aren't.
			my $p=new XML::Parser(Style=>'EasyTree');
			my $tree = $p->parse('<events>'.$node->{'content'}->[0]->{'content'}.'</events>');

			foreach $event (@{$tree->[0]->{'content'}}) {
				next if ($event->{'type'} ne 'e');
				next if ($event->{'name'} ne 'event');
				
				$event->{'attrib'}->{'event'} = $event->{'content'}->[0]->{'content'};
				push @EVENTS, $event->{'attrib'};
				}
			
			}
		elsif ($node->{'name'} eq 'EVENTS') {
			foreach $event (@{$node->{'content'}}) {
				next if ($event->{'type'} ne 'e');
				next if ($event->{'name'} ne 'event');
				
				$event->{'attrib'}->{'event'} = $event->{'content'}->[0]->{'content'};
				push @EVENTS, $event->{'attrib'};
				}
			
			}
		else {
			$ORDERINFO{$node->{'name'}} = $node->{'content'}->[0]->{'content'};
			}

		}
	

	return($ORDERID,\%ORDERINFO,\%CONTENTS,\@EVENTS,\%VIRTUALMAPS);
}




1;
