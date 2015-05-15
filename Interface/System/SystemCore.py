"""
    This file contains the System sub-class as part of the Interface Class
    This class handles the System sub-tabs and any needed connections
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
from PyQt4 import QtCore

# Custom imports
from PlatingCalibration.PlatingCalibrationCore import PlatingCalibration
from SystemCalibration.SystemCalibrationCore import SystemCalibration
from SystemLog.SystemLogCore import SystemLog
from DetectionCalibration.DetectionCalibrationCore import DetectionCalibration
from SystemSettings.SystemSettingsCore import SystemSettings
from Networking.NetworkingCore import Networking
#####################################
# Global Variables
#####################################


#####################################
# SystemCore Definition
#####################################
class System(QtCore.QObject):
    def __init__(self, main_window, master):
        QtCore.QObject.__init__(self)

        # ########## References to highest level window and master widget ##########
        self.main_window = main_window
        self.master = master

        # ########## References to gui elements ##########
        self.settings_tab_widget = self.main_window.settings_tab_widget

        # ########## Instantiations of all sub-tab sub-classes ##########
        self.plating_calibration_tab = PlatingCalibration(self.main_window, self)
        self.system_calibration_tab = SystemCalibration(self.main_window, self)
        self.detection_calibration_tab = DetectionCalibration(self.main_window, self)
        self.system_settings_tab = SystemSettings(self.main_window, self)
        self.networking_tab = Networking(self.main_window, self)
        self.engineering_tab = None
        self.system_log_tab = SystemLog(self.main_window, self)

        # ########## References to preview buttons to un-click them when tab changed ##########
        self.system_cal_preview_button = self.system_calibration_tab.cal_preview_button
        self.detection_cal_preview_button = self.detection_calibration_tab.cal_preview_button

        # ########## Setup of gui elements ##########
        self.settings_tab_widget.setCurrentIndex(0)

        # ########## Make signal/slot connections ##########
        self.connect_signals_to_slots()

    def connect_signals_to_slots(self):
        self.settings_tab_widget.currentChanged.connect(self.on_system_tab_widget_changed)

    def on_system_tab_widget_changed(self):
        if self.system_cal_preview_button.isChecked():
            self.system_cal_preview_button.setChecked(False)

        if self.detection_cal_preview_button.isChecked():
            self.detection_cal_preview_button.setChecked(False)