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
from PyQt4 import QtCore
import logging

# Custom imports

#####################################
# Global Variables
#####################################

#####################################
# PickAndPlateController Definition
#####################################
class PickAndPlateCycleHandler(QtCore.QThread):
    full_system_home_request_signal = QtCore.pyqtSignal()
    x_y_move_request_signal = QtCore.pyqtSignal(float, float)
    z_move_request_signal = QtCore.pyqtSignal(float)
    a_move_request_signal = QtCore.pyqtSignal(int)
    light_change_signal = QtCore.pyqtSignal(int)

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

        # ########## Class Variables ##########
        self.cycle_paused = False

        self.controller_command_complete = False
        self.init_command_complete = False

        self.tinyg_x_location = 0
        self.tinyg_y_location = 0
        self.tinyg_z_location = 0
        self.tinyg_a_location = 0

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

        # Controller to Cycle Handler
        self.main_window.controller.tinyg_location_update_signal.connect(self.on_system_location_changed_slot)
        self.main_window.controller.controller_init_complete_signal.connect(self.on_init_command_completed_slot)
        self.main_window.controller.controller_command_complete_signal.connect(
                self.on_controller_command_completed_slot)

    def run(self):
        self.logger.debug("PickAndPlate Cycle Handler Thread Starting...")
        while self.not_abort_flag:
            if self.cycle_running_flag:
                self.run_main_pick_and_plate_cycle()
                self.cycle_running_flag = False
            else:
                self.msleep(250)

        self.logger.debug("PickAndPlate Cycle Handler Thread Exiting...")

    def run_main_pick_and_plate_cycle(self):
        dish_x = self.settings.value("system/system_calibration/dish_x_center").toFloat()[0]
        dish_y = self.settings.value("system/system_calibration/dish_y_center").toFloat()[0]
        a1_x = self.settings.value("system/system_calibration/a1_x_center").toFloat()[0]
        a1_y = self.settings.value("system/system_calibration/a1_y_center").toFloat()[0]
        waste_x = self.settings.value("system/system_calibration/waste_x_center").toFloat()[0]
        waste_y = self.settings.value("system/system_calibration/waste_y_center").toFloat()[0]

        self.reset_cycle_run_flags_and_variables()

        self.run_init()
        self.set_lights(500)
        self.move_z(29)

        while self.cycle_running_flag:
            self.move_x_y(dish_x, dish_y)
            self.move_z(-10)
            self.move_a(100)
            self.move_z(29)

            self.move_x_y(a1_x, a1_y)
            self.move_z(-10)
            self.move_a(-100)
            self.move_z(29)

            self.move_x_y(waste_x, waste_y)
            self.move_z(-10)
            self.move_a(-50)
            self.move_a(50)
            self.move_z(29)

            self.msleep(2000)

        self.set_lights(0)

        # Run controller init for cycle run
        # Set video controller to cycle mode
        # Move controller to middle of dish, well A1, waste, and go back to home
        # Retrieve initial image
        # while not self.image_ready:
        #     self.msleep(100)


        # Check if embryo's available for pick
        ## If not, ask user if they want to swirl dish and continue
            ## If they choose to continue, re-take image, wait for image ready, and return
            ## Otherwise, set cycle_running flag to False run cycle_end function and return



        # Retrieve keypoints from image and determine best pick
        # Display full plate with detection and new pick / last pick images
        # Pick up embryo
        # Move to desired well

        # self.image_ready = False
        # Emit signal to capture new image

        # Move to waste and expel

        # while (not self.image_ready) or self.cycle_paused:
        #     self.msleep(100)

        # Determine if embryo is gone or if double pick occurred and update statistics

    def move_x_y(self, x, y):
        self.controller_command_complete = False
        self.x_y_move_request_signal.emit(x, y)
        while not self.controller_command_complete:
            self.msleep(50)

    def move_z(self, z):
        self.controller_command_complete = False
        self.z_move_request_signal.emit(z)
        while not self.controller_command_complete:
            self.msleep(50)

    def move_a(self, a):
        self.controller_command_complete = False
        self.a_move_request_signal.emit(a)
        while not self.controller_command_complete:
            self.msleep(50)

    def set_lights(self, brightness):
        self.controller_command_complete = False
        self.light_change_signal.emit(brightness)
        while not self.controller_command_complete:
            self.msleep(50)

    def run_init(self):
        self.init_command_complete = False
        self.full_system_home_request_signal.emit()
        while not self.init_command_complete:
            self.msleep(50)

    def on_cycle_start_pressed_slot(self):
        self.cycle_running_flag = True

    def on_cycle_pause_pressed_slot(self):
        self.cycle_paused = True

    def on_cycle_resume_pressed_slot(self):
        self.cycle_paused = False

    def on_cycle_stop_pressed_slot(self):
        self.cycle_running_flag = False

    def reset_cycle_run_flags_and_variables(self):
        self.cycle_paused = False

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