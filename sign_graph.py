import Simulator
from sfml import sf
from scipy import optimize
import signal
import numpy as np

zhopa = 0                                           # A global variable to use in signal handlers and cycles
GAME_SPEED = 100


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
def check(impact_parameter, speed=15):
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
    return optimal[0]


# Shows what is going on
def show(impact_parameter, speed=15):
    signal.signal(signal.SIGUSR1, signal.SIG_IGN)           # We don't care about pending signals
    signal.signal(signal.SIGUSR2, signal.SIG_IGN)           # We just watch and enjoy
    signal.pthread_sigmask(signal.SIG_SETMASK, [signal.SIGUSR1, signal.SIGUSR2, signal.SIGSYS])

    bg_path = "images/stock-photo.jpg"
    background_image = sf.Texture.from_file(bg_path)
    window = sf.RenderWindow(sf.VideoMode(1920, 1080), "A Swagabitch game")

    background_sprite = sf.Sprite(background_image)
    window.draw(background_sprite)
    window.display()
    # window.framerate_limit = 60                             # Not to spend 100% processor time

    rocket = Simulator.Simulator("images/rocket_tiny.png", impact_parameter, speed)
    our_planet = Simulator.PhysicalBody("images/Earth128.png")

    while window.is_open:
        dt = 1e-3                                           # Not that accurate as in test(), but who cares

        window.clear()
        if sf.Keyboard.is_key_pressed(sf.Keyboard.ESCAPE):
            break

        for event in window.events:
            if not event:
                break

        print(rocket)
        print(our_planet)
        window.draw(background_sprite)
        rocket.draw(window)
        our_planet.draw(window)
        for i in range(GAME_SPEED):
            rocket.physics()
            rocket.move(dt)
        window.display()


