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
		
		self.inside=[]
		self.outside=[]
		self.contour=[]	#incidents Vs by contour line

		self.perps=[] # perpendiculars

		self.all=[] # in+out+contour

	def __repr__(self):
		return "Point(x=%s, y=%s)"%(self.x, self.y)

	def normalize(self,debug=False):
		self.all=self.inside+self.outside+self.contour

		
		if self.inside:
			self.sort(self.inside, debug=False)
		if self.outside:
			self.sort(self.outside, debug=False)
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
			ns = filter(lambda x:x.is_ss(),ns)
		return ns

	def is_contour(self):
		return len(self.contour)>0

	def is_ss(self):
		return not self.is_contour()

	def is_inside(self):
		return len(self.inside)>0 and len(self.outside)==0
	
	def is_outside(self):
		return len(self.outside)>0 and len(self.inside)==0

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
	font = ImageFont.truetype("g.ttf", 20)
	MAXDEPTH=20

	def __init__(self):
		self.POINTS=[]
		self.ENDPOINTS=[]
		self.drawedPoints=[]
		self.drawedLines=[]
		self.drawedTexts=[]
		self.img=None
		self.resize=10

		self.mountain ="#0FF"
		self.valley="#0A0"

	def __del__(self):
		if self.img:
			print "Destructor: saving output"
			self.img.save("test.png")


	def create(self, polygon):
		"Convert polygon from list of vertices to straight skeleton"
		
		# convert to [(x,y), ....]
		polygon = map(lambda coords: tuple(map(lambda y: int(round(y*self.resize)),coords)), polygon)
		
		# polygon has to be in counterclockwise order (if coordinates are interpreted as cartesian)
		if clockwisePolygon(polygon):
			polygon.reverse()

		# Take polygon in format [(x,y), ...] and convert it to list of segments
		# in format [(type, x1,y1, x2,y2)...] where type can be from ("c","i","o") depending whether it is
		# contour line, inner or outer SS. Each edge here are two times
		rawSegments=self.run_CGAL(polygon)
		if not rawSegments:
			return None

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
			if t =="i":
				if p1 not in p2.inside and p2 not in p1.inside:
					if p1 not in p2.contour and p2 not in p1.contour:
						p1.inside.append(p2)
						p2.inside.append(p1)
			elif t =="o":
				if p1 not in p2.outside and p2 not in p1.outside:
					if p1 not in p2.contour and p2 not in p1.contour:
						p1.outside.append(p2)
						p2.outside.append(p1)
			elif t == "c":
				if p1 not in p2.contour and p2 not in p1.contour:
					if p1 in p2.inside:
						p2.inside.remove(p1)
					if p1 in p2.outside:
						p2.outside.remove(p1)
					if p2 in p1.inside:
						p1.inside.remove(p2)
					if p2 in p1.outside:
						p1.outside.remove(p2)
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

		self.draw_SS()

		return True

	def run_CGAL(self, polygon):
		# print polygon
		pointsS = "\n".join(map(lambda x: "%s %s"%x, polygon))	# points in pairs per line

		# p = Popen("./ss", shell=True, stdin=PIPE, stdout=PIPE)
		# resS,dummy = p.communicate(pointsS)
		# print "vvvv"
		# print resS

		rawSegments=[]

		resS = runWithTimeout("./ss", 10, pointsS)
		if resS==None:
			return None

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
			if len(p.outside)==1 and len(p.contour)==0:
				borderPoint=p
				break
		if not borderPoint:
			# this shouldn't happen, but it should work without stripping of border if something goes wrong
			return

		# outerFace, openFace = getFace(borderPoint.ss[0], borderPoint)

		outerFace=getPath(borderPoint, borderPoint.outside[0],direction=0)
		
		while True:
			start = outerFace[-1]
			path = getPath(start,start.outside[0], direction=0)
			
			outerFace+=path

			if borderPoint.outside[0] in path:
				break
			# break

		for a,b in pairs(outerFace):
			try:
				a.outside.remove(b)
			except ValueError:
				pass

			try:
				b.outside.remove(a)
			except ValueError:
				pass

		for p in list(self.points):
			p.normalize()
			if len(p.all)==0:
				self.points.remove(p)


	def get_point(self, x, y, epsilon=1.5):
		"""get or create point on coords x,y"""
		"epsilon: if two points are closer than this they are considered equal (more or less)"

		for point in self.points:
			if distance(x,y, point.x, point.y) < epsilon:
				return point
		else:	##point is not already there => create new
			newPoint = Point(x,y)
			self.points.append(newPoint)
			return newPoint

	def draw_SS(self):
		done = []
		for point in self.points:
			for n in point.contour:
				if (point,n) not in done and (n,point) not in done:
					self.drawLine(n.x,n.y, point.x, point.y, color="#F00")
					done.append( (point, n) )

		inside_edges = []
		outside_edges = []
		for p in self.points:
			if p.is_inside():
				for q in p.inside:
					if (p,q) not in inside_edges and (q,p) not in inside_edges:
						inside_edges.append((p,q))
			if p.is_outside():
				for q in p.outside:
					if (p,q) not in outside_edges and (q,p) not in outside_edges:
						outside_edges.append((p,q)) 

		color = {"inside":{True: self.valley,
							False: self.mountain},
				 "outside":{True: self.mountain,
				 			False: self.valley}}

		def draw_edge(a,b,side): #side="inside"/"outside"
			x=avg(a.x, b.x)
			y=avg(a.y, b.y)

			f1,f1open=getFace(a, b)
			c1A, c1B=getContour(f1)
			f2,f2open=getFace(b,a)
			c2A, c2B=getContour(f2)

			self.drawLine(a.x,a.y, b.x, b.y, color=color[side][convexSS(c1A, c1B, c2A, c2B, x,y)])

		for a,b in inside_edges:
			draw_edge(a,b,"inside")

		for a,b in outside_edges:
			draw_edge(a,b,"outside")

	def create_creases(self):
		# Strategy: 1) take contour edge,
		#			2) walk around and start perpendiculars for all verticies on incident faces
		#				2a) draw perpendicular all all way to its end

		for p in self.points: #make list of SS points
			if p.is_ss():
				self.POINTS.append((p.x,p.y))

		edgesDone = []

		for pid, point in enumerate(self.points):
			if point.is_contour():
				for n in point.contour[:]:

					edge=(point,n)
					if not isEdgeIn(edge, edgesDone):
						edgesDone.append(edge)
						####	THIS WILL BE EXECUTED ONCE PER CONTOUR EDGE:
						contourA,contourB=edge

						halfFaceA,oA = getFace(point,n)
						halfFaceB,oB = getFace(n,point)

						# print len(halfFaceA), len(halfFaceB)
						for halfFace in (halfFaceA, halfFaceB):
							for i,vertex in enumerate(halfFace):
								if vertex.is_ss():
									prev=halfFace[i-1]
									# self.drawPoint(vertex.x, vertex.y, 3, color="#0F0")
									if i==len(halfFace)-1:
										next=halfFace[0]
									else:
										next=halfFace[i+1]


									isecX,isecY = pointLineProjection(contourA.x,contourA.y,contourB.x,contourB.y, vertex.x,vertex.y)
									aNext = angle(prev.x,prev.y, vertex.x,vertex.y, next.x,next.y)	#angle to next vertex
									aIsec = angle(prev.x,prev.y, vertex.x,vertex.y, isecX,isecY)	#angle to intersection
									if aNext>aIsec and 0.001<aIsec<math.pi-0.001:	#if perpendicular goes to face (vs. go outside)
										startP=(vertex.x,vertex.y)
										adjacentN = (prev,vertex,next)
										self.drawPerpendicularSS(startP, halfFace, False, pairs(adjacentN), 0)
		
		done=[]
		for p in self.points:
			for q in p.perps:
				if q not in done:
					self.drawLine(p.x,p.y, q.x,q.y,color="#00F")
			done.append(p)

		return

	def addPerpendicular(self, aX,aY, bX, bY):
		A=self.get_point(aX, aY, epsilon=0.01)
		B=self.get_point(bX, bY, epsilon=0.01)

		if B not in A.perps:
			A.perps.append(B)
		if A not in B.perps:
			B.perps.append(A)

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

		startX,startY=startP
		contour = adjacentE[0]

		# if self.isNearEndPoint(startX,startY, contour):
		# if isNearList(startX,startY, self.ENDPOINTS, epsilon=5):
			# return

		# self.POINTS.append(startP)

		if len(adjacentE)!=1:  #just test if params are OK
			print len(adjacentE)
			print adjacentE
			assert False 	#this has to be one edge, not more

		cA,cB=contour
		cAx, cAy= cA.x, cA.y
		cBx, cBy= cB.x, cB.y
		dx=cBx-cAx
		dy=cBy-cAy

		point2x=startX-dy 	#auxiliary point - through this point will go perpendicular
		point2y=startY+dx

		bestEdge=None
		bestIntersection=None
		bestDistance=float("inf")

		intersectA = pointLineProjection(cAx,cAy,cBx,cBy,startX,startY)
		intersectAx,intersectAy = intersectA

		for e in pairs(face, cyclic=not openFace):	## TODO:put this into function
			eA,eB=e
			if not isEdgeIn(e,adjacentE):
				intersectionB = LIntersectionLS2(startX,startY,point2x,point2y, eA.x,eA.y,eB.x,eB.y)
				if intersectionB:
					intersectionBx,intersectionBy=intersectionB
					dist = distance(startX,startY, intersectionBx,intersectionBy)
					if dist<bestDistance:
						bestDistance=dist
						bestEdge=e
						bestIntersection=intersectionB

		if bestIntersection:
			bestIntersectionx, bestIntersectiony = bestIntersection

			# drawPoint(bestIntersectionx,bestIntersectiony,color="#999")
			self.addPerpendicular(bestIntersectionx,bestIntersectiony,startX,startY)

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
				self.ENDPOINTS.append((bestIntersection, contour))
		else:
			# perpendicular continue to border
			if not last:
				return
			lastX,lastY=last
			l=distance(startX,startY, lastX,lastY)
			dx=(startX-lastX)/l
			dy=(startY-lastY)/l
			newpointX=startX+dx*10000
			newpointY=startY+dy*10000
			self.addPerpendicular(startX,startY,newpointX,newpointY)
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
		startX,startY=startP
		# print startX, startY
		contour = getContour(face)
		if self.isNearEndPoint(startX,startY, contour):
		# if isNearList(startX,startY, self.ENDPOINTS, epsilon=5):
			return
		# self.POINTS.append(startP)

		if not contour:
			if not last:
				return
			## TODO: is this ever used?
			lastX,lastY=last
			dx=startX-lastX
			dy=startY-lastY
			newpointX=startX+dx*100
			newpointY=startY+dy*100
			addPerpendicular(startX,startY,newpointX,newpointY)
			return

		cA,cB=contour
		cAx, cAy= cA.x, cA.y
		cBx, cBy= cB.x, cB.y

		intersectA = pointLineProjection(cAx,cAy,cBx,cBy,startX,startY)
		intersectAx,intersectAy = intersectA

		bestEdge=None
		bestIntersection=None
		bestDistance=float("inf")

		for e in pairs(face, cyclic = not openFace):	#find closest intersection
			eA,eB=e
			if not isEdgeIn(e,adjacentE):
				intersectionB = LIntersectionLS2(startX,startY,intersectAx,intersectAy, eA.x,eA.y,eB.x,eB.y)
				if intersectionB:
					intersectionBx,intersectionBy=intersectionB
					dist = distance(startX,startY, intersectionBx,intersectionBy)
					if dist<bestDistance:
						bestDistance=dist
						bestEdge=e
						bestIntersection=intersectionB

		if not bestEdge:
			"line to border"
			l=distance(cA.x, cA.y, cB.x,cB.y)
			dx=(cA.x-cB.x)/l
			dy=(cA.y-cB.y)/l

			newpointX=startX+dy*10000
			newpointY=startY-dx*10000
			self.addPerpendicular(startX,startY,newpointX,newpointY)
			return
		else:
			bestIntersectionx, bestIntersectiony = bestIntersection

			dx=bestIntersectionx-startX
			dy=bestIntersectiony-startY
			self.addPerpendicular(startX,startY,bestIntersectionx, bestIntersectiony)
			#if we didn't run away from canvas and
				#didn't go into too deep recursion
				#and perpendicular didn't run into vertex
			if self.inBox(bestIntersectionx, bestIntersectiony) \
					and depth<self.MAXDEPTH\
					and (not isNearList(bestIntersectionx,bestIntersectiony, self.POINTS, epsilon=5)):
				
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
				# print "--"
				# print self.inBox(bestIntersectionx, bestIntersectiony)
				# print depth<self.MAXDEPTH, depth
				# print not isNearList(bestIntersectionx,bestIntersectiony, self.POINTS, epsilon=5)
				# if depth>=self.MAXDEPTH:
				# 	self.drawPoint(startX, startY, r=10, color="#FF0")
				# 	self.drawPoint(bestIntersectionx, bestIntersectiony, r=5, color="#000")

	def isNearEndPoint(self, startX, startY, contour):
		for (x,y),edge in self.ENDPOINTS:
			epsilon=1
			if distance(x,y, startX,startY)<epsilon:
				if sameEdge(edge,contour):
					return True
		return False

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


	def drawPoint(self, x,y,r=3,color="#F0F"):
		self.drawedPoints.append((x,y,r,color))

	def drawLine(self,  x1,y1, x2,y2, color="#0F0"):
		self.drawedLines.append( (x1,y1,x2,y2,color))

	def drawText(self, x,y,text):
		self.drawedTexts.append( (x,y,text) )

	def drawit(self, medium="png"):
		print "drawit"
		resize=1
		xoffset=-self.xmin/resize
		yoffset=-self.ymin/resize

		xsize = min(int(self.xlen/resize),10000)
		ysize = min(int(self.ylen/resize),10000)

		img=Image.new('RGB', (xsize,ysize), "#FFFFFF")
		draw = ImageDraw.Draw(img)

		r=lambda: random.randint(-5,5)
		r=lambda:0
		if medium=="png":
			for ax,ay,bx,by,color in self.drawedLines:
				draw.line((int(ax/resize+xoffset)+r(), int(ay/resize+yoffset)+r(), int(bx/resize+xoffset)+r(), int(by/resize+yoffset)+r()), fill=color)

			for x,y, r, color in self.drawedPoints:
				draw.ellipse((int(x/resize+xoffset-r), int(y/resize+yoffset-r), int(x/resize+xoffset+r), int(y/resize+yoffset+r)), fill=color)

			for x,y, text in self.drawedTexts:
				draw.text((int(x/resize+xoffset),int(y/resize+yoffset)), text, fill=(0,0,0),font=self.font)

			img.save("test.png")
		elif medium=="svg":
			import pysvg.structure
			import pysvg.builders
			import pysvg.text

			svg_document = pysvg.structure.Svg()

			shape_builder = pysvg.builders.ShapeBuilder()

			for ax,ay,bx,by,color in self.drawedLines:
				svg_document.addElement(shape_builder.createLine(int(ax/resize+xoffset), int(ay/resize+yoffset), int(bx/resize+xoffset), int(by/resize+yoffset), strokewidth=2, stroke=color))

			for x,y, r, color in self.drawedPoints:
				svg_document.addElement(shape_builder.createCircle(cx=int(x/resize+xoffset), cy=int(y/resize+yoffset), r=r, fill=color))

			for x,y, text in self.drawedTexts:
				t=pysvg.text.Text(x=int(x/resize+xoffset),y=int(y/resize+yoffset),content=text)
				svg_document.addElement(t)

			svg_document.save("test.svg")
