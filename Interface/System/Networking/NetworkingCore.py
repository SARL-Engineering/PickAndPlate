"""
    This file contains the Networking sub-class as part of the System Class
    This class handles logging of networking information and giving users information about current network status
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
import netifaces
import commands
import socket

# Custom imports

#####################################
# Global Variables
#####################################
eth_renew_ip_command = "sudo dhclient -r && sudo dhclient eth0"

internet_test_ip_address = ("8.8.8.8", 53)  # This is google's primary DNS server. Should almost never go down.

#####################################
# DetectionCalibration Class Definition
#####################################
class Networking(QtCore.QThread):
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
        self.ip_address_label = self.main_window.networking_ip_address_label
        self.netmask_label = self.main_window.networking_netmask_label
        self.gateway_label = self.main_window.networking_gateway_label
        self.internet_label = self.main_window.networking_internet_label

        self.log_text_browser = self.main_window.network_log_text_browser

        # ########## Thread flags ##########
        self.not_abort_flag = True

        # ########## Class variables ##########
        self.timeout_counter = 0

        # ########## Make signal/slot connections ##########
        self.connect_signals_to_slots()

        # ########## Start timer ##########
        self.start()

    def connect_signals_to_slots(self):
        pass

    def run(self):
        self.logger.debug("System Networking Thread Starting..")

        while self.not_abort_flag:
            if self.timeout_counter >= (20*1000):
                self.network_update()
                self.timeout_counter = 0

            self.timeout_counter += 200
            self.msleep(200)

        self.logger.debug("System Networking Thread Exiting...")

    def network_update(self):
        try:
            eth0_info = netifaces.ifaddresses("eth0")[netifaces.AF_INET][0]
            ip_address = eth0_info['addr']
            netmask = eth0_info['netmask']
            gateway = netifaces.gateways()['default'][netifaces.AF_INET][0]

            self.ip_address_label.setText(ip_address)
            self.netmask_label.setText(netmask)
            self.gateway_label.setText(gateway)
            self.internet_label.setText(self.internet_connection_available())

        except Exception:
            self.logger.warning("No connection to a network. Attempting reconnection.")

            self.ip_address_label.setText("XXX.XXX.XXX.XXX")
            self.netmask_label.setText("XXX.XXX.XXX.XXX")
            self.gateway_label.setText("XXX.XXX.XXX.XXX")
            self.internet_label.setText("No")

            commands.getoutput(eth_renew_ip_command)

    @staticmethod
    def internet_connection_available():
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(1)
            test_socket.connect(internet_test_ip_address)
            return "Yes"

        except Exception:
            return "No"

    def on_kill_threads_slot(self):
        self.not_abort_flag = False