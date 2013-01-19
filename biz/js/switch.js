function MM_reloadPage(init) {  //reloads the window if Nav4 resized
  if (init==true) with (navigator) {if ((appName=="Netscape")&&(parseInt(appVersion)==4)) {
    document.MM_pgW=innerWidth; document.MM_pgH=innerHeight; onresize=MM_reloadPage; }}
  else if (innerWidth!=document.MM_pgW || innerHeight!=document.MM_pgH) location.reload();
}
MM_reloadPage(true);

function MM_findObj(n, d) { //v4.01
  var p,i,x;  if(!d) d=document; if((p=n.indexOf("?"))>0&&parent.frames.length) {
    d=parent.frames[n.substring(p+1)].document; n=n.substring(0,p);}
  if(!(x=d[n])&&d.all) x=d.all[n]; for (i=0;!x&&i<d.forms.length;i++) x=d.forms[i][n];
  for(i=0;!x&&d.layers&&i<d.layers.length;i++) x=MM_findObj(n,d.layers[i].document);
  if(!x && d.getElementById) x=d.getElementById(n); return x;
}

function MM_showHideLayers() { //v6.0
  var i,p,v,obj,args=MM_showHideLayers.arguments;
  for (i=0; i<(args.length-2); i+=3) if ((obj=MM_findObj(args[i]))!=null) { v=args[i+2];
    if (obj.style) { obj=obj.style; v=(v=='show')?'visible':(v=='hide')?'hidden':v; }
    obj.visibility=v; }
}
//-->

// get the true offset of anything on NS4, IE4/5 & NS6, even if it's in a table!
function getAbsX(elt) { return (elt.x) ? elt.x : getAbsPos(elt,"Left"); }
function getAbsY(elt) { return (elt.y) ? elt.y : getAbsPos(elt,"Top"); }
function getAbsPos(elt,which) {
 iPos = 0;
//	alert(elt.pageX());
 while (elt != null) {
  iPos += elt["offset" + which];
	if (which == "Left") {
		iPos += elt["clientLeft"];
//		iPos += elt["width"];
		}
	if (which == "Top") {
		iPos += elt["clientTop"];
//		iPos += elt["height"];
		}
  elt = elt.offsetParent;
 }

//	iPos = 0;
//	iPos = 'ABC';
// alert(iPos);
 return iPos;
}