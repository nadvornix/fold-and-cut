from __future__ import division
from subprocess import Popen, PIPE
from utils import *

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

	def is_inner(self): #TODO: rename to is_ss
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

	def __init__(self):
		pass

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

		# Now only way how segments can overlap fully.
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
	
	def get_point(self, x, y):
		"""get or create point on coords x,y"""

		for point in self.points:
			if distance(x,y, point.x, point.y) < self.point_tolerance:
				return point
		else:	#point is not already there => create new
			newPoint = Point(x,y)
			self.points.append(newPoint)
			return newPoint

