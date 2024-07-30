#!/usr/bin/env python
# coding: utf-8

# In[1]:


#imports
from statistics import mean
from ipythonblocks import BlockGrid
from IPython.display import HTML, display, clear_output
from time import sleep

import numpy as np
import random
import copy
import collections
import numbers

#Making Thing objects
class Thing:

    def __repr__(self):
        return '<{}>'.format(getattr(self, '__name__', self.__class__.__name__))

    def is_alive(self):
        return hasattr(self, 'alive') and self.alive

    def display(self, canvas, x, y, width, height):
        pass

class Chair(Thing):
    pass

class Trolley(Thing):
    pass

class Person(Thing):
    pass

class Bump(Thing):
    pass


# Setting up environment
class Environment():
    def __init__(self, width, height, boundary=True, color={}, display=False):
        self.things = []
        self.agents = []

        self.done = 1
        self.width = width
        self.height = height
        self.observers = []
        # Sets iteration start and end (no walls).
        self.x_start, self.y_start = (0, 0)
        self.x_end, self.y_end = (self.width, self.height)

        self.grid = BlockGrid(width, height, fill=(200, 200, 200))
        if display:
            self.grid.show()
            self.visible = True
        else:
            self.visible = False
        self.bounded = boundary
        self.colors = color

    def exogenous_change(self):
        pass

    def is_done(self):
        # this isn't used right now
        # if len(self.things) == 3:
        # return True
        # ends when condition is met
        if self.done == 0:
            return True
        return not any(agent.is_alive() for agent in self.agents)

    def step(self):
        if not self.is_done():
            actions = []
            for agent in self.agents:
                if agent.alive:
                    actions.append(agent.program(self.percept(agent)))
                else:
                    actions.append("")
            for (agent, action) in zip(self.agents, actions):
                self.execute_action(agent, action)
            self.exogenous_change()

    def run(self, steps=1000, delay=1):
        for step in range(steps):
            self.update(delay)
            if self.is_done():
                break
            self.step()
        self.update(delay)

    def update(self, delay=1):
        sleep(delay)
        self.reveal()

    def reveal(self):
        self.draw_world()
        # wait for the world to update and
        # apply changes to the same grid instead
        # of making a new one.
        clear_output(wait=True)
        self.grid.show()
        self.visible = True

    def draw_world(self):
        self.grid[:] = (200, 200, 200)
        world = self.get_world()
        for x in range(0, len(world)):
            for y in range(0, len(world[x])):
                if len(world[x][y]):
                    self.grid[y, x] = self.colors[world[x][y][-1].__class__.__name__]

    def list_things_at(self, location, tclass=Thing):
        # gives all objects at the chosen location
        if isinstance(location, numbers.Number):
            return [thing for thing in self.things
                    if thing.location == location and isinstance(thing, tclass)]
        return [thing for thing in self.things
                if all(x == y for x, y in zip(thing.location, location)) and isinstance(thing, tclass)]

    def add_thing(self, thing, location=None):
        # adds objects to the room
        if not isinstance(thing, Thing):
            thing = Agent(thing)
        if thing in self.things:
            print("Can't add the same thing twice")
        else:
            thing.location = location if location is not None else self.default_location(thing)
            self.things.append(thing)
            if isinstance(thing, Agent):
                thing.performance = 0
                self.agents.append(thing)

    def delete_thing(self, thing):
        # deletes objects from the room
        try:
            self.things.remove(thing)
        except ValueError as e:
            print(e)
            print("  in Environment delete_thing")
            print("  Thing to be removed: {} at {}".format(thing, thing.location))
            print("  from list: {}".format([(thing, thing.location) for thing in self.things]))
        if thing in self.agents:
            self.agents.remove(thing)


# agents specification from other things
class Agent(Thing):

    def __init__(self, program=None):
        #when the bots work is done it's easy to kill it and thus no further actions should take place
        self.alive = True
        self.bump = False
        self.holding = []
        self.performance = 0
        if program is None or not isinstance(program, collections.abc.Callable):
            print("Can't find a valid program for {}, falling back to default.".format(self.__class__.__name__))

            def program(percept):
                return eval(input('Percept={}; action? '.format(percept)))

        self.program = program


# set up specific room
class roomarea(Environment):
    def __init__(self, width, height, boundary=True, color={}, display=False):

        super().__init__(width, height, boundary, color, display)
        self.chairs = []
        self.new_chair_index = 0

    def is_inbounds(self, location):

        x, y = location
        return not (x < self.x_start or x >= self.x_end or y < self.y_start or y >= self.y_end)

    def get_world(self):

        result = []
        x_start, y_start = (0, 0)
        x_end, y_end = self.width, self.height
        for x in range(x_start, x_end):
            row = []
            for y in range(y_start, y_end):
                row.append(self.list_things_at((x, y)))
            result.append(row)
        return result

    def step(self):
        for agent in self.agents:
            if (agent.cleaningliquid <= 0) and (agent.location[0] == 0) and (agent.location[1] == 0):
                agent.alive = False
        super().step()

    def percept(self, agent):
        things = self.list_things_at(agent.location)
        ts_up = self.list_things_at([agent.location[0], agent.location[1] - 1])
        ts_down = self.list_things_at([agent.location[0], agent.location[1] + 1])
        ts_left = self.list_things_at([agent.location[0] - 1, agent.location[1]])
        ts_right = self.list_things_at([agent.location[0] + 1, agent.location[1]])
        ts_up_left = self.list_things_at([agent.location[0] - 1, agent.location[1] - 1])
        ts_up_right = self.list_things_at([agent.location[0] + 1, agent.location[1] - 1])
        ts_down_left = self.list_things_at([agent.location[0] - 1, agent.location[1] + 1])
        ts_down_right = self.list_things_at([agent.location[0] + 1, agent.location[1] + 1])
        loc = copy.deepcopy(agent.location)  # find out the target location
        # check if agent is about to bump into a wall
        if agent.direction.direction == Direction.R:
            loc[0] += 1
        elif agent.direction.direction == Direction.L:
            loc[0] -= 1
        elif agent.direction.direction == Direction.D:
            loc[1] += 1
        elif agent.direction.direction == Direction.U:
            loc[1] -= 1
        if not self.is_inbounds(loc):
            things.append(Bump())
        return things, ts_up, ts_down, ts_left, ts_right, ts_up_left, ts_up_right, ts_down_left, ts_down_right

    def execute_action(self, agent, action):
        # changes the state of the environment based on what the agent does.
        # there are the basic actions such as turning and moving
        if action == 'turnright':
            # print('{} decided to {} at location: {}'.format(str(agent)[1:-1], action, agent.location))
            agent.turn(Direction.R)
        elif action == 'turnleft':
            # print('{} decided to {} at location: {}'.format(str(agent)[1:-1], action, agent.location))
            agent.turn(Direction.L)
        elif action == 'moveforward':
            # print('{} decided to move {}wards at location: {}'.format(str(agent)[1:-1], agent.direction.direction, agent.location))
            agent.moveforward()
        # these next two actions check if the action is to clean
        # if acter cleaning the object there is no more cleaning liquid the bot is moved back to the start and stops running
        # due to this a check for liquid isn't needed as it wouldn't be running if it was out
        elif (action == "CleanChair"):
            items = self.list_things_at(agent.location, tclass=Chair)
            if len(items) != 0:
                if agent.CleanChair(items[0]):
                    # print('{} cleaned {} at location: {}'
                    # .format(str(agent)[1:-1], str(items[0])[1:-1], agent.location))
                    agent.useLiquid()
                    self.delete_thing(items[0])
                    # after cleaning if liquid is o it uses the bots current location to return the bot
                    if (agent.cleaningliquid == 0):
                        if agent.direction.direction == Direction.R:
                            agent.turn(Direction.L)
                        if agent.direction.direction == Direction.L:
                            agent.turn(Direction.L)
                        if agent.direction.direction == Direction.D:
                            agent.turn(Direction.L)
                            agent.turn(Direction.L)
                        for i in range(agent.location[1]):
                            agent.moveforward()
                        agent.turn(Direction.L)
                        for i in range(agent.location[0]):
                            agent.moveforward()
                        roomarea.done = 0
                        roomarea.is_done(self)
        elif (action == "CleanTrolley"):
            items = self.list_things_at(agent.location, tclass=Trolley)
            if len(items) != 0:
                if agent.CleanTrolley(items[0]):
                    # print('{} cleaned {} at location: {}'
                    # .format(str(agent)[1:-1], str(items[0])[1:-1], agent.location))
                    agent.useLiquid()
                    self.delete_thing(items[0])
                    if (agent.cleaningliquid == 0):
                        if agent.direction.direction == Direction.R:
                            agent.turn(Direction.L)
                        if agent.direction.direction == Direction.L:
                            agent.turn(Direction.L)
                        if agent.direction.direction == Direction.D:
                            agent.turn(Direction.L)
                            agent.turn(Direction.L)
                        for i in range(agent.location[1]):
                            agent.moveforward()
                        agent.turn(Direction.L)
                        for i in range(agent.location[0]):
                            agent.moveforward()
                        roomarea.done = 0
                        roomarea.is_done(self)


        # At first I tried to mak it clean in different directions in the program but realised the bot may not be looking in the
        # same direction when it sees items and program doesn't implement agents direction

        # I tried to connect the diagnal moves use just the cardinal directions but it doesn't seem to work but I just need to make
        # slight alterations
        elif action == "cleanup":
            if agent.direction.direction == Direction.R:
                agent.turn(Direction.L)
                agent.moveforward()
            if agent.direction.direction == Direction.L:
                agent.turn(Direction.R)
                agent.moveforward()
            if agent.direction.direction == Direction.U:
                agent.moveforward()
            if agent.direction.direction == Direction.D:
                agent.turn(Direction.L)
                agent.turn(Direction.L)
                agent.moveforward()

        elif action == "cleanupright":
            if agent.direction.direction == Direction.R:
                agent.turn(Direction.L)
                agent.moveforward()
                agent.turn(Direction.R)
                agent.moveforward()
            if agent.direction.direction == Direction.L:
                agent.turn(Direction.R)
                agent.moveforward()
                agent.turn(Direction.R)
                agent.moveforward()
            if agent.direction.direction == Direction.U:
                agent.moveforward()
                agent.turn(Direction.R)
                agent.moveforward()
            if agent.direction.direction == Direction.D:
                agent.turn(Direction.L)
                agent.turn(Direction.L)
                agent.moveforward()
                agent.turn(Direction.R)
                agent.moveforward()

        elif action == "cleanupleft":
            if agent.direction.direction == Direction.R:
                agent.turn(Direction.L)
                agent.moveforward()
                agent.turn(Direction.L)
                agent.moveforward()
            if agent.direction.direction == Direction.L:
                agent.turn(Direction.R)
                agent.moveforward()
                agent.turn(Direction.L)
                agent.moveforward()
            if agent.direction.direction == Direction.U:
                agent.moveforward()
                agent.turn(Direction.L)
                agent.moveforward()
            if agent.direction.direction == Direction.D:
                agent.turn(Direction.L)
                agent.turn(Direction.L)
                agent.moveforward()
                agent.turn(Direction.L)
                agent.moveforward()

        elif action == 'cleanleft':
            if agent.direction.direction == Direction.R:
                agent.turn(Direction.L)
                agent.turn(Direction.L)
                agent.moveforward()
            if agent.direction.direction == Direction.L:
                agent.moveforward()
            if agent.direction.direction == Direction.U:
                agent.turn(Direction.L)
                agent.moveforward()
            if agent.direction.direction == Direction.D:
                agent.turn(Direction.R)
                agent.moveforward()

        elif action == 'cleanright':
            if agent.direction.direction == Direction.R:
                agent.moveforward()
            if agent.direction.direction == Direction.L:
                agent.turn(Direction.L)
                agent.turn(Direction.L)
                agent.moveforward()
            if agent.direction.direction == Direction.U:
                agent.turn(Direction.R)
                agent.moveforward()
            if agent.direction.direction == Direction.D:
                agent.turn(Direction.L)
                agent.moveforward()

        elif action == 'cleandown':
            if agent.direction.direction == Direction.R:
                agent.turn(Direction.R)
                agent.moveforward()
            if agent.direction.direction == Direction.L:
                agent.turn(Direction.L)
                agent.moveforward()
            if agent.direction.direction == Direction.U:
                agent.turn(Direction.L)
                agent.turn(Direction.L)
                agent.moveforward()
            if agent.direction.direction == Direction.D:
                agent.moveforward()

        elif action == 'cleandownleft':
            if agent.direction.direction == Direction.R:
                agent.turn(Direction.R)
                agent.moveforward()
                agent.turn(Direction.R)
                agent.moveforward()
            if agent.direction.direction == Direction.L:
                agent.turn(Direction.L)
                agent.moveforward()
                agent.turn(Direction.R)
                agent.moveforward()
            if agent.direction.direction == Direction.U:
                agent.turn(Direction.L)
                agent.turn(Direction.L)
                agent.moveforward()
                agent.turn(Direction.R)
                agent.moveforward()
            if agent.direction.direction == Direction.D:
                agent.moveforward()
                agent.turn(Direction.R)
                agent.moveforward()

        elif action == 'cleandownright':
            if agent.direction.direction == Direction.R:
                agent.turn(Direction.R)
                agent.moveforward()
                agent.turn(Direction.L)
                agent.moveforward()
            if agent.direction.direction == Direction.L:
                agent.turn(Direction.L)
                agent.moveforward()
                agent.turn(Direction.L)
                agent.moveforward()
            if agent.direction.direction == Direction.U:
                agent.turn(Direction.L)
                agent.turn(Direction.L)
                agent.moveforward()
                agent.turn(Direction.L)
                agent.moveforward()
            if agent.direction.direction == Direction.D:
                agent.moveforward()
                agent.turn(Direction.L)
                agent.moveforward()


class Direction:
    R = "right"
    L = "left"
    U = "up"
    D = "down"

    def __init__(self, direction):
        self.direction = direction

    def __add__(self, heading):
        if self.direction == self.R:
            return {
                self.R: Direction(self.D),
                self.L: Direction(self.U),
            }.get(heading, None)
        elif self.direction == self.L:
            return {
                self.R: Direction(self.U),
                self.L: Direction(self.D),
            }.get(heading, None)
        elif self.direction == self.U:
            return {
                self.R: Direction(self.R),
                self.L: Direction(self.L),
            }.get(heading, None)
        elif self.direction == self.D:
            return {
                self.R: Direction(self.L),
                self.L: Direction(self.R),
            }.get(heading, None)

    def move_forward(self, from_location):
        # get the iterable class to return
        iclass = from_location.__class__
        x, y = from_location
        if self.direction == self.R:
            return iclass((x + 1, y))
        elif self.direction == self.L:
            return iclass((x - 1, y))
        elif self.direction == self.U:
            return iclass((x, y - 1))
        elif self.direction == self.D:
            return iclass((x, y + 1))
        
    def __eq__(self, other):
        if isinstance(other, Direction):
            return self.direction == other.direction
        elif isinstance(other, str):
            return self.direction == other
        return False


class CleanBot(Agent):
    def __init__(self, program=None, optimal=False):
        super().__init__(program)
        self.location = [0, 0]
        self.cleaningliquid = 1
        self.direction = Direction("down")
        self.optimal = optimal
        self.path = [self.location]
        self.done_columns = []
        self.needed_cleaning = []
        self.final_column = 0

    # These are to make it such that the bot can clean a specific number of items before returning
    # (in the run block I set the number of items it can clean to the number of chairs and trolleys created so it will clean them all)
    def addLiquid(self, amount):
        self.cleaningliquid = amount

    def useLiquid(self):
        self.cleaningliquid = self.cleaningliquid - 1

    """def faceup(self):
        print("faceup")
        print(self.direction)
        if self.direction == Direction("down"):
            return 'turnleft', 'turnleft', 'goup'
        if self.direction == Direction("left"):
            return 'turnright', 'goup'
        if self.direction == Direction("right"):
            return 'turnleft', 'goup'
        if self.direction == Direction("up"):
            return 'goup'

    def goup(self):
        print("goup")
        if self.location[1] != 0:
            return 'goup'
        if self.location[1] == 0:
            return 'faceleft'

    def faceleft(self):
        if self.direction == Direction("down"):
            return 'turnright', 'goleft'
        if self.direction == Direction("left"):
            return 'goleft'
        if self.direction == Direction("right"):
            return 'turnleft', 'turnleft', 'goleft'
        if self.direction == Direction("up"):
            return 'turnleft', 'goleft'

    def goleft(self):
        if self.location[0] != 0:
            return 'goleft'
        if self.location[1] == 0:
            return 'end'"""

    def moveforward(self, success=True):
        # moveforward possible only if success (i.e. valid destination location)
        if not success:
            return
        if self.direction.direction == Direction.R:
            self.location[0] += 1
        elif self.direction.direction == Direction.L:
            self.location[0] -= 1
        elif self.direction.direction == Direction.D:
            self.location[1] += 1
        elif self.direction.direction == Direction.U:
            self.location[1] -= 1
        
        self.path.append(tuple(self.location))

    def turn(self, d):
        self.direction = self.direction + d

    # I have a seperate functions for each of the objects I must clean however I believe I could have combined them with
    # with an or statement in the if
    def CleanTrolley(self, thing):
        # returns True upon success or False otherwise#
        if isinstance(thing, Trolley):
            return True
        return False

    def CleanChair(self, thing):
        if isinstance(thing, Chair):
            return True
        return False

    def bumpPerson(self, thing):
        # returns True upon success or False otherwise
        if isinstance(thing, Person):
            return True
        return False


def program(percepts):
    things, ts_up, ts_down, ts_left, ts_right, ts_up_left,     ts_up_right, ts_down_left, ts_down_right = percepts

    if bot.optimal:
        if bot.final_column != 0:
            doing_column = bot.final_column
        else:
            doing_column = 1 + (len(bot.done_columns)*3)
    
    # this s used to check if what is on the agents currecnt location and tells it what to do
    for t in things:
        if isinstance(t, Chair):
            return 'CleanChair'
        if isinstance(t, Trolley):
            return 'CleanTrolley'
        if isinstance(t, Bump):
            if bot.optimal:
                if bot.direction == Direction("down"):
                    if bot.location[0] == doing_column:
                        bot.done_columns.append(bot.location[0])
                    bot.turn(Direction.L)
                    #return 'turnleft'
                elif bot.direction == Direction("up"):
                    if bot.location[0] == doing_column:
                        bot.done_columns.append(bot.location[0])
                    bot.turn(Direction.R)
                    #return 'turnright'
                elif bot.direction == Direction("right"):
                    bot.final_column = bot.location[0]
            else:
                choice = random.choice((1, 2))
                if choice == 1:
                    return 'turnright'
                elif choice == 2:
                    return 'turnleft'
        """if isinstance(t, Person): 
            # turn = False
            choice = random.choice((1,2));
            print(f"reached person, turning {choice}")
            if choice == 1:
                return 'turnright'
            elif choice == 2:
                return 'turnleft'"""
    # these are when the bot percepts an object nearby and can choose to appropriate way to get to it
    # After percepting the areas around the bot, the bot will check if there is a trolley or chair, if there is it will use the
    # action appropriate for where around the robot it is(ie. if it's to the top left it will use that action)
    # then in the action it will check what direction the bot is facing and choose depending how it can efficiently move to the
    # object
    # ie. if it sees a chair to the bottom right and the bot's facing down, it will move down one, turn left so it's facing right
    # then move forward again and clean
    
    
    
    for t in ts_up:
        if len(bot.needed_cleaning) > 0:
            continue
        if (isinstance(t, Chair)) or (isinstance(t, Trolley)):
            print("the bot is going up to clean")
            bot.needed_cleaning.append('cleanup')
            bot.needed_cleaning.append('cleandown')

    for t in ts_down:
        if len(bot.needed_cleaning) > 0:
            continue
        if (isinstance(t, Chair)) or (isinstance(t, Trolley)):
            # print("the bot is going down to clean")
            bot.needed_cleaning.append('cleandown')
            bot.needed_cleaning.append('cleanup')

    for t in ts_left:
        if len(bot.needed_cleaning) > 0:
            continue
        if (isinstance(t, Chair)) or (isinstance(t, Trolley)):
            # print("the bot is going left to clean")
            bot.needed_cleaning.append('cleanleft')
            bot.needed_cleaning.append('cleanright')

    for t in ts_right:
        if len(bot.needed_cleaning) > 0:
            continue
        if (isinstance(t, Chair)) or (isinstance(t, Trolley)):
            # print("the bot is going right to clean")
            bot.needed_cleaning.append('cleanright')
            bot.needed_cleaning.append('cleanleft')

    for t in ts_up_left:
        if len(bot.needed_cleaning) > 0:
            continue
        if (isinstance(t, Chair)) or (isinstance(t, Trolley)):
            # print("the bot is going up left to clean")
            bot.needed_cleaning.append('cleanupleft')
            bot.needed_cleaning.append('cleandownright')

    for t in ts_up_right:
        if len(bot.needed_cleaning) > 0:
            continue
        if (isinstance(t, Chair)) or (isinstance(t, Trolley)):
            # print("the bot is going up right to clean")
            bot.needed_cleaning.append('cleanupright')
            bot.needed_cleaning.append('cleandownleft')

    for t in ts_down_left:
        if len(bot.needed_cleaning) > 0:
            continue
        if (isinstance(t, Chair)) or (isinstance(t, Trolley)):
            # print("the bot is going down left to clean")
            bot.needed_cleaning.append('cleandownleft')
            bot.needed_cleaning.append('cleanupright')

    for t in ts_down_right:
        if len(bot.needed_cleaning) > 0:
            continue
        if (isinstance(t, Chair)) or (isinstance(t, Trolley)):
            # print("the bot is going down right to clean")
            bot.needed_cleaning.append('cleandownright')
            bot.needed_cleaning.append('cleanupleft')

    if len(bot.needed_cleaning) > 0:
        temp = bot.needed_cleaning.pop(0)
        return temp
    
    #if bot.needed_cleaning:
    #    return bot.needed_cleaning.pop(0)
        
    if bot.optimal:
        print(bot.location)
        
        
        
        #print(bot.location)
        #print(bot.direction)
        #print(bot.direction == Direction("up"))
        #print(bot.direction == Direction("down"))
        #print(bot.direction == Direction("left"))
        #print(bot.direction == Direction("right"))
        #print(doing_column)
        print(things)
        print(ts_up)
        print(ts_down)
        
        if bot.location[0] < doing_column:
            if bot.direction != Direction("right"):
                print("here10")
                return 'turnright'
            print("here11")
            return 'moveforward'
        if bot.location[0] > doing_column:
            if bot.direction != Direction("left"):
                print("here12")
                return 'turnleft'
            print("here13")
            return 'moveforward'
                
        
        if bot.location[0] == doing_column:
            if (doing_column % 2) == 1:
                for t in things:
                    if isinstance(t, Bump):  
                        if bot.direction == Direction("down"):
                            bot.done_columns.append(bot.location[0])
                            bot.turn(Direction.L)
                            print("here5")
                            return 'turnleft'
                if bot.direction != Direction("down"):
                    print("here1")
                    return 'turnright' 
               
                print("here")
                return 'moveforward'
            elif (doing_column % 2) == 0:
                for t in things:
                    if isinstance(t, Bump):  
                        if bot.direction == Direction("up"):
                            bot.done_columns.append(bot.location[0])
                            bot.turn(Direction.L)
                            print("here4")
                            return 'turnright'
                if bot.direction != Direction("up"):
                    print("here3")
                    return 'turnleft' 
                print("here2")
                return 'moveforward'
            

        
    
    # when not seeing anything this'll have the bot moving randomly with a higher chance or going forward if possible
    choice = random.choice((1, 2, 3, 4, 5, 6, 7, 8))
    if choice == 1:
        return 'turnright'
    elif choice == 2:
        return 'turnleft'
    else:
        return 'moveforward'


# Run
from IPython.display import HTML

# these will create a random size for the room within a changable range, then create a random number of objects less than the
# size of the length of one side of the room, then find a random number within the item range to randomize how many chairs
# and trolleys there are
n = random.randint(3, 20)
print("room size")
print(n)

m = random.randint(2, n - 1)
mm = random.randint(1, m)
width = n
height = n
room = roomarea(width=n, height=n,
                color={'CleanBot': (255, 0, 0), 'Chair': (0, 255, 0), 'Person': (2, 2, 2), 'Trolley': (0, 0, 255)})
bot = CleanBot(program, optimal=True)
# this sets the number of times the bot can clean before returning to the number of items placed
bot.addLiquid(m)
room.add_thing(bot, [0, 0])
objects = []
# this makes sure there are no items on the bots starting area
objects.append([0, 0])

# these create random locations for the objects then place them into the enviornment
chairs = []
while len(chairs) < (m - mm):
    loc_x = random.randint(0, width - 1)
    loc_y = random.randint(0, height - 1)
    if [loc_x, loc_y] not in objects:
        chairs.append([loc_x, loc_y])
        objects.append([loc_x, loc_y])

people = []
while len(people) < 1:
    loc_x = random.randint(0, width - 1)
    loc_y = random.randint(0, height - 1)
    if [loc_x, loc_y] not in objects:
        people.append([loc_x, loc_y])
        objects.append([loc_x, loc_y])

trolleys = []
while len(trolleys) < (mm):
    loc_x = random.randint(0, width - 1)
    loc_y = random.randint(0, height - 1)
    if [loc_x, loc_y] not in objects:
        trolleys.append([loc_x, loc_y])
        objects.append([loc_x, loc_y])

for i in range(len(chairs)):
    room.add_thing(Chair(), chairs[i])

for i in range(len(people)):
    room.add_thing(Person(), people[i])

for i in range(len(trolleys)):
    room.add_thing(Trolley(), trolleys[i])

room.run(5000)

# The algorithmn for part 3 will/should be based based on the fact that the bot can percieve the 8 squares around it, thus if it
# goes down a column it would actually be able to get all objects in the column and the 2 to the left and right of it
# to figure out how many columns and which columns must be used can be mathimatically figured out
# number of columns = width/3(rounded down) + 1
# this works as each column gone down = 3 done(so with 4 columns it would be 4/3(rounded) so 1 + 1 as it would go down the last
# column to find the remainders if they're not all found already)
# now to find which columns we need to choose them conditionally to be the most efficient(if the remainder of width/3 == 0, we
# follow the pattern (colomn x = 2 + (column number)*3) except for the last column where it's x is just width)
# 1 2 3 4 5 6 7 8
# |y|x|y|y|x|y|y|x| this is showing a rudementary grid, if there's an x in the column it means the bot will go down it, if
# |y|x|y|y|x|y|y|x| there's a y it means the but can see it and clean the square
# this was an example of the bot only needing to go up and down realistically 3 times go get all objects in a grid with width 8

# an example of width 7 it's the same except the final column as you can see below
# 1 2 3 4 5 6 7
# |y|x|y|y|x|y|x|
# |y|x|y|y|x|y|x|












# In[ ]:





# In[ ]:





# In[ ]:




