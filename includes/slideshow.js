// Set slideShowSpeed (milliseconds)
var slideShowSpeed = 4000

// Duration of crossfade (seconds)
var crossFadeDuration = 3

var Pic = new Array() // don't touch this
// to add more images, just continue
// the pattern, adding to the array below

Pic[0] = '/includes/header-20101130/images/banner_cubworld-950x280.jpg';
Pic[1] = '/includes/header-20101130/images/banner_redford-950x280.jpg';
Pic[2] = '/includes/header-20101130/images/banner_toynk-950x280.jpg';
Pic[3] = '/includes/header-20101130/images/banner_froggysfog-950x280.jpg';

// =======================================
// do not edit anything below this line
// =======================================

var t
var j = 0
var p = Pic.length

var preLoad = new Array()
for (i = 0; i < p; i++){
   preLoad[i] = new Image()
   preLoad[i].src = Pic[i]
}

function runSlideShow(){
   if (document.all){
      document.images.SlideShow.style.filter="blendTrans(duration=2)"
      document.images.SlideShow.style.filter="blendTrans(duration=crossFadeDuration)"
      document.images.SlideShow.filters.blendTrans.Apply()      
   }
   document.images.SlideShow.src = preLoad[j].src
   if (document.all){
      document.images.SlideShow.filters.blendTrans.Play()
   }
   j = j + 1
   if (j > (p-1)) j=0
   t = setTimeout('runSlideShow()', slideShowSpeed)
}