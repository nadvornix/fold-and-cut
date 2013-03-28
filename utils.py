from __future__ import division
import math,random,itertools

EPSILON=0.01 #TODO: try bigger epsilon on vertex tolerance (epsilon=~3)?

def randomColor():
	choices = list("0123456789ABCDEF")
	code = "".join([random.choice(choices) for i in range(6)])
	return "#"+code

def distance(x1,y1,x2,y2):
	return math.sqrt((x1-x2)**2+(y1-y2)**2)

def angle(Ax,Ay, Bx,By, Cx,Cy):
	"angle between lines A-B and B-C in radians (angle to right)"
	#relative coords (as if B was (0,0)):
	firstDx=float(Ax)-Bx
	firstDy=float(Ay)-By
	secondDx=float(Bx)-Cx
	secondDy=float(By)-Cy
	j = math.pi+math.atan2( firstDx*secondDy - secondDx*firstDy, firstDx*secondDx + firstDy*secondDy)
	return j

def pointLineProjection(Ax,Ay,Bx,By,Px,Py):
	"returns coordinates of projection (S) of point p to line --A---B--"
	Ax,Ay,Bx,By,Px,Py=float(Ax),float(Ay),float(Bx),float(By),float(Px),float(Py)
	k = ((By-Ay) * (Px-Ax) - (Bx-Ax) * (Py-Ay)) / ((By-Ay)**2 + (Bx-Ax)**2)
	Sx = Px - k * (By-Ay)
	Sy = Py + k * (Bx-Ax)
	return Sx, Sy

# Calc the gradient 'm' of a line between p1 and p2
def calculateGradient(p1, p2):
     # Ensure that the line is not vertical
   if (p1[0] != p2[0]):
       m = (p1[1] - p2[1]) / (p1[0] - p2[0])
       return m
   else:
       return None

# Calc the point 'b' where line crosses the Y axis
def calculateYAxisIntersect(p, m):
   return  p[1] - (m * p[0])

# Calc the point where two infinitely long lines (p1 to p2 and p3 to p4) intersect.
# Handle parallel lines and vertical lines (the later has infinate 'm').
# Returns a point tuple of points like this ((x,y),...)  or None
# In non parallel cases the tuple will contain just one point.
# For parallel lines that lay on top of one another the tuple will contain
# all four points of the two lines
def getIntersectPoint(p1x,p1y, p2x,p2y, p3x,p3y, p4x,p4y):
	p1=p1x,p1y
	p2=p2x,p2y
	p3=p3x,p3y
	p4=p4x,p4y

	m1 = calculateGradient(p1, p2)
	m2 = calculateGradient(p3, p4)

	# See if the the lines are parallel
	if (m1 != m2):
		# Not parallel

		# See if either line is vertical
		if (m1 is not None and m2 is not None):
			# Neither line vertical
			b1 = calculateYAxisIntersect(p1, m1)
			b2 = calculateYAxisIntersect(p3, m2)
			x = (b2 - b1) / (m1 - m2)
			y = (m1 * x) + b1
		else:
			# Line 1 is vertical so use line 2's values
			if (m1 is None):
				b2 = calculateYAxisIntersect(p3, m2)
				x = p1[0]
				y = (m2 * x) + b2
			# Line 2 is vertical so use line 1's values
			elif (m2 is None):
				b1 = calculateYAxisIntersect(p1, m1)
				x = p3[0]
				y = (m1 * x) + b1
			else:
				assert False

		return (x,y)
	else:
		# Parallel lines with same 'b' value must be the same line so they intersect
		# everywhere in this case we return the start and end points of both lines
		# the calculateIntersectPoint method will sort out which of these points
		# lays on both line segments
		b1, b2 = None, None # vertical lines have no b value
		if m1 is not None:
		   b1 = calculateYAxisIntersect(p1, m1)

		if m2 is not None:
		   b2 = calculateYAxisIntersect(p3, m2)

		# If these parallel lines lay on one another
		if b1 == b2:
		   return p1x,p1y
		else:
		   return None

def onSameLine(p1x,p1y, p2x,p2y, p3x,p3y, p4x,p4y):
	"if two (infinite) lines lay on one another"
	p1=p1x,p1y
	p2=p2x,p2y
	p3=p3x,p3y
	p4=p4x,p4y

	m1 = calculateGradient(p1, p2)
	m2 = calculateGradient(p3, p4)

	if (m1 == m2): #parallel
		b1, b2 = None, None # vertical lines have no b value
		if m1 is not None:
		   b1 = calculateYAxisIntersect(p1, m1)

		if m2 is not None:
		   b2 = calculateYAxisIntersect(p3, m2)

		# If these parallel lines lay on one another
		if b1 == b2:
		   return True
		else:
		   return False
	else:	# Not parallel
		return False

def nonequalOneFloat(thing, a,b):
	"returns float a or b that is not equal with thing"
	epsilon=0.001
	if abs(a-thing)<epsilon:
		return b
	elif abs(b-thing)<epsilon:
		return a
	else:
		return None

def onSameLineF(p1x,p1y, p2x,p2y, p3x,p3y, p4x,p4y):
	"if two (infinite) lines lay on one another"
	p1=p1x,p1y
	p2=p2x,p2y
	p3=p3x,p3y
	p4=p4x,p4y

	m1 = calculateGradient(p1, p2)
	m2 = calculateGradient(p3, p4)

	if (m1==None and m2==None) or (None not in (m1,m2) and abs(m1-m2) < 0.01): #parallel
		b1, b2 = None, None # vertical lines have no b value
		if m1 is not None:
		   b1 = calculateYAxisIntersect(p1, m1)

		if m2 is not None:
		   b2 = calculateYAxisIntersect(p3, m2)

		# If these parallel lines lay on one another
 #TODO: favorizuje cary blizko pocatku - ma u nich vetsi toleranci ##BUG
		if (b1==None and b2==None) or (abs(b1-b2) <0.01):
		   return True
		else:
		   return False
	else:	# Not parallel
		return False

def splitSegments(rawSegments, point):
	"assumption: segments and point lay all on one line"
	x,y=point
	newSegments=[]
	for type_,Ax,Ay,Bx,By in rawSegments:
		xmin,xmax=min(Ax,Bx),max(Ax,Bx)
		ymin,ymax=min(Ay,By),max(Ay,By)
		E=1. #Epsilon
		if xmin+E<=x<=xmax-E and ymin+E<=y<=ymax-E:	#point is on segment
			newSegments.append((type_,Ax,Ay,x,y))	#order is not important
			newSegments.append((type_,x,y,Bx,By))
		else:
			newSegments.append((type_,Ax,Ay,Bx,By)) #no change
	return newSegments

# def isLF(x,y):
# 	return 0.999*x <= y

def ccw(Ax,Ay,Bx,By,Cx,Cy):
	"Are A,B,C in counterclokwise direction?"
	return (Cy-Ay)*(Bx-Ax) > (By-Ay)*(Cx-Ax)

# def ccwF(Ax,Ay,Bx,By,Cx,Cy):
# 	"Are A,B,C in counterclokwise direction?"
# 	return (Cy-Ay)*(Bx-Ax) >= (By-Ay)*(Cx-Ax)-0.0001

def lineSegmentsIntersectionQ(p1x,p1y, p2x,p2y, p3x,p3y, p4x,p4y):
	## BUG: say false with overlaping 
	return (ccw(p1x,p1y,p3x,p3y,p4x,p4y) != ccw(p2x,p2y,p3x,p3y,p4x,p4y)) and \
				(ccw(p1x,p1y,p2x,p2y,p3x,p3y) != ccw(p1x,p1y,p2x,p2y,p4x,p4y))

# def lineSegmentsIntersectionQF(p1x,p1y, p2x,p2y, p3x,p3y, p4x,p4y):
# 	return (ccwF(p1x,p1y,p3x,p3y,p4x,p4y) != ccwF(p2x,p2y,p3x,p3y,p4x,p4y)) and \
# 				(ccwF(p1x,p1y,p2x,p2y,p3x,p3y) != ccwF(p1x,p1y,p2x,p2y,p4x,p4y))


def lineSegmentsIntersection(p1x,p1y, p2x,p2y, p3x,p3y, p4x,p4y):
	"""Intersection point of two line segments
	Assumes closed intervals"""
	if lineSegmentsIntersectionQ(p1x,p1y, p2x,p2y, p3x,p3y, p4x,p4y):
		return getIntersectPoint(p1x,p1y, p2x,p2y, p3x,p3y, p4x,p4y)
	else:
		return None

# def lineSegmentsIntersectionF(p1x,p1y, p2x,p2y, p3x,p3y, p4x,p4y):
# 	if lineSegmentsIntersectionQF(p1x,p1y, p2x,p2y, p3x,p3y, p4x,p4y):
# 		return getIntersectPoint(p1x,p1y, p2x,p2y, p3x,p3y, p4x,p4y)
# 	else:
# 		return None

def LIntersectionLS(lpAx,lpAy,lpBx,lpBy, lsAx,lsAy,lsBx,lsBy,epsilon=1):
	"intersecion of line and line segment"

	lsminX=min(lsAx,lsBx)
	lsmaxX=max(lsAx,lsBx)
	lsminY=min(lsAy,lsBy)
	lsmaxY=max(lsAy,lsBy)


	#as if it would be both infinite lines
	i=getIntersectPoint(lpAx,lpAy,lpBx,lpBy, lsAx,lsAy,lsBx,lsBy)

	if i:	#Not parallel lines
		#and then check if it is in bounding box
		ix,iy=i
		#TODO: this doesnt work for (almost) vertical/horizontal:!!!!
		if (lsminX-epsilon <= ix <= lsmaxX+epsilon) and (lsminY-epsilon <= iy <= lsmaxY+epsilon):
			#intersection is inside box defined by line segment
			return i

	return None

def isNearList(px,py,l,epsilon=1e-4):
	for x,y in l:
		if distance(px,py,x,y)<epsilon:
			return True
	return False

def isNearListPoints(px,py,l,epsilon=10e-3):
	"same as isNearList but in list are Point()s"
	for p in l:
		if distance(px,py,p.x,p.y)<epsilon:
			return True
	return False

def pointOnSegment(Ax,Ay,Bx,By, Px,Py, epsilonDistance=0.1):
	"say true/false if is point on segment"
	"if it is on corner then answer is True"
	"how far from line it can be is set by epsilonDistance"

	if distance(Ax,Ay,Bx,By)<0.5:
		return distance(Ax,Ay,Px,Py)<0.7

	ix,iy=pointLineProjection(Ax,Ay,Bx,By, Px,Py)
	dist = distance(ix,iy, Px,Py)
	
	if dist>epsilonDistance:
		return False
	#here it is iff it is close to infinite line
	minX,maxX= min(Ax,Bx),max(Ax,Bx)
	minY,maxY= min(Ay,By),max(Ay,By)

	#if it is in bounding box of segment:
	e=0.01 #epsilon for tolerance
	return minX-e<=ix<=maxX+e and minY-e<=iy<=maxY+e


def intersection(la,lb):
	"Set intersection for lists"
	return list(set(la).intersection(set(lb)))

def pairs(l, cyclic=False):
	"take list [1,2,3,4], and returns list of pairs: [(1,2), (2,3), (3,4)]"
	return nTuples(l,2,cyclic)
	# output=[]
	# for i,a in enumerate(l[:-1]):
	# 	output.append( (l[i],l[i+1]) )
	# if len(l)>=2 and cyclic:
	# 	output.append((l[-1],l[0]))
	# return output

def nTuples(l, n, cyclic=False):
	def nth(j):
		"returns nth element of l (cyclic if j>len(l))"
		return l[j%len(l)]
	def nthtuple(i):
		"returns ith tuple of result as list"
		t=[]
		for j in range(n):
			t.append(nth(i+j))
		return t

	if len(l)<n:
		return []
	output=[]

	if cyclic:
		outputLen=len(l)
	else:
		outputLen=len(l)-n+1
	for i in range(outputLen):
		output.append(tuple(nthtuple(i)))

	return output

def clockwisePolygon(polygon):
	""" determines if simple polygon (no crosing) in format [(x,y),...] 
	has its verticies in clockwise or counterclokwise order with coordinates interpreted
	as cartesian coordinates.
	Output: if polygon has no crossing then True->clockwise, False->counterclockwise"""

	a=0.0
	for u,v,w in nTuples(polygon, 3, cyclic=True): # measure all turns
		a+=math.pi-angle(u[0],u[1], v[0],v[1], w[0],w[1])
	return a>0

def avg(*l):
	try:
		return sum(l)/len(l)
	except ZeroDivisionError:
		return 0

def unique(l):
	return list(set(l))

def inflate_rectangle(minX, maxX, minY,maxY, ratio=0.2):
	"enlarge rectangle by ratio (same -> ratio=0.0)"
	lenX=maxX-minX
	lenY=maxY-minY

	dX=(lenX*ratio)/2
	dY=(lenY*ratio)/2

	return (minX-dX, maxX+dX, minY-dY,maxY+dY)


def clip(line, border):
	"clip single line"

	minX,maxX, minY, maxY = border
	Ax,Ay, Bx,By, color = line

	if (minX<=Ax<=maxX and minX<=Bx<=maxX and
		minY<=Ay<=maxY and minY<=By<=maxY):
		return line

	clipped = False

	i = lineSegmentsIntersection(Ax,Ay, Bx,By,  minX,minY, maxX,minY) # top _
	if i:
		clipped=True
		Ix,Iy=i
		if (Ay<Iy):
			Ax,Ay=Ix,Iy
		if (By<Iy):
			Bx,By=Ix,Iy

	i = lineSegmentsIntersection(Ax,Ay, Bx,By,  minX,maxY, maxX,maxY) # bottom _
	if i:
		clipped=True
		Ix,Iy=i
		if (Ay>Iy):
			Ax,Ay=Ix,Iy
		if (By>Iy):
			Bx,By=Ix,Iy

	i = lineSegmentsIntersection(Ax,Ay, Bx,By,  minX,minY, minX,maxY) # left |
	if i:
		clipped=True
		Ix,Iy=i
		if (Ax<Ix):
			Ax,Ay=Ix,Iy
		if (Bx<Ix):
			Bx,By=Ix,Iy
	
	i = lineSegmentsIntersection(Ax,Ay, Bx,By,  maxX,maxY, maxX,minY) # right |
	if i:
		clipped=True
		Ix,Iy=i
		if (Ax>Ix):
			Ax,Ay=Ix,Iy
		if (Bx>Ix):
			Bx,By=Ix,Iy
	if clipped:
		return Ax,Ay,Bx,By,color
	else:
		return None

def clip_lines(lines, border):
	" clip lines to right position and clip them "

	clipped = map(lambda l:clip(l, border), lines)
	return filter(lambda l:l != None, clipped)

def colorString2RGB(s):
	"converts '#5abbff' to something like (0.2, 0.5, 0.99609375)"
	def c2n(c):
		"converts single hex digit to 0.0-0.99609375"
		return int(c,16)/256.0
	if len(s)==4:
		s="#"+s[1]+s[1]+s[2]+s[2]+s[3]+s[3]
	return c2n(s[1:3]),c2n(s[3:5]),c2n(s[5:7])
