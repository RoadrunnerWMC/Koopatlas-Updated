import sys
import os
import os.path

try:
    from PyQt5 import QtCore, QtGui, QtWidgets
    QtCore.QString = str
except ImportError:
    from PyQt4 import QtCore, QtGui
    QtWidgets = QtGui
Qt = QtCore.Qt

from main import KP

from tileset import *
from mapdata import *


