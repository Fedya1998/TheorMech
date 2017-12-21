import Simulator
from sfml import sf
from scipy import optimize
import signal
import numpy as np
from matplotlib import pylab as plt
import functools

zhopa = 0                                           # A global variable to use in signal handlers and cycles
GAME_SPEED = 10


def handler(sig, frame):
    global zhopa
    if sig == signal.SIGUSR1:
        # print("got usr1")
        zhopa = 1
        return
    if sig == signal.SIGUSR2:
        # print("got usr2")
        zhopa = 2
        return


# Checks if the initial speed and impact parameter allows the rocket to fly happily
def check(impact_parameter, speed=0.1):
    # print("check impact ", impact_parameter)
    global zhopa
    rocket = Simulator.Simulator("images/rocket_tiny.png", impact_parameter, speed)
    dt = 1e-3

    zhopa = 0
    while zhopa == 0:
        rocket.physics()
        rocket.move(dt)
    return zhopa


def function_to_minimize(impact_parameter, *args):
    if impact_parameter < 0:
        return 100                                           # 100 is definitely bigger than the impact parameter

    if check(impact_parameter, args[0]) == 2:                # Everything is OK, we can fly happily
        return impact_parameter                              # It is very convenient to return the parameter itself

    else:                                                    # because we need to minimize it
        return 100


# Finds the optimal impact parameter near the ones passed in
def test(impact_parameter, speed=1, tol=1e-4):
    signal.signal(signal.SIGUSR1, handler)
    signal.signal(signal.SIGUSR2, handler)
    par = impact_parameter
    optimal = [par, 100]
    if function_to_minimize(par, speed) == par:
        while True:
            if function_to_minimize(par, speed) < optimal[1]:
                optimal[0] = par
                par -= tol
            else:
                break
    else:
        while True:
            if function_to_minimize(par, speed) < optimal[1]:
                optimal[0] = par
                break
            else:
                par += tol

    print(optimal[0])
    signal.signal(signal.SIGUSR1, signal.SIG_DFL)
    signal.signal(signal.SIGUSR2, signal.SIG_DFL)

    return optimal[0]


# Shows what is going on
def show(impact_parameter, speed=0.1):
    signal.signal(signal.SIGUSR1, signal.SIG_IGN)           # We don't care about pending signals
    signal.signal(signal.SIGUSR2, signal.SIG_IGN)           # We just watch and enjoy
    signal.pthread_sigmask(signal.SIG_SETMASK, [signal.SIGUSR1, signal.SIGUSR2])

    bg_path = "images/stock-photo.jpg"
    background_image = sf.Texture.from_file(bg_path)
    window = sf.RenderWindow(sf.VideoMode(1920, 1080), "A Swagabitch game")

    background_sprite = sf.Sprite(background_image)
    window.draw(background_sprite)
    window.display()
    window.framerate_limit = 60                            # Not to spend 100% CPU time

    rocket = Simulator.Simulator("images/rocket_tiny.png", impact_parameter, speed)
    our_planet = Simulator.PhysicalBody("images/Earth128.png")

    while window.is_open:
        dt = 1e-2                                           # Not that accurate as in test(), but who cares

        window.clear()
        if sf.Keyboard.is_key_pressed(sf.Keyboard.ESCAPE):
            break

        for event in window.events:
            if not event:
                break

        # print(rocket)
        # print(our_planet)
        window.draw(background_sprite)
        rocket.draw(window)
        our_planet.draw(window)
        for i in range(GAME_SPEED):
            rocket.physics()
            rocket.move(dt)
        window.display()
    signal.signal(signal.SIGUSR1, signal.SIG_DFL)
    signal.signal(signal.SIGUSR2, signal.SIG_DFL)


def calc_inflection(impact_parameter, speed):
    signal.signal(signal.SIGUSR1, handler)           # We don't care only about USR2 (Success signal)
    signal.signal(signal.SIGUSR2, signal.SIG_IGN)    # We just watch and enjoy
    signal.pthread_sigmask(signal.SIG_SETMASK, [signal.SIGUSR2])

    rocket = Simulator.Simulator("images/rocket_tiny.png", impact_parameter, speed)

    dt = 1e-3
    global zhopa
    zhopa = 0
    while zhopa == 0:
        rocket.physics()
        rocket.move(dt)
        if rocket.is_far_away_enough():
            angle = rocket.calc_inflection_angle()
            break
    else:
        angle = -1

    signal.signal(signal.SIGUSR1, signal.SIG_DFL)
    signal.signal(signal.SIGUSR2, signal.SIG_DFL)
    # print("angle ", angle)
    return angle


def plot_inflection(impact_parameters=np.linspace(1, 3, num=20), speed=0.1):
    inflections = list(map(lambda x: calc_inflection(x, speed), impact_parameters))
    good_dots = [[], []]
    bad_dots = [[], []]
    for i in range(len(inflections)):
        if inflections[i] != -1:
            good_dots[0].append(impact_parameters[i])
            good_dots[1].append(inflections[i])
        else:
            bad_dots[0].append(impact_parameters[i])
            bad_dots[1].append(inflections[i])
    plt.plot(good_dots[0], good_dots[1], 'g-')
    plt.plot(bad_dots[0], bad_dots[1], 'r-')
    plt.title("Inflection angle", {'fontsize': 28})
    plt.xlabel("Impact parameters (in the Earth radiuses)", {'fontsize': 28})
    plt.ylabel("Angle (radians)", {'fontsize': 28})
    plt.xticks(size=20)
    plt.yticks(size=20)
    plt.grid("on")
    plt.legend(("We fly happily", "We fall down and explode"), prop={'size': 20})
    plt.show()

