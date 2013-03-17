import os,sys,json
import ss
import flask as f
app = f.Flask(__name__)

@app.route("/")
def index():
	return f.render_template('index.html')

@app.route("/process", methods=["POST","GET"])
def process():
	print f.request.form
	pointsS= f.request.form.get("points")
	if (pointsS):
		points = json.loads(pointsS)
		print pointsS
		print "----"
		print len(points)
		ss.LINES=[]
		skeleton = ss.SS()
		print skeleton
		skeleton.create(list(map(tuple,points))) #converting to right format
		size = ss.create_creases(skeleton)
		#size = (lenx,leny, minx,maxx, minx, maxx)
		print ss.LINES
		print len(ss.LINES)
		return json.dumps((size,ss.LINES))
		# print ss.LINES
		# print "/"
	return f.render_template('index.html')

if __name__ == "__main__":
	app.debug = True
	app.run(host='0.0.0.0')
