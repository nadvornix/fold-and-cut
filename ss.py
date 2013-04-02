from __future__ import division

import sys


from classes import *

from utils import *

"""
TODO:
-
"""

"""
NOTES:
- functions with suffix F are fuzzy.
"""

# polygon = [(-100, -100),
# 			(0, -1200),
# 			(100, -100),
# 			(1200,0),
# 			(100,100),
# 			(0,1200),
# 			(-100,100),
# 			(-600,600),
# 			(-1200,0)]

# polygon = [
# 			(0, 1000),
# 			(0,0),
# 			(1000, 0),
# 			(1000, 1000),
# 			]

# polygon = [(500, 0),
# 			(1000, 500),
# 			(500, 1000),
# 			(0,500),]

# polygon = [(1010, 0),
# 			(10,0),
# 			(0, 1010),
# 			(1000, 990),]


# POINTS=[]	# list of all points and intersections including points made for perpendiculars
# LINES=[]


# def die():

# 	sys.exit()


if __name__=="__main__":
	# polygon = [ 
	# 		(-1022,-100),
	# 		(-200,-5),
	# 		(20,233),
	# 		(300,200),
	# 		(500,0),
	# 		(1000,0),
	# 		(1000,1000),
	# 		(-1000,1000),
	# ]

	polygon = [[140, 311.7691453623979], [180, 311.7691453623979],
	 [200, 277.12812921102034], [240, 277.12812921102034], 
	 [260, 311.7691453623979], [300, 311.7691453623979], 
	 [280, 277.12812921102034], [320, 277.12812921102034], 
	 [340, 242.4871130596428], [380, 242.4871130596428], 
	 [360, 207.84609690826525], [320, 207.84609690826525], 
	 [300, 242.4871130596428], [260, 173.20508075688772], 
	 [180, 173.20508075688772], [120, 277.12812921102034], 
	 [160, 277.12812921102034]]


	s= SS()
	s.create(polygon)
	s.create_creases()

	
	# LINES = clip_lines(LINES, (minX,maxX, minY,maxY))



	done=[]
	for point in s.points:	#Debug: draw this graph
		done.append(point)
		for n in point.ss:
			if n not in done:
				s.drawline(n.x,n.y, point.x, point.y, color="#0F0")
		for n in point.contour:
			if n not in done:
				s.drawline(n.x,n.y, point.x, point.y,color="#F00")

	s.drawit()
