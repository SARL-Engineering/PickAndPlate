"""
    This file contains the CycleControl class
    This class handles updating the video window labels and cycle statistics
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
cycle_monitor_wait_for_start_image_path = None
pick_wait_for_start_image_path = None

cycle_monitor_video_error_image_path = None
pick_video_error_image_path = None


#####################################
# Status Class Definition
#####################################
class CycleControl(QtCore.QThread):
    start_cycle_signal = QtCore.pyqtSignal()
    stop_cycle_signal = QtCore.pyqtSignal()
    pause_cycle_signal = QtCore.pyqtSignal()
    resume_cycle_signal = QtCore.pyqtSignal()

    def __init__(self, main_window, master):
        QtCore.QThread.__init__(self)

        # ########## Get the Pick And Plate instance of the logger ##########
        self.logger = logging.getLogger("PickAndPlate")

        # ########## Get the Pick And Plate settings instance ##########
        self.settings = QtCore.QSettings()

        # ########## Reference to highest level window and master widget ##########
        self.main_window = main_window
        self.master = master

        # ########## References to gui objects ##########
        self.cycle_mon_label = self.main_window.cycle_monitor_image_label

        self.last_pick_label = self.main_window.cycle_last_pick_image_label
        self.last_pick_pos_label = self.main_window.cycle_last_pick_position_label

        self.current_pick_label = self.main_window.cycle_current_pick_image_label
        self.current_pick_pos_label = self.main_window.cycle_current_pick_position_label

        self.current_pick_num_label = self.main_window.cycle_current_pick_number_label
        self.total_picked_num_label = self.main_window.cycle_total_picked_label
        self.mispick_label = self.main_window.cycle_mispicks_label
        self.double_pick_label = self.main_window.cycle_double_picks_label
        self.total_detected_label = self.main_window.cycle_total_detected_label
        self.time_elapsed_label = self.main_window.cycle_time_elapsed_label
        self.time_remaining_label = self.main_window.cycle_time_remaining_label
        self.success_rate_label = self.main_window.cycle_success_rate_label

        self.is_chorionated_button = self.main_window.cycle_is_chorionated_button
        self.start_button = self.main_window.cycle_start_button
        self.pause_resume_button = self.main_window.cycle_pause_resume_button
        self.stop_button = self.main_window.cycle_stop_button

        # ########## Class Variables ##########
        self.cycle_is_running = False

        # ########## Make signal/slot connections ##########
        self.connect_signals_to_slots()

        # ########## Set labels to defaults ##########
        self.set_labels_to_defaults()

    def connect_signals_to_slots(self):
        self.start_button.clicked.connect(self.on_start_button_pressed_slot)
        self.pause_resume_button.clicked.connect(self.on_pause_resume_button_pressed_slot)
        self.stop_button.clicked.connect(self.on_stop_button_pressed_slot)
        self.stop_button.clicked.connect(self.on_stop_button_pressed_slot)

        self.start_cycle_signal.connect(self.main_window.cycle_handler.on_cycle_start_pressed_slot)
        self.stop_cycle_signal.connect(self.main_window.cycle_handler.on_cycle_stop_pressed_slot)
        self.pause_cycle_signal.connect(self.main_window.cycle_handler.on_cycle_pause_pressed_slot)
        self.resume_cycle_signal.connect(self.main_window.cycle_handler.on_cycle_resume_pressed_slot)

        self.main_window.video.requested_image_ready_signal.connect(self.on_cycle_monitor_image_ready_slot)

    def set_labels_to_defaults(self):
        self.cycle_mon_label

        self.last_pick_label
        self.last_pick_pos_label.setText("Waiting for start")

        self.current_pick_label
        self.current_pick_pos_label.setText("Waiting for start")

        self.current_pick_num_label.setText("N/A")
        self.total_picked_num_label.setText("N/A")
        self.mispick_label.setText("N/A")
        self.double_pick_label.setText("N/A")
        self.total_detected_label.setText("N/A")
        self.time_elapsed_label.setText("N/A")
        self.time_remaining_label.setText("N/A")
        self.success_rate_label.setText("N/A")

    def on_start_button_pressed_slot(self):
        self.set_labels_to_defaults()
        self.cycle_is_running = True
        self.master.cycle_running = True
        self.start_button.setEnabled(False)
        self.start_cycle_signal.emit()

    def on_pause_resume_button_pressed_slot(self):
        if self.cycle_is_running:
            if self.pause_resume_button.text() == "Pause":
                self.pause_resume_button.setText("Resume")
                self.pause_cycle_signal.emit()
            else:
                self.pause_resume_button.setText("Pause")
                self.resume_cycle_signal.emit()

    def on_stop_button_pressed_slot(self):
        if self.cycle_is_running:
            self.cycle_is_running = False
            self.pause_resume_button.setText("Pause")
            self.start_button.setEnabled(True)
            self.master.cycle_running = False
            self.stop_cycle_signal.emit()

    def on_cycle_monitor_image_ready_slot(self):
        try:
            self.cycle_mon_label.setPixmap(QtGui.QPixmap.fromImage(self.main_window.video.cycle_monitor_qimage))
        except:
            pass
