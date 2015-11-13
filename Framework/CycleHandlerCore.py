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
        self.do_cycle_init = False
        self.cycle_paused = False
        self.pick_complete = False

        self.image_ready = False

        # ########## Make signal/slot connections ##########
        self.connect_signals_to_slots()

        # ########## Start timer ##########
        # FIXME: REMOVE THIS FIXME self.start()

    def connect_signals_to_slots(self):
        pass

    def run(self):
        self.logger.debug("PickAndPlate Cycle Handler Thread Starting...")
        while self.not_abort_flag:
            if self.cycle_running_flag:
                self.run_main_pick_and_plate_cycle()
            else:
                self.msleep(250)

        self.logger.debug("PickAndPlate Cycle Handler Thread Exiting...")

    def run_main_pick_and_plate_cycle(self):
        if self.do_cycle_init:
            self.reset_cycle_run_flags_and_variables()
            # Run controller init for cycle run
            # Set video controller to cycle mode
            # Move controller to middle of dish, well A1, waste, and go back to home
            # Retrieve initial image
            while not self.image_ready:
                self.msleep(100)


        # Check if embryo's available for pick
        ## If not, ask user if they want to swirl dish and continue
            ## If they choose to continue, re-take image, wait for image ready, and return
            ## Otherwise, set cycle_running flag to False run cycle_end function and return



        # Retrieve keypoints from image and determine best pick
        # Display full plate with detection and new pick / last pick images
        # Pick up embryo
        # Move to desired well

        self.image_ready = False
        # Emit signal to capture new image

        # Move to waste and expel

        while (not self.image_ready) or self.cycle_paused:
            self.msleep(100)

        # Determine if embryo is gone or if double pick occurred and update statistics


    def on_cycle_start_pressed_slot(self):
        self.do_cycle_init = True
        self.cycle_running_flag = True

    def on_cycle_pause_pressed_slot(self):
        self.cycle_paused = True

    def on_cycle_resume_pressed_slot(self):
        self.cycle_paused = False

    def on_cycle_stop_pressed_slot(self):
        self.cycle_running_flag = False

    def reset_cycle_run_flags_and_variables(self):
        self.cycle_paused = False
        self.pick_complete = True
        self.image_ready = False

    def on_kill_threads_slot(self):
        self.not_abort_flag = False