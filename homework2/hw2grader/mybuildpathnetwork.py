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

# Creates the path network as a list of lines between all path nodes that are traversable by the agent.
def myBuildPathNetwork(pathnodes, world, agent = None):
    lines = []
    ### YOUR CODE GOES BELOW HERE ###
    for x in range(len(pathnodes)):
        for y in range(len(pathnodes)):
            if y > x:
                obstructed = False
                for obs in world.getObstacles():
                    if rayTraceWorld(pathnodes[x], pathnodes[y], obs.getLines()) is not None:
                        obstructed = True
                if not obstructed:
                    lines.append((pathnodes[x], pathnodes[y]))

    for line in lines:
        for obs in world.getObstacles():
            for point in obs.getPoints():
                if minimumDistance(line, point) < agent.getMaxRadius():
                    if line in lines:
                        lines.remove(line)
    ### YOUR CODE GOES ABOVE HERE ###
    return lines
