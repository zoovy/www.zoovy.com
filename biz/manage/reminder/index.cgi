#!/usr/bin/perl

use lib "/httpd/modules";
use NAGBOT;
use GT;
use CGI;
use ZOOVY;

($USERNAME) = ZOOVY::authenticate('/biz');
$q = new CGI;

$template_file = "index.shtml";

print $q->header;

$GT::TAG{"<!-- REMINDER_LIST -->"} = &build_reminders();
&GT::print_form("",$template_file);

exit;

##
## assumes $USERNAME is set.
##
sub build_reminders
{
  $c = "";
  @nags = &NAGBOT::fetch_nags($USERNAME);
  $c .= "<table>";
  $c .= "<tr>";
   $c .= "<td></td>";
   $c .= "<td><font face='Arial'><b>External Item</b></font></td>";
   $c .= "<td><font face='Arial'><b>Last Reminder</b></font></td>";  
  $c .= "</tr>";
  foreach $nag (@nags)
    {
    ($ID, $CODE, $LAST) = split(',',$nag);
    $c .= "<tr><td></td><td><a href=''>$CODE</a></td><td>$LAST</td></tr>";
    }
  $c .= "</table>";
  return($c);	
}