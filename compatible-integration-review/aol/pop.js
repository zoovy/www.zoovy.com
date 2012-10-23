var MonitorWidth = screen.width;
var MonitorHeight = screen.height;
function popx() {
		 var wide = "550";
		 var high = "412";
  		 var locx = (MonitorWidth-wide)/2, locy = (MonitorHeight-high)/2;
		 var aol = window.open('http://gfx.zoovy.com/learning/aol/index.html','AOL Integration','width='+wide+',height='+high+', screenx='+locx+', screeny='+locy+', top='+locy+', left='+locx+', scrollbars=no, menubar=no, status=no');
}

function pop() {
		 var wide = "550";
		 var high = "412";
  		 var locx = (MonitorWidth-wide)/2, locy = (MonitorHeight-high)/2;
		 var approvers = window.open('http://gfx.zoovy.com/learning/aol/','upload','width='+wide+',height='+high+', screenx='+locx+', screeny='+locy+', top='+locy+', left='+locx+', scrollbars=no, menubar=no, status=yes');
}