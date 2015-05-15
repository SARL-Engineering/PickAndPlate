"""
    This file contains the Tables Class
    This class handles the tables tab on the main tab widget and it's display of run data
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
# PickAndPlateLogger Definition
#####################################
class Tables(QtCore.QThread):
    def __init__(self, main_window, master):
        QtCore.QThread.__init__(self)

        # ########## Reference to system logger ##########
        self.logger = logging.getLogger("PickAndPlate")

        # ########## Reference to highest level window and master class ##########
        self.main_window = main_window
        self.master = master

        # ########## Create Instance of settings ##########
        self.settings = QtCore.QSettings()

        # ########## References to gui elements ##########
        self.table1_combobox = self.main_window.tables_table1_combobox
        self.table1_widget = self.main_window.tables_table1_widget

        self.table2_combobox = self.main_window.tables_table2_combobox
        self.table2_widget = self.main_window.tables_table2_widget

        # ########## Thread flags ##########
        self.not_abort_flag = True

        # ########## Init functions ##########
        self.connect_signals_to_slots()
        self.start()

    def connect_signals_to_slots(self):
        pass

    def run(self):
        self.logger.debug("Tables Thread Starting...")
        while self.not_abort_flag:
            self.msleep(200)

        self.logger.debug("Tables Thread Exiting...")

    def on_kill_threads_slot(self):
        self.not_abort_flag = False