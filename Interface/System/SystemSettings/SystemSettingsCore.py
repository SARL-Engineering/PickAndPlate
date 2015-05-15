"""
    This file contains the System Settings sub-class as part of the System Class
    This class handles changes to system settings that are more general
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

#####################################
# Global Variables
#####################################


#####################################
# Settings Class Definition
#####################################
class SystemSettings(QtCore.QObject):

    system_image_preview_options_changed_signal = QtCore.pyqtSignal(int)

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
        self.unit_id_sb = self.main_window.settings_unit_id_spinbox
        self.timezone_cb = self.main_window.settings_timezone_combobox

        self.camera_res_width_sb = self.main_window.settings_camera_res_width_spinbox
        self.camera_res_height_sb = self.main_window.settings_camera_res_height_spinbox
        self.apply_cam_settings_button = self.main_window.settings_apply_camera_settings_button

        self.cal_preview_button = self.main_window.system_calibration_image_preview_button
        self.image_preview_label = self.main_window.system_calibration_image_preview_label

        # ########## Load settings and set widgets to values ##########
        self.load_and_show_settings()

        # ########## Make signal/slot connections ##########
        self.connect_signals_to_slots()

    def connect_signals_to_slots(self):
        self.unit_id_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)
        self.timezone_cb.currentIndexChanged.connect(self.save_changed_values_to_settings_slot)
        self.camera_res_width_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)
        self.camera_res_height_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)

        self.apply_cam_settings_button.clicked.connect(self.main_window.video.on_general_camera_settings_changed_slot)

        self.cal_preview_button.toggled.connect(self.system_image_preview_options_changed_slot)
        self.system_image_preview_options_changed_signal.connect(
            self.main_window.video.system_calibration_preview_status_slot)

        self.main_window.video.requested_image_ready_signal.connect(self.on_requested_image_ready_slot)

    def save_changed_values_to_settings_slot(self):
        self.settings.setValue("system/system_settings/unit_id", self.unit_id_sb.value())
        self.settings.setValue("system/system_settings/timezone_index", self.timezone_cb.currentIndex())

        self.settings.setValue("system/system_settings/camera_res_width", self.camera_res_width_sb.value())
        self.settings.setValue("system/system_settings/camera_res_height", self.camera_res_height_sb.value())

    def load_and_show_settings(self):
        self.unit_id_sb.setValue(self.settings.value("system/system_settings/unit_id").toInt()[0])
        self.timezone_cb.setCurrentIndex(self.settings.value("system/system_settings/timezone_index").toInt()[0])

        self.camera_res_width_sb.setValue(self.settings.value("system/system_settings/camera_res_width").toInt()[0])
        self.camera_res_height_sb.setValue(self.settings.value("system/system_settings/camera_res_height").toInt()[0])

    def system_image_preview_options_changed_slot(self):
        self.system_image_preview_options_changed_signal.emit(self.cal_preview_button.isChecked())

        if not self.cal_preview_button.isChecked():
            self.image_preview_label.clear()

    def on_requested_image_ready_slot(self):
        if self.cal_preview_button.isChecked():
            self.image_preview_label.setPixmap(QtGui.QPixmap.fromImage(self.main_window.video.settings_and_cal_qimage))