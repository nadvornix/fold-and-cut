from __future__ import division
from subprocess import Popen, PIPE
from utils import *
import Image,ImageDraw,ImageFont


class Face():
	def __init__(self):
		self.contour=None
		self.vertices=[]

class Point():
	def __init__(self,x,y):
		self.x=x
		self.y=y
		self.ss=[]	#list of incident vertices by Skeleton
		self.contour=[]	#incidents Vs by contour line

	def __repr__(self):
		return "Point(x=%s, y=%s)"%(self.x, self.y)

	def normalize(self,debug=False):
		self.all=self.ss+self.contour

		if self.ss:
			self.sort(self.ss, debug=False)
		if self.contour:
			self.sort(self.contour, debug=False)	#?
		if self.all:	# this is always?
			self.sort(self.all, debug=debug)

	def sort(self, l, debug=False):
		"""sort so that relative cyclic order of neighbors is correct (= corresponding to embedding)"""
		first = l[0]

		l.sort(key=lambda point: angle(first.x,first.y, self.x,self.y, point.x, point.y))

		if debug:
			print "first: ", first.y, first.x
			print "self: ", self.y, self.x
			print "+++++"
			for n in l:
				print "to (%s,%s) is %s " %	(n.x,n.y,angle(n)*(180/math.pi) )
			print "++++"

	def forks(self, from_, all=True):
		"possible routes when comming from from_ (first is most right, last most left)"
		"all=False means: take edges only from SS and not contours"
		"Note: first has to be normalized"
		# if all:
		# 	ns=list(self.all)
		# else:
		# 	ns=list(self.ss)
		ns=list(self.all)
		index = ns.index(from_)
		del ns[index]   #rotation
		ns+=ns[:index]
		del ns[:index]

		if not all:
			ns = filter(lambda x:x.is_inner(),ns)
		return ns

	def is_contour(self):
		return len(self.contour)>0

	def is_inner(self):
		return not self.is_contour()

	def getFaces(self):	## NOT USED?
		assert False
		faces=[]
		for n in self.all:
			vertices=[]
			faces.append(vertices)
			last=self
			node=n
			i=0
			direction=0 	#direction==0 means leftest, -1 is rightest
			while node!=self:
				if direction==0:
					vertices.append(node)
				elif direction==-1:
					vertices.insert(0, node)

				tmp=node
				try:
					node=node.forks(last)[direction]
				except IndexError:
					last=n
					node=self
					direction=-1
					continue
				print node


				last=tmp
				i+=1

			print ">>",i

			break	#XXX: debug
		return faces

class SS():
	point_tolerance=1.5 # if two points are closer than this they are considered equal (more or less)
	font = ImageFont.truetype("g.ttf", 50)
	MAXDEPTH=0

	def __init__(self):
		self.POINTS=[]
		self.drawedPoints=[]
		self.drawedLines=[]
		self.drawedTexts=[]
		self.img=None

	def __del__(self):
		if self.img:
			print "Destructor: saving output"
			self.img.save("test.png")


	def create(self, polygon):
		"Convert polygon from list of vertices to straight skeleton"
		
		# convert to [(x,y), ....]
		polygon = map(lambda x: tuple(map(int,x)), polygon)
		
		# polygon has to be in counterclockwise order (if coordinates are interpreted as cartesian)
		if clockwisePolygon(polygon):
			polygon.reverse()

		# Take polygon in format [(x,y), ...] and convert it to list of segments
		# in format [(type, x1,y1, x2,y2)...] where type can be from ("c","i","o") depending whether it is
		# contour line, inner or outer SS. Each edge here are two times
		rawSegments=self.run_CGAL(polygon)

		# rawSegments=filter(lambda x: x[0] in ("i", "c"), rawSegments)		

		# Extract from it corner points of segments (include lots of duplicities). 
		# result is in form [(x,y)...]
		rawPoints=self.segmentsToPoints(rawSegments)

		# Save points to self.points in format [Point(), ...] and remove duplicities.
		self.cleanPoints(rawPoints)

		# Take all segments one by one and if is point on them then it will split 
		# them by it split them and create new segment
		# (output is in same format as inpput)
		# also remove all very short segments (_<0.1)
		splited=self.split_all_Segs_by_all_Ps(rawSegments)

		# Now only way how segments can FRAME fully.
		# convert segments to [(type,Point,Point)....]
		segments = self.cleanSegments(splited)

		# set neighbours (and prefer contour lines if possible)
		for t,p1,p2 in segments:
			if t in ("i","o"):
				if p1 not in p2.ss and p2 not in p1.ss:
					if p1 not in p2.contour and p2 not in p1.contour:
						p1.ss.append(p2)
						p2.ss.append(p1)
			elif t == "c":
				if p1 not in p2.contour and p2 not in p1.contour:
					if p1 in p2.ss:
						p2.ss.remove(p1)
					if p2 in p1.ss:
						p1.ss.remove(p2)
					p1.contour.append(p2)
					p2.contour.append(p1)

		# set (cyclic) order of neighbours as in planar embedding
		for i, point in enumerate(self.points):
			point.normalize()


		contour = filter(lambda p: p.is_contour(), self.points)

		self.minX=reduce(min, map(lambda p:p.x, contour))
		self.maxX=reduce(max, map(lambda p:p.x, contour))
		self.minY=reduce(min, map(lambda p:p.y, contour))
		self.maxY=reduce(max, map(lambda p:p.y, contour))

		self.lenX=self.maxX-self.minX
		self.lenY=self.maxY-self.minY

		self.xmin,self.xmax, self.ymin,self.ymax = inflate_rectangle(self.minX, self.maxX, self.minY, self.maxY, 3)
		
		self.xlen=self.xmax-self.xmin
		self.ylen=self.ymax-self.ymin

		# stripe unnecessary border
		self.stripeBorder()

		# extend lines on border to border
		self.extendBorderLines()




	def run_CGAL(self, polygon):
		# print polygon
		pointsS = "\n".join(map(lambda x: "%s %s"%x, polygon))	# points in pairs per line

		p = Popen("./ss", shell=True, stdin=PIPE, stdout=PIPE)
		resS,dummy = p.communicate(pointsS)
		rawSegments=[]
		for line in resS.split("\n"):
			try:
				type_, x1,y1,x2,y2 = line.split()
				x1,y1,x2,y2 = float(x1),float(y1),float(x2),float(y2)
				rawSegments.append( (type_, x1,y1,x2,y2) )
				# print type, x1,y1,x2,y2
			except ValueError:	#empty or fault line in output of ./ss
				pass
		return rawSegments

	def segmentsToPoints(self, rawSegments):
		""" just extract ending points from segments and save them in format [(x,y),...] 
    	"""
		rawPoints=[]
		for type_,x1,y1,x2,y2 in rawSegments:
			rawPoints.append( (x1,y1) )
			rawPoints.append( (x2,y2) )
		return rawPoints	

	def cleanPoints(self, rawPoints):
		self.points=[]
		for x,y in rawPoints:
			self.get_point(x,y)

	def split_all_Segs_by_all_Ps(self, rawSegments):
		splited=[]

		for segment in rawSegments:
			subsegments=[segment]
			for p in self.points:
				for i,ss in enumerate(list(subsegments)):
					type_,x1,y1,x2,y2=ss
					if pointOnSegment(x1,y1,x2,y2, p.x,p.y, epsilonDistance=2):# if p is on segment:
						# split segment by that point (ie: replace old subsegment by two new)
						del subsegments[i]

						subsegments.append((type_, x1,y1, p.x,p.y))
						subsegments.append((type_, p.x,p.y, x2,y2))
			splited+=subsegments

		#remove all edges shorten than e:
		e=0.1
		splited = filter(lambda a: distance(a[1],a[2], a[3],a[4])>=e,splited)

		return splited

	def cleanSegments(self, rawSegments):
		segments=[]
		for t,x1,y1,x2,y2 in rawSegments:
			p1=self.get_point(x1,y1)
			p2=self.get_point(x2,y2)
			segments.append( (t,p1,p2) )
		return segments
	
	def stripeBorder(self):
		borderPoint=None
		for p in self.points:
			if len(p.ss)==1 and len(p.contour)==0:
				borderPoint=p
				break
		if not borderPoint:
			# this shouldn't happen, but it should work without stripping of border if something goes wrong
			return

		# outerFace, openFace = getFace(borderPoint.ss[0], borderPoint)

		outerFace=getPath(borderPoint, borderPoint.ss[0],direction=0)
		
		while True:
			start = outerFace[-1]
			path = getPath(start,start.ss[0], direction=0)
			
			outerFace+=path

			if borderPoint.ss[0] in path:
				break
			# break

		# for p in outerFace:
		# 	print p
		# 	self.drawPoint(p.x, p.y, color="#F55")

		for a,b in pairs(outerFace):
			try:
				a.ss.remove(b)
			except ValueError:
				pass

			try:
				b.ss.remove(a)
			except ValueError:
				pass

		for p in list(self.points):
			p.normalize()
			if len(p.all)==0:
				self.points.remove(p)


	def get_point(self, x, y):
		"""get or create point on coords x,y"""

		for point in self.points:
			if distance(x,y, point.x, point.y) < self.point_tolerance:
				return point
		else:	#point is not already there => create new
			newPoint = Point(x,y)
			self.points.append(newPoint)
			return newPoint

	def create_creases(self):
		for v in self.points:
			self.POINTS.append((v.x,v.y))

		done=[]
		for point in self.points:	#Debug: draw this graph
			done.append(point)
			for n in point.ss:
				if n not in done:
					self.drawline(n.x,n.y, point.x, point.y)
			for n in point.contour:
				if n not in done:
					self.drawline(n.x,n.y, point.x, point.y, color="#FF0000")

		# Strategy: 1) take contour edge,
		#			2) walk around and start perpendiculars for all verticies on incident faces
		#				2a) draw perpendicular all all way to its end
		edgesDone = []

		for pid, point in enumerate(self.points):
			if point.is_contour():
				for n in point.contour[:]:

					edge=(point,n)
					if not isEdgeIn(edge, edgesDone):
						edgesDone.append(edge)
						####	THIS WILL BE EXECUTED ONCE PER CONTOUR EDGE:
						contourA,contourB=edge

						x=avg(contourA.x,contourB.x)
						y=avg(contourA.y,contourB.y)
						self.drawPoint(x, y, 3, color="#0FF")

						halfFaceA,oA = getFace(point,n)
						halfFaceB,oB = getFace(n,point)

						# print len(halfFaceA), len(halfFaceB)
						for halfFace in (halfFaceA, halfFaceB):
							for i,vertex in enumerate(halfFace):
								if vertex.is_inner():
									prev=halfFace[i-1]
									self.drawPoint(vertex.x, vertex.y, 3, color="#0F0")
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
										
										self.drawPoint(vertex.x, vertex.y, 2)
										self.drawPerpendicularSS(startP, halfFace, False, pairs(adjacentN), 0)
										# else:
										# 	drawline(vertex.x, vertex.y, vertex.x+20, vertex.y+20, "#000")
		# img=Image.new('RGB', (int(lenx), int(leny)), "#FFFFFF")
		# draw = ImageDraw.Draw(img)
		# for line in LINES:
		# 	x1,y1,x2,y2,color=line
		# 	draw.line((int(x1-minx), int(y1-miny), int(x2-minx), int(y2-miny)), fill=color)
		# done=[]




		# for point in ss.points:	#Debug: draw this graph
		# 	done.append(point)
		# 	for n in point.ss:
		# 		if n not in done:
		# 			draw.line((int(n.x-minx), int(n.y-miny), int(point.x-minx), int(point.y-miny)), fill="#0F0")
		# 	for n in point.contour:
		# 		if n not in done:
		# 			draw.line((int(n.x-minx), int(n.y-miny), int(point.x-minx), int(point.y-miny)), fill="#FF0000")
		

		# return (minx,maxx, minx, maxx),LINES
		return


	def drawPerpendicularContour(self, startP, face,openFace, adjacentE, depth=0,last=None):
		"""
		parameters are same as in drawPerpendicularSS
		"""
		# print "C", "~"*100
		# print "startP: ",startP
		# print "face: ",face
		# print "openFace",openFace
		# print "adjacentE: ",adjacentE
		# print "depth",depth
		# print "last",last

		self.POINTS.append(startP)

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

		# print "best:"
		# print bestIntersection
		# print bestEdge

		if bestIntersection:
			bestIntersectionx, bestIntersectiony = bestIntersection
			# drawPoint(bestIntersectionx,bestIntersectiony,color="#999")
			self.drawline(bestIntersectionx,bestIntersectiony,startX,startY,color="#00F")

			if self.inBox(bestIntersectionx, bestIntersectiony) \
					and depth<self.MAXDEPTH \
					and not isNearList(bestIntersectionx,bestIntersectiony, self.POINTS, epsilon=5):
				otherF, openF = otherFace(face, bestEdge)
				self.drawPerpendicularSS(bestIntersection,
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
			self.drawline(startX,startY,newpointX,newpointY,color="#00F")
			return
		return

	def drawPerpendicularSS(self, startP, face,openFace, adjacentE, depth=0, last=None):
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
		# print "S", "="*100
		# print "startP: ",startP
		# print "face: ",face
		# print "adjacentE: ",adjacentE
		# print "depth",depth
		# print "last",last
		self.POINTS.append(startP)
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
			self.drawline(startX,startY,newpointX,newpointY,color="#00F")
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
			self.drawline(startX,startY,newpointX,newpointY,color="#00F")
			# print ":("
			return

		else:
			bestIntersectionx, bestIntersectiony = bestIntersection
			self.drawline(startX,startY,bestIntersectionx, bestIntersectiony, color="#0000FF")
			# drawPoint(bestIntersectionx, bestIntersectiony, color="#F00")
			#if we didn't run away from canvas and
				#didn't go into too deep recursion
				#and perpendicular didn't run into vertex
			if self.inBox(bestIntersectionx, bestIntersectiony) \
					and depth<self.MAXDEPTH\
					and not isNearList(bestIntersectionx,bestIntersectiony, self.POINTS, epsilon=5):
				
				otherF, openF = otherFace(face, bestEdge)
				if isContourE(*bestEdge):
					self.drawPerpendicularContour(bestIntersection,
										otherF,
										openF,
										[bestEdge],
										depth=depth+1,
										last=startP)
				else:
					self.drawPerpendicularSS(bestIntersection,
										otherF,
										openF,
										[bestEdge],
										depth=depth+1,
										last=startP)
			else:
				pass
				# print bestIntersectionx, bestIntersectiony
				# print inBox(bestIntersectionx, bestIntersectiony)
				# print depth<MAXDEPTH
				# print not isNearList(bestIntersectionx,bestIntersectiony, POINTS, epsilon=5)
				# print "outside"

	def inBox(self, x,y):
		return self.xmin<=x<=self.xmax and self.ymin<=y<=self.ymax

	def extendBorderLines(self):
		borderPoints=[]
		for p in self.points:
			if len(p.all)==1:
				borderPoints.append(p)

		# for p in borderPoints:
		# 	self.drawPoint(int(p.x), int(p.y), color="#0F0")

		for p in borderPoints:
			n=p.all[0]
			dx = p.x-n.x
			dy = p.y-n.y
			p.x = p.x+100*dx
			p.y = p.y+100*dy

		for p in self.points:
			p.normalize()


	def drawPoint(self, x,y,r=10,color="#FF00FF"):
		self.drawedPoints.append((x,y,r,color))
		# draw.ellipse((int(x-minx-r), int(y-miny-r), int(x-minx+r), int(y-miny+r)),fill=color)

	def drawline(self,  x1,y1, x2,y2, color="#00FF00"):
		# draw.line((int(x1-minx), int(y1-miny), int(x2-minx), int(y2-miny)), fill=color)
		# LINES.append( (x1,y1, x2,y2, color))
		self.drawedLines.append( (x1,y1,x2,y2,color))


	def drawtext(self, x,y,text):
		self.drawedTexts.append( (x,y,text) )
		# draw.text((int(x-minx),int(y-miny)),text,fill=(0,0,0),font=font)

	def drawit(self):
		# xoffset = (xlen+self.FRAME-self.lenX)/2 - self.minX
		# yoffset = (ylen+self.FRAME-self.lenY)/2 - self.minY

		xoffset=-self.xmin
		yoffset=-self.ymin

		img=Image.new('RGB', (int(self.xlen), int(self.ylen)), "#FFFFFF")
		draw = ImageDraw.Draw(img)

		for ax,ay,bx,by,color in self.drawedLines:
			draw.line((int(ax+xoffset), int(ay+yoffset), int(bx+xoffset), int(by+yoffset)), fill=color)

		for x,y, r, color in self.drawedPoints:
			draw.ellipse((int(x+xoffset-r), int(y+yoffset-r), int(x+xoffset+r), int(y+yoffset+r)), fill=color)

		for x,y, text in self.drawedTexts:
			draw.text((int(x+xoffset),int(y+yoffset)), text, fill=(0,0,0),font=self.font)

		img.save("test.png")

