'''
 * Copyright (c) 2014, 2015 Entertainment Intelligence Lab, Georgia Institute of Technology.
 * Originally developed by Mark Riedl.
 * Last edited by Mark Riedl 05/2015
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
'''

import sys, pygame, math, numpy, random, time, copy, operator
from pygame.locals import *

from constants import *
from utils import *
from core import *

# Creates a path node network that connects the midpoints of each nav mesh together
def myCreatePathNetwork(world, agent = None):
	nodes = []
	edges = []
	polys = []
	### YOUR CODE GOES BELOW HERE ###

	allPoints = world.getPoints()
	obstacles = world.getObstacles()
	possiblePolys = []

	# take three points from all points and try to form a triangle from it
	for a in allPoints:
		for b in allPoints:
			for c in allPoints:
				if a == b or b == c or c == a:
					continue
				if not checkTriangleCollision(world, possiblePolys, a, b, c) and not checkTriangleInObstacleOrObstacleInTriangle(world, obstacles, possiblePolys, a, b, c):
					possiblePolys.append(list((a, b, c)))

	# making sure the possible polygon is not a repeat and then adding it
	for poly in possiblePolys:
		poly.sort()
		if poly not in polys:
			polys.append(poly)

	# checking for adjacent polygons in the mesh and combining them
	for x in range(len(polys)):
		for poly1 in polys:
			for poly2 in polys:
				if poly1 == poly2:
					continue
				if polygonsAdjacent(poly1, poly2):
					mergedPoly = mergePolygons(poly1, poly2)
					if isConvex(mergedPoly):
						polys.remove(poly1)
						polys.remove(poly2)
						polys.append(mergedPoly)
						break

	# now getting the path nodes and the path edges
	# setting the midpoint of adjacent polygons to be the nodes (option 2 in hw pdf)
	for poly1 in polys:
		possibleNodes = []
		for poly2 in polys:
			if poly1 == poly2:
				continue
			sharedEdge = polygonsAdjacent(poly1, poly2)
			if sharedEdge:
				midPoint = (((sharedEdge[0][0] + sharedEdge[1][0])/2) , ((sharedEdge[0][1] + sharedEdge[1][1])/2))
				possibleNodes.append(midPoint)
				if midPoint not in nodes:
					nodes.append(midPoint)
		# creating the path edges by joining path nodes, if they have enough space for agent to move
		for x in range(len(possibleNodes)):
			if x == len(possibleNodes) - 1:
				if checkPathOKForAgent(obstacles, possibleNodes[x], possibleNodes[0], agent):
					edges.append((possibleNodes[x], possibleNodes[0]))
			else:
				if checkPathOKForAgent(obstacles, possibleNodes[x], possibleNodes[x + 1], agent):
					edges.append((possibleNodes[x], possibleNodes[x + 1]))

	### YOUR CODE GOES ABOVE HERE ###
	return nodes, edges, polys

def checkTriangleCollision(world, possiblePolys, a, b, c):
	worldLines = world.getLines()
	# adding lines of possible polys to world lines because we want to make sure it doesn't collide with them either
	# basically treating them as obstacles
	for poly in possiblePolys:
		worldLines.append((poly[0], poly[1]))
		worldLines.append((poly[1], poly[2]))
		worldLines.append((poly[0], poly[2]))

	#checking if possible poly edges collide with any existing lines
	if (rayTraceWorldNoEndPoints(a, b, worldLines) is not None and (a, b) not in worldLines and (b, a) not in worldLines) or \
	(rayTraceWorldNoEndPoints(b, c, worldLines) is not None and (b, c) not in worldLines and (c, b) not in worldLines) or \
	(rayTraceWorldNoEndPoints(a, c, worldLines) is not None and (a, c) not in worldLines and (c, a) not in worldLines):
		return True

	return False

def checkTriangleInObstacleOrObstacleInTriangle(world, obstacles, possiblePolys, a, b, c):
	worldLines = world.getLines()

	for poly in possiblePolys:
		worldLines.append((poly[0], poly[1]))
		worldLines.append((poly[1], poly[2]))
		worldLines.append((poly[0], poly[2]))

	for obs in obstacles:

		# checking if an obstacle is inside our possible polygon
		# basically just checking if the center of the obstacle is inside
		obsPts = obs.getPoints()
		obsCenterX = 0
		obsCenterY = 0

		for (x, y) in obsPts:
			obsCenterX = obsCenterX + x
			obsCenterY = obsCenterY + y

		obsCenterX = obsCenterX / len(obsPts)
		obsCenterY = obsCenterY / len(obsPts)

		if pointInsidePolygonPoints((obsCenterX, obsCenterY), (a, b, c)):
			return True

		# checking if our triangles are inside any obstacles
		# using midpoints here because if a poly is gonna be inside, then all points will be inside, so midpoint is easiest
		# any case where not all of poly are in obstacle would be covered by above collision method
		midpt1 = (((a[0] + b[0])/2) , ((a[1] + b[1])/2))
		midpt2 = (((b[0] + c[0])/2) , ((b[1] + c[1])/2))
		midpt3 = (((a[0] + c[0])/2) , ((a[1] + c[1])/2))

		if (pointInsidePolygonLines(midpt1, obs.getLines())) and (a, b) not in worldLines and (b, a) not in worldLines or \
		(pointInsidePolygonLines(midpt2, obs.getLines())) and (b, c) not in worldLines and (c, b) not in worldLines or \
		(pointInsidePolygonLines(midpt3, obs.getLines())) and (a, c) not in worldLines and (c, a) not in worldLines:
			return True

	return False

def mergePolygons(poly1, poly2):
	mergedPts = []
	for point in poly1:
		mergedPts.append(point)
	for point in poly2:
		if point not in mergedPts:
			mergedPts.append(point)

	# now need to make sure that the points are in proper so its an actual convex polygon, and not some sort of criss-crossed shape
	centroidX = 0
	centroidY = 0

	for (x, y) in mergedPts:
		centroidX = centroidX + x
		centroidY = centroidY + y

	centroidX = centroidX / len(mergedPts)
	centroidY = centroidY / len(mergedPts)

	sortingList = []
	sortingDict = {}

	# to sort the points in a proper order we use the angle with respect to the centroid
	for (x,y) in mergedPts:
		angle = math.atan2(centroidY - y, centroidX - x)
		sortingList.append(angle)
		sortingDict[angle] = (x,y)

	sortingList.sort()
	sortedPts = []
	for point in sortingList:
		sortedPts.append(sortingDict[point])

	return sortedPts

def checkPathOKForAgent(obstacles, a, b, agent=None):
	for obs in obstacles:
		for pt in obs.getPoints():
			if minimumDistance((a, b), pt) <= agent.getMaxRadius():
				return False
	return True