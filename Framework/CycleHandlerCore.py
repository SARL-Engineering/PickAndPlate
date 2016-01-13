"""
    This file contains the CycleHandlerCore sub-class as part of the Framework Class
    This class handles the logic behind running pick and plate cycles
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
from math import sqrt, pow, isnan
import qimage2ndarray
import cv2
import time

# Custom imports

#####################################
# Global Variables
#####################################
CAL_POINT_DIST_MM = 25

NO_EMBRYO_THRESHOLD = 3

BUTTON_CONTINUE = 0
BUTTON_EXIT = 1
BUTTON_WAIT = 2


#####################################
# PickAndPlateController Definition
#####################################
class PickAndPlateCycleHandler(QtCore.QThread):
    full_system_home_request_signal = QtCore.pyqtSignal()
    x_y_move_request_signal = QtCore.pyqtSignal(float, float)
    z_move_request_signal = QtCore.pyqtSignal(float)
    a_move_request_signal = QtCore.pyqtSignal(int)
    light_change_signal = QtCore.pyqtSignal(int)
    motor_state_change_signal = QtCore.pyqtSignal(int)

    cycle_run_state_change_signal = QtCore.pyqtSignal(bool)
    cycle_run_image_request_signal = QtCore.pyqtSignal()
    interface_cycle_stop_signal = QtCore.pyqtSignal()

    no_embryos_msg_box_show_signal = QtCore.pyqtSignal()
    no_embryos_msg_decision_signal = QtCore.pyqtSignal(int)

    pick_images_ready_signal = QtCore.pyqtSignal()
    pick_positions_ready_signal = QtCore.pyqtSignal(float, float)

    def __init__(self, main_window):
        QtCore.QThread.__init__(self)

        # ########## Get the Pick And Plate instance of the logger ##########
        self.logger = logging.getLogger("PickAndPlate")

        # ########## Get the Pick And Plate settings instance ##########
        self.settings = QtCore.QSettings()

        # ########## Reference to highest level window ##########
        self.main_window = main_window

        # ########## Thread flags ##########
        self.not_abort_flag = True
        self.cycle_running_flag = False
        self.cycle_init_flag = False
        self.cycle_end_flag = False

        # ########## Class Variables ##########
        self.cycle_paused = False

        self.controller_command_complete = False
        self.init_command_complete = False

        self.tinyg_x_location = 0
        self.tinyg_y_location = 0
        self.tinyg_z_location = 0
        self.tinyg_a_location = 0

        self.dish_x = 0
        self.dish_y = 0
        self.a1_x = 0
        self.a1_y = 0
        self.waste_x = 0
        self.waste_y = 0

        self.dish_center_px_x = 0
        self.dish_center_px_y = 0
        self.dist_cal_x = 0
        self.dist_cal_y = 0
        self.mm_per_px = 0

        self.cropped_only_raw = None
        self.cycle_monitor_qimage = None
        self.last_pick_qimage = None
        self.current_pick_qimage = None

        self.full_run_keypoints_array = []
        self.current_frame_keypoints = None

        self.cur_plate_x = None
        self.cur_plate_y = None

        self.data_received = False

        self.button_state = BUTTON_WAIT
        self.no_embryo_count = 0

        self.pick_images_displayed = False

        # Statistical variables
        self.current_pick_number = 0
        self.total_plated = 0
        self.mispicks = 0
        self.double_picks = 0
        self.total_detected = 0
        self.time_elapsed = 0
        self.time_remaining = 0
        self.success_rate = 0

        # ########## Make signal/slot connections ##########
        self.connect_signals_to_slots()

        # ########## Start timer ##########
        self.start()

    def connect_signals_to_slots(self):
        # CycleHandler to Controller
        self.x_y_move_request_signal.connect(self.main_window.controller.on_x_y_axis_move_requested_slot)
        self.z_move_request_signal.connect(self.main_window.controller.on_z_axis_move_requested_slot)
        self.a_move_request_signal.connect(self.main_window.controller.on_a_axis_move_requested_slot)
        self.full_system_home_request_signal.connect(self.main_window.controller.on_full_system_homing_requested_slot)
        self.light_change_signal.connect(self.main_window.controller.on_light_change_request_signal_slot)
        self.motor_state_change_signal.connect(self.main_window.controller.on_motor_state_change_request_signal_slot)

        # Controller to Cycle Handler
        self.main_window.controller.tinyg_location_update_signal.connect(self.on_system_location_changed_slot)
        self.main_window.controller.controller_init_complete_signal.connect(self.on_init_command_completed_slot)
        self.main_window.controller.controller_command_complete_signal.connect(
                self.on_controller_command_completed_slot)

        # VideoCore to CycleHandler
        self.main_window.video.requested_image_ready_signal.connect(self.on_video_requested_image_ready_slot)

        # CycleHandler to VideoCore
        self.cycle_run_state_change_signal.connect(self.main_window.video.cycle_run_changed_slot)
        self.cycle_run_image_request_signal.connect(self.main_window.video.on_cycle_run_image_requested_slot)

        # CycleHandler MessageBox Signals/Slots
        self.no_embryos_msg_box_show_signal.connect(self.on_no_more_embryos_found_slot)
        self.no_embryos_msg_decision_signal.connect(self.on_msg_decision_made_slot)
# TODO: FIGURE OUT WHY I CAN"T RUN MULTIPLE CYCLES
    def run(self):
        self.logger.debug("PickAndPlate Cycle Handler Thread Starting...")
        while self.not_abort_flag:
            if self.cycle_running_flag:
                if self.cycle_init_flag:
                    self.run_cycle_init()
                    self.cycle_init_flag = False

                self.check_if_no_embryos()

                if self.cycle_end_flag:
                    self.cycle_end_flag = False
                    self.move_z(29)
                    self.move_x_y(0,0)
                    self.set_lights(0)
                    self.interface_cycle_stop_signal.emit()
                    self.set_motors(False)
                    self.cycle_running_flag = False
                else:
                    self.run_main_pick_and_plate_cycle()

            else:
                self.msleep(250)

        self.logger.debug("PickAndPlate Cycle Handler Thread Exiting...")

    def run_main_pick_and_plate_cycle(self):

        while not self.data_received:
            self.cycle_run_image_request_signal.emit()
            self.set_motors(True)
            self.msleep(100)

        embryo_x_px = 0
        embryo_y_px = 0

        for point in self.current_frame_keypoints:
            if (not isnan(point.pt[0])) and (not isnan(point.pt[1])):
                embryo_x_px = point.pt[0]
                embryo_y_px = point.pt[1]
                break

        # self.logger.info("Center X: " + str(self.dish_center_px_x) + "\tX: " + str(embryo_x_px))
        # self.logger.info("Center Y: " + str(self.dish_center_px_y) + "\tY: " + str(embryo_y_px))

        if embryo_x_px and embryo_y_px:
            self.no_embryo_count = 0

            embryo_x = (self.dish_x - ((embryo_x_px - self.dish_center_px_x) * self.mm_per_px))
            embryo_y = (self.dish_y + ((embryo_y_px - self.dish_center_px_y) * self.mm_per_px))

            self.pick_positions_ready_signal.emit(embryo_x, embryo_y)
            self.make_current_and_last_pick_images(embryo_x_px, embryo_y_px)

            traverse_height = 20
            pick_depth = -17
            place_depth = -16

            # self.logger.info("Center X: " + str(self.dish_x) + "\tX: " + str(embryo_x))
            # self.logger.info("Center Y: " + str(self.dish_y) + "\tY: " + str(embryo_y))

            # Move up and over to found embryo co-ordinates
            self.move_z(traverse_height)
            self.move_x_y(embryo_x, embryo_y)

            # Move to pick depth, suck up embryo, and move back up
            self.move_z(pick_depth)
            self.move_a(150)
            self.move_z(traverse_height)

            # Move to the next unused well on the plate, then go down and expel embryo
            self.move_x_y(self.cur_plate_x, self.cur_plate_y)
            self.move_z(place_depth)
            self.move_a(-150)

            # Move pick head back up and to the waste container
            self.move_z(traverse_height)
            self.move_x_y(self.waste_x, self.waste_y)

            # Now that we're at the waste container, start looking for a new image
            self.cycle_run_image_request_signal.emit()
            self.data_received = False

            # Move down in waste and dispel any extra fluid
            self.move_z(-5)
            self.move_a(-90)
            self.move_a(90)
            self.move_z(traverse_height)

            # Increment well
            if (self.cur_plate_y + 9) > (self.a1_y + (11*9)):
                self.cur_plate_x += 9
                self.cur_plate_y = self.a1_y
            else:
                self.cur_plate_y += 9

            if self.cur_plate_x > (self.a1_x + (7*9)):
                self.cycle_end_flag = True

        else:
            self.no_embryo_count += 1
            self.data_received = False
            self.msleep(200)

    ########## Handling for no more embryos ###########
    def check_if_no_embryos(self):
        run_once = True
        if self.no_embryo_count > (NO_EMBRYO_THRESHOLD - 1):
            self.button_state = BUTTON_WAIT
            while self.button_state == BUTTON_WAIT:
                if run_once:
                    self.move_z(29)
                    self.move_x_y(0,0)
                    self.no_embryos_msg_box_show_signal.emit()
                    run_once = False

                self.set_lights(0)
                self.msleep(1500)
                self.set_lights(1000)
                self.msleep(1500)
                self.set_motors(True)

            if self.button_state == BUTTON_CONTINUE:
                self.no_embryo_count = 0
            else:
                self.cycle_end_flag = True

    def on_no_more_embryos_found_slot(self):
        msg = QtGui.QMessageBox()
        msg.setWindowTitle("No Embryos Detected")
        msg.setText("Press \"Continue\" if plating is not complete.\nTo stop current plating run, press \"Exit\".")
        msg.setModal(True)
        msg.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        # Make and add custom labeled buttons
        continue_button = msg.addButton("Continue", QtGui.QMessageBox.ActionRole)
        exit_button = msg.addButton("Exit", QtGui.QMessageBox.ActionRole)

        # Set stylesheet
        msg.setStyleSheet("QLabel{ color:rgb(202, 202, 202); }" +
        "QMessageBox{ background-color:rgb(55, 55, 55);}" +
        "QPushButton{ background-color:rgb(15,15,15); color:rgb(202, 202, 202);}")

        # Move box to center of screen
        box_size = msg.sizeHint()
        screen_size = QtGui.QDesktopWidget().screen().rect()
        msg.move((screen_size.width()/2 - box_size.width()/2), (screen_size.height()/2 - box_size.height()/2) )

        msg.exec_()

        clicked_button = msg.clickedButton()
        if clicked_button == continue_button:
            self.no_embryos_msg_decision_signal.emit(BUTTON_CONTINUE)
        elif clicked_button == exit_button:
            self.no_embryos_msg_decision_signal.emit(BUTTON_EXIT)


    def on_msg_decision_made_slot(self, decision):
        self.button_state = decision

    ########## Movement and Controller Methods ###########
    def move_x_y(self, x, y):
        #start = time.time()
        self.controller_command_complete = False
        self.x_y_move_request_signal.emit(x, y)
        while not self.controller_command_complete:
            # self.logger.info("Waiting for x_y")
            self.msleep(150)

    def move_z(self, z):
        self.controller_command_complete = False
        self.z_move_request_signal.emit(z)
        while not self.controller_command_complete:
            # self.logger.info("Waiting for z")
            self.msleep(150)

    def move_a(self, a):
        self.controller_command_complete = False
        self.a_move_request_signal.emit(a)
        while not self.controller_command_complete:
            # self.logger.info("Waiting for a")
            self.msleep(150)

    def set_lights(self, brightness):
        self.controller_command_complete = False
        self.light_change_signal.emit(brightness)
        while not self.controller_command_complete:
            # self.logger.info("Waiting for lights")
            self.msleep(150)

    def set_motors(self, state):
        self.controller_command_complete = False
        self.motor_state_change_signal.emit(state)
        while not self.controller_command_complete:
            # self.logger.info("Waiting for lights")
            self.msleep(150)

    def run_hardware_init(self):
        self.init_command_complete = False
        self.full_system_home_request_signal.emit()
        while not self.init_command_complete:
            # self.logger.info("Waiting for init complete")
            self.msleep(150)

    ########## Image Methods ###########
    def make_current_and_last_pick_images(self, embryo_x, embryo_y):
        self.last_pick_qimage = self.current_pick_qimage
        current_pick_raw = self.crop_image(self.cropped_only_raw, embryo_x, embryo_y)
        current_pick_raw = cv2.resize(current_pick_raw, (150, 150))
        self.current_pick_qimage = self.convert_to_qimage(current_pick_raw)

        self.pick_images_displayed = False
        self.pick_images_ready_signal.emit()
        while not self.pick_images_displayed:
            self.msleep(50)

    def on_pick_images_displayed_slot(self):
        self.pick_images_displayed = True

    @staticmethod
    def convert_to_qimage(input_matrix):
        return qimage2ndarray.array2qimage(input_matrix)


    @staticmethod
    def crop_image(input_matrix, embryo_x, embryo_y):
        side_length = 75

        x1 = embryo_x - (side_length/2)
        x2 = embryo_x + (side_length/2)
        y1 = embryo_y - (side_length/2)
        y2 = embryo_y + (side_length/2)

        cropped = input_matrix[y1:y2, x1:x2]

        return cropped

    ########## General Informational Display Methods ###########

    ##########  ###########
    def run_cycle_init(self):
        self.set_motors(True)
        self.cycle_run_state_change_signal.emit(True)
        self.cycle_run_image_request_signal.emit()
        self.set_cycle_run_flags_and_variables()
        self.run_hardware_init()
        self.set_lights(1000)
        self.move_z(29)

        self.data_received = False

    def on_cycle_start_pressed_slot(self):
        self.cycle_running_flag = True
        self.cycle_init_flag = True

    def on_cycle_pause_pressed_slot(self):
        self.cycle_paused = True

    def on_cycle_resume_pressed_slot(self):
        self.cycle_paused = False

    def on_cycle_stop_pressed_slot(self):
        self.cycle_end_flag = True

    def set_cycle_run_flags_and_variables(self):
        # Control flags / vars
        self.cycle_paused = False
        self.no_embryo_count = 0

        # Cal Vars
        self.dish_x = self.settings.value("system/system_calibration/dish_x_center").toFloat()[0]
        self.dish_y = self.settings.value("system/system_calibration/dish_y_center").toFloat()[0]
        self.a1_x = self.settings.value("system/system_calibration/a1_x_center").toFloat()[0]
        self.a1_y = self.settings.value("system/system_calibration/a1_y_center").toFloat()[0]
        self.waste_x = self.settings.value("system/system_calibration/waste_x_center").toFloat()[0]
        self.waste_y = self.settings.value("system/system_calibration/waste_y_center").toFloat()[0]

        self.dish_center_px_x = self.settings.value("system/system_calibration/crop_x_center").toInt()[0]
        self.dish_center_px_y = self.settings.value("system/system_calibration/crop_y_center").toInt()[0]
        self.dist_cal_x = self.settings.value("system/system_calibration/distance_cal_x").toInt()[0]
        self.dist_cal_y = self.settings.value("system/system_calibration/distance_cal_y").toInt()[0]
        self.mm_per_px = CAL_POINT_DIST_MM / sqrt(pow(self.dist_cal_x, 2) + pow(self.dist_cal_y, 2))

        self.cur_plate_x = self.a1_x
        self.cur_plate_y = self.a1_y

    def on_video_requested_image_ready_slot(self):
        self.cropped_only_raw = self.main_window.video.cropped_only_raw # USED TO BE A .COPY HERE
        self.current_frame_keypoints = self.main_window.video.keypoints
        self.data_received = True

    def on_controller_command_completed_slot(self):
        self.controller_command_complete = True

    def on_init_command_completed_slot(self):
        self.init_command_complete = True

    def on_system_location_changed_slot(self, x, y, z, a):
        self.tinyg_x_location = x
        self.tinyg_y_location = y
        self.tinyg_z_location = z
        self.tinyg_a_location = a

    def on_kill_threads_slot(self):
        self.not_abort_flag = False