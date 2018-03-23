import numpy as np
from functools import partial
from ompl import util as ou
from ompl import base as ob
from ompl import control as oc
from ompl import geometric as og
from scipy.integrate import odeint

from gym_urbandriving.planning import Trajectory


# Dynamics model for our car. Ydim of car should be 40 (default)
def integrator(state, t, acc, delta_f):
    x, y, vel, rad_angle = state
    # Differential equations
    beta = np.arctan((20. / (20. + 20.)) * np.tan(delta_f))
    dx = vel * np.cos(rad_angle + beta)
    dy = vel * -np.sin(rad_angle + beta)
    dangle = (vel / 20.) * np.sin(beta)
    dvel = acc
    output = [dx, dy, dvel, dangle]
    return output

class RRTMPlanner:
    def __init__(self, agents, planner=None, time=None, goal= None, prune = None, selection = None):
        """
        A Kino-Dynamic Planner for multiple agents. 
        
        Parameters
        ----------
        agents : list 
            Agents to be planned over
        planner : str
            Type of Planner to use
        time : float
            Duration to run Planenr
        goal, prune, selection: float
            Parameters of planner, which can be searched over
        """
        self.agents = agents
        self.num_agents = len(agents)

        self.path = []
        self.planner = planner
        self.time = time
        self.goal = goal
        self.prune = prune
        self.selection = selection


    def plan(self, state):
        """
        Generate a plan for the agents
        
        Parameters
        ----------
        state : state of the enviroment
            The plan is generated starting at this state

        Returns:
        ----------
            paths: a list of Trajectories with mode 'cs' (ie. controls to generate the desired trajectory)
            If no trjaectory is found, returns None
        """

        start_state = state
        # construct the state space we are planning in
        # State space will be [x, y, vel, angle]
        # Note: I found docs for ODEStateSpace and MorseStateSpace
        space = ob.RealVectorStateSpace(4*self.num_agents)
        
        
        # set the bounds for the R^2 part of SE(2)
        bounds = ob.RealVectorBounds(4*self.num_agents)
        
        for i in range(self.num_agents):
            car_idx = i*4
            bounds.setLow(car_idx, 0)
            bounds.setLow(car_idx+1, 0)
            bounds.setLow(car_idx+2, 0) # This is the velocity component. Set to a negative number to allow backtracking
            bounds.setLow(car_idx+3, 0)
            bounds.setHigh(car_idx+0, state.dimensions[0]) 
            bounds.setHigh(car_idx+1, state.dimensions[1])
            bounds.setHigh(car_idx+2, 5)
            bounds.setHigh(car_idx+3, 2*np.pi)

        space.setBounds(bounds)

        # create a control space
        cspace = oc.RealVectorControlSpace(space, 2*self.num_agents)

        # set the bounds for the control space
        cbounds = ob.RealVectorBounds(2*self.num_agents)
        for i in range(self.num_agents):
            cbounds.setLow(-3.)
            cbounds.setHigh(3.)

        cspace.setBounds(cbounds)

        def isStateValid(spaceInformation, state):
            # perform collision checking or check if other constraints are
            # satisfied
            for i in range(self.num_agents):
                car_idx = i*4
                start_state.dynamic_objects[i].shapely_obj = None
                start_state.dynamic_objects[i].x = state[car_idx]
                start_state.dynamic_objects[i].y = state[car_idx+1]
                start_state.dynamic_objects[i].angle = state[car_idx+3]
                if start_state.collides_any(i):
                     return False
            return spaceInformation.satisfiesBounds(state)

        def propagate(start, control, duration, state):
            # State propogator to allow ompl to step to another state given a list of actions
            assert(duration == 1.0)

            for i in range(self.num_agents):

                car_idx = i*4
                cntr_idx = i*2

                # Rest of these lines are from car kinematic step functions
                action = (control[cntr_idx], control[cntr_idx+1])
                obj = start_state.dynamic_objects[i]

                if obj.dynamics_model == "kinematic":
                    state[car_idx], state[car_idx+1], state[car_idx+2], state[car_idx+3] = \
                        obj.kinematic_model_step(action, start[car_idx], start[car_idx+1], start[car_idx+2], start[car_idx+3])
                else:
                    state[car_idx], state[car_idx+1], state[car_idx+2], state[car_idx+3] = \
                        obj.point_model_step(action, start[car_idx], start[car_idx+1], start[car_idx+2], start[car_idx+3])


        # define a simple setup class
        ss = oc.SimpleSetup(cspace)
        ss.setStateValidityChecker(ob.StateValidityCheckerFn(partial(isStateValid, ss.getSpaceInformation())))
        ss.setStatePropagator(oc.StatePropagatorFn(propagate))

        # create a start state
        start = ob.State(space)

        for i in range(self.num_agents):
            car_idx = i*4
            start()[car_idx] = state.dynamic_objects[i].x
            start()[car_idx+1] = state.dynamic_objects[i].y
            start()[car_idx+2] = state.dynamic_objects[i].vel
            start()[car_idx+3] = state.dynamic_objects[i].angle

        goal = ob.State(space);

        # create a goal state
        for i in range(self.num_agents):
            car_idx = i*4
            goal_state = state.dynamic_objects[i].destination
        
            goal()[car_idx] = goal_state[0]
            goal()[car_idx+1] = goal_state[1]
            goal()[car_idx+2] = goal_state[2]
            goal()[car_idx+3] = goal_state[3]


        # set the start and goal states
        ss.setStartAndGoalStates(start, goal, 0.05)
        # (optionally) set planner
        si = ss.getSpaceInformation()


        if self.planner == 'RRT':
            planner = oc.RRT(si) # this is the default
        elif self.planner == 'SST':
            planner = oc.SST(si)
        elif self.planner == 'EST':
            planner = oc.EST(si)
        elif self.planner == 'KPIECE':
            planner = oc.KPIECE1(si)
        else:
            planner = oc.RRT(si)

        if not self.selection is None:
            planner.setSelectionRadius(self.selection)
        if not self.prune is None:
            planner.setPruningRadius(self.prune)
        
        if not self.goal is None:
            planner.setGoalBias(self.goal)

        ss.setPlanner(planner)
        # (optionally) set propagation step size
        si.setPropagationStepSize(1) # Propagation step size should be 1 to match our model
        
        # attempt to solve the problem
        if not self.time == None:
            solved = ss.solve(self.time) # 30 second time limit
        else: 
            solved = ss.solve(60.0)

        if solved:
            # prints the path to screen
            print("Found solution:\n%s" % ss.getSolutionPath())
            path = ss.getSolutionPath().printAsMatrix()
            path = [l.split(" ") for l in path.splitlines()]

            num_controls = 2*self.num_agents+1
            
            path = [[float(i) for i in l][-num_controls:] for l in path][1:]
            paths = []
            for i in range(self.num_agents):
                car_idx = i*2
                agent_path = Trajectory(mode='cs')

                for control in path:
                    for r in range(int(control[-1])):
                        agent_path.add_point([control[car_idx],control[car_idx+1]])
                
                paths.append(agent_path)
            return paths
        else:
            return None
        
        

        
            