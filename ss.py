from __future__ import division

import sys

import Image,ImageDraw,ImageFont

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

MAXDEPTH=20
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


POINTS=[]	# list of all points and intersections including points made for perpendiculars
LINES=[]
font = ImageFont.truetype("g.ttf", 50)


def die():
	print "die: saving output"
	img.save("test.png")
	sys.exit()


def drawPoint(x,y,r=10,color="#FF00FF"):
	pass
	# draw.ellipse((int(x-minx-r), int(y-miny-r), int(x-minx+r), int(y-miny+r)),fill=color)

def drawline( x1,y1, x2,y2, color="#00FF00"):
	# draw.line((int(x1-minx), int(y1-miny), int(x2-minx), int(y2-miny)), fill=color)
	# LINES.append( (x1,y1, x2,y2, color))
	LINES.append( (x1,y1,x2,y2,color))


def drawtext(x,y,text):
	pass
	# draw.text((int(x-minx),int(y-miny)),text,fill=(0,0,0),font=font)


def getPath(point,n,direction=0):
	"""go still left in direction point->n.
	direction=0 means go as left as you can, direction=-1 means right"""
	vertices=[n]

	try:
		next = n.forks(point, all=True)[direction]#most left
		last=n
		while not (next in vertices):
			vertices.append(next)
			tmp=next
			try:
				next = next.forks(last, all=True)[direction]
			except IndexError:
				next=last
			last=tmp
	except IndexError:
		pass 	# first node is last
	return vertices

def getFace(point,n):
	p1=getPath(point,n,direction=0)
	p2=getPath(n,point,direction=-1)

	for v in p2:
		if v not in p1:
			p1.insert(0,v)	#prepend
	openFace = p1[0]==p2[-1]
	return p1,openFace

def getContour(face):
	for v in face:
		for c in v.contour:
			if (v in c.contour) and (c in face):
				return (c,v)
	return None

def isContourE(e1,e2):
	return e2 in e1.contour and e1 in e2.contour

def sameEdge(e1,e2):
	"If e1 and e2 [edges in (Point,Point) format] are same (regardless of order)"
	(e1A,e1B),(e2A,e2B)=e1,e2
	return ((e1A,e1B)==(e2A,e2B)) or ( (e1A,e1B)==(e2B, e2A) )

def isEdgeIn(e,l):
	"if edge e is in list l [edges are in (Point,Point) format]"
	for e2 in l:
		if sameEdge(e,e2):
			return True
	return False

def inBox(x,y):
	return minx<=x<=maxx and miny<=y<=maxy

def otherFace(face,edge):
	"around `edge` are two faces. This returns that distinct from `face`"
	eA,eB=edge
	f1,f1open=getFace(eA,eB)
	f2,f2open=getFace(eB,eA)
	f1l=len(intersection(face, f1))
	f2l=len(intersection(face, f2))
	if f1l==2:
		return f1,f1open
	elif f2l==2:
		return f2,f2open
	else:
		assert False


def drawPerpendicularContour(startP, face,openFace, adjacentE, depth=0,last=None):
	"""
	parameters are same as in drawPerpendicularSS
	"""
	print "C", "~"*100
	print "startP: ",startP
	print "face: ",face
	print "openFace",openFace
	print "adjacentE: ",adjacentE
	print "depth",depth
	print "last",last

	POINTS.append(startP)

	startX,startY=startP
	# drawPoint(startX,startY,color="#F00")

	if len(adjacentE)!=1:  #just test if params are OK
		print len(adjacentE)
		print adjacentE
		assert False 	#this has to be one edge, not more

	contour = adjacentE[0]
	cA,cB=contour
	cAx, cAy= cA.x, cA.y
	cBx, cBy= cB.x, cB.y
	dx=cBx-cAx
	dy=cBy-cAy

	point2x=startX-dy 	#auxiliary point - through this point will go perpendicular
	point2y=startY+dx

	# drawline(startX,startY,  startX-dy*0.1,startY+dx*0.1,color="#F00")

	bestEdge=None
	bestIntersection=None
	bestDistance=float("inf")

	intersectA = pointLineProjection(cAx,cAy,cBx,cBy,startX,startY)
	intersectAx,intersectAy = intersectA

	for e in pairs(face,cyclic=not openFace):	##TODO:put this into function
		eA,eB=e
		if not isEdgeIn(e,adjacentE):
			intersectionB = LIntersectionLS(startX,startY,point2x,point2y, eA.x,eA.y,eB.x,eB.y)
			if intersectionB:
				intersectionBx,intersectionBy=intersectionB
				dist = distance(startX,startY, intersectionBx,intersectionBy)
				if dist<bestDistance:
					bestDistance=dist
					bestEdge=e
					bestIntersection=intersectionB

	print "best:"
	print bestIntersection
	print bestEdge

	if bestIntersection:
		bestIntersectionx, bestIntersectiony = bestIntersection
		# drawPoint(bestIntersectionx,bestIntersectiony,color="#999")
		drawline(bestIntersectionx,bestIntersectiony,startX,startY,color="#00F")

		if inBox(bestIntersectionx, bestIntersectiony) \
				and depth<MAXDEPTH \
				and not isNearList(bestIntersectionx,bestIntersectiony, POINTS, epsilon=5):
			otherF, openF = otherFace(face, bestEdge)
			drawPerpendicularSS(bestIntersection,
				otherF,
				openF,
				[bestEdge],
				depth+1,
				last=startP)
	else:
		# perpendicular continue to border
		if not last:
			return
		lastX,lastY=last
		dx=startX-lastX
		dy=startY-lastY
		newpointX=startX+dx*100
		newpointY=startY+dy*100
		drawline(startX,startY,newpointX,newpointY,color="#00F")
		return
	return
def drawPerpendicularSS(startP, face,openFace, adjacentE, depth=0, last=None):
	"""
	Draw perpendicular from edge that is SS (ie: not contour)
	- StartP: coords of point where to start drawing.
	- face: (halfface) on which this perpendicular lays
	- adjacentE: [(Point,Point)..] edge on which startP lays. Two startP is on vertex
	- dept: auxiliary variable - to prevent too deep recursion
	- last Point - for determining direction when there is no contour on this straight skeleton
	assumptions
	- perpendicular goes into face
	"""
	print "S", "="*100
	print "startP: ",startP
	print "face: ",face
	print "adjacentE: ",adjacentE
	print "depth",depth
	print "last",last
	POINTS.append(startP)
	startX,startY=startP
	# drawPoint(startX, startY, color="#000")
	contour = getContour(face)

	if not contour:	#draw line to end of canvas #TODO:Bug: the can be intersection althrough there is no contour!!!!
	#fix: move this lower (when there is no intersection) as in drawPerpendicularContour
		if not last:
			return
		lastX,lastY=last
		dx=startX-lastX
		dy=startY-lastY
		newpointX=startX+dx*100
		newpointY=startY+dy*100
		drawline(startX,startY,newpointX,newpointY,color="#00F")
		return

	cA,cB=contour
	cAx, cAy= cA.x, cA.y
	cBx, cBy= cB.x, cB.y

	intersectA = pointLineProjection(cAx,cAy,cBx,cBy,startX,startY)
	intersectAx,intersectAy = intersectA

	bestEdge=None
	bestIntersection=None
	bestDistance=float("inf")

	for e in pairs(face,cyclic = not openFace):	#find closest intersection
		eA,eB=e
		if not isEdgeIn(e,adjacentE):
			intersectionB = LIntersectionLS(startX,startY,intersectAx,intersectAy, eA.x,eA.y,eB.x,eB.y)
			if intersectionB:
				intersectionBx,intersectionBy=intersectionB
				dist = distance(startX,startY, intersectionBx,intersectionBy)
				if dist<bestDistance:
					bestDistance=dist
					bestEdge=e
					bestIntersection=intersectionB

	if not bestEdge:
		"line to border (write it after there are some)"
		if not last:
			return
		lastX,lastY=last
		dx=startX-lastX
		dy=startY-lastY
		newpointX=startX+dx*100
		newpointY=startY+dy*100
		drawline(startX,startY,newpointX,newpointY,color="#00F")
		print ":("
		return

	else:
		bestIntersectionx, bestIntersectiony = bestIntersection
		drawline(startX,startY,bestIntersectionx, bestIntersectiony, color="#0000FF")
		# drawPoint(bestIntersectionx, bestIntersectiony, color="#F00")
		#if we didn't run away from canvas and
			#didn't go into too deep recursion
			#and perpendicular didn't run into vertex
		if inBox(bestIntersectionx, bestIntersectiony) \
				and depth<MAXDEPTH\
				and not isNearList(bestIntersectionx,bestIntersectiony, POINTS, epsilon=5):
			
			otherF, openF = otherFace(face, bestEdge)
			if isContourE(*bestEdge):
				drawPerpendicularContour(bestIntersection,
									otherF,
									openF,
									[bestEdge],
									depth=depth+1,
									last=startP)
			else:
				drawPerpendicularSS(bestIntersection,
									otherF,
									openF,
									[bestEdge],
									depth=depth+1,
									last=startP)
		else:
			print bestIntersectionx, bestIntersectiony
			print inBox(bestIntersectionx, bestIntersectiony)
			print depth<MAXDEPTH
			print not isNearList(bestIntersectionx,bestIntersectiony, POINTS, epsilon=5)
			print "outside"

def create_creases(ss):

	for v in ss.points:
		POINTS.append((v.x,v.y))
	# for x,y in :
		# POINTS.append((x,y))
	global maxy, miny, maxx, minx
	maxy=max(map(lambda a: a.y,ss.points))+50
	miny=min(map(lambda a: a.y,ss.points))-50
	maxx=max(map(lambda a: a.x,ss.points))+50
	minx=min(map(lambda a: a.x,ss.points))-50
	lenx=maxx-minx
	leny=maxy-miny

	done=[]
	for point in ss.points:	#Debug: draw this graph
		done.append(point)
		for n in point.ss:
			if n not in done:
				drawline(n.x,n.y, point.x, point.y)
		for n in point.contour:
			if n not in done:
				drawline(n.x,n.y, point.x, point.y,color="#FF0000")

	# Strategy: 1) take contour edge,
	#			2) walk around and start perpendiculars for all verticies on incident faces
	#				2a) draw perpendicular all all way to its end
	edgesDone = []

	for point in ss.points[:]:
		if point.is_contour():
			for n in point.contour[:]:

				edge=(point,n)
				if not isEdgeIn(edge, edgesDone):
					edgesDone.append(edge)
					####	THIS WILL BE EXECUTED ONCE PER CONTOUR EDGE:
					contourA,contourB=edge

					# x=avg(contourA.x,contourB.x)
					# y=avg(contourA.y,contourB.y)
					# drawPoint(x+20, y+20, color="#0F0")

					halfFaceA,oA = getFace(point,n)
					halfFaceB,oB = getFace(n,point)

					print len(halfFaceA), len(halfFaceB)
					for halfFace in (halfFaceA, halfFaceB):
						for i,vertex in enumerate(halfFace):
							if vertex.is_inner():
								prev=halfFace[i-1]
								if i==len(halfFace)-1:
									next=halfFace[0]
								else:
									next=halfFace[i+1]

								isecX,isecY = pointLineProjection(contourA.x,contourA.y,contourB.x,contourB.y, vertex.x,vertex.y)
								aNext = angle(prev.x,prev.y, vertex.x,vertex.y, next.x,next.y)	#angle to next vertex
								aIsec = angle(prev.x,prev.y, vertex.x,vertex.y, isecX,isecY)	#angle to intersection
								if aNext>aIsec:	#if perpendicular goes to face (vs. go outside)
									startP=(vertex.x,vertex.y)
									adjacentN = (prev,vertex,next)
									drawPerpendicularSS(startP, halfFace, False, pairs(adjacentN), 0)
	img=Image.new('RGB', (int(lenx), int(leny)), "#FFFFFF")
	print lenx, minx,maxx
	draw = ImageDraw.Draw(img)
	for line in LINES:
		x1,y1,x2,y2,color=line
		print "(%s,%s) -- (%s,%s)" % (x1,y1,x2,y2)
		draw.line((int(x1-minx), int(y1-miny), int(x2-minx), int(y2-miny)), fill=color)
	done=[]
	print len(LINES),"!!!"
	# for point in ss.points:	#Debug: draw this graph
	# 	done.append(point)
	# 	for n in point.ss:
	# 		if n not in done:
	# 			draw.line((int(n.x-minx), int(n.y-miny), int(point.x-minx), int(point.y-miny)), fill="#0F0")
	# 	for n in point.contour:
	# 		if n not in done:
	# 			draw.line((int(n.x-minx), int(n.y-miny), int(point.x-minx), int(point.y-miny)), fill="#FF0000")
	img.save("test.png")
	return (lenx,leny, minx,maxx, minx, maxx)
									# die()
						# die()
if __name__=="__main__":
	polygon = [ 
			(-1022,-100),
			(-200,-5),
			(20,233),
			(300,200),
			(500,0),
			(1000,0),
			(1000,1000),
			(-1000,1000),
	]


	done=[]
	for point in ss.points:	#Debug: draw this graph
		done.append(point)
		for n in point.ss:
			if n not in done:
				drawline(n.x,n.y, point.x, point.y)
		for n in point.contour:
			if n not in done:
				drawline(n.x,n.y, point.x, point.y,color="#FF0000")

	ss= SS()
	ss.create(polygon)
	create_creases(ss)
	

	# img=Image.new('RGB', (int(lenx)+100, int(leny)+100), "#FFFFFF")
	# draw = ImageDraw.Draw(img)
	# print maxy,miny,maxx,minx,lenx,leny

	# img.save("test.png")
	print ":-)"