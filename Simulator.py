import numpy as np
import math
from sfml import sf
import inspect
import os
import signal
from read_only_properties import *

G = 6.67e-11
PLANET_RADIUS = 6371e3
PLANET_MASS = 5.9742e24
g_max = 9.8
k = 1.38e-21
T_max = 300
ATM_HEIGHT = 1e4
METERS_PER_PIXEL = 1e5
PLANET_COORD = (1920. / 2, 720.)
AIR_MASS = 5e-26
GAME_SPEED = 100


def failure():
    os.kill(os.getpid(), signal.SIGUSR1)


def success():
    os.kill(os.getpid(), signal.SIGUSR2)


@read_only_properties('__mass', '__coord', '__texture', '__sprite', '__radius')
class PhysicalBody(object):
    __mass = PLANET_MASS
    __coord = PLANET_COORD
    __texture = sf.Texture
    __sprite = sf.Sprite
    __radius = PLANET_RADIUS

    def __init__(self, image_path):
        self.__texture = sf.Texture.from_file(image_path)
        self.__sprite = sf.Sprite(self.__texture)
        self.__sprite.origin = self.__radius / METERS_PER_PIXEL, self.__radius / METERS_PER_PIXEL

    def draw(self, window):
        self.__sprite.position = self.__coord
        self.__sprite.rotate(0.2)
        window.draw(self.__sprite)

    def __str__(self):
        attributes = inspect.getmembers(self, lambda a: not (inspect.isroutine(a)))
        dump = str()
        for attr in attributes:
            if not attr[0].startswith('__') and not attr[0].endswith('__'):
                dump += str(attr[0]) + " = " + str(attr[1]) + '\n'
        return dump + '\n'


@read_only_properties('__mass', '__initial_v', '__resistance_coef',
                      '__super_square', '__texture', '__sprite', '__radius', '__max_density')
class Simulator:
    def __init__(self, image_path, impact_parameter, speed):
        self.__mass = 1e4
        self.__velocity = np.array((0., 0.))
        self.__coord = np.array((700., 700.))
        self.__acceleration = np.array((0., 0.))
        self.__resistance_coef = 0.2
        self.__super_square = 1.
        self.__texture = sf.Texture
        self.__sprite = sf.Sprite
        self.__radius = 0.5
        self.__max_density = 1.2041                   # Change this to 0 if you don't give a damn about the atmosphere
        self.__forces = list()
        self.__old_height = 1e10
        self.__trust_me = 0
        self.__already_sent_signal = False

        phi = self.__calc_angle_by_impact_par(impact_parameter)
        self.__velocity = np.array((np.cos(phi), np.sin(phi))) * speed
        self.__initial_v = np.array(self.__velocity)
        self.__texture = sf.Texture.from_file(image_path)
        self.__sprite = sf.Sprite(self.__texture)
        self.__sprite.origin = self.__radius / METERS_PER_PIXEL, self.__radius / METERS_PER_PIXEL
        self.__forces = [self.__calc_resistance, self.__calc_gravitation]

    def __str__(self):
        print("Height = ", self.__calc_height())
        attributes = inspect.getmembers(self, lambda a: not (inspect.isroutine(a)))
        dump = str()
        for attr in attributes:
            if not attr[0].startswith('__') and not attr[0].endswith('__'):
                dump += str(attr[0]) + " = " + str(attr[1]) + '\n'
        return dump + '\n'

    def __calc_angle_by_impact_par(self, impact_parameter):
        coord_relative = PLANET_COORD - self.__coord
        hypotenuse = np.linalg.norm(coord_relative) * METERS_PER_PIXEL
        impact_parameter_in_pixels = float(impact_parameter) * PLANET_RADIUS / METERS_PER_PIXEL
        alpha = self.__angle(np.array((1., 0)), coord_relative)
        gamma = np.arcsin(impact_parameter_in_pixels / hypotenuse * METERS_PER_PIXEL)
        return gamma + alpha

    def is_far_away_enough(self):
        if self.__calc_height() > 2.5e7:
            return True
        else:
            return False
        
    @staticmethod
    def __angle(v1, v2):
        v1_normed = v1 / np.linalg.norm(v1)
        v2_normed = v2 / np.linalg.norm(v2)
        dot = np.dot(v1_normed, v2_normed)
        cross = np.cross(v1_normed, v2_normed)
        return np.arctan2(cross, dot)

    def calc_inflection_angle(self):
        return self.__angle(self.__velocity, self.__initial_v)
    
    def move(self, dt):
        height = self.__calc_height()
        if height < 0 and not self.__already_sent_signal:
            failure()
            self.__already_sent_signal = True
        elif height > self.__old_height and not self.__already_sent_signal:
            self.__trust_me += 1
            if self.__trust_me == 3:                                            # The rocket is definitely retiring
                success()
                self.__already_sent_signal = True

        self.__old_height = height
        self.__coord += self.__velocity * dt * GAME_SPEED
        for i in [0, 1]:
            if self.__velocity[i] and self.__acceleration[i] / self.__velocity[i] < -1e3:
                self.__velocity[i] = 0
            else:
                self.__velocity[i] += self.__acceleration[i] * dt * GAME_SPEED

    def draw(self, window):
        self.__sprite.position = self.__coord
        if self.__velocity.all():
            if self.__angle(np.array((1., 0.)), self.__velocity) < 0:
                self.__sprite.rotation = self.__angle(np.array((1., 0.)), self.__velocity) * 180 / math.pi + 360 + 45
            else:
                self.__sprite.rotation = self.__angle(np.array((1., 0.)), self.__velocity) * 180 / math.pi + 45
        window.draw(self.__sprite)

    # Calculates the height above the Earth
    def __calc_height(self):
        height = np.linalg.norm(self.__coord - PLANET_COORD) * METERS_PER_PIXEL - PLANET_RADIUS
        return height

    # R = -1/2 * c * S * v^2
    def __calc_resistance(self):
        r = np.array(-0.5 * self.__velocity * METERS_PER_PIXEL ** 2
                     * self.__resistance_coef
                     * self.__super_square
                     * self.__calc_atm_density()
                     * self.__velocity.__abs__())
        return r

    def __calc_gravitation(self):
        gravitation = np.array(-G * self.__mass * PLANET_MASS
                               / (np.linalg.norm((self.__coord - PLANET_COORD) * METERS_PER_PIXEL) ** 3)
                               * (self.__coord - PLANET_COORD) * METERS_PER_PIXEL)
        return gravitation

    # a = F / m as Newton said one day
    def physics(self):
        f = np.array((0., 0.))
        for force in self.__forces:
            f += force()
        self.__acceleration = f / self.__mass / METERS_PER_PIXEL            # and divide by that to convert to pixels

    # rho = rho_0 * exp(-m * g * H / k / T)
    def __calc_atm_density(self):
        if self.__max_density == 0:
            return 0

        height = self.__calc_height()
        if height < ATM_HEIGHT:
            if self.__calc_temp() <= 0:
                return 0
            else:
                if self.__calc_temp() == 0:
                    return 0
                else:
                    density = self.__max_density * math.exp(-AIR_MASS * self.__calc_g()
                                                            * self.__calc_height()
                                                            / k / self.__calc_temp())
                if density is None:
                    raise ValueError
                return density
        else:
            return 0

    def __calc_g(self):
        return g_max * (PLANET_RADIUS / np.linalg.norm((self.__coord - PLANET_COORD) * METERS_PER_PIXEL)) ** 2

    # Oh man WTF is written below
    def __calc_temp(self):
        height = self.__calc_height()
        if height < 11e3:
            temp = (-83. - 15) / 11e3 * self.__calc_height()

        elif height < 14e3:
            temp = -75.

        elif height < 40e3:
            temp = (30. + 83) / (45e3 - 12e3) * (height - 12e3)

        elif height < 45e3:
            temp = 0.

        elif height < 72e3:
            temp = (-123. - 30) / (72e3 - 45e3) * (height - 45e3)

        elif height < 1e5:
            temp = -83.

        elif height < 18e4:
            temp = (100. - 123) / (18e4 - 85e3) * (height - 85e3)

        else:
            temp = 1e3

        return temp + 273.
