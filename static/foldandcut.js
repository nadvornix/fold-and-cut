
//CONFIG:
var SNAP_DISTANCE=10;

var CELLX=20; // size of half of side of triangle grid [half is from hist. reasons :-)]

var examplePolygons = [	
//six pointed star
	[[160, 277.12812921102034], [200, 207.84609690826525], 
	 [160, 138.56406460551017], [240, 138.56406460551017], 
	 [280, 69.28203230275508], [320, 138.56406460551017], 
	 [400, 138.56406460551017], [360, 207.84609690826525], 
	 [400, 277.12812921102034], [320, 277.12812921102034], 
	 [280, 346.41016151377545], [240, 277.12812921102034]],
//turtle:
	[[140, 311.7691453623979], [180, 311.7691453623979],
	 [200, 277.12812921102034], [240, 277.12812921102034], 
	 [260, 311.7691453623979], [300, 311.7691453623979], 
	 [280, 277.12812921102034], [320, 277.12812921102034], 
	 [340, 242.4871130596428], [380, 242.4871130596428], 
	 [360, 207.84609690826525], [320, 207.84609690826525], 
	 [300, 242.4871130596428], [260, 173.20508075688772], 
	 [180, 173.20508075688772], [120, 277.12812921102034], 
	 [160, 277.12812921102034]],
					
				];	//example polygons, must correspond (only) to index.html

////////// END OF CONFIG
var sqrt3 = Math.sqrt(3);

var CANVAS = $('#canvasY')[0];
var WIDTH = CANVAS.width;
var HEIGHT = CANVAS.height;


// STATE==0: drawing
// STATE==1: polygon is closed and submiting and editing is enabled
// STATE==2: drawing is disabled and is displayed result
var STATE=0;
var SELECTED=-1;
var DRAGGING=-1;	//Are we moving with some point. -1 if not, otherwise index of point

var content = CANVAS.getContext("2d");
var points = new Array();	//list of corners of polygon
var pointsBak = new Array();	//copy of ^, used when needed recover from crossing
var RESULT=undefined
///////////////////

function round_to_multiple(v, base){
	// returns integer n so that n*base is closest possible to v
	return Math.round(v/base); 
}

function triangle_snap(x,y) {
	// returns closest [x,y] from triangular grid x,y from argument
	var yn=round_to_multiple(y/CELLX,sqrt3);
	if (yn%2==0){
		var newx=round_to_multiple(x/CELLX,2)*2;
	}
 	else{
		var newx=round_to_multiple(x/CELLX-1, 2)*2 + 1;
	}
	return [CELLX*newx,CELLX*yn*sqrt3];
}


function distance(x1,y1,x2,y2){
	return Math.sqrt((x2-x1)*(x2-x1) + (y2-y1)*(y2-y1));
}

function draw_line(x1,y1,x2,y2, color){
	color = typeof color !== 'undefined' ? color : "#000000";
	content.beginPath();

	//line:
	content.moveTo(x1, y1);
	content.lineTo(x2, y2);
	content.strokeStyle = color;
	
	content.stroke();
}

function draw_circle(x,y,r,color, border){
	border = typeof border !== 'undefined' ? border : true;
	content.beginPath();
	content.arc(x, y, r, 0, 8, true);
	content.fillStyle = color;
	if (! border){
		content.strokeStyle="#FFF";
	}
    content.fill();
    content.stroke();
}

// function line_intersection(p0_x, p0_y, p1_x, p1_y, p2_x, p2_y, p3_x, p3_y) 
// {		//if lines (both given by two points) A1-A2 and B1-B2 intersect
// 	var s1_x, s1_y, s2_x, s2_y;
// 	s1_x = p1_x - p0_x;
// 	s1_y = p1_y - p0_y;
// 	s2_x = p3_x - p2_x;
// 	s2_y = p3_y - p2_y;

// 	var s, t;
// 	s = (-s1_y * (p0_x - p2_x) + s1_x * (p0_y - p2_y)) / (-s2_x * s1_y + s1_x * s2_y);
// 	t = ( s2_x * (p0_y - p2_y) - s2_y * (p0_x - p2_x)) / (-s2_x * s1_y + s1_x * s2_y);

// 	if (s > 0 && s < 1 && t > 0 && t < 1) { // Collision detected 
// 		return true;
// 	}else {
// 		return false;
// 	}
// }

function max (a,b) {
	if (a>b){
		return a;
	}
	else {
		return b;
	}
}

function min (a,b) {
	if (a<b){
		return a;
	}
	else {
		return b;
	}
}

function crossp(a1,a2, b1,b2){
	//cross product (a1,a2) x (b1,b2)
	return a1*b2 - b1*a2;
}

function different_signs(a,b){
	return a*b<=0;
}

function direction(Ax,Ay,Bx,By,Cx,Cy){
	return crossp(Cx-Ax, Cy-Ay, Bx-Ax, By-Ay);
}

function onSegment(Ax,Ay,Bx,By,Cx,Cy, cornerOK){
	//borderOK means that touchinch by corner points are ok
	if (cornerOK){
		return 	min(Ax, Bx)<Cx && Cx<max(Ax, Bx) &&
				min(Ay, By)<Cy && Cy<max(Ay, By);
	}
	else {
		return 	min(Ax, Bx)<=Cx && Cx<=max(Ax, Bx) &&
				min(Ay, By)<=Cy && Cy<=max(Ay, By);
	}	
}


function line_intersection(Ax, Ay, Bx, By, Cx, Cy, Dx, Dy, cornerOK){
	d1=direction(Cx, Cy, Dx, Dy, Ax, Ay);
	d2=direction(Cx, Cy, Dx, Dy, Bx, By);
	d3=direction(Ax, Ay, Bx, By, Cx, Cy);
	d4=direction(Ax, Ay, Bx, By, Dx, Dy);

	if (((d1>0 && d2<0) || (d1<0 && d2>0)) &&
		((d3>0 && d4<0) || (d3<0 && d4>0))) {
		return true;
	}
	else if (d1==0 && onSegment(Cx,Cy, Dx, Dy, Ax, Ay, cornerOK)){
		return true;
	}
	else if (d2==0 && onSegment(Cx, Cy, Dx, Dy, Bx, By, cornerOK)){
		return true;
	}
	else if (d3==0 && onSegment(Ax, Ay, Bx, By, Cx, Cy, cornerOK)){
		return true;
	}
	else if (d4==0 && onSegment(Ax, Ay, Bx, By, Dx, Dy, cornerOK)){
		return true;
	}

	return false;
}


// function line_intersection(Ax, Ay, Bx, By, Cx, Cy, Dx, Dy){
// 	//returns whether A-B and C-D insersect
// 	// is "aggressive" - says true even if are only touching
// 	if (max(Ax,Bx)>=min(Cx, Dx) && 
// 		max(Cx,Dx)>=min(Ax, Bx) && 
// 		max(Ay,By)>=min(Cy, Dy) && 
// 		max(Cy,Dy)>=min(Ay, By) ){	//if rectangles intersects

// 		return different_signs(	crossp(Cx-Ax, Cy-Ay, Bx-Ax, By-Ay), 
// 								crossp(Dx-Ax, Dy-Ay, Bx-Ax, By-Ay))

// 	}

// 		return false;
// }

function sqruare(x) { return x * x }
function distanceSquared(x1,y1, x2, y2) { return sqruare(x1 - x2) + sqruare(y1- y2) }
function distToSegmentSquared(x,y, Ax,Ay, Bx,By) {
  var l2 = distanceSquared(Ax,Ay, Bx,By);
  if (l2 == 0) return distanceSquared(x,y, Ax,By);
  var t = ((x - Ax) * (Bx - Ax) + (y - Ay) * (By - Ay)) / l2;
  if (t < 0) return distanceSquared(x,y, Ax,Ay);
  if (t > 1) return distanceSquared(x,y, Bx,By);
  return distanceSquared(x,y, Ax + t * (Bx - Ax),
                     Ay + t * (By - Ay));
}
function distToSegment(x,y, Ax,Ay, Bx,By) { 
	return Math.sqrt(distToSegmentSquared(x,y, Ax,Ay, Bx,By));
}

function getMouseX(e){	//X coordinate of mouse (relative in canvas)
	var x;
    if (e.pageX != undefined ) {
	    x = e.pageX;
    }
    else {
	    x = e.clientX + document.body.scrollLeft + document.documentElement.scrollLeft;
    }
    return x-CANVAS.offsetLeft;
}
function getMouseY(e){
	var y;
	if (e.pageY != undefined) {
	    y = e.pageY;
    }
    else {
	    y = e.clientY + document.body.scrollTop + document.documentElement.scrollTop;
    }

	return y-CANVAS.offsetTop;
}

function setState(state){
	STATE=state;
	button=$("#SentButton")[0];
	if (state==1){
		button.disabled=false;
	}
	else {
		button.disabled=true;
	}
	$("#removePointButton")[0].disabled=true;
}

function isCrossing(ps, open){	//check if there is some crossing in polygon with verticies ps
	//open: is polygon open/closed?
	console.log("isc:");
	console.log(ps);
	open = typeof open !== 'undefined' ? open : false; //Open is by default false
	if (open){
		start=1;
	}
	else {
		start=0;
	}

	for (var i = start; i<(ps.length); i++) {
		for (var j=start; j<ps.length; j++){
			if (j!=i){
				if (i==0){
					pointA1= ps[ps.length-1]
					pointA2= ps[0]
				}
				else{
					pointA1= ps[i-1]
					pointA2= ps[i]
				}

				cycDist=i-j;	//cyclic distance from one segment to another [how far is i ahead of j]
				if (cycDist<0){
					cycDist+=ps.length;
				}

				pA1x = pointA1[0];
				pA1y = pointA1[1];
				pA2x = pointA2[0];
				pA2y = pointA2[1];

				if (j==0){
					pointB1= ps[ps.length-1];
					pointB2= ps[0];
				}
				else{
					pointB1= ps[j-1];
					pointB2= ps[j];
				}				
				pB1x = pointB1[0];
				pB1y = pointB1[1];
				pB2x = pointB2[0];
				pB2y = pointB2[1];

				epsilon =0.5;  //points has to be at least epsilonpixels from segments
				if (cycDist!=ps.length-1){
					if (distToSegment(pB1x,pB1y, pA1x, pA1y, pA2x, pA2y)<epsilon){
						return true;
					}
				}
				if (cycDist!=1){
					if (distToSegment(pB2x,pB2y, pA1x, pA1y, pA2x, pA2y)<epsilon){
						return true;
					}
				}

				cornerOK=true;
				if (line_intersection(pA1x, pA1y, pA2x, pA2y,  pB1x,pB1y,pB2x,pB2y, cornerOK)){
					return true;
				}
			}
		}
	}
	return false;
}

function selectPoint(index){
	SELECTED=index;
	$("#removePointButton")[0].disabled=false;
}
function unselectPoint(){
	SELECTED=-1;
	$("#removePointButton")[0].disabled=true;
}


function redraw(){
	CANVAS.width = CANVAS.width;	//erase everything

	// RECT grid:
	// for (var x = 1; x < WIDTH; x += 50) {	//GRID
	// 	draw_line(x,0, x,HEIGHT-5, "#CCCCCC");	//vertical
	// }

	// for (var y = 1; y < HEIGHT; y += 50) {
	//   draw_line(0,y, WIDTH-5,y, "#CCCCCC");		//horizontal
	// }

	////// TRIANGULAR grid:
	// for (var x=-CELLX*100; x<WIDTH; x+=2*CELLX){ //  this shape: \
	// 	draw_line(x, 0, x+(HEIGHT*(1/sqrt3)), HEIGHT, "#CCC");
	// }

	// for (var x=0; x<WIDTH*1.9; x+=2*CELLX){ //  this shape: /
	// 	draw_line(x, 0, x-HEIGHT*(1/sqrt3),HEIGHT, "#CCC");
	// }

	// for (var y=0; y<HEIGHT; y+=CELLX*sqrt3){	// 		this shape: -
	// 	draw_line(0, y, WIDTH, y, "#CCC");
	// }

	if (STATE==0 || STATE==1){
		rowheight=CELLX*sqrt3/2;
		for (var yn=0; yn<HEIGHT/rowheight; yn+=1){
			if (yn%2==1){
				start=CELLX;
			}
			else{
				start=0;
			}
			y=yn*CELLX*sqrt3;

			for (var x=start; x<=WIDTH; x+=2*CELLX){
				draw_circle(x, y, 3, "#AAA", false);
			}
		}
	}

	var list_size = (points.length);

	if (STATE==0 || STATE==1){
		for(var i = 0; i < (list_size); i++) {	//draw polygon
			if(list_size > 1 && i>=1) {
				var point1 = points[(i-1)];
				var point2 = points[(i)];

				draw_line(point1[0], point1[1], point2[0], point2[1]);
				draw_circle(point2[0], point2[1], 2,"#000");	//little circle on knee:
			}
		}
	}
	if (STATE==1){	//draw line from last to first
		draw_line(points[0][0], points[0][1], points[list_size-1][0], points[list_size-1][1]);
		draw_circle(points[0][0], points[0][1], 2,"#000");
	}
	if (STATE==2){
		for (var i=0; i<RESULT.length; i++){
			var segment=RESULT[i];
			draw_line(segment[0], segment[1], segment[2], segment[3], segment[4]);
		}
	}

	if(list_size >= 1 && STATE==0) {	//red point at beggining
		draw_circle(points[0][0], points[0][1],5,"red", false)
	}
	if (STATE==1 && SELECTED!=-1){
		for(var i = 0; i < (list_size); i++) {	//red circle on selected
			if(i==SELECTED){
				draw_circle(points[i][0], points[i][1], 5,"red", false);
			}
		}
	}

	if (STATE==0){
		if (window.points.length>0){
			$("#removePointButton")[0].disabled=false;
		}
		else {
			$("#removePointButton")[0].disabled=true;
		}
	}
}
 

///////////////////// LISTENERS:

canvasY.addEventListener('mousemove', function(e) {
    var snapped=triangle_snap(getMouseX(e),getMouseY(e));
   
    var x=snapped[0];
    var y=snapped[1];

    var list_size = (points.length);

	redraw();

	if (STATE==1 && DRAGGING!=-1){	//Draging point around
		points[DRAGGING][0]=x;
		points[DRAGGING][1]=y;
	}
	else if (STATE==0){
	    //snaping:
		if(list_size >= 1) {
			firstX = window.points[0][0];
			firstY = window.points[0][1];
			if (distance(x,y,firstX,firstY)<SNAP_DISTANCE){
				x=firstX;
				y=firstY;
			}
			var bod = points[(list_size-1)];
			draw_line(bod[0], bod[1], x,y);
		}
		else {
			draw_circle(x, y,5,"red")
		}
	}

});

$('#canvasY').mousedown(function(e) {
    var x=getMouseX(e);
    var y=getMouseY(e);

	// redraw();
    if (!isCrossing(points)){
		for (var i=0; i<points.length; i++){
			pointsBak[i]=points[i].slice(0);
		}
    }

 	if (STATE==1){
		for (var i = (points.length)-1; i>=0; --i) {	//START DRAGGING
			var point = points[i];
			if (distance(point[0],point[1], x,y) < SNAP_DISTANCE){
				DRAGGING=i;
				selectPoint(i);
				return;
			}
		}
 
		snapped=triangle_snap(x,y);
		console.log(snapped);
		console.log(points);
		for (var i = 0; i<(points.length); i++) {
			if (i==0){
				p1 = points[0];
				p2 = points[points.length-1];
			}
			else {
				p1 = points[i];
				p2 = points[i-1];
			}

			if (distToSegment(x,y,p1[0],p1[1],p2[0],p2[1])<SNAP_DISTANCE){	//adding new point
				newPoints = points.slice(0,i); //adding to right place
				newPoints.push(snapped);
				newPoints= newPoints.concat(points.slice(i, points.length)); 
				console.log("newpoints:");
				console.log(newPoints);
				console.log(points);
				if (!isCrossing(newPoints)){
					points=newPoints;
					selectPoint(i);
					break;
				}
				console.log("done");
			}
		}
	}
	// redraw();
})

$('#canvasY').mouseup(function(e) {
	snapped=triangle_snap(getMouseX(e),getMouseY(e));
  	var x=snapped[0];
  	var y=snapped[1];
	// redraw();

	if (STATE==0){	//adding new point when first drawing
		for (var i = 1; i<(points.length); i++) {	// do not let making points at existing (except first)
			var point = points[i];
			if (distance(point[0],point[1], x,y)<SNAP_DISTANCE){
				return;	
			}
		}

		if (window.points.length>2){
			firstX = window.points[0][0];
			firstY = window.points[0][1];
			if (distance(x,y,firstX,firstY)<SNAP_DISTANCE && !isCrossing(points, false)) {	// closing polygon - last edge
				setState(1);
				redraw();
				return;
			}
		}

		points.push(new Array(snapped[0], snapped[1]));
		if (isCrossing(points, true)){
			points.pop(); //revert adding last point if it causes crossing
			return;
		}
		
		// new Array(x, y);
	}
	else if (STATE==1){
		unselectPoint();
		for (var i = 0; i<points.length  ; i++) {
			var point = points[i];
			if (distance(point[0],point[1], x, y)<SNAP_DISTANCE){
				selectPoint(i);
			}
		}

		if (DRAGGING!=-1){
			DRAGGING=-1;
			if (isCrossing(points)){
				for (var i=0; i<points.length; i++){
					points[i]=pointsBak[i];
				}
			}
		}
	}

	redraw();
})


//////////////// 	NON-CANVAS
SentButton.addEventListener("click", function (e){	//SUBMIT button
	$.post("./process", { points: JSON.stringify(points) } , function (data, textStatus, jqXHR){
		var size=data[0];		//(lenx,leny, minx,maxx, minx, maxx)
		var lenx = size[0];
		var leny = size[1];
		var minx = size[2];
		var maxx = size[3];
		var miny = size[4];
		var maxy = size[5];

		var factorx=CANVAS.width/lenx;
		var factory=CANVAS.height/leny;
		var factor=Math.min(factorx,factory)
		RESULT=new Array()
		for (var i=0; i<data[1].length; i++){
			x1=data[1][i][0];
			y1=data[1][i][1];
			x2=data[1][i][2];
			y2=data[1][i][3];
			color=data[1][i][4];
			RESULT[i]=[
						(x1-minx)*factor,
						(y1-miny)*factor,
						(x2-minx)*factor,
						(y2-miny)*factor,
						color,
						];
		}

		setState(2);
		redraw();
	},"json");
});


function removePoint(e){
	var pbak  = points.slice();
	
	if (STATE==1 && SELECTED!=-1 && points.length>3){
		points.splice(SELECTED, 1); 
		unselectPoint();
	}
	else if (STATE==0){
		points=points.slice(0, points.length-1);
	}
	if (isCrossing(points,true)){
		points=pbak;
	}
	redraw();
}
removePointButton.addEventListener("click", removePoint);//remove Point button

function loadExample(e){
	link = e.target;
	number = parseInt(link.getAttribute("num"));

	setState(1);
	if (points.length>1){
		var r=confirm("Loading example will delete current drawing. Continue?");
		if (r==false)
		{
			return;
		}
	}
	points = examplePolygons[number];
	redraw();
}

loadbuttons=$(".loadExample");		// (automatic) adding actions to "load example X" links
for (var i=0; i<loadbuttons.length; i++){
	button = loadbuttons[i]
	button.addEventListener("click",  loadExample);
}

redraw();	//initial drawing
