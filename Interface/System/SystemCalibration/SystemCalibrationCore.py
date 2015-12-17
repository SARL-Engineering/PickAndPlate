"""
    This file contains the System Calibration sub-class as part of the System Class
    This class handles changes to system settings for calibration
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
# SystemCalibration Class Definition
#####################################
class SystemCalibration(QtCore.QObject):

    camera_focus_exposure_changed_signal = QtCore.pyqtSignal(int, int)

    system_location_request_signal = QtCore.pyqtSignal()
    full_system_home_request_signal = QtCore.pyqtSignal()
    x_y_move_relative_request_signal = QtCore.pyqtSignal(float, float)
    x_y_move_request_signal = QtCore.pyqtSignal(float, float)
    z_move_request_signal = QtCore.pyqtSignal(float)
    light_change_signal = QtCore.pyqtSignal(int)

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
        self.toolbox = self.main_window.system_calibration_toolbox

        self.crop_x_center_sb = self.main_window.crop_x_center_spin_box
        self.crop_y_center_sb = self.main_window.crop_y_center_spin_box
        self.camera_focus_sb = self.main_window.camera_focus_spinbox
        self.camera_exposure_sb = self.main_window.camera_exposure_spinbox
        self.crop_dimension_sb = self.main_window.crop_dimension_spin_box
        self.apply_focus_exposure_button = self.main_window.system_calibration_exposure_focus_button

        self.distance_cal_x_sb = self.main_window.distance_calibration_x_spin_box
        self.distance_cal_y_sb = self.main_window.distance_calibration_y_spin_box
        self.usable_area_offset_sb = self.main_window.usable_area_offset_spin_box

        self.res_combo_box = self.main_window.alignment_resolution_combo_box
        self.x_left_button = self.main_window.alignment_x_left_button
        self.x_right_button = self.main_window.alignment_x_right_button
        self.y_up_button = self.main_window.alignment_y_up_button
        self.y_down_button = self.main_window.alignment_y_down_button
        self.triple_zero_button = self.main_window.alignment_triple_zero_button
        self.z_up_button = self.main_window.alignment_z_up_button
        self.z_down_button = self.main_window.alignment_z_down_button
        self.z_max_button = self.main_window.alignment_z_max_button

        self.full_home_button = self.main_window.alignment_full_home_button
        self.save_z_center_button = self.main_window.alignment_save_precision_z_button
        self.save_dish_button = self.main_window.alignment_save_dish_button
        self.save_a1_button = self.main_window.alignment_save_a1_button
        self.save_waste_button = self.main_window.alignment_save_waste_button

        self.lights_on_button = self.main_window.alignment_lights_on_button
        self.lights_off_button = self.main_window.alignment_lights_off_button

        self.cal_preview_button = self.main_window.system_calibration_image_preview_button

        # ########## Local Class Variables ##########
        self.request_complete = True

        self.tinyg_z_location = None
        self.tinyg_x_location = None
        self.tinyg_y_location = None


        # ########## Set up gui elements ##########
        self.toolbox.setCurrentIndex(0)

        # ########## Load settings and set widgets to values ##########
        self.load_and_show_settings()

        # ########## Make signal/slot connections ##########
        self.connect_signals_to_slots()

    def connect_signals_to_slots(self):
        # ########## Local interface and settings connections ##########
        self.crop_x_center_sb.valueChanged.connect(self.save_non_pick_head_changed_values_to_settings_slot)
        self.crop_y_center_sb.valueChanged.connect(self.save_non_pick_head_changed_values_to_settings_slot)

        self.camera_focus_sb.valueChanged.connect(self.save_non_pick_head_changed_values_to_settings_slot)
        self.camera_exposure_sb.valueChanged.connect(self.save_non_pick_head_changed_values_to_settings_slot)
        self.crop_dimension_sb.valueChanged.connect(self.save_non_pick_head_changed_values_to_settings_slot)

        self.distance_cal_x_sb.valueChanged.connect(self.save_non_pick_head_changed_values_to_settings_slot)
        self.distance_cal_y_sb.valueChanged.connect(self.save_non_pick_head_changed_values_to_settings_slot)
        self.usable_area_offset_sb.valueChanged.connect(self.save_non_pick_head_changed_values_to_settings_slot)

        self.apply_focus_exposure_button.clicked.connect(self.on_focus_or_exposure_changed_slot)
        self.camera_focus_exposure_changed_signal.connect(self.main_window.video.configure_v4l2_camera_settings_slot)

        self.x_right_button.clicked.connect(self.on_x_positive_clicked_slot)
        self.x_left_button.clicked.connect(self.on_x_negative_clicked_slot)
        self.y_up_button.clicked.connect(self.on_y_positive_clicked_slot)
        self.y_down_button.clicked.connect(self.on_y_negative_clicked_slot)
        self.z_up_button.clicked.connect(self.on_z_positive_clicked_slot)
        self.z_down_button.clicked.connect(self.on_z_negative_clicked_slot)

        self.triple_zero_button.clicked.connect(self.on_x_y_z_zero_clicked_slot)
        self.z_max_button.clicked.connect(self.on_z_max_clicked_slot)

        self.save_z_center_button.clicked.connect(self.on_save_precision_z_center_clicked_slot)

        # ########## External connections ##########
        self.system_location_request_signal.connect(self.main_window.controller.broadcast_location_slot)
        self.main_window.controller.tinyg_location_update_signal.connect(self.on_system_location_changed_slot)

        self.x_y_move_relative_request_signal.connect(
            self.main_window.controller.on_x_y_axis_move_relative_requested_slot)
        self.x_y_move_request_signal.connect(self.main_window.controller.on_x_y_axis_move_requested_slot)
        self.z_move_request_signal.connect(self.main_window.controller.on_z_axis_move_requested_slot)

        self.full_home_button.clicked.connect(self.main_window.controller.on_full_system_homing_requested_slot)


    def save_non_pick_head_changed_values_to_settings_slot(self):
        self.settings.setValue("system/system_calibration/crop_x_center", self.crop_x_center_sb.value())
        self.settings.setValue("system/system_calibration/crop_y_center", self.crop_y_center_sb.value())
        self.settings.setValue("system/system_calibration/camera_focus", self.camera_focus_sb.value())
        self.settings.setValue("system/system_calibration/camera_exposure", self.camera_exposure_sb.value())
        self.settings.setValue("system/system_calibration/crop_dimension", self.crop_dimension_sb.value())

        self.settings.setValue("system/system_calibration/distance_cal_x", self.distance_cal_x_sb.value())
        self.settings.setValue("system/system_calibration/distance_cal_y", self.distance_cal_y_sb.value())
        self.settings.setValue("system/system_calibration/usable_area_offset", self.usable_area_offset_sb.value())

    def load_and_show_settings(self):
        self.crop_x_center_sb.setValue(self.settings.value("system/system_calibration/crop_x_center").toInt()[0])
        self.crop_y_center_sb.setValue(self.settings.value("system/system_calibration/crop_y_center").toInt()[0])
        self.camera_focus_sb.setValue(self.settings.value("system/system_calibration/camera_focus").toInt()[0])
        self.camera_exposure_sb.setValue(self.settings.value("system/system_calibration/camera_exposure").toInt()[0])
        self.crop_dimension_sb.setValue(self.settings.value("system/system_calibration/crop_dimension").toInt()[0])

        self.distance_cal_x_sb.setValue(self.settings.value("system/system_calibration/distance_cal_x").toInt()[0])
        self.distance_cal_y_sb.setValue(self.settings.value("system/system_calibration/distance_cal_y").toInt()[0])
        self.usable_area_offset_sb.setValue(self.settings.value("system/system_calibration/usable_area_offset")
                                            .toInt()[0])

    def on_x_positive_clicked_slot(self):
        if self.request_complete:
            self.request_complete = False
            resolution = float(self.res_combo_box.currentText())
            self.x_y_move_relative_request_signal.emit(resolution, 0)

    def on_x_negative_clicked_slot(self):
        if self.request_complete:
            self.request_complete = False
            resolution = float(self.res_combo_box.currentText())
            self.x_y_move_relative_request_signal.emit(-resolution, 0)

    def on_y_positive_clicked_slot(self):
        if self.request_complete:
            self.request_complete = False
            resolution = float(self.res_combo_box.currentText())
            self.x_y_move_relative_request_signal.emit(0, resolution)


    def on_y_negative_clicked_slot(self):
        if self.request_complete:
            self.request_complete = False
            resolution = float(self.res_combo_box.currentText())
            self.x_y_move_relative_request_signal.emit(0, -resolution)

    def on_z_positive_clicked_slot(self):
        pass

    def on_z_negative_clicked_slot(self):
        pass

    def on_x_y_z_zero_clicked_slot(self):
        if self.request_complete:
            self.x_y_move_request_signal.emit(0 ,0)
            self.z_move_request_signal.emit(0)

    def on_z_max_clicked_slot(self):
        pass

    def on_do_full_homing_clicked_slot(self):
        pass

    def on_save_precision_z_center_clicked_slot(self):
        self.settings.setValue("system/system_calibration/precision_z_x_center", self.tinyg_x_location)
        self.settings.setValue("system/system_calibration/precision_z_y_center", self.tinyg_y_location)

    def on_save_dish_center_clicked_slot(self):
        pass

    def on_save_a1_center_clicked_slot(self):
        pass

    def on_save_waste_center_clicked_slot(self):
        pass

    def on_system_location_changed_slot(self, x, y, z, a):
        self.tinyg_x_location = x
        self.tinyg_y_location = y
        self.tinyg_z_location = z

        self.request_complete = True

    def on_focus_or_exposure_changed_slot(self):
        self.camera_focus_exposure_changed_signal.emit(self.camera_focus_sb.value(), self.camera_exposure_sb.value())

