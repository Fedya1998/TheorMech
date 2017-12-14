import Simulator
import time
from sfml import sf
import datetime
from scipy import optimize
import numpy as np
import math
import os, signal
import sign_graph

# 2.27477783 without atmosphere
# 2.276 with atmosphere

r_min = sign_graph.test(2.3, 15)
# sign_graph.show(2)
print(r_min)
