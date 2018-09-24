import fluids
from fluids.utils import fluids_print
import argparse
import time

key_help = """
Keyboard commands for when visualizer is running:
   .            Increases debug visualization
   ,            Decreases debug visualization
   o            Switches observation type
"""

parser = argparse.ArgumentParser(description='FLUIDS First Order Lightweight Urban Intersection Driving Simulator',
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=key_help)
parser.add_argument('-b', metavar='N', type=int, default=10, 
                    help='Number of background cars')
parser.add_argument('-c', metavar='N', type=int, default=1, 
                    help='Number of controlled cars')
parser.add_argument('-p', metavar='N', type=int, default=5, 
                    help='Number of background pedestrians')
parser.add_argument('-v', metavar='N', type=int, default=1,
                    help='Visualization level')
parser.add_argument('-o', metavar='str', type=str, default="birdseye",
                    choices=["none", "birdseye", "grid"],
                    help='Observation type')
parser.add_argument('--screen-height', metavar='N', dest='screen_dim', type=int, default=800,
                    help='Sets screen height')
parser.add_argument('--no-trafficlights', dest='trafficlights', action='store_false', default=True,
                    help='Disables vehicle crossing lights')
parser.add_argument('--no-pedlights', dest='pedlights', action='store_false', default=True,
                    help='Disables pedestrian crossing lights')
parser.add_argument('--time', metavar='N', type=int, default=0,
                    help="Max time to run simulation")
parser.add_argument('--fps', metavar='N', dest='fps', type=int, default=0,
                    help='Sets max FPS, default is unlimited FPS')
parser.add_argument('--state', metavar='file', type=str, default=fluids.STATE_CITY,
                    help='Layout file for state generation')

args = parser.parse_args()
fluids_print("Parameters: Num background cars : {}".format(args.b))
fluids_print("            Num controlled cars : {}".format(args.c))
fluids_print("            Num controlled peds : {}".format(args.p))
fluids_print("            Visualization level : {}".format(args.v))
fluids_print("            Observation type    : {}".format(args.o))
fluids_print("            Scene layout        : {}".format(args.state))
fluids_print("            Simulation time     : {}".format("unlimited" if not args.time else args.time))
fluids_print("            Pedestrian lights   : {}".format("enabled" if args.pedlights else "disabled"))
fluids_print("            Traffic lights      : {}".format("enabled" if args.trafficlights else "disabled"))
fluids_print("            Max FPS             : {}".format("unbound" if not args.fps else args.fps))

fluids_print("")


obs = {"none"     :fluids.OBS_NONE,
       "birdseye" :fluids.OBS_BIRDSEYE,
       "grid"     :fluids.OBS_GRID}[args.o]

simulator = fluids.FluidSim(visualization_level=args.v,
                            fps                =args.fps,
                            obs_space          =obs,
                            screen_dim         =args.screen_dim,
                            background_control =fluids.BACKGROUND_CSP)


state = fluids.State(layout=args.state,
                     background_cars    =args.b,
                     controlled_cars    =args.c,
                     background_peds    =args.p,
                     use_traffic_lights =args.trafficlights,
                     use_ped_lights     =args.pedlights)

simulator.set_state(state)

data_saver = fluids.DataSaver(fluid_sim=simulator, file="./data/fluids_test", obs=[fluids.OBS_GRID], batch_size=100)
simulator.set_data_saver(data_saver)

t = 0
curr = time.time()
while not args.time or t < args.time:
    actions = simulator.get_supervisor_actions(fluids.VelocityAction, keys=simulator.get_control_keys())
    rew = simulator.step(actions)
    obs = simulator.get_observations(simulator.get_control_keys())
    # simulator.render()
    if t % 100 == 0:
        now = time.time()
        elapsed = now - curr
        fluids_print("Seconds elapsed per 100 obs: {}".format(elapsed))
        curr = time.time()
    t = t + 1
