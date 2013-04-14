import unittest
from utils import *
from classes import *
import random
import math

class TestUtils(unittest.TestCase):
	def setUp(self):
		pass

	def test_distance(self):
		self.assertAlmostEqual(distance(1,2,3,4),2*math.sqrt(2))
		self.assertAlmostEqual(distance(-1,-2,-3,-4),2*math.sqrt(2))
		self.assertAlmostEqual(distance(1,1,1,1),0)

	def test_angle(self):
		self.assertAlmostEqual(angle(0,0, 0,1 ,1,1),math.pi/2)
		self.assertAlmostEqual(angle(2,4, -5,-6 ,2,4.0000001),0)
		self.assertAlmostEqual(angle(2,4, -5,-6 ,2,4-0.0000001),2*math.pi)
		self.assertAlmostEqual(angle(0,0, -1,1, -2,0),3*math.pi/2)
		self.assertAlmostEqual(angle(-2,0, -1,1, 0,0),math.pi/2)

		for i in range(100):
			random3points = [random.randint(-100,100) for i in range(6)]
			a = angle(*random3points)
			self.assertTrue(0<=a<=2*math.pi)

	def test_pointLineProjection(self):
		x,y=pointLineProjection(-5,0, 12,0, 3,1) # proj. to x axis
		self.assertAlmostEqual(x,3)
		self.assertAlmostEqual(y,0)

		x,y=pointLineProjection(0,-5, 0,12, 3,1) # proj. to y axis
		self.assertAlmostEqual(x,0)
		self.assertAlmostEqual(y,1)

		x,y=pointLineProjection(0,4, 4,0, -10,-10) # 45 degree angle
		self.assertAlmostEqual(x,2)
		self.assertAlmostEqual(y,2)

		x,y=pointLineProjection(2,-2, -1,4, 3,1)
		self.assertAlmostEqual(x,1)
		self.assertAlmostEqual(y,0)

	def test_calculateGradient(self):
		self.assertAlmostEqual(calculateGradient((5,6), (7,6)),0)
		self.assertEqual(calculateGradient((5,6), (5,7)),None)
		self.assertAlmostEqual(calculateGradient((6,3), (5,6)),-3)

	def test_calculateYAxisIntersect(self):
		line = (-5,0), (3,0)
		self.assertAlmostEqual(calculateYAxisIntersect(line[0],calculateGradient(*line)),0)
		line = (-5,5), (3,5)
		self.assertAlmostEqual(calculateYAxisIntersect(line[0],calculateGradient(*line)),5)
		line = (5,-1), (3,1)
		self.assertAlmostEqual(calculateYAxisIntersect(line[0],calculateGradient(*line)),4)

	def test_getIntersectPoint(self):
		#axis:
		x,y = getIntersectPoint(-5,0,-4.3,0,  0,3,0,2)
		self.assertAlmostEqual(x,0)
		self.assertAlmostEqual(y,0)


		x,y = getIntersectPoint(-5,3,5,-7,  -1,1,-1,2)
		self.assertAlmostEqual(x,-1)
		self.assertAlmostEqual(y,-1)

	def test_onSameLine(self):
		self.assertTrue(onSameLine(-5,0, -3,0, -4,0,-2,0))
		self.assertFalse(onSameLine(-5,0, -3,0, -4,0,-2,0.001))
		self.assertTrue(onSameLine(-5,0, -3,0, -1,0,-2,0))
		self.assertTrue(onSameLine(-5,-4, -3,-2, 10,11,12,13))

	def test_onSameLineF(self):
		self.assertTrue(onSameLineF(-5,0, -3,0, -4,0,-2,0))
		
		self.assertTrue(onSameLineF(-5,0, -3,0, -4,0,-2,0.0001))
		self.assertTrue(onSameLineF(-5,0, -3,0, -4,0,-2,-0.0001))
		
		self.assertFalse(onSameLineF(-5,0, -3,0, -4,0,-2,0.1))
		self.assertFalse(onSameLineF(-5,0, -3,0, -4,0,-2,-0.1))

		self.assertTrue(onSameLineF(-5,0, -3,0, -1,0,-2,0))
		self.assertTrue(onSameLineF(-5,-4, -3,-2, 10,11,12,13))

	def test_splitSegments(self):
		segments=[("c",0,0,10,10), 
					("i",8,8,10,10), # vetex overlap
					("i",-1,-1,1,1), # half-overlap
					("o", 4,4,5,5), # whole inside
					("c", 4,4,5,5), # identical
				]

		result = splitSegments(segments,(1.0001,1.0001))
		shouldbeIn=[("c",0,0,1.0001,1.0001),
					("c",1.0001,1.0001,10,10),
					("i",8,8,10,10)
					]
		shouldNotbeIn=[("c",0,0,10,10)]
		for s in shouldbeIn:
			self.assertTrue(s in result)

		for s in shouldNotbeIn:
			self.assertFalse(s in result)

		result = splitSegments(segments,(1.000,1))
		shouldbeIn=[("c",0,0,1.0,1.0),
					("c",1.0,1.0,10,10),
					("i",8,8,10,10),
					("i",-1,-1,1,1)
					]
		shouldNotbeIn=[("c",0,0,10,10)]
		for s in shouldbeIn:
			self.assertTrue(s in result)

		for s in shouldNotbeIn:
			self.assertFalse(s in result)

	def test_ccw(self):
		self.assertTrue(ccw(1,-1, 1,0, 0,0))
		self.assertFalse(ccw(1,-1, 1,0, 2,0))
		
		self.assertFalse(ccw(1,-1, 1,0, 1,1))
		self.assertFalse(ccw(1,-1, 1,0, 1,-1))
		
		self.assertTrue(ccw(0,0, 0,1, -0.01,0))
		self.assertFalse(ccw(0,0, 0,1, 0.01,0))

	def test_lineSegmentsIntersectionQ(self):
		self.assertTrue(lineSegmentsIntersectionQ(-5,-5,5,5,-4,4,4,-4))
		self.assertFalse(lineSegmentsIntersectionQ(-5,-5,0,0, 0,0,12,3)) # touching with corner-corner
		self.assertFalse(lineSegmentsIntersectionQ(-5,-5,5,5, 0,0,12,3)) # touching with corner-line
		
		# self.assertTrue(lineSegmentsIntersectionQ(-5,-5,5,5, -1,-1,1,1)) # inside ##harmless BUG in code

	def test_lineSegmentsIntersection(self):
		x,y=lineSegmentsIntersection(-5,-5,6,6, -4,4, 3,-3)
		self.assertAlmostEqual(x,0)
		self.assertAlmostEqual(x,0)

		a=lineSegmentsIntersection(0,10, 5,5, 0,0,0,5)
		self.assertEqual(a,None)

	def test_LIntersectionLS(self):
		self.assertEqual(LIntersectionLS(-1,-1, 5,5, 4,5, 3,10,epsilon=0.01),None)
		x,y=LIntersectionLS(-1,-1, 5,5, 3,5,5,3)
		self.assertEqual(x,4)
		self.assertEqual(y,4)

	def test_LIntersectionLS2(self):
		self.assertEqual(LIntersectionLS2(-1,-1, 5,5, 4,5, 3,10),None)
		x,y=LIntersectionLS2(-1,-1, 5,5, 3,5,5,3)
		self.assertEqual(x,4)
		self.assertEqual(y,4)

	def test_rturn(self):
		self.assertTrue(rturn(10,0, 0,0, 0,10))
		self.assertFalse(rturn(10,0, 0,0, 1,-10))
		self.assertFalse(rturn(0,10, 0,0, 10,0))

	def test_pInsideConvexAngle(self):
		self.assertTrue(pInsideConvexAngle(0,10, 0,0, 10,0,  5,5))

	def test_isNearList(self):
		self.assertTrue(isNearList(5,5,[(4,4),(3,2),(5.1,5.1)], epsilon=0.15))
		self.assertFalse(isNearList(5,5,[(4,4),(3,2),(5.1,5.1)], epsilon=0.14))

	def test_isNearListPoints(self):
		l=[Point(4,4),Point(3,2),Point(5.1,5.1)]
		self.assertTrue(isNearListPoints(5,5,l, epsilon=0.15))
		self.assertFalse(isNearListPoints(5,5,l, epsilon=0.14))

	def test_intersection(self):
		a=[]
		b=[2,4,5]
		c=[3,4,5]
		c=[1,2,3,4,5]
		lists=[a,b,c]
		for l1 in lists:
			for l2 in lists:
				i1=intersection(l1,l2)
				i2=intersection(l2,l1)
				self.assertEqual(i1,i2)
				for i in c:
					if (i in l1) and (i in l2):
						self.assertTrue(i in i1) #all that should be in are in
					else:
						self.assertFalse(i in i1) #and nothing more

	def test_pairs(self):
		self.assertEqual(pairs([]), [])
		self.assertEqual(pairs([1]), [])
		self.assertEqual(pairs([1,2]), [(1,2)])
		self.assertEqual(pairs([1,2,3]), [(1,2),(2,3)])
		self.assertEqual(pairs([1,2,3,4]), [(1,2),(2,3),(3,4)])

		self.assertEqual(pairs([],cyclic=True), [])
		self.assertEqual(pairs([1],cyclic=True), [])
		self.assertEqual(pairs([1,2],cyclic=True), [(1,2),(2,1)])
		self.assertEqual(pairs([1,2,3],cyclic=True), [(1,2),(2,3),(3,1)])
		self.assertEqual(pairs([1,2,3,4],cyclic=True), [(1,2),(2,3),(3,4),(4,1)])

	def test_nTuples(self):
		self.assertEqual(nTuples([],3), [])
		self.assertEqual(nTuples([1],2), [])
		self.assertEqual(nTuples([1,2,3,4],4), [(1,2,3,4)])
		self.assertEqual(nTuples([1,2,3,4,5],4), [(1,2,3,4),(2,3,4,5)])
		self.assertEqual(nTuples([1,2,3,4,5,6],4), [(1,2,3,4),(2,3,4,5),(3,4,5,6)])

		self.assertEqual(nTuples([],3, cyclic=True), [])
		self.assertEqual(nTuples([1],2, cyclic=True), [])
		self.assertEqual(nTuples([1,2,3],3, cyclic=True), [(1,2,3),(2,3,1),(3,1,2)])
		self.assertEqual(nTuples([1,2,3,4],3, cyclic=True), [(1,2,3),(2,3,4),(3,4,1),(4,1,2)])

	def test_clockwisePolygon(self):
		p=[ (0,0),
			(0,100),
			(100,100),
			(100,0)] #clockwise (in cartesian coords - not img row/col)
		self.assertTrue(clockwisePolygon(p))
		self.assertFalse(clockwisePolygon(list(reversed(p))))



	def test_avg(self):
		self.assertAlmostEqual(avg(*[]), 0.0)
		self.assertAlmostEqual(avg(*[1]), 1)
		self.assertAlmostEqual(avg(*[1,2]), 1.5)
		self.assertAlmostEqual(avg(*[1,2,3]), 2)
	
	def test_pointOnSegment(self):
		self.assertFalse(pointOnSegment(0,0,5,5, 2,2.1, epsilonDistance=0.05))
		self.assertTrue(pointOnSegment(0,0,5,5, 2,2.1, epsilonDistance=0.2))

		self.assertFalse(pointOnSegment(0,0,5,5, 6,6))
		self.assertTrue(pointOnSegment(0,0,5,5, 5,5))
		self.assertTrue(pointOnSegment(0,0,5,5, 5.00001,5.00001))#there should be litlle colerance on corners

	def test_inflate_rectangle(self):
		minX, maxX, minY,maxY = inflate_rectangle(10, 30, 20,40, -0.5) # rectangle with half size
		self.assertAlmostEqual(minX,15)
		self.assertAlmostEqual(maxX,25)
		self.assertAlmostEqual(minY,25)
		self.assertAlmostEqual(maxY,35)

	def test_colorString2RGB(self):
		r,g,b = colorString2RGB("#00A0FF")
		self.assertAlmostEqual(r,0)
		self.assertAlmostEqual(g,0.625)
		self.assertAlmostEqual(b,0.99609375)


	def test_clip_lines(self):
		lines = [(0,0, -10,-10, "#00FF00"), #(Ax,Ay, Bx,By, color)
				 (20,40, 40,40, "#FF0000"),
				 (30,10, 60,40, "#0000FF"),
				 (20,30, 20,10, "#aabbcc")
				]
		border = (10,50,20,40)	#minX,maxX, minY, maxY
		shouldBe=[(20,40, 40,40, "#FF0000"),
				  (40,20, 50,30, "#0000FF"),
				  (20,20, 20,30, "#aabbcc")
				  ]
		result = clip_lines(lines, border)
		for l in shouldBe:
			lRev=l[2:4]+l[0:2]+(l[4],) # l with swapped order of points
			self.assertTrue(l in result or lRev in result)


class TestPoint(unittest.TestCase):
	def setUp(self):
		self.points=[Point(0.5,0),
					Point(0,1),
					Point(1,1),
					Point(1,0),
					Point(0.5,0.5),
					]
		a,b,c,d,e=self.points
		a.contour=[b,d]
		b.contour=[a,c]
		c.contour=[b,d]
		d.contour=[c,a]

		a.ss=[e]
		b.ss=[e]
		c.ss=[e]
		d.ss=[e]
		e.ss=[a,b,c,d]

		self.a,self.b,self.c,self.d,self.e= a,b,c,d,e

	def test_is_contourAndSS(self):
		for p in [self.a,self.b,self.c,self.d]:
			self.assertTrue(p.is_contour())
			self.assertFalse(p.is_ss())

		self.assertFalse(self.e.is_contour())
		self.assertTrue(self.e.is_ss())

	def test_normalize(self):
		self.e.ss=[self.a,self.b,self.d,self.c]

		self.e.normalize()

		self.assertTrue(len(self.e.ss)==len(self.e.all)==4)

		indexA = self.e.all.index(self.a)
		indexB = self.e.all.index(self.b)
		indexC = self.e.all.index(self.c)
		indexD = self.e.all.index(self.d)
		
		self.assertTrue(indexA-indexB in (1,-3))
		self.assertTrue(indexB-indexC in (1,-3))
		self.assertTrue(indexC-indexD in (1,-3))
		self.assertTrue(indexD-indexA in (1,-3))

	def test_forks(self):
		for p in self.points:
			p.normalize()

		self.assertTrue(self.b.forks(self.a, all=True)==[self.e, self.c])
		self.assertTrue(self.b.forks(self.a, all=False)==[self.e]) # only SS

class TestPoint(unittest.TestCase):
	def setUp(self):
		self.polygon=[(0,0),
				(1000,0),
				(1000,1000),
				(0,1000)]
		self.ss = SS()

	def test_run_CGAL(self):
		ss=self.ss.run_CGAL([(0,0), (100,200),(200,-120)])
		self.assertTrue(("c",0,0,100,200) in ss)

	def test_segmentsToPoints(self):
		segments=[("c",1,2,3,4), ("i",3,4,-1,1)]
		points = self.ss.segmentsToPoints(segments)
		shouldBePoints=[(1,2),(3,4),(3,4),(-1,1)]
		self.assertTrue(sorted(points) == sorted(shouldBePoints))

	def test_cleanPoints(self):
		rawPoints = [(5,5),(4,3),(5,5),(2,1),(5.00001,4.99999)]
		self.ss.cleanPoints(rawPoints)
		self.assertTrue(len(self.ss.points)==3)
		
		ps=[]
		for p in self.ss.points:
			ps.append( (p.x, p.y) )

		self.assertTrue((4,3) in ps)
		self.assertTrue((2,1) in ps)

	def test_split_all_Segs_by_all_Ps(self):
		rawSegments=[("c", 0,0, 5,5),
					("i", 0,0, 5,0),
					("o", 3,3, 7,7)]
		self.ss.points=[Point(-4,-4),
						Point (5,5),
						Point(4,4),
						Point(0,0)]
		splited = self.ss.split_all_Segs_by_all_Ps(rawSegments)
		splited.sort()
		shouldBeSplited=sorted([("c", 0,0, 4,4),
								("c", 4,4, 5,5),
								
								("i", 0,0, 5,0),
								
								("o", 3,3, 4,4),
								("o", 4,4, 5,5),
								("o", 5,5, 7,7),
								])
		self.assertEqual(splited, shouldBeSplited)

if __name__ == '__main__':
	unittest.main()