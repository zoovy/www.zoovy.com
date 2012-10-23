#!/usr/bin/perl -w
use strict;
use warnings;
use CGI::Carp qw(fatalsToBrowser);
use CGI qw(param);
use lib "/httpd/modules";
require EBAY2;
require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_P&16');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }


my $CATID = param('CATID');
my $V = param('V');
## V=ebay-.accessories_miscellaneous - form field name to return

##
### NOTE: check /httpd/servers/ebay2008/
##

my $udbh = &DBINFO::db_user_connect($USERNAME);
my ($html, $res);

## fetch categories with parent_id
my $sth = $udbh->prepare('SELECT id,name,leaf FROM ebay_categories WHERE parent_id=? AND id!=parent_id');
$sth = $udbh->prepare('SELECT id,name,leaf FROM ebay_categories WHERE level=?') if not $CATID;

if($CATID) {
  $res = $sth->execute($CATID);
} else {
  $res = $sth->execute(1);
}

if(int $res) {
  while(my ($cat_id, $cat_name, $cat_leaf) = $sth->fetchrow_array()) {
    if (not $cat_leaf) {
      my $sth2 = $udbh->prepare('SELECT count(id) FROM ebay_categories WHERE parent_id=?');
      $sth2->execute($cat_id);
      my $count = $sth2->fetchrow_array;
      $count--;
      $sth2->finish;
      $html .= "<li><a href=\"catchooser2008.cgi?V=$V&CATID=$cat_id\">$cat_name ($count)</a></li>\n";
    } else {
      $html .= "<li><a href=\"javascript:window.opener.document.forms['thisFrm'].elements['$V'].value='$cat_id'; window.close();\">$cat_name (leaf)</a></li>\n";
    }
  }
}
$sth->finish;
$html = "<ul>$html</ul>\n";


## fetch all parents
if($CATID) {
  $sth = $udbh->prepare('SELECT id,parent_id,name,level from ebay_categories where id=?');
  $res = $sth->execute($CATID);
  if(int $res) {
    my ($cat_id, $cat_parent_id, $cat_name, $cat_level) = $sth->fetchrow_array();
    $sth->finish;
    $html = "<ul><li><a href=\"catchooser2008.cgi?V=$V&CATID=$cat_id\">$cat_name</a></li><li>$html</li></ul>";
    foreach (1..$cat_level-1) {
      $sth = $udbh->prepare('SELECT id,parent_id,name from ebay_categories where id=?');
      $sth->execute($cat_parent_id);
      ($cat_id, $cat_parent_id, $cat_name) = $sth->fetchrow_array();
      $sth->finish;
      $html = "<ul><li><a href=\"catchooser2008.cgi?V=$V&CATID=$cat_id\">$cat_name</a></li><li>$html</li></ul>";
    }
  }
}

$html = "<ul><li><a href=\"catchooser2008.cgi?V=$V\"><strong>eBay Categories</strong></a></li><li>$html</li></ul>";

$html = 'Content-type: text/html; charset=utf-8

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
  <title>Choose category</title>
  <style type="text/css">
    ul { list-style:none; margin:0.5em 1em; padding:0; }
  </style>
</head>
<body>'.$html.'</body>
</html>
';

print $html;
&DBINFO::db_user_close();
