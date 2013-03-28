import os,sys,json
import ss
from utils import clip_lines,inflate_rectangle,colorString2RGB
import flask as f
import random

from random import randint
app = f.Flask(__name__)

@app.route("/")
def index():
	return f.render_template('index.html')

@app.route("/process", methods=["POST","GET"])
def process():
	pointsS= f.request.form.get("points")
	if (pointsS):
		points = json.loads(pointsS)
		ss.LINES=[]
		skeleton = ss.SS()
		skeleton.create(points)

		size,lines = ss.create_creases(skeleton)
		ss.drawit(lines)

		contour = filter(lambda p: p.is_contour(), skeleton.points)
		minX=reduce(min, map(lambda p:p.x, contour))
		maxX=reduce(max, map(lambda p:p.x, contour))
		
		minY=reduce(min, map(lambda p:p.y, contour))
		maxY=reduce(max, map(lambda p:p.y, contour))

		# print minX,maxX, minY, maxY
		minX,maxX, minY, maxY = inflate_rectangle(minX,maxX, minY, maxY, 0.2)
		lines = clip_lines(lines, (minX,maxX, minY,maxY))

		return json.dumps(((minX,maxX, minY,maxY),lines))
	return f.render_template('index.html')

@app.route("/svg", methods=["GET","POST"])
def svg():
	"Note: Y-coordinate is not cartesian but like in images: bigger Y=> lower"
	import pysvg.structure
	import pysvg.builders
	import pysvg.text

	jsondata=f.request.form.get("data")
	if not jsondata:
		return "bad data"
	
	LINES = json.loads(jsondata)
	
	svg_document = pysvg.structure.Svg()

	shape_builder = pysvg.builders.ShapeBuilder()

	minX=reduce(min, map(lambda p: min(p[0],p[2]),LINES))
	minY=reduce(min, map(lambda p: min(p[1],p[3]),LINES))

	for Ax,Ay, Bx,By,color in LINES:
		svg_document.addElement(shape_builder.createLine(Ax-minX, Ay-minY, Bx-minX, By-minY, strokewidth=2, stroke=color))

	response = f.make_response(svg_document.getXML())
	response.headers['Content-Type']  = "image/svg+xml"
	response.headers['Content-Disposition']  = "attachment; filename=foldandcut.svg"
	return response


@app.route("/pdf", methods=["GET","POST"])
def pdf():
	from reportlab.pdfgen import canvas

	jsondata=f.request.form.get("data")
	if not jsondata:
		return "bad data"
	

	LINES = json.loads(jsondata)
	
	minX=reduce(min, map(lambda p: min(p[0],p[2]),LINES))
	maxX=reduce(max, map(lambda p: max(p[0],p[0]),LINES))
	minY=reduce(min, map(lambda p: min(p[1],p[3]),LINES))
	maxY=reduce(max, map(lambda p: max(p[1],p[3]),LINES))
	lenX=maxX-minX
	lenY=maxY-minY

	c = canvas.Canvas("foldandcut.pdf", pagesize=(lenX, lenY))

	for Ax,Ay, Bx,By,color in LINES:
		r,g,b = colorString2RGB(color)
		c.setStrokeColorRGB(r, g, b)

		c.line(Ax-minX, -Ay+maxY, Bx-minX, -By+maxY)
		# , strokewidth=2, stroke=color)
		# c.line(0,0,50,50)

	response = f.make_response(c.getpdfdata())
	response.headers['Content-Type']  = "application/pdf "
	response.headers['Content-Disposition']  = "attachment; filename=foldandcut.pdf"
	return response


if __name__ == "__main__":
	app.debug = True
	app.run(host='0.0.0.0')
