//
// <script type="text/javascript" src="/biz/ajax/include.js">
//
function ajaxNotify(method,data) {
	req = false;
	// branch for native XMLHttpRequest object
	if(window.XMLHttpRequest) {
		try {	req = new XMLHttpRequest(); } catch(e) { req = false; }

		} 
	// branch for IE/Windows ActiveX version
	else if(window.ActiveXObject) {
		try {	req = new ActiveXObject("Msxml2.XMLHTTP"); } catch(e) {
        	try { req = new ActiveXObject("Microsoft.XMLHTTP"); } catch(e) { req = false; }
	      }
	  	}
	  	
	if(req) {
		req.onreadystatechange = processReqChange;
		if (data.length<500) {
			req.open("GET", "/biz/ajax/handler.pl?v=1&m="+escape(method)+"&data="+escape(data), true);
			req.setRequestHeader("If-Modified-Since", "Sat, 1 Jan 2000 00:00:00 GMT");
			req.send('');
			}
		else {
			req.open("POST","/biz/ajax/handler.pl", true);
			req.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
			req.setRequestHeader("If-Modified-Since", "Sat, 1 Jan 2000 00:00:00 GMT");
			// req.send('var1=data1&var2=data2');
		//	data.replace('&','&amp;');
		//	data.replace('<','&lt;');
		//	data.replace('>','&gt;');
		//	data.replace('"','&quot;');
			req.send("v=1&m="+method+"&data="+escape(data));
			};
		}	
	}
	
//
// on success this executes the "handleResponse" function
//
function processReqChange() {
    // only if req shows "loaded"
    if (req.readyState == 4) {
        // only if "OK"
        if (req.status == 200) {
            // ...processing statements go here...
				handleResponse(req.responseText);
        } else {
            alert("There was a problem retrieving the XML data:\n" +
                req.statusText);
        }
    }
}

// takes a string e.g. k1=v1&k2=v2&k3=v3 and returns an associative array
function kvTxtToArray(txt) {
	var params = new Array();
	txt = txt.substring(1);	 // strip off the ?
	for(var i=0; i < txt.split("&").length; i++) {
		var kvpair = txt.split("&")[i];	
		params[ unescape(kvpair.split("=")[0]) ] = unescape(kvpair.split("=")[1]);
		}

	// use the line below to test if its working!
	// for(var i in params) { alert(i + ' : ' + params[ i ]); }
	return(params);
	}
