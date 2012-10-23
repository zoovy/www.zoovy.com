


var j = 1;  //starting point for rotator.
var p = 5; //number of divs to rotate through.
var zi = 1; //used to increment a zindex. keeps going up so slide that appears is always on top. this is to solve an IE issue.


function runSlideShow(){

		lastj = j;  //last value of j (1 - 4)
		j = j + 1;
		if (j > p){j=1}

		focusSlide = $('slide'+j);
//IE was not handling the 'appear' well because of zindex issue. setting only the zindex causes a 'flash' of the image before fading in
// so now it's hidden, zindex is changed, and then faded in. i heart IE.
		focusSlide.style.display = 'none';
		focusSlide.style.zIndex = zi;

		Effect.Appear(focusSlide, { duration:2, from:0.0, to:2.0 });
		
		zi++;
		t = setTimeout('runSlideShow()', 6000);
		
	}
	