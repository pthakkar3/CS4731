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

import sys, pygame, math, numpy, random, time, copy
from pygame.locals import * 

from constants import *
from utils import *
from core import *
from mycreatepathnetwork import *
from mynavigatorhelpers import *
from heapq import *


###############################
### AStarNavigator
###
### Creates a path node network and implements the A* algorithm to create a path to the given destination.
			
class AStarNavigator(NavMeshNavigator):

	def __init__(self):
		NavMeshNavigator.__init__(self)
		

	### Create the path node network.
	### self: the navigator object
	### world: the world object
	def createPathNetwork(self, world):
		self.pathnodes, self.pathnetwork, self.navmesh = myCreatePathNetwork(world, self.agent)
		return None
		
	### Finds the shortest path from the source to the destination using A*.
	### self: the navigator object
	### source: the place the agent is starting from (i.e., its current location)
	### dest: the place the agent is told to go to
	def computePath(self, source, dest):
		self.setPath(None)
		### Make sure the next and dist matrices exist
		if self.agent != None and self.world != None: 
			self.source = source
			self.destination = dest
			### Step 1: If the agent has a clear path from the source to dest, then go straight there.
			###   Determine if there are no obstacles between source and destination (hint: cast rays against world.getLines(), check for clearance).
			###   Tell the agent to move to dest
			### Step 2: If there is an obstacle, create the path that will move around the obstacles.
			###   Find the path nodes closest to source and destination.
			###   Create the path by traversing the self.next matrix until the path node closest to the destination is reached
			###   Store the path by calling self.setPath()
			###   Tell the agent to move to the first node in the path (and pop the first node off the path)
			if clearShot(source, dest, self.world.getLinesWithoutBorders(), self.world.getPoints(), self.agent):
				self.agent.moveToTarget(dest)
			else:
				start = findClosestUnobstructed(source, self.pathnodes, self.world.getLinesWithoutBorders())
				end = findClosestUnobstructed(dest, self.pathnodes, self.world.getLinesWithoutBorders())
				if start != None and end != None:
					# print len(self.pathnetwork)
					newnetwork = unobstructedNetwork(self.pathnetwork, self.world.getGates())
					# print len(newnetwork)
					closedlist = []
					path, closedlist = astar(start, end, newnetwork)
					if path is not None and len(path) > 0:
						path = shortcutPath(source, dest, path, self.world, self.agent)
						self.setPath(path)
						if self.path is not None and len(self.path) > 0:
							first = self.path.pop(0)
							self.agent.moveToTarget(first)
		return None
		
	### Called when the agent gets to a node in the path.
	### self: the navigator object
	def checkpoint(self):
		myCheckpoint(self)
		return None

	### This function gets called by the agent to figure out if some shortcuts can be taken when traversing the path.
	### This function should update the path and return True if the path was updated.
	def smooth(self):
		return mySmooth(self)

	def update(self, delta):
		myUpdate(self, delta)


def unobstructedNetwork(network, worldLines):
	newnetwork = []
	for l in network:
		hit = rayTraceWorld(l[0], l[1], worldLines)
		if hit == None:
			newnetwork.append(l)
	return newnetwork




def astar(init, goal, network):
	#print("A-star called")
	path = []
	open = []
	closed = []
	### YOUR CODE GOES BELOW HERE ###
	# heuristic will be distance to get there(cost) + distance to goal
	# this is how I will sort open
	distances = {init: 0}
	previous = {}
	heuristic = {init: distances[init] + distance(init, goal)}
	open.append(init)
	current = init
	while current != goal and open:
		open = sortOpen(open, heuristic)
		current = open[0]
		closed.append(current)
		open.remove(current)
		successors = getSuccessors(current, network)
		for s in successors:
			if s not in closed:
				sCost = distances[current] + distance(current, s)
				if s not in open or sCost < distances[s]:
					distances[s] = sCost
					previous[s] = current
					heuristic[s] = distances[s] + distance(s, goal)
					if s not in open:
						open.append(s)

	if current == goal:
		path.append(current)
		while current in previous:
			current = previous[current]
			if current == init:
				continue
			else:
				path = [current] + path
		path = [init] + path


	### YOUR CODE GOES ABOVE HERE ###
	return path, closed

def sortOpen(open, heuristic):
	sorted = []
	for node in open:
		sorted.append((node, heuristic[node]))
	sorted.sort(key=lambda x: x[1])
	for x in range(len(sorted)):
		sorted[x] = sorted[x][0]
	return sorted

def getSuccessors(node, network):
	successors = []
	for edge in network:
		if node in edge and node == edge[0] and edge[1] not in successors:
			successors.append(edge[1])
		elif node in edge and node == edge[1] and edge[0] not in successors:
			successors.append(edge[0])
	return successors


def myUpdate(nav, delta):
	### YOUR CODE GOES BELOW HERE ###
	# print("update called")
	gates = nav.world.getGates()
	for gate in gates:
		if nav.getDestination() is None or rayTrace(nav.agent.getLocation(), nav.agent.moveTarget,
													gate) is not None or minimumDistance(gate,
																						 nav.agent.getLocation()) <= nav.agent.getMaxRadius():
			nav.agent.stopMoving()
			nav.setPath(None)
			break

	### YOUR CODE GOES ABOVE HERE ###
	return None



def myCheckpoint(nav):
	### YOUR CODE GOES BELOW HERE ###
	# gates = nav.world.getGates()
	# for gate in gates:
	# 	if nav.getDestination() is None or rayTrace(nav.agent.getLocation(), nav.agent.moveTarget,
	# 												gate) is not None or minimumDistance(gate,
	# 																					 nav.agent.getLocation()) <= nav.agent.getMaxRadius():
	# 		nav.agent.stopMoving()
	# 		break

	### YOUR CODE GOES ABOVE HERE ###
	return None


### Returns true if the agent can get from p1 to p2 directly without running into an obstacle.
### p1: the current location of the agent
### p2: the destination of the agent
### worldLines: all the lines in the world
### agent: the Agent object
def clearShot(p1, p2, worldLines, worldPoints, agent):
	### YOUR CODE GOES BELOW HERE ###

	if rayTraceWorldNoEndPoints(p1, p2, worldLines) is not None:
		return False
	else:
		for point in worldPoints:
			if minimumDistance((p1, p2), point) <= agent.getMaxRadius():
				return False
		return True

	### YOUR CODE GOES ABOVE HERE ###
	return False

