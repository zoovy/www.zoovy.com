#!/usr/bin/perl

use strict;
use lib "/httpd/modules";
use TODO;
use ZOOVY;
use ZTOOLKIT;
use URI::Escape;
use GTOOLS;
use LUSER;

my ($LU) = LUSER->authenticate();
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

## $LU->log('PRODEDIT.NUKEIMG',"[PID:$PID] Nuking image $img ".$prodref->{'zoovy:prod_image'.$img},'INFO');

my $ACTION = $ZOOVY::cgiv->{'ACTION'};
my $TAB = $ZOOVY::cgiv->{'TAB'};


my $todo = TODO->new($USERNAME,LUSER=>$LUSERNAME);


my $template_file = 'index.shtml';

if ($ACTION eq 'CONFIG-SAVE') {
	$LU->set('todo.setup', (defined $ZOOVY::cgiv->{'SETUP'})?1:0 );	
	if ($ZOOVY::cgiv->{'TESTING'}) {
		}
	$LU->save();
	$TAB = 'CONFIG';
	}


if ($ACTION eq 'SORT') {
	$todo->set_sort($ZOOVY::cgiv->{'SORT'});
	}

if ($ACTION eq 'CREATE') {
	$todo->add(name=>$ZOOVY::cgiv->{'NAME'},
		link=>$ZOOVY::cgiv->{'LINK'},
		priority=>$ZOOVY::cgiv->{'PRIORITY'},
		assignto=>$ZOOVY::cgiv->{'ASSIGNTO'}
		);
	}


if ($ACTION =~ /ASSIGNTO\:(.*?)$/) {
	my $ASSIGNTO = $1;
	my @TASKS = ();
	foreach my $p (keys %{$ZOOVY::cgiv}) {
		if ($p =~ /task-(.*?)$/) { push @TASKS, $1; }
		}
	if (scalar(@TASKS)>0) {
		$todo->assignto(\@TASKS,$ASSIGNTO);
		}
	}

if ($ACTION eq 'COMPLETE') {
	foreach my $p (keys %{$ZOOVY::cgiv}) {
		if ($p =~ /task-(.*?)$/) { $todo->complete($1); }
		}
	}

if ($ACTION eq 'DELETE') {
	## remove flagged items
	foreach my $p (keys %{$ZOOVY::cgiv}) {
		if ($p =~ /task-(.*?)$/) { $todo->delete($1); }
		}
	## remove completed items
	foreach my $task (@{$todo->list()}) {
		if ($task->{'COMPLETED_GMT'}>0) {
			$todo->delete($task->{'ID'});
			}
		}
	}


if ($TAB eq 'CONFIG') {

	$GTOOLS::TAG{'<!-- CHK_SETUP -->'} = $LU->get('todo.setup')?'checked':'';

	$template_file = 'config.shtml';
	}
else {
	
	$todo->verify();

	my $userlist = '<option value=\"\">Everybody</option>';
	my $USERS = &TODO::list_users($USERNAME);
	foreach my $luser (sort keys %{$USERS}) {
		my $userref = $USERS->{$luser};
		$userlist .= "<option value=\"$userref->{'LUSER'}\">[$userref->{'LUSER'}] $userref->{'FULLNAME'}</option>";
		}
	$GTOOLS::TAG{'<!-- ASSIGNTO -->'} = $userlist; 


	my $c = '';
	my $t = time();
	my $clickjs = '';
	my $class = '';
	foreach my $task (@{$todo->list()}) {
	
		$class = ($class eq 'r0')?'r1':'r0';
	
		# print STDERR "$task->{'CLASS'} ne $TAB)\n";
		next if (($TAB ne '') && ($task->{'CLASS'} ne $TAB));
		$c .= "<tr class=$class>";
		
		if ($task->{'COMPLETED_GMT'}==0) {
			$c .= "<td valign=top><input class=\"taskRightClick tooltip\" title=\"right click for context menu\" type=\"checkbox\" id=\"task-$task->{'ID'}\" name=\"task-$task->{'ID'}\"></td>";
			# $clickjs .= "thisFrm.elements['task-$task->{'ID'}'].checked = not thisFrm.elements['task-$task->{'ID'}'].checked;\n";
			}
		else {
			$c .= "<td valign=top></td>";
			}
	
		my $markup = '';
		if ($task->{'COMPLETED_GMT'}>0) { $markup .= "<strike>"; }
		if (($task->{'DUE_GMT'}>0) && ($task->{'DUE_GMT'} < $t)) { $markup .= "<font color='red'>"; }

		$c .= "<td nowrap valign=top>";
		$c .= &ZTOOLKIT::pretty_date($task->{'CREATED_GMT'},-3);
		$c .= "</td>";
	
		$c .= "<td valign=top>";
		$c .= "$markup$task->{'TITLE'}";
		$c .= qq~<div id="detail-$task->{'ID'}" style="display: visible;" class="hint">$task->{'DETAIL'}</div>~;
		$c .= "</td>";
	
		if (not defined $task->{'DUE_GMT'}) {
			$c .= "<td valign=top><center>".$markup."n/a</td>";
			}
		else {
			$c .= "<td valign=top><center>$markup".&ZTOOLKIT::pretty_date($task->{'DUE_GMT'},0)."</td>";
			}
	
		if (not defined $task->{'PRIORITY'}) { $task->{'PRIORITY'} = 1; }
		$c .= "<td valign=top><center>$markup$task->{'PRIORITY'}</td>";
	
		if ($task->{'LINK'} ne '') { 
			if ($task->{'DETAIL'} eq '') { $task->{'DETAIL'} = 'No DETAIL are available'; }
			$task->{'DETAIL'} =~ s/[\n\r]+/ /gs;
			$task->{'DETAIL'} =~ s/'/\\'/gs;
			$task->{'DETAIL'} =~ s/"//gs;
			$c .= "<td valign=top>$markup<a target=\"_top\" onmouseover=\"writetxt('$task->{'DETAIL'}')\" onmouseout=\"writetxt(0)\" href=\"$task->{'LINK'}\">Lets Do It!</a></td>"; 
			} 
		else { 
			$c .= "<td valign=top></td>"; 
			}
	
		$c .= "<td valign=top>$task->{'LUSER'}</td>";
		$c .= "</tr>";
		}
	
	
	
	
	if ($c eq '') {
		$c .= qq~
			<tr><td valign=top><div class='warning'>No items</div></td></tr>
			~;
		}
	else {
		$c = qq~
		<thead>
			<tr>
				<th valign=top class="zoovytableheader"><input type='checkbox' onClick="
	for (i=0; i<thisFrm.length; i++) {
	  if (thisFrm.elements[i].name.substring(0,5) == 'task-') {
			 thisFrm.elements[i].checked = this.checked;
			 }
		 }"></th>
				<th valign=top class="zoovytableheader"><b><a href="index.cgi?ACTION=SORT&SORT=CREATED_GMT">Created</a></b></th>
				<th valign=top class="zoovytableheader"><b><a href="index.cgi?ACTION=SORT&SORT=TASK">Task</a></b></th>
				<th valign=top class="zoovytableheader"><b><a href="index.cgi?ACTION=SORT&SORT=DUE_GMT">Due Date</a></b></th>
				<th valign=top class="zoovytableheader"><b><a href="index.cgi?ACTION=SORT&SORT=PRIORITY">Priority</a></b></th>
				<th valign=top class="zoovytableheader"><b><a href="index.cgi?ACTION=SORT&SORT=LINK">Quick Link</a></b></th>
				<th valign=top class="zoovytableheader"><b><a href="index.cgi?ACTION=SORT&SORT=LUSER">Assigned To</a></b></th>
			</tr>
		</thead>
			~.$c;
	
		my $actions = '';
		my $contextmenu = '';
		my ($users) = &TODO::list_users($USERNAME);
		foreach my $luser (keys %{$users}) {
			next if (uc($luser) eq uc($LUSERNAME));
			$actions .= "<option value=\"ASSIGNTO:$luser\">Assign to: $luser</option>";
			$contextmenu .= "<li><a href=\"#ASSIGNTO:$luser\">Assign: $luser</a></li>";
			}
	
		$GTOOLS::TAG{'<!-- ACTIONS -->'} = qq~
	<table>
		<tr>
			<td valign=top>
			Actions: <select name="ACTION">
				<option value=" -- "></option>
				<option value="COMPLETE">Set as Completed</option>
				<option value="DELETE">Remove from List</option>
				$actions
			</select>
			</td>
			<td valign=top>
			<input class="button showLoadingModal" type="submit" value="  Update  ">
			</td>
		</tr>
	</table>
		~;

		$GTOOLS::TAG{'<!-- CONTEXTMENUOPTIONS -->'} = qq~
		<li><a href=\"http://www.google.com\">go to google</a></li>
		<li><a href=\"#STATUS:COMPLETE\">Set Completed</a></li>
		<li><a href=\"#PRIORITY:1\">Priority High</a></li>
		<li><a href=\"#PRIORITY:2\">Priority Medium</a></li>
		<li><a href=\"#PRIORITY:3\">Priority Low</a></li>
		$contextmenu
		~;

		}
	
	
	
	my $state = 0;
	if (defined $LU) { ($state) = $LU->get('todo.addnew',0); }
	my $stateicon = "http://www.zoovy.com/biz/ajax/navcat_icons/miniup.gif";
	if ($state == 1) { $stateicon = "http://www.zoovy.com/biz/ajax/navcat_icons/minidown.gif"; }
	if ($state == -1) { $stateicon = "/images/blank.gif"; }
	
	$GTOOLS::TAG{'<!-- LIST -->'} = $c;
	$GTOOLS::TAG{'<!-- TAB -->'} = $TAB;
	}

my @TABS = ();
push @TABS, { name=>'All', selected=>($TAB eq '')?1:0, link=>'/biz/todo/index.cgi?', target=>'_top' };
push @TABS, { name=>'Info', selected=>($TAB eq 'INFO')?1:0, link=>'/biz/todo/index.cgi?TAB=INFO', target=>'_top' };
push @TABS, { name=>'Tasks', selected=>($TAB eq 'TODO')?1:0, link=>'/biz/todo/index.cgi?TAB=TODO', target=>'_top' };
push @TABS, { name=>'Warnings', selected=>($TAB eq 'WARN')?1:0, link=>'/biz/todo/index.cgi?TAB=WARN', target=>'_top' };
push @TABS, { name=>'Errors', selected=>($TAB eq 'ERROR')?1:0, link=>'/biz/todo/index.cgi?TAB=ERROR', target=>'_top' };
push @TABS, { name=>'Config', selected=>($TAB eq 'CONFIG')?1:0, link=>'/biz/todo/index.cgi?TAB=CONFIG', target=>'_top' };

&GTOOLS::output(
	'title'=>$USERNAME."'s To Do List",
	'file'=>$template_file,
	'help'=>'#50809',
	'header'=>1,
	'jquery'=>1,
	'headjs'=>q~
<script type="text/javascript">
// necessary for checkbox qtip tooltips to work (normally we can just call $('.tooltip').qtip(); .. but checkboxes don't work

// necessary for contextMenu
$(document).ready( function() {
 
    $(".taskRightClick").contextMenu({
        menu: 'taskRightClick'
    },
        function(action, el, pos) {
        alert(
            'Action: ' + action + '\n\n' +
            'Element ID: ' + $(el).attr('id') + '\n\n' +
            'X: ' + pos.x + '  Y: ' + pos.y + ' (relative to element)\n\n' +
            'X: ' + pos.docX + '  Y: ' + pos.docY+ ' (relative to document)'
            );
    });
 
});




</script>
~,
	'tabs'=>\@TABS,
	'bc'=>[
		{ name=>'To Do List', link=>'/biz/todo', target=>'_top' }
		]
	);


