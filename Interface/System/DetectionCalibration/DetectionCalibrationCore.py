"""
    This file contains the Detection Calibration sub-class as part of the System Class
    This class handles changes to detection settings that are used to detect embryos
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
# DetectionCalibration Class Definition
#####################################
class DetectionCalibration(QtCore.QObject):

    detection_image_preview_options_changed_signal = QtCore.pyqtSignal(int, str, str)
    image_displayed_signal = QtCore.pyqtSignal()

    light_change_signal = QtCore.pyqtSignal(int)
    motor_state_change_signal = QtCore.pyqtSignal(int)

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
        self.embryo_set_gb = self.main_window.detection_embryo_settings_group_box
        self.embryo_min_dist_sb = self.main_window.detection_embryo_min_dist_spin_box
        self.embryo_min_size_sb = self.main_window.detection_min_embryo_size_spin_box
        self.embryo_max_size_sb = self.main_window.detection_max_embryo_size_spin_box

        self.min_binary_thresh_sb = self.main_window.detection_min_binary_threshold_spin_box
        self.min_blob_dist_sb = self.main_window.detection_min_distance_between_blobs_spin_box
        self.min_repeat_sb = self.main_window.detection_min_repeatability_spin_box

        self.blob_thresh_min_sb = self.main_window.detection_blob_threshold_min_spin_box
        self.blob_thresh_max_sb = self.main_window.detection_blob_threshold_max_spin_box
        self.blob_thresh_step_sb = self.main_window.detection_blob_threshold_step_spin_box

        self.blob_area_gb = self.main_window.detection_blob_area_group_box
        self.blob_area_min_sb = self.main_window.detection_blob_area_min_spin_box
        self.blob_area_max_sb = self.main_window.detection_blob_area_max_spin_box

        self.blob_circularity_gb = self.main_window.detection_blob_circularity_group_box
        self.blob_circularity_min_sb = self.main_window.detection_blob_circularity_min_spin_box
        self.blob_circularity_max_sb = self.main_window.detection_blob_circularity_max_spin_box

        self.blob_convexity_gb = self.main_window.detection_blob_convexity_group_box
        self.blob_convexity_min_sb = self.main_window.detection_blob_convexity_min_spin_box
        self.blob_convexity_max_sb = self.main_window.detection_blob_convexity_max_spin_box

        self.blob_inertia_gb = self.main_window.detection_blob_inertia_group_box
        self.blob_inertia_min_sb = self.main_window.detection_blob_inertia_min_spin_box
        self.blob_inertia_max_sb = self.main_window.detection_blob_inertia_max_spin_box

        self.num_detected_label = self.main_window.detection_num_detected_label

        self.profile_sel_combo_box = self.main_window.detection_calibration_profile_selection_combo_box
        self.cal_preview_button = self.main_window.detection_calibration_image_preview_button
        self.cal_preview_combo_box = self.main_window.detection_calibration_image_preview_combo_box

        self.image_preview_label = self.main_window.detection_calibration_image_preview_label

        self.lights_on_button = self.main_window.detection_lights_on_button
        self.lights_off_button = self.main_window.detection_lights_off_button
        self.motors_on_button = self.main_window.detection_motors_on_button
        self.motors_off_button = self.main_window.detection_motors_off_button

        # ########## Class variables ##########
        self.profile_change_lockout = False

        # ########## Load settings and set widgets to values ##########
        self.load_and_show_settings()

        # ########## Make signal/slot connections ##########
        self.connect_signals_to_slots()

    def connect_signals_to_slots(self):
        self.embryo_set_gb.toggled.connect(self.save_changed_values_to_settings_slot)
        self.embryo_min_dist_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)
        self.embryo_min_size_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)
        self.embryo_max_size_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)

        self.min_binary_thresh_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)
        self.min_blob_dist_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)
        self.min_repeat_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)

        self.blob_thresh_min_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)
        self.blob_thresh_max_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)
        self.blob_thresh_step_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)

        self.blob_area_gb.toggled.connect(self.save_changed_values_to_settings_slot)
        self.blob_area_min_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)
        self.blob_area_max_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)

        self.blob_circularity_gb.toggled.connect(self.save_changed_values_to_settings_slot)
        self.blob_circularity_min_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)
        self.blob_circularity_max_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)

        self.blob_convexity_gb.toggled.connect(self.save_changed_values_to_settings_slot)
        self.blob_convexity_min_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)
        self.blob_convexity_max_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)

        self.blob_inertia_gb.toggled.connect(self.save_changed_values_to_settings_slot)
        self.blob_inertia_min_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)
        self.blob_inertia_max_sb.valueChanged.connect(self.save_changed_values_to_settings_slot)

        self.profile_sel_combo_box.currentIndexChanged.connect(self.load_and_show_settings)
        self.profile_sel_combo_box.currentIndexChanged.connect(self.detection_image_preview_options_changed_slot)
        self.cal_preview_button.toggled.connect(self.detection_image_preview_options_changed_slot)
        self.cal_preview_combo_box.currentIndexChanged.connect(self.detection_image_preview_options_changed_slot)

        self.detection_image_preview_options_changed_signal.connect(
            self.main_window.video.detection_calibration_preview_status_slot)

        self.image_displayed_signal.connect(self.main_window.video.images_displayed_slot)

        self.main_window.video.requested_image_ready_signal.connect(self.on_requested_image_ready_slot)
        self.main_window.video.number_embryos_detected_signal.connect(self.on_detected_embryos_number_changed_slot)

        self.lights_on_button.clicked.connect(self.on_lights_on_clicked_slot)
        self.lights_off_button.clicked.connect(self.on_lights_off_clicked_slot)
        self.motors_on_button.clicked.connect(self.on_motors_on_clicked_slot)
        self.motors_off_button.clicked.connect(self.on_motors_off_clicked_slot)

        # External
        self.light_change_signal.connect(self.main_window.controller.on_light_change_request_signal_slot)
        self.motor_state_change_signal.connect(self.main_window.controller.on_motor_state_change_request_signal_slot)

    def save_changed_values_to_settings_slot(self):
        if not self.profile_change_lockout:
            if self.profile_sel_combo_box.currentText() == "Dechorionated":
                prefix = "d_"
            else:
                prefix = "c_"

            self.settings.setValue("system/detection_calibration/" + prefix + "embryo_settings_enabled",
                                   int(self.embryo_set_gb.isChecked()))
            self.settings.setValue("system/detection_calibration/" + prefix + "embryo_min_dist",
                                   self.embryo_min_dist_sb.value())
            self.settings.setValue("system/detection_calibration/" + prefix + "embryo_min_size",
                                   self.embryo_min_size_sb.value())
            self.settings.setValue("system/detection_calibration/" + prefix + "embryo_max_size",
                                   self.embryo_max_size_sb.value())

            self.settings.setValue("system/detection_calibration/" + prefix + "min_binary_thresh",
                                   self.min_binary_thresh_sb.value())
            self.settings.setValue("system/detection_calibration/" + prefix + "min_blob_distance",
                                   self.min_blob_dist_sb.value())
            self.settings.setValue("system/detection_calibration/" + prefix + "min_repeat",
                                   self.min_repeat_sb.value())

            self.settings.setValue("system/detection_calibration/" + prefix + "blob_thresh_min",
                                   self.blob_thresh_min_sb.value())
            self.settings.setValue("system/detection_calibration/" + prefix + "blob_thresh_max",
                                   self.blob_thresh_max_sb.value())
            self.settings.setValue("system/detection_calibration/" + prefix + "blob_thresh_step",
                                   self.blob_thresh_step_sb.value())

            self.settings.setValue("system/detection_calibration/" + prefix + "blob_area_enabled",
                                   int(self.blob_area_gb.isChecked()))
            self.settings.setValue("system/detection_calibration/" + prefix + "blob_area_min",
                                   self.blob_area_min_sb.value())
            self.settings.setValue("system/detection_calibration/" + prefix + "blob_area_max",
                                   self.blob_area_max_sb.value())

            self.settings.setValue("system/detection_calibration/" + prefix + "blob_circularity_enabled",
                                   int(self.blob_circularity_gb.isChecked()))
            self.settings.setValue("system/detection_calibration/" + prefix + "blob_circularity_min",
                                   self.blob_circularity_min_sb.value())
            self.settings.setValue("system/detection_calibration/" + prefix + "blob_circularity_max",
                                   self.blob_circularity_max_sb.value())

            self.settings.setValue("system/detection_calibration/" + prefix + "blob_convexity_enabled",
                                   int(self.blob_convexity_gb.isChecked()))
            self.settings.setValue("system/detection_calibration/" + prefix + "blob_convexity_min",
                                   self.blob_convexity_min_sb.value())
            self.settings.setValue("system/detection_calibration/" + prefix + "blob_convexity_max",
                                   self.blob_convexity_max_sb.value())

            self.settings.setValue("system/detection_calibration/" + prefix + "blob_inertia_enabled",
                                   int(self.blob_inertia_gb.isChecked()))
            self.settings.setValue("system/detection_calibration/" + prefix + "blob_inertia_min",
                                   self.blob_inertia_min_sb.value())
            self.settings.setValue("system/detection_calibration/" + prefix + "blob_inertia_max",
                                   self.blob_inertia_max_sb.value())

    def load_and_show_settings(self):
        self.profile_change_lockout = True

        if self.profile_sel_combo_box.currentText() == "Dechorionated":
            prefix = "d_"
        else:
            prefix = "c_"

        self.embryo_set_gb.setChecked(
            self.settings.value("system/detection_calibration/" + prefix + "embryo_settings_enabled").toInt()[0])
        self.embryo_min_dist_sb.setValue(
            self.settings.value("system/detection_calibration/" + prefix + "embryo_min_dist").toDouble()[0])
        self.embryo_min_size_sb.setValue(
            self.settings.value("system/detection_calibration/" + prefix + "embryo_min_size").toDouble()[0])
        self.embryo_max_size_sb.setValue(
            self.settings.value("system/detection_calibration/" + prefix + "embryo_max_size").toDouble()[0])

        self.min_binary_thresh_sb.setValue(
            self.settings.value("system/detection_calibration/" + prefix + "min_binary_thresh").toInt()[0])
        self.min_blob_dist_sb.setValue(
            self.settings.value("system/detection_calibration/" + prefix + "min_blob_distance").toDouble()[0])
        self.min_repeat_sb.setValue(
            self.settings.value("system/detection_calibration/" + prefix + "min_repeat").toInt()[0])

        self.blob_thresh_min_sb.setValue(
            self.settings.value("system/detection_calibration/" + prefix + "blob_thresh_min").toInt()[0])
        self.blob_thresh_max_sb.setValue(
            self.settings.value("system/detection_calibration/" + prefix + "blob_thresh_max").toInt()[0])
        self.blob_thresh_step_sb.setValue(
            self.settings.value("system/detection_calibration/" + prefix + "blob_thresh_step").toInt()[0])

        self.blob_area_gb.setChecked(
            self.settings.value("system/detection_calibration/" + prefix + "blob_area_enabled").toInt()[0])
        self.blob_area_min_sb.setValue(
            self.settings.value("system/detection_calibration/" + prefix + "blob_area_min").toDouble()[0])
        self.blob_area_max_sb.setValue(
            self.settings.value("system/detection_calibration/" + prefix + "blob_area_max").toDouble()[0])

        self.blob_circularity_gb.setChecked(
            self.settings.value("system/detection_calibration/" + prefix + "blob_circularity_enabled").toInt()[0])
        self.blob_circularity_min_sb.setValue(
            self.settings.value("system/detection_calibration/" + prefix + "blob_circularity_min").toDouble()[0])
        self.blob_circularity_max_sb.setValue(
            self.settings.value("system/detection_calibration/" + prefix + "blob_circularity_max").toDouble()[0])

        self.blob_convexity_gb.setChecked(
            self.settings.value("system/detection_calibration/" + prefix + "blob_convexity_enabled").toInt()[0])
        self.blob_convexity_min_sb.setValue(
            self.settings.value("system/detection_calibration/" + prefix + "blob_convexity_min").toDouble()[0])
        self.blob_convexity_max_sb.setValue(
            self.settings.value("system/detection_calibration/" + prefix + "blob_convexity_max").toDouble()[0])

        self.blob_inertia_gb.setChecked(
            self.settings.value("system/detection_calibration/" + prefix + "blob_inertia_enabled").toInt()[0])
        self.blob_inertia_min_sb.setValue(
            self.settings.value("system/detection_calibration/" + prefix + "blob_inertia_min").toDouble()[0])
        self.blob_inertia_max_sb.setValue(
            self.settings.value("system/detection_calibration/" + prefix + "blob_inertia_max").toDouble()[0])

        self.profile_change_lockout = False

    def detection_image_preview_options_changed_slot(self):
        self.detection_image_preview_options_changed_signal.emit(self.cal_preview_button.isChecked(),
                                                                 self.cal_preview_combo_box.currentText(),
                                                                 self.profile_sel_combo_box.currentText())
        if not self.cal_preview_button.isChecked():
            self.image_preview_label.clear()

    def on_requested_image_ready_slot(self):
        if self.cal_preview_button.isChecked():
            self.image_preview_label.setPixmap(QtGui.QPixmap.fromImage(self.main_window.video.settings_and_cal_qimage))
            self.image_displayed_signal.emit()

    def on_detected_embryos_number_changed_slot(self, number):
        self.num_detected_label.setText(str(number))

    def on_lights_on_clicked_slot(self):
        self.light_change_signal.emit(1000)

    def on_lights_off_clicked_slot(self):
        self.light_change_signal.emit(0)

    def on_motors_on_clicked_slot(self):
        self.motor_state_change_signal.emit(True)

    def on_motors_off_clicked_slot(self):
        self.motor_state_change_signal.emit(False)