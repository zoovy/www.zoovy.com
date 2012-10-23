#!/usr/bin/perl

use lib "/httpd/modules";
use GTOOLS;
use LUSER;

my ($LU) = LUSER->authenticate();
if (not defined $LU) { warn "Auth"; exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { warn "No auth"; exit; }

&GTOOLS::output(
	'*LU'=>$LU,
	'*io'=>*DATA,
	'header'=>1,
	'jquery'=>1,
	);


__DATA__
<!-- SETUP_TAB -->


<script type="text/javascript" src="https://static.zoovy.com/graphics/general/jslib/zmvc/v1/controller.js"></script>
<script type="text/javascript" src="https://static.zoovy.com/graphics/general/jslib/zmvc/v1/model.js"></script>
<script type="text/javascript">

var myController;   //later, we can move this into the $(function below, but I want the var on the global level for ease of testing.

$(function() {
	console.log("start controller");
   myController = new zController({
      "username":"<!-- USERNAME -->",
      "sdomain":"<!-- USERNAME -->.zoovy.com",
      "jqurl":"http://www.zoovy.com/webapi/jquery/index.cgi"
      // "secureURL" : "https://ssl.zoovy.com/"
      });  //instantiate controller. handles all logic and communication between model and view.

   });
</script>

<script type="text/javascript">
<!--

function updateImage(id) {
	var file = $('#'+id+'-field').val();
	var src = myController.utilityFunctions.makeImage({'name':file,'h':100,'w':100});
	$('#company_name-img').attr( "src", src );
	myController.utilityFunctions.dataDumper("src"+src);
	}

//-->
</script>

<div>USERNAME: <!-- USERNAME --></div>
<div>LUSER: <!-- LUSER --></div>
<div>PRT: <!-- PRT --></div>

<form action="index.cgi">

<img id="company_name-img" src="">
<input id="company_name-field" type="textbox" name="company_name" 
	onChange="console.log('change'); $(this).trigger('blur');" 
	onBlur="updateImage('company_name');" value="1/a/water_lilies.jpg">
<script type="text/javascript">
$(function(){ $('#company_name-field').trigger('blur'); });
</script>


<input type="submit" value=" Save " onClick="save();">

<input type="button" Value="Click me" onClick="$('#company_name-field').val('asdf').trigger('blur');">

</form>

