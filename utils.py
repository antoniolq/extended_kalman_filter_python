'''
utils provides helper classes and methods.
'''

from enum import Enum
import numpy as np
import numpy.matlib

from math import sin, cos, pi, sqrt, atan2, pow

def state_vector_to_scalars(state_vector):
    return (state_vector[0][0],state_vector[1][0],state_vector[2][0],state_vector[3][0])

def cart_2_polar(state_vector):
    px,py,vx,vy = state_vector_to_scalars(state_vector)

    '''
    Transforms the state vector into the polar space.
    '''
    try:
        ro      = sqrt(px**2 + py**2)
        phi     = atan2(py,px)
        ro_dot  = (px*vx + py*vy)/ro

        return np.array([ro, phi, ro_dot]).reshape((3,1))
    except ZeroDivisionError as e:
        raise ValueError('px and py cannot be zero.') from e

def polar_2_cart(ro, phi, ro_dot):
    '''
    ro: range
    phi: bearing
    ro_dot: range rate

    Takes the polar coord based radar reading and convert to cart coord x,y
    return (x,y)
    '''
    return (cos(phi) * ro, sin(phi) * ro)


def calculate_rmse(estimations, ground_truth):
    '''
    Root Mean Squared Error.
    '''
    raise NotImplementedError

def calculate_jacobian(state_vector):
    '''
    Creates a Jacobian matrix from the state vector. This is a polynomial approximation of the
    funtion that maps the state vector to the polar coordinates.


    float pxpysqroot = sqrt(px*px+py*py);
	float term31 = pow((py*(vx*py - vy*px))/(px*px+py*py),(3/2));
	float term32 = pow((px*(vy*px - vx*py))/(px*px+py*py),(3/2));

    px/pxpysqroot     , py/pxpysqroot     , 0, 0,
    -(py/(px*px+py*py)), (px/(px*px+py*py)), 0, 0,
    term31, term32, px/pxpysqroot, py/pxpysqroot;
    '''
    px,py,vx,vy = state_vector_to_scalars(state_vector)
    Hj = np.matlib.zeros((3,4))

    xy_squared_sum = px**2+py**2
    xy_squared_sum_sqrt = sqrt(xy_squared_sum)

    xvx_yvy_mul_diff = vx*py - vy*px

    px_div_xy_squared_sum_sqrt = px/xy_squared_sum_sqrt
    py_div_xy_squared_sum_sqrt = py/xy_squared_sum_sqrt

    Hj[0,0] = px_div_xy_squared_sum_sqrt
    Hj[0,1] = py_div_xy_squared_sum_sqrt

    Hj[1,0] = -py/xy_squared_sum
    Hj[1,1] = px/xy_squared_sum

    Hj[2,0] = pow((py*xvx_yvy_mul_diff)/xy_squared_sum,(3/2))
    Hj[2,1] = pow((px*xvx_yvy_mul_diff)/xy_squared_sum,(3/2))
    Hj[2,2] = px_div_xy_squared_sum_sqrt
    Hj[2,2] = py_div_xy_squared_sum_sqrt

    return Hj


class SensorType(Enum):
    '''
    Enum types for the sensors. Future sensors would be added here.
    '''
    LIDAR = 'L'
    RADAR = 'R'


class MeasurementPacket:
    '''
    Defines a measurement datapoint for multiple sensor types.
    '''
    def __init__(self, packet):
        self.sensor_type = SensorType.LIDAR if packet[0] == 'L' else SensorType.RADAR

        if self.sensor_type == SensorType.LIDAR:
            self.setup_lidar(packet)
        elif self.sensor_type == SensorType.RADAR:
            self.setup_radar(packet)

    def setup_radar(self, packet):
        self.rho_measured       = packet[1]
        self.phi_measured       = packet[2]
        self.rhodot_measured    = packet[3]
        self.timestamp          = packet[4]
        self.x_groundtruth      = packet[5]
        self.y_groundtruth      = packet[6]
        self.vx_groundtruth     = packet[7]
        self.vy_groundtruth     = packet[8]

    def setup_lidar(self, packet):
        self.x_measured         = packet[1]
        self.y_measured         = packet[2]
        self.timestamp          = packet[3]
        self.x_groundtruth      = packet[4]
        self.y_groundtruth      = packet[5]
        self.vx_groundtruth     = packet[6]
        self.vy_groundtruth     = packet[7]

    @property
    def z(self):
        '''
        Returns a vectorized version of the measurement for EKF typically called z.
        '''
        if self.sensor_type == SensorType.LIDAR:
            return np.array([self.x_measured,self.y_measured]).reshape((2,1))
        elif self.sensor_type == SensorType.RADAR:
            return np.array([self.rho_measured,self.phi_measured,self.rhodot_measured]).reshape((3,1))

    def __str__(self):
        if self.sensor_type == SensorType.LIDAR:
            return "LIDAR (timestamp: {:>8}) \n MEASUREMENT [{:>4} {:>4}] \n  GROUND TRUTH [{:>4} {:>4} {:>4} {:>4}]".format(
                    self.timestamp,

                    self.x_measured,
                    self.y_measured ,

                    self.x_groundtruth ,
                    self.y_groundtruth,
                    self.vx_groundtruth,
                    self.vy_groundtruth)

        elif self.sensor_type == SensorType.RADAR:
            return "RADAR (timestamp: {:>8}) \n MEASUREMENT [{:>4} <> {:>4} <> {:>4}] \n GROUND TRUTH [{:>4} <> {:>4} <> {:>4} <> {:>4}]".format(
                    self.timestamp    ,

                    self.rho_measured,
                    self.phi_measured ,
                    self.rhodot_measured,

                    self.x_groundtruth,
                    self.y_groundtruth ,
                    self.vx_groundtruth,
                    self.vy_groundtruth )
