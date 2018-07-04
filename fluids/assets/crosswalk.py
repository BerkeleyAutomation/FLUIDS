import numpy as np
from fluids.assets.shape import Shape
from fluids.assets.waypoint import Waypoint

class CrossWalk(Shape):
    def __init__(self, **kwargs):
        Shape.__init__(self, color=(120, 150, 20), **kwargs)
        point0 = (self.points[2] + self.points[3]) / 2
        point1 = (self.points[0] + self.points[1]) / 2

        self.start_waypoints = [Waypoint(point0[0], point0[1], self.angle),
                                Waypoint(point1[0], point1[1], self.angle + np.pi)]
        self.end_waypoints   = [Waypoint(point1[0], point1[1], self.angle),
                                Waypoint(point0[0], point0[1], self.angle + np.pi)]
        self.start_waypoints[0].nxt = [self.end_waypoints[0]]
        self.start_waypoints[1].nxt = [self.end_waypoints[1]]


    def render(self, surface, **kwargs):
        if self.vis_level > 3:
            super(CrossWalk, self).render(surface, **kwargs)
