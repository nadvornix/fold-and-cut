
//CONFIG:
var SNAP_DISTANCE=10

var examplePolygons = [	[ [0,0],[0,50],[50,0] ],
					[ [5,300],[300,300],[300,5],[5,5] ]
				];	//example polygons, must correspond (only) to index.html

////////// END OF CONFIG

var CANVAS = $('#canvasY')[0];
var WIDTH = CANVAS.width;
var HEIGHT = CANVAS.height;

// STATE==0: drawing
// STATE==1: polygon is closed and submiting and editing is enabled
var STATE=0;
var SELECTED=-1;


var content = CANVAS.getContext("2d");
var points = new Array();	//list of corners of polygon

///////////////////

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

function draw_circle(x,y,r,color){
	content.beginPath();
	content.arc(x, y, r, 0, 8, true);
	content.fillStyle = color;
    content.fill();
    content.stroke();
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
	if (state==0){
		button.disabled=true;
	}
	else if (state==1){
		button=$("#SentButton")[0];
		button.disabled=false;
	}
}


function redraw(){
	CANVAS.width = CANVAS.width;	//erase everything

	for (var x = 1; x < WIDTH; x += 50) {	//GRID
		draw_line(x,0, x,HEIGHT-5, "#CCCCCC");	//vertical
	}

	for (var y = 1; y < HEIGHT; y += 50) {
	  draw_line(0,y, WIDTH-5,y, "#CCCCCC");		//horizontal
	}

	var list_size = (points.length);
	if(list_size >= 1 && STATE==0) {
		draw_circle(points[0][0], points[0][1],5,"red")
	}	

	for(var i = 0; i < (list_size); i++) {	//draw polygon
		if(list_size > 1 && i>=1) {
			var point1 = points[(i-1)];
			var point2 = points[(i)];

			draw_line(point1[0], point1[1], point2[0], point2[1]);
			draw_circle(point2[0], point2[1], 2,"#000");	//little circle on knee:
		}
	}
	if (STATE==1){	//draw line from last to first
		draw_line(points[0][0], points[0][1], points[list_size-1][0], points[list_size-1][1]);
		draw_circle(points[0][0], points[0][1], 2,"#000");
	}

	for(var i = 0; i < (list_size); i++) {	//red circle on selected
		if(i==SELECTED){
			draw_circle(points[i][0], points[i][1], 5,"red");
		}
	}
}
 

///////////////////// LISTENERS:
canvasY.addEventListener('click', function(e) {
	var x;
    var y;
    if (e.pageX != undefined && e.pageY != undefined) {
    x = e.pageX;
    y = e.pageY;
    }
    else {
    x = e.clientX + document.body.scrollLeft +
            document.documentElement.scrollLeft;
    y = e.clientY + document.body.scrollTop +
            document.documentElement.scrollTop;
    }
    x -= CANVAS.offsetLeft;
	y -= CANVAS.offsetTop;
	

	if (STATE==0){
		for (var i = 1; i<(points.length); i++) {	// do not let making points near existing (except first)
			var point = points[i];
			if (distance(point[0],point[1], x,y)<SNAP_DISTANCE){
				return;	
			}
		}

		if (window.points.length>1){
			firstX = window.points[0][0];
			firstY = window.points[0][1];
			// alert(firstY+","+firstX)
			if (distance(x,y,firstX,firstY)<SNAP_DISTANCE){
				// alert(distance(x,y,firstX,firstY));
				setState(1);
				// window.points[(window.points.length)] = new Array(firstX, firstY);
				redraw();
				return;
			}
		}
		window.points[(window.points.length)] = new Array(x, y);
	}
	else if (STATE==1){
		SELECTED=-1;
		for (var i = (points.length)-1; i>=0  ; --i) {
			var point = points[i];
			if (distance(point[0],point[1], x,y)<SNAP_DISTANCE){
				SELECTED=i;
			}
		}
	}
	redraw();
});

canvasY.addEventListener('mousemove', function(e) {
	redraw();
	if (STATE==1){
		return;
	}
	
	var x=getMouseX(e);
    var y=getMouseY(e);
    var list_size = (points.length);

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
});

// SentButton.addEventListener('mousemove', function(e) {
// 	alert(1);
// 	});

SentButton.addEventListener("click", function (e){
	$.post("./process", { points: JSON.stringify(points) } ,function (data, textStatus, jqXHR){},"json");
});



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
}

loadbuttons=$(".loadExample");		// (automatic) adding actions to "load example X" links
for (var i=0; i<loadbuttons.length; i++){
	button = loadbuttons[i]
	button.addEventListener("click",  loadExample);
}

redraw();	//initial drawing
