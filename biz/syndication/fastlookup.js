
function ajaxUpdate(MKT, me) {
//	alert('ajaxUpdateStart');

   var nc = me.name;
   var val = document.catFrm[me.name].value;
   
   // alert(nc+'='+val);
   // $('txt!'+me.name).innerHTML;
   
   new Ajax.Request('/biz/syndication/fastlookup.cgi', {
   	asynchronous: 1,
   	postBody: 'MKT='+MKT+'&CATID='+val, 
   	onComplete: function(request){ 
			// alert(val);
      	$('txt!'+me.name).innerHTML = request.responseText;
      	// alert('RESPONSE: '+request.responseText);
      	} 
      } 
   ) ;
   	
//	alert('ajaxUpdateEnd');
	}



