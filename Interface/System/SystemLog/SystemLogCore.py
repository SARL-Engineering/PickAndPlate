"""
    This file contains the System Log sub-class as part of the Interface Class
    This class handles the system log tab and any needed connections
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
from os.path import exists, getsize

# Custom imports
from Framework import LoggerCore

#####################################
# Global Variables
#####################################


#####################################
# SystemLog Definition
#####################################
class SystemLog(QtCore.QThread):

    text_ready_signal = QtCore.pyqtSignal(str)

    def __init__(self, main_window, master):
        QtCore.QThread.__init__(self)

        # ########## Reference to system logger ##########
        self.logger = logging.getLogger("PickAndPlate")
        self.log_path = LoggerCore.application_log_full_path
        self.log_file_reader = open(self.log_path, 'r')

        # ########## Reference to top level window ##########
        self.main_window = main_window
        self.master = master

        # ########## References to gui elements ##########
        self.log_text_browser = self.main_window.system_log_text_browser
        self.log_text_browser_scrollbar = self.main_window.system_log_text_browser.verticalScrollBar()
        self.info_checkbox = self.main_window.system_log_info_checkbox
        self.warning_checkbox = self.main_window.system_log_warning_checkbox
        self.error_checkbox = self.main_window.system_log_error_checkbox
        self.debug_checkbox = self.main_window.system_log_debug_checkbox

        # ########## Class variables ##########
        self.prev_checked_info = self.info_checkbox.isChecked()
        self.prev_checked_warning = self.warning_checkbox.isChecked()
        self.prev_checked_error = self.error_checkbox.isChecked()
        self.prev_checked_debug = self.debug_checkbox.isChecked()
        self.prev_log_file_size = 0

        # ########## Thread flags ##########
        self.not_abort_flag = True

        # ########## Init functions ##########
        self.connect_signals_to_slots()
        self.start()

    def connect_signals_to_slots(self):
        self.text_ready_signal.connect(self.log_text_browser.setText)

    def run(self):
        self.logger.debug("System Log Thread Starting...")
        while self.not_abort_flag:
            while self.should_update_text():
                self.send_logfile_text_to_browser()
            self.msleep(200)

        self.logger.debug("System Log Thread Exiting...")

    def should_update_text(self):
        return_value = False

        if self.info_checkbox.isChecked() != self.prev_checked_info:
            return_value = True
            self.prev_checked_info = self.info_checkbox.isChecked()

        if self.warning_checkbox.isChecked() != self.prev_checked_warning:
            return_value = True
            self.prev_checked_warning = self.warning_checkbox.isChecked()

        if self.error_checkbox.isChecked() != self.prev_checked_error:
            return_value = True
            self.prev_checked_error = self.error_checkbox.isChecked()

        if self.debug_checkbox.isChecked() != self.prev_checked_debug:
            return_value = True
            self.prev_checked_debug = self.debug_checkbox.isChecked()

        if self.logfile_changed():
            return_value = True

        return return_value

    def logfile_changed(self):
        if not exists(self.log_path):
            return False
        elif getsize(self.log_path) != self.prev_log_file_size:
            self.prev_log_file_size = getsize(self.log_path)
            return True
        else:
            return False

    def send_logfile_text_to_browser(self):
        log_browser_string = ""

        self.log_file_reader.seek(0)
        log_lines = self.log_file_reader.readlines()

        for line in reversed(log_lines):
            log_line_type = line.split(" ")[0]

            if log_line_type == "INFO":
                if self.info_checkbox.isChecked():
                    log_browser_string += line
            elif log_line_type == "WARNING":
                if self.warning_checkbox.isChecked():
                    log_browser_string += line
            elif log_line_type == "ERROR":
                if self.error_checkbox.isChecked():
                    log_browser_string += line
            elif log_line_type == "DEBUG":
                if self.debug_checkbox.isChecked():
                    log_browser_string += line
            else:
                log_browser_string += line

        self.text_ready_signal.emit(log_browser_string)

    def on_kill_threads_slot(self):
        self.not_abort_flag = False

