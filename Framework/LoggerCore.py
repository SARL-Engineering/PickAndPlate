"""
    This file contains the PickAndPlateLogging sub-class as part of the Framework Class
    This class handles initializing the python logger and performing cleanup on log files
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
from os import makedirs
from os.path import expanduser, exists
import datetime
import time

# Custom imports

#####################################
# Global Variables
#####################################
current_date = str(datetime.date.today())
application_hidden_path_root = expanduser("~") + "/.PickAndPlate"  # Change /.pnp to whatever the short program name is
application_logging_path = application_hidden_path_root + "/logs"
application_log_full_path = application_logging_path + "/" + current_date + ".txt"


#####################################
# PickAndPlateLogger Definition
#####################################
class PickAndPlateLogger(QtCore.QObject):
    def __init__(self, console_output=True):
        QtCore.QObject.__init__(self)

        # ########## Local class variables ##########
        self.console_output = console_output

        # ########## Get the Pick And Plate instance of the logger ##########
        self.make_logging_paths()
        self.logger = logging.getLogger("PickAndPlate")
        self.logger_file = open(application_log_full_path, 'a')

        # ########## Set up logger with desired settings ##########
        self.setup_logger()

        # ########## Place divider in log file to see new program launch ##########
        self.add_startup_log_buffer_text()

    @staticmethod
    def make_logging_paths():
        if not exists(application_logging_path):
            makedirs(application_logging_path)

    def setup_logger(self):
        self.logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(fmt='%(levelname)s : %(asctime)s :  %(message)s', datefmt='%m/%d/%y %H:%M:%S')

        self.make_logging_paths()

        file_handler = logging.FileHandler(filename=application_log_full_path)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)

        if self.console_output:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.DEBUG)
            self.logger.addHandler(console_handler)

    def add_startup_log_buffer_text(self):
        self.logger_file.write("\n########## New Instance of Application Started ##########\n\n")
        self.logger_file.close()

# TODO: Add in logging cleanup so we don't run out of space over time