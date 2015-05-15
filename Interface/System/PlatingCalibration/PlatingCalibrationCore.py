"""
    This file contains the Plating Calibration sub-class as part of the System Class
    This class handles changes to plating settings for calibration
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
import logging

# Custom imports

#####################################
# Global Variables
#####################################


#####################################
# PickAndPlateLogger Definition
#####################################
class PlatingCalibration(QtCore.QObject):
    def __init__(self, main_window, master):
        QtCore.QObject.__init__(self)

        # ########## Get the Pick And Plate instance of the logger ##########
        self.logger = logging.getLogger("PickAndPlate")

        # ########## Get the Pick And Plate settings instance ##########
        self.settings = QtCore.QSettings()

        # ########## Reference to highest level window and master widget ##########
        self.main_window = main_window
        self.master = master

        # ########## References to gui objects ##########
        self.toolbox = self.main_window.plating_calibration_toolbox

        self.d_pick_height_sb = self.main_window.dechorionated_pick_height_spin_box
        self.d_place_height_sb = self.main_window.dechorionated_place_height_spin_box
        self.d_pick_tube_diameter_sb = self.main_window.dechorionated_pick_tube_diameter_spin_box
        self.d_pick_volume_sb = self.main_window.dechorionated_pick_volume_spin_box
        self.d_jerk_sb = self.main_window.dechorionated_jerk_spin_box

        self.c_pick_height_sb = self.main_window.chorionated_pick_height_spin_box
        self.c_place_height_sb = self.main_window.chorionated_place_height_spin_box
        self.c_pick_tube_diameter_sb = self.main_window.chorionated_pick_tube_diameter_spin_box
        self.c_pick_volume_sb = self.main_window.chorionated_pick_volume_spin_box
        self.c_jerk_sb = self.main_window.chorionated_jerk_spin_box

        # ########## Set up gui elements ##########
        self.toolbox.setCurrentIndex(0)

        # ########## Load settings and set widgets to values ##########
        self.load_and_show_settings()

        # ########## Make signal/slot connections ##########
        self.connect_signals_to_slots()

    def connect_signals_to_slots(self):
        self.d_pick_height_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)
        self.d_place_height_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)
        self.d_pick_tube_diameter_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)
        self.d_pick_volume_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)
        self.d_jerk_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)

        self.c_pick_height_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)
        self.c_place_height_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)
        self.c_pick_tube_diameter_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)
        self.c_pick_volume_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)
        self.c_jerk_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)

    def save_changed_values_to_settings_slot(self):
        self.settings.setValue("system/plating_calibration/d_pick_height", self.d_pick_height_sb.value())
        self.settings.setValue("system/plating_calibration/d_place_height", self.d_place_height_sb.value())
        self.settings.setValue("system/plating_calibration/d_tube_diameter", self.d_pick_tube_diameter_sb.value())
        self.settings.setValue("system/plating_calibration/d_pick_volume", self.d_pick_volume_sb.value())
        self.settings.setValue("system/plating_calibration/d_jerk", self.d_jerk_sb.value())

        self.settings.setValue("system/plating_calibration/c_pick_height", self.c_pick_height_sb.value())
        self.settings.setValue("system/plating_calibration/c_place_height", self.c_place_height_sb.value())
        self.settings.setValue("system/plating_calibration/c_tube_diameter", self.c_pick_tube_diameter_sb.value())
        self.settings.setValue("system/plating_calibration/c_pick_volume", self.c_pick_volume_sb.value())
        self.settings.setValue("system/plating_calibration/c_jerk", self.c_jerk_sb.value())

    def load_and_show_settings(self):
        self.d_pick_height_sb.setValue(self.settings.value("system/plating_calibration/d_pick_height").toDouble()[0])
        self.d_place_height_sb.setValue(self.settings.value("system/plating_calibration/d_place_height").toDouble()[0])
        self.d_pick_tube_diameter_sb.setValue(self.settings.value("system/plating_calibration/d_tube_diameter").toDouble()[0])
        self.d_pick_volume_sb.setValue(self.settings.value("system/plating_calibration/d_pick_volume").toDouble()[0])
        self.d_jerk_sb.setValue(self.settings.value("system/plating_calibration/d_jerk").toInt()[0])

        self.c_pick_height_sb.setValue(self.settings.value("system/plating_calibration/c_pick_height").toDouble()[0])
        self.c_place_height_sb.setValue(self.settings.value("system/plating_calibration/c_place_height").toDouble()[0])
        self.c_pick_tube_diameter_sb.setValue(self.settings.value("system/plating_calibration/c_tube_diameter").toDouble()[0])
        self.c_pick_volume_sb.setValue(self.settings.value("system/plating_calibration/c_pick_volume").toDouble()[0])
        self.c_jerk_sb.setValue(self.settings.value("system/plating_calibration/c_jerk").toInt()[0])