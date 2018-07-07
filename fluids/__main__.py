import fluids
from fluids.utils import fluids_print
import argparse

parser = argparse.ArgumentParser(description='FLUIDS First Order Lightweight Urban Intersection Driving Simulator')
parser.add_argument('-b', metavar='N', type=int, default=10, 
                    help='Number of background cars')
parser.add_argument('-c', metavar='N', type=int, default=1, 
                    help='Number of controlled cars')
parser.add_argument('-p', metavar='N', type=int, default=5, 
                    help='Number of background pedestrians')
parser.add_argument('-v', metavar='N', type=int, default=1,
                    help='Visualization level')
parser.add_argument('--state', metavar='file', type=str, default=fluids.STATE_CITY,
                    help='Layout file for state generation')

args = parser.parse_args()
fluids_print("Parameters: Num background cars : {}".format(args.b))
fluids_print("            Num controlled cars : {}".format(args.c))
fluids_print("            Num controlled peds : {}".format(args.p))
fluids_print("            Visualization level : {}".format(args.v))
fluids_print("            Scene layout        : {}".format(args.state))
fluids_print("")

simulator = fluids.FluidSim(visualization_level=args.v,
                            state              =args.state,
                            background_cars    =args.b,
                            controlled_cars    =args.c,
                            background_peds    =args.p,
                            fps                =0,
                            obs_space          =fluids.OBS_BIRDSEYE,
                            background_control =fluids.BACKGROUND_CSP) 
while True:
    actions = {k: fluids.KeyboardAction() for k in simulator.get_control_keys()}
    obs, rew = simulator.step(actions)