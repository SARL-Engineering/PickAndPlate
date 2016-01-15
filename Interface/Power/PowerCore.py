"""
    This file contains the Power sub-class as part of the Interface Class
    This class handles the power tab and and its connections
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
import time
import subprocess

# Custom imports

#####################################
# Global Variables
#####################################
reboot_command = "sudo reboot"
shutdown_command = "sudo poweroff"


TERMINATE_DELAY = 8  # Delay in seconds before all threads that haven't ended are terminated

#####################################
# Power Class Definition
#####################################
class Power(QtCore.QObject):

    kill_threads_signal = QtCore.pyqtSignal()

    def __init__(self, main_window, master):
        QtCore.QObject.__init__(self)

        # ########## References to highest level window ##########
        self.main_window = main_window
        self.master = master

        # ########## References to gui elements ##########
        self.reboot_button = self.main_window.reboot_button
        self.power_off_button = self.main_window.power_off_button
        self.exit_to_desktop_button = self.main_window.exit_to_desktop_button

        # ########## References to all QThreads for killing on exit ##########
        self.threads = []
        self.threads.append(self.master.system_tab.networking_tab)
        self.threads.append(self.master.system_tab.system_log_tab)
        self.threads.append(self.main_window.video)
        self.threads.append(self.main_window.controller)
        self.threads.append(self.main_window.cycle_handler)
        self.threads.append(self.master.status)
        self.threads.append(self.master.tables_tab)

        # ########## Setup signal and slot connections ##########
        self.connect_signals_to_slots()

    def connect_signals_to_slots(self):
        self.reboot_button.clicked.connect(self.on_reboot_button_pressed_slot)
        self.power_off_button.clicked.connect(self.on_power_off_button_pressed_slot)
        self.exit_to_desktop_button.clicked.connect(self.on_exit_to_desktop_pressed_slot)
        self.connect_kill_threads_signals()

    def connect_kill_threads_signals(self):
        for thread in self.threads:
            self.kill_threads_signal.connect(thread.on_kill_threads_slot)

    def kill_all_threads(self):
        self.kill_threads_signal.emit()

        all_threads_killed = False
        num_threads_running = 0
        terminate_has_run = False

        start_time = time.time()
        while not all_threads_killed:
            for thread in self.threads:
                if thread.isRunning():
                    num_threads_running += 1

            if num_threads_running > 0:
                num_threads_running = 0

                if not terminate_has_run:
                    if (time.time()-start_time) > TERMINATE_DELAY:
                        for thread in self.threads:
                            if thread.isRunning():
                                print "Terminated"
                                thread.terminate()
                        terminate_has_run = True
                        all_threads_killed = True
            else:
                all_threads_killed = True

    def on_reboot_button_pressed_slot(self):
        self.kill_all_threads()
        subprocess.Popen(reboot_command.split(), stdout=subprocess.PIPE)
        self.main_window.close()

    def on_power_off_button_pressed_slot(self):
        self.kill_all_threads()
        subprocess.Popen(shutdown_command.split(), stdout=subprocess.PIPE)
        self.main_window.close()

    def on_exit_to_desktop_pressed_slot(self):
        self.kill_all_threads()
        self.main_window.close()
