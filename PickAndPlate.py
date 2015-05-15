#!/usr/bin/env python

"""
    Main file used to launch the pick and plate gui.
    No other files should be used for launching this application.
"""

__author__ = "Corwin Perren"
__copyright__ = "None"
__credits__ = [""]
__license__ = "GPL (GNU General Public License)"
__version__ = "0.1 Alpha"
__maintainer__ = "Corwin Perren"
__email__ = "caperren@caperren.com"
__status__ = "Development"

# This file is part of "Pick And Plate".
#
# "Pick And Plate" is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# "Pick And Plate" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Pick And Plate".  If not, see <http://www.gnu.org/licenses/>.

#####################################
# Imports
#####################################
# Python native imports
import sys
from PyQt4 import QtCore, QtGui, uic
import signal

import logging

# Custom imports
from Interface.InterfaceCore import PickAndPlateInterface
from Framework.LoggerCore import PickAndPlateLogger
from Framework.SettingsCore import PickAndPlateSettings
from Framework.VideoCore import PickAndPlateVideo

#####################################
# Global Variables
#####################################
form_class = uic.loadUiType("/home/debian/PickAndPlate/Interface/PickAndPlateUI.ui")[0]  # Load the UI


#####################################
# Event Filter Class Definition
#####################################
class TouchScreenEventFilter(QtCore.QObject):
    """
        This class is an event filter to remove extra screen presses.
        Essentially it is software debouncing for the touchscreen. It hopefully won't be needed...
    """

    def __init__(self):
        QtCore.QObject.__init__(self)
        self.press_count = 0
        self.release_count = 0

    def eventFilter(self, receiver, event):
        if(event.type() == QtCore.QEvent.MouseButtonPress) or (event.type() == QtCore.QEvent.MouseButtonDblClick):
            pass
        elif event.type() == QtCore.QEvent.MouseButtonRelease:
            pass
        else:
            return super(TouchScreenEventFilter, self).eventFilter(receiver, event)
        return super(TouchScreenEventFilter, self).eventFilter(receiver, event)


#####################################
# PickAndPlateWindow Class Definition
#####################################
class PickAndPlateWindow(QtGui.QMainWindow, form_class):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)

        # ########## Set up QT Application Window ##########
        self.setupUi(self)  # Has to be first call in class in order to link gui form objects

        # ########## Create the system logger and get an instance of it ##########
        self.logger_core = PickAndPlateLogger(console_output=True)
        self.logger = logging.getLogger("PickAndPlate")

        # ########## Setup and get program settings ##########
        self.settings = PickAndPlateSettings(self)

        # ########## Instantiation of program classes ##########
        self.video = PickAndPlateVideo(self)

        self.interface = PickAndPlateInterface(self)  # This one HAS to be last so it can handle killing threads

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # This allows the keyboard interrupt kill to work  properly
    app = QtGui.QApplication(sys.argv)  # Create the base qt gui application
    myWindow = PickAndPlateWindow()  # Make a window in this application using the pnp MyWindowClass
    myWindow.setFixedSize(800, 480)  # Set the window to resolution of of 4D Systems' 4DCAPE-70T beaglebone black shield
    myWindow.setWindowFlags(myWindow.windowFlags() |  # Sets the windows flags to:
                            QtCore.Qt.FramelessWindowHint |  # remove the border and frame on the application,
                            QtCore.Qt.WindowStaysOnTopHint)  # and makes the window stay on top of all others
    myWindow.statusBar().setSizeGripEnabled(False)  # Disable the option to resize the window
    myWindow.show()  # Show the window in the application

    # screenFilter = TouchScreenEventFilter()  # Still might be needed if multiple presses from touchscreen breaks stuff
    # app.installEventFilter(screenFilter)

    app.exec_()  # Execute launching of the application
