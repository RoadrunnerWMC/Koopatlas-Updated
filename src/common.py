import sys
import os
import os.path
from math import sin, cos, pi

from PyQt6 import QtCore, QtGui, QtWidgets
QtCompatVersion = QtCore.QT_VERSION

# these match Qt 4's "QTimeLine::SineCurve" and "QTimeLine::CosineCurve", respectively
def easingCurveSin(t):
    return (-cos(t * 2 * pi) + 1) / 2
def easingCurveCos(t):
    return (sin(t * 2 * pi) + 1) / 2

from main import KP

from tileset import *
from mapdata import *


