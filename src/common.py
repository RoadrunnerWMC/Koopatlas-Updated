import sys
import os
import os.path

try:
    from PyQt5 import QtCore, QtGui, QtWidgets
    QtCore.QString = str
except ImportError:
    import sip
    sip.setapi('QVariant', 2)
    from PyQt4 import QtCore, QtGui
    QtWidgets = QtGui
Qt = QtCore.Qt
QtCompatVersion = QtCore.QT_VERSION

from main import KP

from tileset import *
from mapdata import *


