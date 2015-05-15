"""
    This file contains the Pick and Plate Interface Class
    This class handles gui to framework connections and gui updating
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
from PyQt4 import QtCore, QtGui
import logging

# Custom imports
from Status.StatusCore import Status
from CycleControl.CycleControlCore import CycleControl
from Tables.TablesCore import Tables
from System.SystemCore import System
from Power.PowerCore import Power

#####################################
# Global Variables
#####################################


#####################################
# PickAndPlateInterface Class Definition
#####################################
class PickAndPlateInterface(QtCore.QObject):
    def __init__(self, main_window):
        QtCore.QObject.__init__(self)

        # ########## Reference to system logger ##########
        self.logger = logging.getLogger("PickAndPlate")

        # ########## Reference to top level window ##########
        self.main_window = main_window

        # ########## Reference to main_window gui elements ##########
        self.main_tab_widget = self.main_window.main_tab_widget

        # ########## Class variables ##########
        self.last_tab_index = 0

        # ########## Instantiations of status class ##########
        self.status = Status(self.main_window, self)

        # ########## Instantiations of tab classes ##########
        self.cycle_control_tab = CycleControl(self.main_window, self)
        self.tables_tab = Tables(self.main_window, self)
        self.system_tab = System(self.main_window, self)
        self.power_tab = Power(self.main_window, self)

        # ########## References to preview buttons to un-click them when tab changed ##########
        self.system_cal_preview_button = self.system_tab.system_calibration_tab.cal_preview_button
        self.detection_cal_preview_button = self.system_tab.detection_calibration_tab.cal_preview_button

        # ########## Setup of gui elements ##########
        self.main_tab_widget.setCurrentIndex(0)

        # ########## Make signal/slot connections ##########
        self.connect_signals_to_slots()

    def connect_signals_to_slots(self):
        self.main_tab_widget.currentChanged.connect(self.on_main_tab_widget_tab_changed)

    def on_main_tab_widget_tab_changed(self, index):
        # This event handler makes sure you can't click on the time / id number tab
        # There was no nice way to overlay widgets without nasty code, so I opted for this instead.
        # Still not very nice, but not the worst either
        if index == 4:
            self.main_tab_widget.setCurrentIndex(self.last_tab_index)
        else:
            self.last_tab_index = index

        if self.system_cal_preview_button.isChecked():
            self.system_cal_preview_button.setChecked(False)

        if self.detection_cal_preview_button.isChecked():
            self.detection_cal_preview_button.setChecked(False)