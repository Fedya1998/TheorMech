import Simulator
from sfml import sf
from scipy import optimize
import numpy as np
import math
import os
import signal


zhopa = 0


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


def check(impact_parameter, speed=15):
    # print("check impact ", impact_parameter)
    global zhopa
    rocket = Simulator.Simulator("images/rocket_tiny.png", impact_parameter, speed)
    dt = 1e-4

    zhopa = 0
    while zhopa == 0:
        rocket.physics()
        rocket.move(dt)
    return zhopa


def function_to_minimize(impact_parameter):
    # print("impact parameter ", impact_parameter)
    if impact_parameter < 0:
        return 100
    if check(impact_parameter) == 2:
        # print("return ", impact_parameter)
        return impact_parameter
    else:
        # print("return 100")
        return 100


def test(impact_parameter, speed, delta=0.1):
    signal.signal(signal.SIGUSR1, handler)
    signal.signal(signal.SIGUSR2, handler)
    r_min = optimize.brute(function_to_minimize, (slice(impact_parameter - delta, impact_parameter + delta, 1e-3),))
    print("r min ", r_min, "F ", function_to_minimize(r_min))
    return r_min


def show(impact_parameter, speed=15):
    signal.signal(signal.SIGUSR1, signal.SIG_IGN)
    signal.signal(signal.SIGUSR2, signal.SIG_IGN)
    signal.signal(signal.SIGSYS, signal.SIG_IGN)
    signal.pthread_sigmask(signal.SIG_SETMASK, [signal.SIGUSR1, signal.SIGUSR2, signal.SIGSYS])

    bg_path = "/home/fedya/bg/stock-photo.jpg"
    background_image = sf.Texture.from_file(bg_path)
    window = sf.RenderWindow(sf.VideoMode(1920, 1080), "A Swagabitch game")

    background_sprite = sf.Sprite(background_image)
    window.draw(background_sprite)
    window.display()
    window.framerate_limit = 60

    rocket = Simulator.Simulator("images/rocket_tiny.png", impact_parameter, speed)
    our_planet = Simulator.PhysicalBody("images/Earth128.png")

    while window.is_open:
        dt = 1e-3

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
        rocket.physics()
        rocket.move(dt)
        window.display()


