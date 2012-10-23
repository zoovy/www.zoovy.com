//
function handleResponse(txt) {

   if (txt == '') {
      // empty response, must have been a set only
      }
   else if (txt.indexOf('?') == 0) {
      // NOTE: multiple ? can be returned.
      // ?k1=v1 (NOT XML)
      var txtLines = new Array();
      txtLines = txt.split('?');    // split the txt into lines (separated by ?)
      for (var i = 0;i<txtLines.length;i++) {
         var params = kvTxtToArray('?' + txtLines[i]);
         // alert('i['+i+']='+txtLines[i]);
        	// alert(i+' '+params['m']);

         if (txtLines[i] == '') {}  // blank line (probably the first record)
         else if (params['m'] == 'loadcontent') {
			//	alert(params['div']);
            $(params['div']).innerHTML = params['html'];
            }
			else if (params['m'] == 'eval') {
				// runs javascript
				try { eval(params['js']); } catch (e) { alert('failed: '+params['js']); }
				}
			else if (params['m'] == 'loadselect') {
				// to set options pass: c=count#&s=selectedid&t0=text0&v0=value0&t1=text1&v1=value1
				var theSel = $(params['id']);
				theSel.options.length = 0; // removes all options.
				var i=0;
				while (params['t'+i] != undefined) {
					theSel.options[i] = new Option(params['t'+i],params['v'+i]);
					i++;
					}
				}
         else {
            // unknown request handler!
            }
         // end of each line.
         }
      }
   else {
      alert('unknown data format sent to handleResponse: '+txt);
      }
   }


// 
function esc(str) {
	// note: eventually we need to make a better escape
	return(encodeURIComponent(str));
	}

function unesc(str) {
	return(decodeURIComponent(str));
	}


// NOTE: this doesn't work!
function kvArrayToTxt(qq) {
	var txt = '';
	var k = '';
	alert('length: '+qq.length);
	for ( k in qq ) {
		alert(k.valueOf);
		if (k != '') {
			alert('KEY: '+k);
			txt = txt + esc(k)+"="+esc( qq[k] )+'&';
			}
		}
	alert(txt);
	return(txt);
	}

// takes a string e.g. k1=v1&k2=v2&k3=v3 and returns an associative array
function kvTxtToArray(txt) {
	// alert('kvTxtToArray: '+txt);
	var params = new Array();

	if (txt.charAt(0) == '?') {
		txt = txt.substring(1);	 // strip off the ?
		}
	for(var i=0; i < txt.split("&").length; i++) {
		var kvpair = txt.split("&")[i];	
		// alert('kvpair: '+kvpair);
		params[ unesc(kvpair.split("=")[0]) ] = unesc(kvpair.split("=")[1]);
		}

	// use the line below to test if its working!
	// for(var i in params) { alert(i + ' : ' + params[ i ]); }
	return(params);
	}


// checks to see if a specific value is an an array.
Array.prototype.inArray = function (value) {
	var i;
	for (i=0; i < this.length; i++) {
		if (this[i] === value) {
			return true;
		}
	}
	return false;
};

// removes a specific value from an array (useful for keeping state)
Array.prototype.popValue = function (value) {
	var i;
	for (i=0; i < this.length; i++) {
		if (this[i] === value) {
			this.splice(i,1); i--;
		}
	}
};

function getRadioValue(r) {
	var result = undefined;
	for (var i=0; i < r.length; i++) {
   	if (r[i].checked) { result = r[i].value; }
	   }
	return(result);
	}



