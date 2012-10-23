
function parseDataSet(dataset) {
	$('DATA').value=dataset;
	$('BUTTON').value=' Running (please wait) ';

	var txtLines = new Array();
	txtLines = dataset.split('?');    // split the txt into lines (separated by ?)
	$('output').innerHTML = '<b>Retrieved data for '+(txtLines.length-1)+' listing(s).</b><br><br>';

	doStuff(txtLines,1);

	function doStuff(txtLines,i) {
		var objDiv = $('output');
		var params = kvTxtToArray('?' + txtLines[i]);
		objDiv.innerHTML = objDiv.innerHTML + '<b> #'+i+'. '+params['Msg'] + '</b><br>';

		new Effect.Highlight(objDiv, { 
			afterFinish: function(obj) { 
			var postBody = 'ACTION=AJAX-EXECUTEDATASET&'+txtLines[i];
		   new Ajax.Request('/biz/manage/ebay/refresh.cgi',
		      { postBody: postBody,asynchronous: 1,onComplete: function(request){
					// parseDataSet(request.responseText);
					objDiv.innerHTML = objDiv.innerHTML+'RESPONSE: '+request.responseText+'<br><hr>';
					objDiv.scrollTop = objDiv.scrollHeight;
					objDiv.focus();

					i++;
					if (txtLines.length>i) {			
						doStuff(txtLines,i);
						}
					else {
						$('output').innerHTML = $('output').innerHTML + "<font color='blue'>Finished</font><br><br><br>";
						$('BUTTON').value=' Refresh Again ';
						$('output').scrollTop = $('output').scrollHeight;
						}
					} } ) ;
			
			} } );
		}

	
	}

//
// subtype can be either Save or Close
//
function loadDataSet() {
   var vars = $('VARS').value;
   var m = $('METHOD').value;
   var verb = $('VERB').value;

	$('output').innerHTML = '<b>Please wait while we load your data. </b><br>debug: '+m+' - '+vars;
   var postBody = 'ACTION=AJAX-LOADDATASETS&METHOD='+m+'&VARS='+vars+'&VERB='+verb;
	
	new Ajax.Request('/biz/manage/ebay/refresh.cgi',
      { postBody: postBody,asynchronous: 1,onComplete: function(request){parseDataSet(request.responseText);} } ) ;

   }


function makeSyncRequest(url, data){
     http_request = false;

     if (window.XMLHttpRequest) { // Mozilla, Safari,...
               http_request = new XMLHttpRequest();
               if (http_request.overrideMimeType) {
                    http_request.overrideMimeType('text/xml');
                    // See note below about this line
               }
          } else if (window.ActiveXObject) { // IE
               try {
                    http_request = new ActiveXObject("Msxml2.XMLHTTP");
               } catch (e) {
                    try {
                         http_request = new ActiveXObject("Microsoft.XMLHTTP");
                    } catch (e) {}
               }
          }


          if (!http_request) {
               alert('Giving up :( Cannot create an XMLHTTP instance');
               return false;
	     }

     // http_request.asynchronous = false;
     http_request.open('GET', url + '?' + data, false);
     http_request.send(null);

	  return(http_request.responseText);
     }


