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

# self.serial_out_queue.append(self.convert_to_json({'ajd':0.01}))
# self.msleep(30)  # Required for config changes
# self.serial_out_queue.append(self.convert_to_json({'ajh':10000}))
# self.msleep(30)  # Required for config changes
# self.serial_out_queue.append(self.convert_to_json({'atm':100}))
# self.msleep(50)  # Required for config changes
# self.serial_out_queue.append(self.convert_to_json({'ajm':5000}))
# self.msleep(30)  # Required for config changes
# self.serial_out_queue.append(self.convert_to_json({'atn':-100}))
# self.msleep(30)  # Required for config changes
# self.serial_out_queue.append(self.convert_to_json({'asv':500}))
# self.msleep(30)  # Required for config changes
# self.serial_out_queue.append(self.convert_to_json({'ajm':2500}))
# self.msleep(50)  # Required for config changes
# self.serial_out_queue.append(self.convert_to_json({'avm':5000}))
# self.msleep(30)  # Required for config changes
# self.serial_out_queue.append(self.convert_to_json({'afr':5000}))
# self.msleep(30)  # Required for config changes
# self.serial_out_queue.append(self.convert_to_json({'aam':1}))
# self.msleep(30)  # Required for config changes
# self.serial_out_queue.append(self.convert_to_json({'afr':16000}))
# self.msleep(50)  # Required for config changes
# self.serial_out_queue.append(self.convert_to_json({'x':None}))
# self.serial_out_queue.append(self.convert_to_json({'a':None}))


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
SERIAL_BAUD = 115200

INITIALIZING_STATE = 0
READY_FOR_USE_STATE = 1
ALARM_STATE = 2
PROGRAM_STOP_STATE = 3
PROGRAM_END_STATE = 4
MOTION_RUNNING_STATE = 5
MOTION_HOLDING_STATE = 6
PROBE_CYCLE_STATE = 7
RUNNING_STATE = 8
HOMING_STATE = 9

MACHINE_STATES = ["Initializing State", "Ready for Use State", "Alarm State", "Program Stop State", "Program End State",
                  "Motion Running State", "Motion Holding State", "Probe Cycle State", "Running State", "Homing State"]

ROUGH = 0
FINE = 1

MM_PER_UL = 0.1215
#12.15mm per 100 microliter
#0.1215mm per microliter

#####################################
# PickAndPlateController Definition
#####################################
class SerialHandler(QtCore.QThread):
    tinyg_current_location_signal = QtCore.pyqtSignal(float, float, float, float)
    tinyg_current_machine_state_signal = QtCore.pyqtSignal(int)
    tinyg_command_processed_signal = QtCore.pyqtSignal()

    def __init__(self):
        QtCore.QThread.__init__(self)

        # ########## Get the Pick And Plate instance of the logger ##########
        self.logger = logging.getLogger("PickAndPlate")

        # ########## Get the Pick And Plate settings instance ##########
        self.settings = QtCore.QSettings()

        # ########## Thread flags ##########
        self.not_abort_flag = True
        self.reconnect_to_tinyg_flag = True

        # ########## Class Variables ##########
        #Internal
        self.serial = serial.Serial()
        self.serial_connected = False

        self.serial_in_buffer = ""
        self.serial_out_queue = []

        # TinyG Returned Information Storage
        self.tinyg_x_location = 0
        self.tinyg_y_location = 0
        self.tinyg_z_location = 0
        self.tinyg_a_location = 0

        self.tinyg_velocity = 0
        self.tinyg_machine_state = 0
        self.tinyg_serial_buffer_remaining = 32


        self.start()

    def run(self):
        while self.not_abort_flag:
            if self.reconnect_to_tinyg_flag:
                self.reconnect_to_tinyg()
            else:
                if self.serial.inWaiting() > 0:
                    self.read_from_tinyg()
                else:
                    if self.serial_out_queue:
                        self.send_one_line_from_queue()
            self.msleep(50)

    def reconnect_to_tinyg(self):
       try:
            self.serial = serial.Serial(SERIAL_PORT, SERIAL_BAUD)  # Should never change unless you do bad things....
            if self.serial.isOpen():
                self.reconnect_to_tinyg_flag = False
                self.clear_hardware_and_software_buffers()
            self.msleep(2500)
       except:
            self.logger.error("Unable to connect to TinyG. Trying again.")
            self.msleep(1000)

    def send_one_line_from_queue(self):
        if self.tinyg_serial_buffer_remaining > 10:
            # self.logger.info("Send String: " + str(self.serial_out_queue[0])[:-1])
            self.serial.write(self.serial_out_queue[0])
            del self.serial_out_queue[0]

    def read_from_tinyg(self):
        current_char = ''
        while not (current_char == '\n'):
            if self.serial.inWaiting() > 0:
                current_char = self.serial.read(1)
                self.serial_in_buffer += current_char

        self.process_tinyg_response()

    def process_tinyg_response(self):
        if ord(self.serial_in_buffer[0]) < 40:
            self.serial_in_buffer = self.serial_in_buffer[1:]
            self.logger.info("Buffer is corrupted.")
        try:
            processed_json = json.loads(self.serial_in_buffer)

            if 'sr' in processed_json:
                system_response = processed_json['sr']
                if 'vel' in system_response:
                    self.tinyg_velocity = float(system_response['vel'])
                if 'posx' in system_response:
                    self.tinyg_x_location = float(system_response['posx'])
                if 'posy' in system_response:
                    self.tinyg_y_location = float(system_response['posy'])
                if 'posz' in system_response:
                    self.tinyg_z_location = float(system_response['posz'])
                if 'posa' in system_response:
                    self.tinyg_a_location = float(system_response['posa'])
                if 'stat' in system_response:
                    self.tinyg_machine_state = int(system_response['stat'])
                    self.tinyg_current_machine_state_signal.emit(self.tinyg_machine_state)

                self.tinyg_current_location_signal.emit(self.tinyg_x_location, self.tinyg_y_location, \
                                                        self.tinyg_z_location, self.tinyg_a_location)

                #print "X: " + str(self.tinyg_x_location) + " Y: " + str(self.tinyg_y_location) + " Z: " + \
                #      str(self.tinyg_z_location) + " VEL: " + str(self.tinyg_velocity)

                print "Processed: " + str(processed_json)

            elif 'qr' in processed_json:
                self.tinyg_serial_buffer_remaining = int(processed_json['qr'])

            elif 'r' in processed_json:
                self.tinyg_command_processed_signal.emit()
                print "Processed: " + str(processed_json)

        except:
            pass

        self.serial_in_buffer = ""

    def clear_hardware_and_software_buffers(self):
        self.clear_hardware_buffers()
        self.serial_out_queue = []
        self.serial_in_buffer = ""

    def clear_hardware_buffers(self):
        while self.serial.inWaiting() > 0:
            self.serial.read(1)

    def on_light_change_requested_slot(self, brightness):
        if brightness > 0:
            brightness = self.constrain_to_range(brightness, 0, 1000)
            self.serial_out_queue.append(self.convert_to_json({'gc': 'M3 S' + str(brightness)}))
        else:
            self.serial_out_queue.append(self.convert_to_json({'gc': 'M3 S0'}))

    def on_z_homing_requested_slot(self, precision):
        if precision == ROUGH:
            self.serial_out_queue.append(self.convert_to_json({'zsn':0}))
            self.msleep(30)  # Required for config changes
            self.serial_out_queue.append(self.convert_to_json({'zsx':1}))
            self.msleep(30)  # Required for config changes
            self.serial_out_queue.append(self.convert_to_json({'gc': 'G28.2 Z0'}))
        elif precision == FINE:
            pass
            self.serial_out_queue.append(self.convert_to_json({'gc': 'G28.2 X0 Y0'}))

    def on_x_y_homing_requested_slot(self):
        self.serial_out_queue.append(self.convert_to_json({'gc': 'G28.2 X0 Y0'}))

    def on_a_homing_requested_slot(self):
        self.serial_out_queue.append(self.convert_to_json({'gc': 'G28.2 A0'}))


    def on_absolute_position_change_requested_slot(self, x, y, z, a):
        out_string = 'G90 G0'
        out_string += ' X' + str(x)
        out_string += ' Y' + str(y)
        out_string += ' Z' + str(z)
        out_string += ' A' + str(a)

        self.serial_out_queue.append(self.convert_to_json({'gc': out_string}))

    def on_relative_position_change_requested_slot(self, x, y, z, a):
        out_string = 'G91 G0'
        out_string += ' X' + str(x)
        out_string += ' Y' + str(y)
        out_string += ' Z' + str(z)
        out_string += ' A' + str(a)

        self.serial_out_queue.append(self.convert_to_json({'gc': out_string}))

    @staticmethod
    def convert_to_json(to_send):
        return json.dumps(to_send) + '\n'  # Newline necessary for TinyG to process

    @staticmethod
    def constrain_to_range(number, min_val, max_val):
        return min(max_val, max(number, min_val))

    def on_kill_threads_slot(self):
        self.not_abort_flag = False


#####################################
# PickAndPlateController Definition
#####################################
class PickAndPlateController(QtCore.QThread):
    tinyg_move_absolute_signal = QtCore.pyqtSignal(float, float, float, float)
    tinyg_move_relative_signal = QtCore.pyqtSignal(float, float, float, float)
    tinyg_z_home_signal = QtCore.pyqtSignal(int)
    tinyg_x_y_home_signal = QtCore.pyqtSignal()
    tinyg_a_home_signal = QtCore.pyqtSignal()
    tinyg_light_change_signal = QtCore.pyqtSignal(int)

    requested_move_complete_signal = QtCore.pyqtSignal()

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
        self.system_init_flag = True

        # ########## Class Variables ##########
        self.serial_handler = SerialHandler()

        self.tinyg_x_location = 0
        self.tinyg_y_location = 0
        self.tinyg_z_location = 0
        self.tinyg_a_location = 0

        self.tinyg_x_location_desired = 0
        self.tinyg_y_location_desired = 0
        self.tinyg_z_location_desired = 0
        self.tinyg_a_location_desired = 0

        self.tinyg_machine_state = INITIALIZING_STATE

        self.tinyg_command_processed = False


        # ########## Make signal/slot connections ##########
        self.connect_signals_to_slots()

        # ########## Start thread ##########
        self.start()

    def connect_signals_to_slots(self):
        #PickAndPlateController to SerialHandler
        self.tinyg_light_change_signal.connect(self.serial_handler.on_light_change_requested_slot)
        self.tinyg_z_home_signal.connect(self.serial_handler.on_z_homing_requested_slot)
        self.tinyg_x_y_home_signal.connect(self.serial_handler.on_x_y_homing_requested_slot)
        self.tinyg_a_home_signal.connect(self.serial_handler.on_a_homing_requested_slot)
        self.tinyg_move_absolute_signal.connect(self.serial_handler.on_absolute_position_change_requested_slot)
        self.tinyg_move_relative_signal.connect(self.serial_handler.on_relative_position_change_requested_slot)

        #SerialHandler to PickAndPlateController
        self.serial_handler.tinyg_current_location_signal.connect(self.on_tinyg_location_changed_slot)
        self.serial_handler.tinyg_current_machine_state_signal.connect(self.on_tinyg_machine_state_changed_slot)
        self.serial_handler.tinyg_command_processed_signal.connect(self.on_tinyg_command_processed_successfully_slot)

    def run(self):
        self.logger.debug("PickAndPlate Controller Thread Starting...")

        while not self.tinyg_machine_state != READY_FOR_USE_STATE:
            self.msleep(250)

        self.msleep(1500)

        while self.not_abort_flag:
            if self.system_init_flag:
                self.run_system_init_slot()

        self.serial_handler.not_abort_flag = False
        self.serial_handler.wait()
        self.logger.debug("PickAndPlate Controller Thread Exiting...")


    def run_system_init_slot(self):



        self.system_init_flag = False


    def run_rough_homing_sequence_slot(self):
        pass

    def run_precision_home_sequence_slot(self):
        pass

    def on_start_cycle_pressed_slot(self):
        # self.convert_to_json_and_send({'gc': 'M3 S1000'})
        # self.convert_to_json_and_send({'gc': 'G90 G0 Z12'})
        # self.convert_to_json_and_send({'gc': 'G90 G0 X-125 Y-110'})
        # self.convert_to_json_and_send({'gc': 'G90 G0 Z-14'})
        #
        #
        # self.convert_to_json_and_send({'gc': 'G90 G0 Z12'})
        # self.convert_to_json_and_send({'gc': 'G90 G0 X-34 Y-135'})
        # self.convert_to_json_and_send({'gc': 'G90 G0 Z-13'})
        #
        # self.convert_to_json_and_send({'gc': 'G90 G0 Z-2'}) # COULD BE USED TO DEMO WHOLE PLATE
        # self.convert_to_json_and_send({'gc': 'G90 G0 Z12'})
        # self.convert_to_json_and_send({'gc': 'G90 G0 X-125 Y0'})
        # self.convert_to_json_and_send({'gc': 'G90 G0 Z0'})
        # self.convert_to_json_and_send({'gc': 'M5'})
        #
        # # for x in range(10):
        # #     self.convert_to_json_and_send({'gc': 'G90 G0 X-125 Y-110'})
        # #     self.convert_to_json_and_send({'gc': 'G90 G0 X-34 Y-135'})
        # #     self.convert_to_json_and_send({'gc': 'G90 G0 X-125 Y0'})
        #
        # self.convert_to_json_and_send({'gc': 'G90 G0 X-9.25 Y-9'})
        pass
    ########## Methods for general commands / light control ##########
    def on_light_change_requested_slot(self, brightness):
        self.tinyg_command_processed = False
        self.tinyg_light_change_signal.emit(brightness)

        while not self.tinyg_command_processed:
            self.msleep(50)

    ########## Methods for all axes ##########
    def on_full_system_homing_requested_slot(self):
        self.on_a_axis_home_requested_slot()
        self.on_z_axis_homing_requested_slot(ROUGH)
        self.on_x_y_axis_move_relative_requested_slot(-20, -20)
        self.on_x_y_axes_homing_requested_slot()

    ########## Z Axis Methods ##########
    def on_z_axis_move_requested_slot(self, z):
        current_a = self.tinyg_a_location
        current_x = self.tinyg_x_location
        current_y = self.tinyg_y_location

        self.tinyg_z_location_desired = z
        self.tinyg_move_absolute_signal.emit()(current_x, current_y, self.tinyg_z_location_desired, current_a)

        while self.tinyg_z_location != self.tinyg_z_location_desired:
            self.msleep(50)

    def on_z_axis_homing_requested_slot(self, type):
        self.tinyg_z_home_signal.emit(type)
        self.tinyg_machine_state = HOMING_STATE

        while self.tinyg_machine_state == HOMING_STATE:
            self.msleep(50)

    ########## X Y Axis Methods ##########
    def on_x_y_axis_move_requested_slot(self, x, y):
        current_a = self.tinyg_a_location
        current_z = self.tinyg_z_location
        self.tinyg_x_location_desired = x
        self.tinyg_y_location_desired = y

        self.tinyg_move_absolute_signal.emit(self.tinyg_x_location_desired, self.tinyg_y_location_desired, \
                                             current_z, current_a)

        while (self.tinyg_x_location_desired != self.tinyg_x_location) or \
                (self.tinyg_y_location_desired != self.tinyg_y_location):
            self.msleep(50)

    def on_x_y_axis_move_relative_requested_slot(self, x, y):
        current_x = self.tinyg_x_location
        current_y = self.tinyg_y_location

        self.tinyg_x_location_desired = x + current_x
        self.tinyg_y_location_desired = y + current_y

        self.tinyg_move_relative_signal.emit(x, y, 0, 0)

        while (self.tinyg_x_location_desired != self.tinyg_x_location) or \
                (self.tinyg_y_location_desired != self.tinyg_y_location):
            self.msleep(50)

    def on_x_y_axes_homing_requested_slot(self):
        self.tinyg_x_y_home_signal.emit()
        self.tinyg_machine_state = HOMING_STATE

        while self.tinyg_machine_state == HOMING_STATE:
            self.msleep(50)

    ########## A Axis Methods ##########
    def on_a_axis_move_requested_slot(self, microliters):
        current_a_position = self.tinyg_a_location
        move_amount = (MM_PER_UL * microliters)
        self.tinyg_a_location_desired = (MM_PER_UL * microliters) + current_a_position

        self.tinyg_move_relative_signal.emit(0, 0, 0, move_amount)

        while self.tinyg_a_location != self.tinyg_a_location_desired:
            self.msleep(50)

        self.requested_move_complete_signal.emit()

    def on_a_axis_home_requested_slot(self):
        self.tinyg_a_home_signal.emit()
        self.tinyg_machine_state = HOMING_STATE

        while self.tinyg_machine_state == HOMING_STATE:
            self.msleep(50)



    def on_stop_cycle_button_pressed_slot(self):
        self.convert_to_json_and_send({'gc': 'M5'})

    ########## Cross thread variable synchronization ##########
    def on_tinyg_location_changed_slot(self, x, y, z, a):
        self.tinyg_x_location = x
        self.tinyg_y_location = y
        self.tinyg_z_location = z
        self.tinyg_a_location = a

    def on_tinyg_machine_state_changed_slot(self, state):
        self.tinyg_machine_state = state

    def on_tinyg_command_processed_successfully_slot(self):
        self.tinyg_command_processed = True

    ########## Program End Kill Thread Method ##########
    def on_kill_threads_slot(self):
        self.not_abort_flag = False

