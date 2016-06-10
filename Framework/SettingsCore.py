"""
    This file contains the Settings sub-class as part of the Framework Class
    This class handles initialization of system settings and handling defaults when no settings are found
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

#####################################
# Global Variables
#####################################


#####################################
# PickAndPlateLogger Definition
#####################################
class PickAndPlateSettings(QtCore.QObject):
    def __init__(self, main_window):
        QtCore.QObject.__init__(self)

        # ########## Reference to highest level window ##########
        self.main_window = main_window

        # ########## Set up settings for program ##########
        self.setup_pick_and_plate_settings()

        # ########## Create Instance of settings ##########
        self.settings = QtCore.QSettings()

        # ########## Load settings, overwriting with defaults if no settings exist ##########
        self.load_settings_or_overwrite_with_defaults()

    @staticmethod
    def setup_pick_and_plate_settings():
        QtCore.QCoreApplication.setOrganizationName("OSU SARL")
        QtCore.QCoreApplication.setOrganizationDomain("ehsc.oregonstate.edu/sarl")
        QtCore.QCoreApplication.setApplicationName("Pick And Plate")

    def load_settings_or_overwrite_with_defaults(self):
        self.load_system_tab_settings()
        self.settings.sync()

    def load_system_tab_settings(self):
        self.load_plating_calibration_tab_settings()
        self.load_system_calibration_tab_settings()
        self.load_detection_calibration_tab_settings()
        self.load_system_settings_tab_settings()

    def load_plating_calibration_tab_settings(self):
        self.settings.setValue("system/plating_calibration/d_pick_height",
                               self.settings.value("system/plating_calibration/d_pick_height", 4.56).toDouble()[0])

        self.settings.setValue("system/plating_calibration/d_place_height",
                               self.settings.value("system/plating_calibration/d_place_height", 4.56).toDouble()[0])

        self.settings.setValue("system/plating_calibration/d_tube_diameter",
                               self.settings.value("system/plating_calibration/d_tube_diameter", 1.98).toDouble()[0])

        self.settings.setValue("system/plating_calibration/d_pick_volume",
                               self.settings.value("system/plating_calibration/d_pick_volume", 10.15).toDouble()[0])

        self.settings.setValue("system/plating_calibration/d_jerk",
                               self.settings.value("system/plating_calibration/d_jerk", 50).toInt()[0])

        self.settings.setValue("system/plating_calibration/c_pick_height",
                               self.settings.value("system/plating_calibration/c_pick_height", 4.56).toDouble()[0])

        self.settings.setValue("system/plating_calibration/c_place_height",
                               self.settings.value("system/plating_calibration/c_place_height", 4.56).toDouble()[0])

        self.settings.setValue("system/plating_calibration/c_tube_diameter",
                               self.settings.value("system/plating_calibration/c_tube_diameter", 2.35).toDouble()[0])

        self.settings.setValue("system/plating_calibration/c_pick_volume",
                               self.settings.value("system/plating_calibration/c_pick_volume", 8.56).toDouble()[0])

        self.settings.setValue("system/plating_calibration/c_jerk",
                               self.settings.value("system/plating_calibration/c_jerk", 75).toInt()[0])

    def load_system_calibration_tab_settings(self):
        self.settings.setValue("system/system_calibration/crop_x_center",
                               self.settings.value("system/system_calibration/crop_x_center", 150).toInt()[0])

        self.settings.setValue("system/system_calibration/crop_y_center",
                               self.settings.value("system/system_calibration/crop_y_center", 150).toInt()[0])

        self.settings.setValue("system/system_calibration/camera_focus",
                               self.settings.value("system/system_calibration/camera_focus", 85).toInt()[0])

        self.settings.setValue("system/system_calibration/camera_exposure",
                               self.settings.value("system/system_calibration/camera_exposure", 175).toInt()[0])

        self.settings.setValue("system/system_calibration/crop_dimension",
                               self.settings.value("system/system_calibration/crop_dimension", 200).toInt()[0])

        self.settings.setValue("system/system_calibration/distance_cal_x",
                               self.settings.value("system/system_calibration/distance_cal_x", 120).toInt()[0])

        self.settings.setValue("system/system_calibration/distance_cal_y",
                               self.settings.value("system/system_calibration/distance_cal_y", 10).toInt()[0])

        self.settings.setValue("system/system_calibration/usable_area_offset",
                               self.settings.value("system/system_calibration/usable_area_offset", 8).toInt()[0])

    def load_detection_calibration_tab_settings(self):
        self.settings.setValue("system/detection_calibration/min_binary_thresh",
                               self.settings.value("system/detection_calibration/min_binary_thresh", 90).toInt()[0])
        self.settings.setValue("system/detection_calibration/min_blob_distance",
                               self.settings.value("system/detection_calibration/min_blob_distance", 5).toDouble()[0])
        self.settings.setValue("system/detection_calibration/min_repeat",
                               self.settings.value("system/detection_calibration/min_repeat", 5).toInt()[0])

        self.settings.setValue("system/detection_calibration/blob_thresh_min",
                               self.settings.value("system/detection_calibration/blob_thresh_min", 15).toInt()[0])
        self.settings.setValue("system/detection_calibration/blob_thresh_max",
                               self.settings.value("system/detection_calibration/blob_thresh_max", 20).toInt()[0])
        self.settings.setValue("system/detection_calibration/blob_thresh_step",
                               self.settings.value("system/detection_calibration/blob_thresh_step", 10).toInt()[0])

        self.settings.setValue("system/detection_calibration/blob_color_enabled",
                               self.settings.value("system/detection_calibration/blob_color_enabled", 1).toInt()[0])
        self.settings.setValue("system/detection_calibration/blob_color",
                               self.settings.value("system/detection_calibration/blob_color", 150).toInt()[0])

        self.settings.setValue("system/detection_calibration/blob_area_enabled",
                               self.settings.value("system/detection_calibration/blob_area_enabled", 1).toInt()[0])
        self.settings.setValue("system/detection_calibration/blob_area_min",
                               self.settings.value("system/detection_calibration/blob_area_min", 35).toDouble()[0])
        self.settings.setValue("system/detection_calibration/blob_area_max",
                               self.settings.value("system/detection_calibration/blob_area_max", 40).toDouble()[0])

        self.settings.setValue("system/detection_calibration/blob_circularity_enabled",
                               self.settings.value("system/detection_calibration/blob_circularity_enabled", 1).toInt()[
                                   0])
        self.settings.setValue("system/detection_calibration/blob_circularity_min",
                               self.settings.value("system/detection_calibration/blob_circularity_min", 15).toDouble()[
                                   0])
        self.settings.setValue("system/detection_calibration/blob_circularity_max",
                               self.settings.value("system/detection_calibration/blob_circularity_max", 150).toDouble()[
                                   0])

        self.settings.setValue("system/detection_calibration/blob_convexity_enabled",
                               self.settings.value("system/detection_calibration/blob_convexity_enabled", 1).toInt()[0])
        self.settings.setValue("system/detection_calibration/blob_convexity_min",
                               self.settings.value("system/detection_calibration/blob_convexity_min", 15).toDouble()[0])
        self.settings.setValue("system/detection_calibration/blob_convexity_max",
                               self.settings.value("system/detection_calibration/blob_convexity_max", 150).toDouble()[
                                   0])

        self.settings.setValue("system/detection_calibration/blob_inertia_enabled",
                               self.settings.value("system/detection_calibration/blob_inertia_enabled", 1).toInt()[0])
        self.settings.setValue("system/detection_calibration/blob_inertia_min",
                               self.settings.value("system/detection_calibration/blob_inertia_min", 200).toDouble()[0])
        self.settings.setValue("system/detection_calibration/blob_inertia_max",
                               self.settings.value("system/detection_calibration/blob_inertia_max", 200).toDouble()[0])

    def load_system_settings_tab_settings(self):
        self.settings.setValue("system/system_settings/unit_id",
                               self.settings.value("system/system_settings/unit_id", 1).toInt()[0])
        self.settings.setValue("system/system_settings/timezone_index",
                               self.settings.value("system/system_settings/timezone_index", 5).toInt()[0])

        self.settings.setValue("system/system_settings/camera_res_width",
                               self.settings.value("system/system_settings/camera_res_width", 864).toInt()[0])
        self.settings.setValue("system/system_settings/camera_res_height",
                               self.settings.value("system/system_settings/camera_res_height", 480).toInt()[0])
