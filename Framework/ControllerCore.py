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

# 8.73125mm from center of precision to tangential edge of x_y rods


#####################################
# Imports
#####################################
# Python native imports
from PyQt4 import QtCore
import logging
import serial
import json
import time
from math import sqrt, pow
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

IGNORE_VALUE = 1000

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

        # Block to turn off lights when program closes properly
        self.serial_out_queue = []
        self.on_light_change_requested_slot(0)
        self.send_one_line_from_queue()

    def reconnect_to_tinyg(self):
       try:
            self.serial = serial.Serial(SERIAL_PORT, SERIAL_BAUD)  # Should never change unless you do bad things....
            if self.serial.isOpen():
                self.reconnect_to_tinyg_flag = False
                self.clear_hardware_and_software_buffers()
                self.reset_tinyg()
            self.msleep(2500)
       except:
            self.logger.error("Unable to connect to TinyG. Trying again.")
            self.msleep(1000)

    def send_one_line_from_queue(self):
        if self.tinyg_serial_buffer_remaining > 10:
            self.serial.write(self.serial_out_queue[0])
            # self.logger.info("Command: " + str(self.serial_out_queue[0]))
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

                self.tinyg_current_location_signal.emit(self.tinyg_x_location, self.tinyg_y_location,
                                                        self.tinyg_z_location, self.tinyg_a_location)

            elif 'qr' in processed_json:
                self.tinyg_serial_buffer_remaining = int(processed_json['qr'])

            elif 'r' in processed_json:
                special_response = processed_json['r']
                if 'sys' in special_response:
                    self.logger.debug("Sys:" + str(special_response['sys']))
                if '1' in special_response:
                    self.logger.debug("1:" + str(special_response['1']))
                if 'x' in special_response:
                    self.logger.debug("x:" + str(special_response['x']))
                if '2' in special_response:
                    self.logger.debug("2:" + str(special_response['2']))
                if 'y' in special_response:
                    self.logger.debug("y:" + str(special_response['y']))
                if '3' in special_response:
                    self.logger.debug("3:" + str(special_response['3']))
                if 'z' in special_response:
                    self.logger.debug("z:" + str(special_response['z']))
                if '4' in special_response:
                    self.logger.debug("4:" + str(special_response['4']))
                if 'a' in special_response:
                    self.logger.debug("a:" + str(special_response['a']))
                if 'p1' in special_response:
                    self.logger.debug("p1:" + str(special_response['p1']))
                self.tinyg_command_processed_signal.emit()

            #self.logger.info("Processed: " + str(processed_json))
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

    def reset_tinyg(self):
        self.serial_out_queue.append("^x\n")

        # self.serial_out_queue.append(self.convert_to_json({'xvm':12500}))
        # self.serial_out_queue.append(self.convert_to_json({'yvm':10000}))
        # self.serial_out_queue.append(self.convert_to_json({'zvm':5000}))
        # self.serial_out_queue.append(self.convert_to_json({'zzb':6.5}))
        # self.serial_out_queue.append(self.convert_to_json({'ajm':1000}))
        # self.serial_out_queue.append(self.convert_to_json({'xjm':2000}))
        # self.serial_out_queue.append(self.convert_to_json({'yjm':2000}))
        # self.serial_out_queue.append(self.convert_to_json({'afr':8000}))
        # self.serial_out_queue.append(self.convert_to_json({'avm':8000}))
        # self.serial_out_queue.append(self.convert_to_json({'ajm':2000}))

    def on_motor_state_change_requested_slot(self, state):
        if state:
            self.serial_out_queue.append(self.convert_to_json({'me': None})) # Keep motors on for 30 minutes
        else:
            self.serial_out_queue.append(self.convert_to_json({'md': None}))

    def on_dump_tinyg_settings_dump_slot(self):
        self.serial_out_queue.append(self.convert_to_json({'sys': None}))
        self.serial_out_queue.append(self.convert_to_json({'1': None}))
        self.serial_out_queue.append(self.convert_to_json({'x': None}))
        self.serial_out_queue.append(self.convert_to_json({'2': None}))
        self.serial_out_queue.append(self.convert_to_json({'y': None}))
        self.serial_out_queue.append(self.convert_to_json({'3': None}))
        self.serial_out_queue.append(self.convert_to_json({'z': None}))
        self.serial_out_queue.append(self.convert_to_json({'4': None}))
        self.serial_out_queue.append(self.convert_to_json({'a': None}))
        self.serial_out_queue.append(self.convert_to_json({'p1': None}))

    def on_light_change_requested_slot(self, brightness):
        if brightness > 0:
            brightness = self.constrain_to_range(brightness, 0, 1000)
            self.serial_out_queue.append(self.convert_to_json({'gc': 'M3 S' + str(brightness)}))
        else:
            self.serial_out_queue.append(self.convert_to_json({'gc': 'M3 S0'}))

    def on_z_homing_requested_slot(self, precision):
        if precision == ROUGH:
            self.serial_out_queue.append(self.convert_to_json({'zsv':500}))
            self.msleep(30)
            self.serial_out_queue.append(self.convert_to_json({'zsn':0}))
            self.msleep(30)  # Required for config changes
            self.serial_out_queue.append(self.convert_to_json({'zsx':1}))
            self.msleep(30)  # Required for config changes
            self.serial_out_queue.append(self.convert_to_json({'gc': 'G28.2 Z0'}))
        elif precision == FINE:
            self.serial_out_queue.append(self.convert_to_json({'zsv':100}))
            self.msleep(30)
            self.serial_out_queue.append(self.convert_to_json({'zsn':1}))
            self.msleep(30)  # Required for config changes
            self.serial_out_queue.append(self.convert_to_json({'zsx':0}))
            self.msleep(30)  # Required for config changes
            self.serial_out_queue.append(self.convert_to_json({'gc': 'G28.2 Z0'}))

    def on_x_y_homing_requested_slot(self):
        self.serial_out_queue.append(self.convert_to_json({'gc': 'G28.2 X0 Y0'}))

    def on_x_y_precision_homing_requested_slot(self):
        self.serial_out_queue.append(self.convert_to_json({'gc': 'G28.2 X0'}))
        self.on_relative_position_change_requested_slot(0, -10, 0, 0)
        self.serial_out_queue.append(self.convert_to_json({'gc': 'G28.2 Y0'}))

    def on_a_homing_requested_slot(self):
        self.serial_out_queue.append(self.convert_to_json({'gc': 'G28.2 A0'}))

    def on_absolute_position_change_requested_slot(self, x, y, z, a):
        out_string = 'G90 G0'

        if x != IGNORE_VALUE:
            out_string += ' X' + str(x)

        if y != IGNORE_VALUE:
            out_string += ' Y' + str(y)

        if z != IGNORE_VALUE:
            out_string += ' Z' + str(z)

        if a != IGNORE_VALUE:
            out_string += ' A' + str(a)

        self.serial_out_queue.append(self.convert_to_json({'gc': out_string}))

    def on_absolute_position_with_feedrate_change_requested_slot(self, x, y, z, a, f):
        out_string = 'G90 G1'

        if x != IGNORE_VALUE:
            out_string += ' X' + str(x)

        if y != IGNORE_VALUE:
            out_string += ' Y' + str(y)

        if z != IGNORE_VALUE:
            out_string += ' Z' + str(z)

        if a != IGNORE_VALUE:
            out_string += ' A' + str(a)

        if f != IGNORE_VALUE:
            out_string += ' F' + str(f)

        self.serial_out_queue.append(self.convert_to_json({'gc': out_string}))

    def on_relative_position_change_requested_slot(self, x, y, z, a):
        out_string = 'G91 G0'

        if x != 0:
            out_string += ' X' + str(x)

        if y != 0:
            out_string += ' Y' + str(y)

        if z != 0:
            out_string += ' Z' + str(z)

        if a != 0:
            out_string += ' A' + str(a)

        self.serial_out_queue.append(self.convert_to_json({'gc': out_string}))

    def on_tinyg_reset_requested_slot(self):
        self.serial_out_queue.append("^x\n")

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
    tinyg_move_absolute_with_feedrate_signal = QtCore.pyqtSignal(float, float, float, float, float)
    tinyg_move_relative_signal = QtCore.pyqtSignal(float, float, float, float)
    tinyg_z_home_signal = QtCore.pyqtSignal(int)
    tinyg_x_y_home_signal = QtCore.pyqtSignal()
    tinyg_x_y_precision_home_signal = QtCore.pyqtSignal()
    tinyg_a_home_signal = QtCore.pyqtSignal()
    tinyg_light_change_signal = QtCore.pyqtSignal(int)
    tinyg_dump_settings_signal = QtCore.pyqtSignal()
    tinyg_motor_state_change_signal = QtCore.pyqtSignal(int)
    tinyg_location_update_signal = QtCore.pyqtSignal(float, float, float, float)

    controller_command_complete_signal = QtCore.pyqtSignal()
    controller_init_complete_signal = QtCore.pyqtSignal()

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

        # ########## Class Variables ##########
        self.serial_handler = SerialHandler()

        self.tinyg_x_location = 0
        self.tinyg_y_location = 0
        self.tinyg_z_location = 0
        self.tinyg_a_location = 0

        self.tinyg_machine_state = INITIALIZING_STATE

        self.tinyg_command_processed = False

        self.command_queue = []

        self.timing_start_time = 0
        self.timing_stop_time = 0

        # ########## Make signal/slot connections ##########
        self.connect_signals_to_slots()

        # ########## Start thread ##########
        self.start()

    def connect_signals_to_slots(self):
        #PickAndPlateController to SerialHandler
        self.tinyg_light_change_signal.connect(self.serial_handler.on_light_change_requested_slot)
        self.tinyg_motor_state_change_signal.connect(self.serial_handler.on_motor_state_change_requested_slot)
        self.tinyg_z_home_signal.connect(self.serial_handler.on_z_homing_requested_slot)
        self.tinyg_x_y_home_signal.connect(self.serial_handler.on_x_y_homing_requested_slot)
        self.tinyg_x_y_precision_home_signal.connect(self.serial_handler.on_x_y_precision_homing_requested_slot)
        self.tinyg_a_home_signal.connect(self.serial_handler.on_a_homing_requested_slot)
        self.tinyg_move_absolute_signal.connect(self.serial_handler.on_absolute_position_change_requested_slot)
        self.tinyg_move_absolute_with_feedrate_signal.connect(
            self.serial_handler.on_absolute_position_with_feedrate_change_requested_slot)
        self.tinyg_move_relative_signal.connect(self.serial_handler.on_relative_position_change_requested_slot)
        self.tinyg_dump_settings_signal.connect(self.serial_handler.on_dump_tinyg_settings_dump_slot)

        #SerialHandler to PickAndPlateController
        self.serial_handler.tinyg_current_location_signal.connect(self.on_tinyg_location_changed_slot)
        self.serial_handler.tinyg_current_machine_state_signal.connect(self.on_tinyg_machine_state_changed_slot)
        self.serial_handler.tinyg_command_processed_signal.connect(self.on_tinyg_command_processed_successfully_slot)

    def run(self):
        self.logger.debug("PickAndPlate Controller Thread Starting...")

        self.msleep(350)
        while not self.tinyg_machine_state == INITIALIZING_STATE:
            self.msleep(250)

        self.command_queue.append({'Command':'System Initialization'})
        self.msleep(1500)

        while self.not_abort_flag:

            if self.command_queue:
                current_command = self.command_queue[0]
                # self.logger.debug("Command Queue: " + str(self.command_queue))
                del self.command_queue[0]

                if current_command['Command'] == 'System Initialization':
                    self.initial_system_homing_request()
                    self.light_change_requested(0)
                if current_command['Command'] == 'Initial Homing':
                    self.initial_system_homing_request()
                elif current_command['Command'] == 'Full Homing':
                    self.full_system_homing_request()
                elif current_command['Command'] == 'Z Move ABS':
                    self.z_axis_move_request(current_command['Z'])
                elif current_command['Command'] == 'Z Move ABS w/Feedrate':
                    self.z_axis_move_with_feedrate_request(current_command['Z'], current_command['F'])
                elif current_command['Command'] == 'Z Move REL':
                    self.z_axis_move_relative_request(current_command['Z'])
                elif current_command['Command'] == 'Z Home':
                    self.z_home_request(current_command['Type'])
                elif current_command['Command'] == 'X/Y Move ABS':
                    self.x_y_move_request(current_command['X'], current_command['Y'])
                elif current_command['Command'] == 'X/Y Move ABS w/Feedrate':
                    self.x_y_move_with_feedrate_request(current_command['X'], current_command['Y'],
                                                        current_command['F'])
                elif current_command['Command'] == 'X/Y Move REL':
                    self.x_y_move_relative_request(current_command['X'], current_command['Y'])
                elif current_command['Command'] == 'X/Y Home':
                    self.x_y_home_request()
                elif current_command['Command'] == 'X/Y Precision Home':
                    self.x_y_axis_precision_home_request()
                elif current_command['Command'] == 'A Move REL':
                    self.a_axis_move_request(current_command['uL'])
                elif current_command['Command'] == 'A Home':
                    self.a_axis_home_request()
                elif current_command['Command'] == 'Light Change':
                    self.light_change_requested(current_command['Brightness'])
                elif current_command['Command'] == 'Motor State Change':
                    self.motor_state_change_requested(current_command['State'])
            else:
                self.msleep(50)

        self.serial_handler.not_abort_flag = False
        self.serial_handler.wait()
        self.logger.debug("PickAndPlate Controller Thread Exiting...")

    ########## Methods for general commands / light control ##########
    def on_light_change_request_signal_slot(self, brightness):
        self.command_queue.append({'Command':'Light Change', 'Brightness':brightness})

    def light_change_requested(self, brightness):
        self.tinyg_command_processed = False
        self.tinyg_light_change_signal.emit(brightness)

        while not self.tinyg_command_processed:
            self.msleep(50)

        self.controller_command_complete_signal.emit()

    def on_motor_state_change_request_signal_slot(self, state):
        self.command_queue.append({'Command':'Motor State Change', 'State':state})

    def motor_state_change_requested(self, state):
        self.tinyg_command_processed = False
        self.tinyg_motor_state_change_signal.emit(state)

        while not self.tinyg_command_processed:
            self.msleep(50)

        self.controller_command_complete_signal.emit()

    ########## Methods for all axes ##########
    def initial_system_homing_request(self):
        #self.tinyg_dump_settings_signal.emit()
        self.light_change_requested(1000)
        self.z_home_request(ROUGH)
        self.x_y_move_relative_request(-5, -10)
        self.a_axis_home_request()
        self.a_axis_move_request(100)
        self.x_y_home_request()

    def on_initial_system_homing_requested_slot(self):
        self.command_queue.append({'Command':'Initial Homing'})

    def full_system_homing_request(self):
        precision_z_x_center = self.settings.value("system/system_calibration/precision_z_x_center").toFloat()[0]
        precision_z_y_center = self.settings.value("system/system_calibration/precision_z_y_center").toFloat()[0]

        self.initial_system_homing_request()

        self.light_change_requested(1000)
        self.x_y_move_request(precision_z_x_center, precision_z_y_center)
        self.z_axis_move_request(-25)
        self.z_home_request(FINE)
        self.x_y_axis_precision_home_request()
        self.msleep(3500)

        while (self.tinyg_x_location != 0) or (self.tinyg_y_location != 0):
            self.x_y_move_request(0, 0)

        self.z_axis_move_request(0)

        self.controller_init_complete_signal.emit()

    def on_full_system_homing_requested_slot(self):
        self.command_queue.append({'Command':'Full Homing'})


    ########## Z Axis Methods ##########
    def on_z_axis_move_requested_slot(self, z):
        self.timing_start_time = time.time()
        self.command_queue.append({'Command':'Z Move ABS', 'Z':z})

    def on_z_axis_move_with_feedrate_requested_slot(self, z, f):
        self.command_queue.append({'Command':'Z Move ABS w/Feedrate', 'Z':z, 'F':f})

    def on_z_axis_move_relative_requested_slot(self, z):
        self.timing_start_time = time.time()
        self.command_queue.append({'Command':'Z Move REL', 'Z':z})

    def z_axis_move_request(self, z):
        self.tinyg_move_absolute_signal.emit(IGNORE_VALUE, IGNORE_VALUE, z, IGNORE_VALUE)

        self.msleep(350)
        while self.tinyg_machine_state == MOTION_RUNNING_STATE:
            self.msleep(50)

        self.controller_command_complete_signal.emit()

    def z_axis_move_with_feedrate_request(self, z, f):
        self.tinyg_move_absolute_with_feedrate_signal.emit(IGNORE_VALUE, IGNORE_VALUE, z, IGNORE_VALUE, f)

        self.msleep(350)
        while self.tinyg_machine_state == MOTION_RUNNING_STATE:
            self.msleep(50)

        self.controller_command_complete_signal.emit()

    def z_axis_move_relative_request(self, z):
        self.tinyg_move_relative_signal.emit(0, 0, z, 0)

        self.msleep(350)
        while self.tinyg_machine_state == MOTION_RUNNING_STATE:
            self.msleep(50)

        #self.timing_stop_time = time.time()
        #self.logger.info("Z move completed in " + str(self.timing_stop_time-self.timing_start_time) + " seconds.")
        self.controller_command_complete_signal.emit()

    def on_z_axis_homing_requested_slot(self, homing_type):
        self.command_queue.append({'Command':'Z Home', 'Type':homing_type})

    def z_home_request(self, homing_type):
        self.tinyg_z_home_signal.emit(homing_type)
        self.tinyg_machine_state = HOMING_STATE

        self.msleep(350)
        while self.tinyg_machine_state == HOMING_STATE:
            self.msleep(50)

        self.msleep(1000)

    ########## X Y Axis Methods ##########
    def on_x_y_axis_move_requested_slot(self, x, y):
        #self.timing_start_time = time.time()

        #self.logger.info("Received X_Y at " + str(time.time()) + " seconds.")
        self.command_queue.append({'Command':'X/Y Move ABS', 'X':x, 'Y':y})

    def on_x_y_axis_move_with_feedrate_requested_slot(self, x, y, f):
        #self.timing_start_time = time.time()

        #self.logger.info("Received X_Y at " + str(time.time()) + " seconds.")
        self.command_queue.append({'Command':'X/Y Move ABS w/Feedrate', 'X':x, 'Y':y, 'F':f})

    def on_x_y_axis_move_relative_requested_slot(self, x, y):
        self.timing_start_time = time.time()
        self.command_queue.append({'Command':'X/Y Move REL', 'X':x, 'Y':y})

    def x_y_move_request(self, x ,y):
        self.tinyg_move_absolute_signal.emit(x, y,
                                             IGNORE_VALUE, IGNORE_VALUE)

        self.msleep(350)
        while self.tinyg_machine_state == MOTION_RUNNING_STATE:
            self.msleep(50)

        self.controller_command_complete_signal.emit()

    def x_y_move_with_feedrate_request(self, x ,y, f):
        self.tinyg_move_absolute_with_feedrate_signal.emit(x, y,
                                             IGNORE_VALUE, IGNORE_VALUE, f)

        self.msleep(350)
        while self.tinyg_machine_state == MOTION_RUNNING_STATE:
            self.msleep(50)

        self.controller_command_complete_signal.emit()

    def x_y_move_relative_request(self, x, y):
        self.tinyg_move_relative_signal.emit(x, y, 0, 0)

        self.msleep(350)
        while self.tinyg_machine_state == MOTION_RUNNING_STATE:
            self.msleep(50)

        self.controller_command_complete_signal.emit()


    def on_x_y_axes_homing_requested_slot(self):
        self.timing_start_time = time.time()
        self.command_queue.append({'Command':'X/Y Home'})

    def x_y_home_request(self):
        self.tinyg_x_y_home_signal.emit()
        self.tinyg_machine_state = HOMING_STATE

        self.msleep(350)
        while self.tinyg_machine_state == HOMING_STATE:
            self.msleep(50)

        self.msleep(1000)

    def on_x_y_axis_precision_home_requested_slot(self):
        self.timing_start_time = time.time()
        self.command_queue.append({'Command':'X/Y Precision Home'})

    def x_y_axis_precision_home_request(self):
        self.tinyg_x_y_precision_home_signal.emit()
        self.tinyg_machine_state = HOMING_STATE

        self.msleep(350)
        while self.tinyg_machine_state == HOMING_STATE:
            self.msleep(50)

        self.msleep(1000)

    ########## A Axis Methods ##########
    def on_a_axis_move_requested_slot(self, microliters):
        self.timing_start_time = time.time()
        self.command_queue.append({'Command':'A Move REL', 'uL':microliters})

    def a_axis_move_request(self, micro_liters):
        move_amount = (MM_PER_UL * micro_liters)

        self.tinyg_move_relative_signal.emit(0, 0, 0, move_amount)

        self.msleep(350)
        while self.tinyg_machine_state == MOTION_RUNNING_STATE:
            self.msleep(50)

        #self.timing_stop_time = time.time()
        #self.logger.info("A move completed in " + str(self.timing_stop_time-self.timing_start_time) + " seconds.")
        self.controller_command_complete_signal.emit()


    def on_a_axis_home_requested_slot(self):
        self.timing_start_time = time.time()
        self.command_queue.append({'Command':'A Home'})

    def a_axis_home_request(self):
        self.tinyg_a_home_signal.emit()
        self.tinyg_machine_state = HOMING_STATE

        self.msleep(350)
        while self.tinyg_machine_state == HOMING_STATE:
            self.msleep(50)

        self.msleep(1000)

    ########## Cross thread variable synchronization ##########
    def on_tinyg_location_changed_slot(self, x, y, z, a):
        self.tinyg_x_location = x
        self.tinyg_y_location = y
        self.tinyg_z_location = z
        self.tinyg_a_location = a

        self.broadcast_location_slot()

    def on_tinyg_machine_state_changed_slot(self, state):
        self.tinyg_machine_state = state

    def on_tinyg_command_processed_successfully_slot(self):
        self.tinyg_command_processed = True

    def broadcast_location_slot(self):
        self.tinyg_location_update_signal.emit(self.tinyg_x_location, self.tinyg_y_location, self.tinyg_z_location,
            (self.tinyg_a_location/MM_PER_UL))

    ########## Program End Kill Thread Method ##########
    def on_kill_threads_slot(self):
        self.not_abort_flag = False

