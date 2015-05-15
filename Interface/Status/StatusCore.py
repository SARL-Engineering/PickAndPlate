"""
    This file contains the StatusCore sub-class as part of the Interface Class
    This class handles updating the bottom status labels and date / time / ID for the application
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
import datetime

# Custom imports

#####################################
# Global Variables
#####################################
UTC_offsets = [
    (-12, 0), (-11, 0), (-10, 0), (-9, -30), (-9, 0), (-8, 0), (-7, 0), (-6, 0),
    (-5, 0), (-4, -30), (-4, 0), (-3, -30), (-3, 0), (-2, 0), (-1, 0), (0, 0),
    (1, 0), (2, 0), (3, 0), (3, 30), (4, 0), (4, 30), (5, 0), (5, 30), (5, 45),
    (6, 0), (6, 30), (7, 0), (8, 0), (8, 45), (9, 0), (9, 30), (10, 0),
    (10, 30), (11, 0), (11, 30), (12, 0), (12, 45), (13, 0), (14, 0)
]

#####################################
# Status Class Definition
#####################################
class Status(QtCore.QThread):

    datetime_id_changed_signal = QtCore.pyqtSignal(str)

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
        self.current_task_lb = self.main_window.status_current_task_label
        self.status_lb = self.main_window.status_task_status_label
        self.status_pb = self.main_window.status_task_progress_bar

        self.main_tab_widget = self.master.main_tab_widget

        # ########## Thread flags ##########
        self.thread_sleep_ms = 200
        self.not_abort_flag = True

        # ########## Class Variables ##########
        self.previous_date_id_string = None

        self.date_id_label_update_timeout = 10000  # Ten second update interval
        self.datetime_id_update_counter = self.date_id_label_update_timeout

        # ########## Make signal/slot connections ##########
        self.connect_signals_to_slots()

        # ########## Start timer ##########
        self.start()

    def connect_signals_to_slots(self):
        self.datetime_id_changed_signal.connect(self.update_datetime_id_label)

    def run(self):
        self.logger.debug("Status Thread Starting..")

        while self.not_abort_flag:

            if self.datetime_id_update_counter >= self.date_id_label_update_timeout:
                self.get_new_datetime_id_string()
                self.datetime_id_update_counter = 0

            self.datetime_id_update_counter += self.thread_sleep_ms
            self.msleep(self.thread_sleep_ms)

        self.logger.debug("Status Thread Exiting...")

    def get_new_datetime_id_string(self):
        unit_id = self.settings.value("system/system_settings/unit_id").toInt()[0]
        timezone_offsets = UTC_offsets[self.settings.value("system/system_settings/timezone_index").toInt()[0]]

        now = datetime.datetime.now()
        hour_string = str((now.hour+timezone_offsets[0]) % 12).zfill(2)

        if (((now.hour+timezone_offsets[0]) % 24) == 12) or (((now.hour+timezone_offsets[0]) % 24) == 0):
                hour_string = str(12)

        if ((now.hour+timezone_offsets[0]) % 24) >= 12:
            am_pm = "PM"
        else:
            am_pm = "AM"

        time_id_str = "%s:%s " % (hour_string,
                                  str((now.minute+timezone_offsets[1]) % 60).zfill(2)) + \
                      am_pm + " %s/%s/%s | #" % (str(now.month).zfill(2), str(now.day).zfill(2), str(now.year)[2:]) +\
                      str(unit_id).zfill(2)

        if time_id_str != self.previous_date_id_string:
            self.datetime_id_changed_signal.emit(time_id_str)
            self.previous_date_id_string = time_id_str

    def update_datetime_id_label(self, string):
        self.main_tab_widget.setTabText(4, string)

    def on_kill_threads_slot(self):
        self.not_abort_flag = False