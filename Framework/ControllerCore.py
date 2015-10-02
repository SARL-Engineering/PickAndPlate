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
# SerialReader Definition
#####################################
class SerialReader(QtCore.QThread):
    def __init__(self, serial_object):
        QtCore.QThread.__init__(self)

        # ########## Thread flags ##########
        self.not_abort_flag = True

        self.serial = serial_object

    def run(self):
        while self.not_abort_flag:
            if self.serial.inWaiting() > 0:
                self.serial.readline()
            else:
                self.msleep(50)


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
        self.serial_reader = None
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
            #elif self.serial.inWaiting() > 0:
            #    self.read_from_tinyg()
            else:
                self.msleep(50)

        self.serial_reader.not_abort_flag = False
        self.serial_reader.wait()
        self.logger.debug("PickAndPlate Controller Thread Exiting...")

    def reconnect_to_tinyg(self):
        self.serial = serial.Serial(SERIAL_PORT, 115200)  # Should never change unless you do bad things....
        if self.serial.isOpen():
            self.reconnect_to_tinyg_flag = False
            self.serial_reader = SerialReader(serial)
            self.run_system_init_slot()

    def run_system_init_slot(self):
        ##### Current important values for calibration #####
        # Current center of precision homing stand is X-9 Y-9.5
        # Radius of 15 gauge tube is 0.72475mm
        # Distance from calibration post to center of z cal plate
        # Z12 clears plate
        # X-125 Y-110 is roughly center of dish
        # Z-14 is nicely in the water
        # Well A1 is X-34 Y-135 and Z-13
        ##### End of important values #####
        delay_time = 5000

        self.convert_to_json_and_send({'gc': 'M3 S800'})
        self.msleep(delay_time)
        self.convert_to_json_and_send({'zsn':0})
        self.msleep(delay_time)
        self.convert_to_json_and_send({'zsx':1})
        self.msleep(delay_time)
        self.convert_to_json_and_send({'gc': 'G28.2 Z0'})
        self.msleep(delay_time)
        self.convert_to_json_and_send({'gc': 'G91 G0 X-10 Y-10'})
        self.msleep(delay_time)
        self.convert_to_json_and_send({'gc': 'G28.2 X0 Y0'})
        self.msleep(delay_time)

        self.convert_to_json_and_send({'gc': 'G90 G0 X-9.25 Y-9'})
        self.msleep(delay_time)

        self.convert_to_json_and_send({'zsn':1})
        self.msleep(delay_time)
        self.convert_to_json_and_send({'zsx':0})
        self.msleep(delay_time)
        self.convert_to_json_and_send({'gc': 'G28.2 Z0'})
        self.msleep(delay_time)

        self.convert_to_json_and_send({'gc': 'G90 G0 Z2.5'})
        self.msleep(delay_time)
        self.convert_to_json_and_send({'gc': 'G28.2 X0'})
        self.msleep(delay_time)
        self.convert_to_json_and_send({'gc': 'G90 G0 X-5 Y-20'})
        self.msleep(delay_time)
        self.convert_to_json_and_send({'gc': 'G28.2 Y0'})
        self.msleep(delay_time)

        self.convert_to_json_and_send({'gc': 'G90 G0 X-5.487875 Y-4.763125 Z-3'})
        self.msleep(delay_time)

        #Start DEMO
        count = 3
        #while count > 0:
        self.convert_to_json_and_send({'gc': 'G90 G0 Z12'})
        self.msleep(delay_time)
        self.convert_to_json_and_send({'gc': 'G90 G0 X-125 Y-110'})
        self.msleep(delay_time)
        self.convert_to_json_and_send({'gc': 'G90 G0 Z-14'})
        self.msleep(delay_time)
        #self.msleep(suck_delay)
        self.convert_to_json_and_send({'gc': 'G90 G0 Z12'})
        self.msleep(delay_time)
        self.convert_to_json_and_send({'gc': 'G90 G0 X-34 Y-135'})
        self.msleep(delay_time)
        self.convert_to_json_and_send({'gc': 'G90 G0 Z-13'})
        self.msleep(delay_time)
        #self.msleep(suck_delay)
        #self.convert_to_json_and_send({'gc': 'G90 G0 Z-2'}) COULD BE USED TO DEMO WHOLE PLATE
        self.convert_to_json_and_send({'gc': 'G90 G0 Z12'})
        self.msleep(delay_time)
        self.convert_to_json_and_send({'gc': 'G90 G0 X-125 Y0'})
        self.msleep(delay_time)
        self.convert_to_json_and_send({'gc': 'G90 G0 Z0'})
        self.msleep(delay_time)
            #self.msleep(suck_delay)
           # count -= 1



    def run_rough_homing_sequence_slot(self):
        pass

    def run_precision_home_sequence_slot(self):
        pass

    def read_from_tinyg(self):
        self.serial_in_buffer += self.serial.read(1)
        if self.serial_in_buffer[-1] == '\n':
            self.process_tinyg_response()

    def convert_to_json_and_send(self, to_send):
        self.write_to_tinyg(json.dumps(to_send))

    def write_to_tinyg(self, to_write):
        self.serial.write(to_write + '\n')

    def process_tinyg_response(self):
        try:
            processed_json = json.loads(self.serial_in_buffer)

            self.serial_in_buffer = ""
        except:
            pass

    def on_kill_threads_slot(self):
        self.not_abort_flag = False