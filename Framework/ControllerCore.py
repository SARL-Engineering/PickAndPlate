"""
    This file contains the ControllerCore sub-class as part of the Framework Class
    This class handles initializing and interfacing with the mutli-axis controller
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
import serial
import json

# Custom imports

#####################################
# Global Variables
#####################################
SERIAL_PORT = '/dev/ttyUSB0'

#####################################
# PickAndPlateController Definition
#####################################
class PickAndPlateController(QtCore.QThread):
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
        self.reconnect_to_tinyg_flag = True
        self.send_command_to_tinyg_flag = False

         # ########## Class Variables ##########
        self.serial = None
        self.serial_in_buffer = ""

        # ########## Make signal/slot connections ##########
        self.connect_signals_to_slots()

        # ########## Start thread ##########
        self.start()

    def connect_signals_to_slots(self):
        pass

    def run(self):

        self.logger.debug("PickAndPlate Controller Thread Starting...")
        while self.not_abort_flag:
            if self.reconnect_to_tinyg_flag:
                self.reconnect_to_tinyg()
            elif self.send_command_to_tinyg_flag:
                pass
            elif self.serial.inWaiting() > 0:
                self.read_from_tinyg()
            else:
                self.msleep(50)

        self.logger.debug("PickAndPlate Controller Thread Exiting...")

    def reconnect_to_tinyg(self):
        self.serial = serial.Serial(SERIAL_PORT, 115200)  # Should never change unless you do bad things....
        if self.serial.isOpen():
            self.reconnect_to_tinyg_flag = False

    def run_system_init_slot(self):
        pass

    def run_rough_homing_sequence_slot(self):
        pass

    def run_precision_home_sequence_slot(self):
        pass

    def read_from_tinyg(self):
        self.serial_in_buffer += self.serial.read(1)
        if self.serial_in_buffer[-1] == '\n':
            self.process_tinyg_response()

    def write_to_tinyg(self, to_write):
        self.serial.write(to_write + '\n')

    def process_tinyg_response(self):
        processed_json = json.loads(self.serial_in_buffer)

        self.serial_in_buffer = ""

    def on_kill_threads_slot(self):
        self.not_abort_flag = False