import os,sys,json

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
		print points
		print len(points)
		
	return f.render_template('index.html')

if __name__ == "__main__":
	app.debug = True
	app.run(host='0.0.0.0')
