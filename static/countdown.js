function countdown(count) {

var demo = document.getElementById("projectionScreen"),
	  countDown = document.getElementById("counter"),
    masterTimeline = new TimelineMax({delay:0.1})

TweenMax.set(demo, {transformOrigin:"center", autoAlpha:1, xPercent:-50, yPercent:-50});
TweenMax.set("#rightLeg", {transformOrigin:"0% 0%", rotation:30, x:5});
TweenMax.set("#leftLeg", {transformOrigin:"100% 0%", rotation:-30, x:-5});
TweenMax.set("#screenBars, #shadow", {transformOrigin:"50% 50%"});
TweenMax.set("#rotator, #supports", {transformOrigin:"50% 100%"});
TweenMax.set("#shadow", {scaleX:0, autoAlpha:0});
TweenMax.set("#screen", {transformOrigin:"50% 0%", scaleY:0});
TweenMax.set("#centerShadowBottom, #movieClip",{autoAlpha:0, transformOrigin:"center"});




// start the countdown with the count variable value
countDown.textContent = count;



// create the projection screen animation
function projector() {
var tl = new TimelineMax();
tl.from("#supports", 0.6, {scaleY:0, ease:Expo.easeInOut})
  .add("legExtension")
  .to("#rightLeg", 0.4, {rotation:0, x:0, ease:Power2.easeOut}, "legExtension")
  .to("#leftLeg", 0.4, {rotation:0, x:0, ease:Power2.easeOut},"legExtension")
  .from("#screenBars",0.6,{scaleX:0, ease:Expo.easeOut}, "legExtension")
  .to("#centerShadowBottom",0.3,{autoAlpha:1}, "legExtension")
  .add("screenDown","-=0.25")
  .to("#screen", 0.6, {scaleY:1, ease:Power4.easeOut},"screenDown")
  .from("#screenBottom, #centerShadowBottom", 0.6, {y:-569, ease:Power4.easeOut},"screenDown")
  .to("#shadow", 0.6, {scaleX:1, autoAlpha:.2, ease:Power4.easeOut},"screenDown")
  .to("#film", 1.5, {autoAlpha:1});
return tl;
}

// create the countdown animation
function theCount() {
var tl = new TimelineMax({repeat:count-1, onRepeat:changeIt});
tl.to("#rotator", 1, {rotation:360, ease:Linear.easeNone})
  .fromTo( ".big", 1 , {drawSVG:'0 0%'}, {drawSVG:'0% 100%', ease:Linear.easeNone},0 );
return tl;
}

// fade out the countdown and show GreenSock info
function movie() {
var tl = new TimelineMax();
tl.to("#film", 0.2, {autoAlpha:0})
  .set("#movieClip", {autoAlpha:1})
  .add("textEnter")
  .from("#line1", 1, {x:-700, ease:Back.easeOut}, "textEnter")
  .from("#line2", 1, {x:700, ease:Back.easeOut}, "textEnter")
  .from("#sock", 0.75, {y:260, ease:Power3.easeOut}, "textEnter+=0.5");
return tl;
}

// change the countdown on each repeat of the film leader animation
function changeIt() {
	count--;
	countDown.textContent = count;
}



/* ---------------------------------------------------------------
	 Correctly size/resize and position the SVG
	---------------------------------------------------------------*/

function sizeAll() {
	/*var h = window.innerHeight,
		  w = window.innerWidth;

	if ( w > h) {
		TweenMax.set(demo, {height:h, width:h});
		}

	else {
		TweenMax.set(demo, {height:w, width:w});

		}
		*/

		TweenMax.set(demo, {height:"150px", width:"150px"});
}

$(window).resize(sizeAll);

sizeAll();

// master timeline with all sections

masterTimeline
	.add( projector() )
	.add( theCount(),"-=1.5" )
	.add( movie() );


}
