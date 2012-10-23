// BEGIN CODE FOR LIST ORDERING
function move(sel,incr){
	var i = sel.selectedIndex;	// current selection
	if( i < 0 ) return;
	var j = i + incr;		// where it will move to
	if( j < 0 || j >= sel.length ) return;


   var temp = sel.options[i].text;	// swap them
	sel.options[i].text = sel.options[j].text;
	sel.options[j].text = temp;
	
	temp = sel.options[i].value;
	sel.options[i].value = sel.options[j].value;
	sel.options[j].value = temp;

	sel.selectedIndex = j;		// make new location selected	
}

function setorder(list,field) {	// copy ordered options to the hidden field
	var i = 0;

	if (list.length<=0) { return true; }

	var result = list.options[0].value;
	for( i = 1; i < list.length; i++ ) {
		result = result + '|' + list.options[i].value;
	}
	field.value = result;
	return true;
}

// END LIST ORDERING CODE
// BEGIN SELECT LIST SWITCH CODE

function selSwitch(btn)
{
   var i= btnType = 0;
   var isList1 = doIt = false;

	var btnValue = btn.value;
	if (btnValue == "   add") { btnValue = "  >  "; }
	if (btnValue == "remove") { btnValue = "  <  "; }	

   if (btnValue == "  >  " || btnValue == "  <  ") 
      btnType = 1;
   else if (btnValue == " >> " || btnValue == " << ") 
      btnType = 2;
   else
      btnType = 3;

   with (document.ordering)
   {
      isList1 = (btnValue.indexOf('>') != -1) ? true : false;     

      with ( ((isList1)? list1: list2) )
      {
         for (i = 0; i < length; i++)
         {
            doIt = false;
            if (btnType == 1)
            { 
               if(options[i].selected) doIt = true;
            }
            else if (btnType == 2)
            {
               doIt = true;
            } 
            else 
               if (!options[i].selected) doIt = true;
             
            if (doIt)
            {
               with (options[i])
               {
                  if (isList1)
                     list2.options[list2.length] 
                     = new Option( text, value );
                  else
                     list1.options[list1.length] 
                     = new Option( text, value );
               } 
               options[i] = null;
               i--;
            } 
         //  if(navigator.appName == "Netscape" ) 
         //     history.go(0);

         } // end for loop
         if (options[0] != null)
            options[0].selected = true;
      } // end with islist1
   } // end with document
}

function doSel(selObj)
{
   var i = 0;
   for (i = 0; i < selObj.length; i++)
      alert("The value is '" + selObj.options[i].value + "'");

}
// END SELECT LIST SWITCH CODE
