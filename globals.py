from PySide2.QtGui import QColor
import sys
from os.path import join, abspath


collected_icons = {}
config = dict([e[:e.find("=")], e[e.find("=") + 1:]] for e in open("config.conf", "r").read().splitlines())
bgcolor = QColor.fromRgb(25, 35, 45)
sizebarcolor = QColor.fromRgb(64, 26, 0)
