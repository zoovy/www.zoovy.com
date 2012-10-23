
/******************************************
* DHTML Ad Box (By Matt Gabbert at http://www.nolag.com)
* Visit http://www.dynamicdrive.com/ for full script
* This notice must stay intact for use
******************************************/

adTime=10;  // seconds ad reminder is shown
chanceAd=1; // ad will be shown 1 in X times (put 1 for everytime)

var ns=(document.layers);
var ie=(document.all);
var w3=(document.getElementById && !ie);
var calunit=ns? "" : "px"
adCount=0;
function initAd(){
	if(!ns && !ie && !w3) return;
	if(ie)		adDiv=eval('document.all.mandatoryDiv.style');
	else if(ns)	adDiv=eval('document.layers["mandatoryDiv"]');
	else if(w3)	adDiv=eval('document.getElementById("mandatoryDiv").style');
	randAd=Math.ceil(Math.random()*chanceAd);
        if (ie||w3)
        adDiv.visibility="visible";
        else
        adDiv.visibility ="show";
	if(randAd==1) showAd();
}
function showAd(){
if(adCount<adTime*10){adCount+=1;
	if (ie){documentWidth  =truebody().offsetWidth/2+truebody().scrollLeft-20;
	documentHeight =truebody().offsetHeight/2+truebody().scrollTop-20;}	
	else if (ns){documentWidth=window.innerWidth/2+window.pageXOffset-20;
	documentHeight=window.innerHeight/2+window.pageYOffset-20;} 
	else if (w3){documentWidth=self.innerWidth/2+window.pageXOffset-20;
	documentHeight=self.innerHeight/2+window.pageYOffset-20;} 
	adDiv.left=documentWidth-200+calunit;adDiv.top =documentHeight-200+calunit;
	setTimeout("showAd()",100);}else closeAd();
}
function closeAd(){
if (ie||w3)
adDiv.display="none";
else
adDiv.visibility ="hide";
}

function truebody(){
return (document.compatMode && document.compatMode!="BackCompat")? document.documentElement : document.body
}

onload=initAd;
