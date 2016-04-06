"""
    This file contains the PickAndPlateVideo sub-class as part of the Framework Class
    This class handles initializing and interfacing with the
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
import cv2
import numpy
import qimage2ndarray
import subprocess
from math import sqrt, isnan, pow
from datetime import datetime

# Custom imports

#####################################
# Global Variables
#####################################
set_video_format_command = "v4l2-ctl --set-fmt-video="  # Sets the camera to mjepg mode
set_focus_mode_command = "v4l2-ctl -d /dev/video0 -c focus_auto=0"
set_focus_value_command = "v4l2-ctl -d /dev/video0 -c focus_absolute="
set_exposure_mode_command = "v4l2-ctl -d /dev/video0 -c exposure_auto=1"
set_exposure_value_command = "v4l2-ctl -d /dev/video0 -c exposure_absolute="

SYSTEM_CAMERA_FRAME_RATE = 5

CV_CAP_PROP_FRAME_WIDTH = 3
CV_CAP_PROP_FRAME_HEIGHT = 4
CV_CAP_PROP_FPS = 5
CV_CAP_PROP_FOURCC = 6

RED = (255, 0, 0)
GREEN = (0, 255, 0)

#####################################
# Miscellaneous Notes
#####################################
# The beaglebone black is very very picky about what USB hubs it's okay with working with. Also, whether or not they
# are self powered makes a difference as well. The hub at the link below I've tested to be working with external power.
# Belkin AC Powered Ultra-Slim Series 4-Port USB 2.0 Hub (F4U040v)
# http://www.amazon.com/gp/product/B005A0B3FG?psc=1&redirect=true&ref_=oh_aui_search_detailpage

#####################################
# FrameGrabber Class
#####################################
class FrameGrabber(QtCore.QThread):
    def __init__(self, x, y):
        QtCore.QThread.__init__(self)

        self.video_camera = cv2.VideoCapture(0)

        self.video_camera.set(CV_CAP_PROP_FRAME_WIDTH, x)
        self.video_camera.set(CV_CAP_PROP_FRAME_HEIGHT, y)
        self.video_camera.set(CV_CAP_PROP_FPS, SYSTEM_CAMERA_FRAME_RATE)

        self.not_abort = True
        self.process_continuous = False
        self.process_single = False

    def run(self):
        while self.not_abort:
            if self.process_continuous:
                self.video_camera.grab()
                self.msleep(15)
            elif self.process_single:
                self.video_camera.grab()
                self.process_single = False
            else:
                self.msleep(200)

    def set_process_continuous(self):
        self.process_single = False
        self.process_continuous = True

    def set_process_single(self):
        self.process_continuous = False
        self.process_single = True

    def stop_processing(self):
        self.process_single = False
        self.process_continuous = False



#####################################
# PickAndPlateVideo Definition
#####################################
class PickAndPlateVideo(QtCore.QThread):

    DETECTION_CAL = "Detection Calibration"
    SYSTEM_CAL = "System Calibration"
    CYCLE_RUN = "Cycle Run"

    requested_image_ready_signal = QtCore.pyqtSignal()
    embryo_info_signal = QtCore.pyqtSignal(int, int, int)
    number_embryos_detected_signal = QtCore.pyqtSignal(int)

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

        self.reconnect_to_camera_flag = True
        self.camera_connected_flag = False

        self.setup_params_once = False
        self.wait_for_image_req = True

        # ########## Class Variables ##########
        self.frame_grabber = None

        self.video_camera = None
        self.dev_null_writer = open('/dev/null', 'w')

        self.raw_frame = numpy.array([])
        self.rgb_frame = numpy.array([])
        self.greyscale_frame = numpy.array([])

        self.cropped_only_raw = None
        self.settings_and_cal_qimage = None
        self.cycle_monitor_qimage = None
        self.last_pick_qimage = None
        self.current_pick_qimage = None

        self.video_being_used = False
        self.video_output_widget_name = None
        self.video_output_type = None
        self.detection_profile_name = None

        self.images_displayed = False
        self.count = 0

        self.current_params = cv2.SimpleBlobDetector_Params()
        self.keypoints = None
        self.valid_embryos = None
        self.pickable_embryos = None

        self.embryo_set_en = 0
        self.embryo_min_dist = 0
        self.embryo_min_size = 0
        self.embryo_max_size = 0

        self.min_thresh = 0
        self.x_res = 0
        self.y_res = 0
        self.x_center = 0
        self.y_center = 0
        self.crop_dim_half = 0
        self.usable_offset = 0

        self.take_image = False
        self.image_count = 0

        # ########## Make signal/slot connections ##########
        self.connect_signals_to_slots()

        # ########## Start timer ##########
        self.start()

    def connect_signals_to_slots(self):
        pass

    def run(self):
        self.logger.debug("PickAndPlate Video Thread Starting...")
        while self.not_abort_flag:
            if self.reconnect_to_camera_flag:
                self.reconnect_to_camera()
                self.msleep(500)
            elif self.camera_connected_flag:
                if self.video_being_used:
                    #self.frame_grabber.should_process_video = True
                    self.get_camera_frame()
                    self.show_needed_images()
                else:
                    self.frame_grabber.stop_processing()
                    #self.frame_grabber.should_process_video = False
                self.msleep(40)

        self.frame_grabber.not_abort = False
        self.frame_grabber.wait()
        self.logger.debug("PickAndPlate Video Thread Exiting...")

    def reconnect_to_camera(self):
        x_res = self.settings.value("system/system_settings/camera_res_width").toInt()[0]
        y_res = self.settings.value("system/system_settings/camera_res_height").toInt()[0]

        focus_value = self.settings.value("system/system_calibration/camera_focus").toInt()[0]
        exposure_value = self.settings.value("system/system_calibration/camera_exposure").toInt()[0]

        self.frame_grabber = FrameGrabber(x_res, y_res)

        self.video_camera = self.frame_grabber.video_camera

        if not self.video_camera.isOpened():
            self.camera_connected_flag = False
        else:
            self.frame_grabber.start()
            self.configure_v4l2_camera_settings_slot(focus_value, exposure_value)
            self.reconnect_to_camera_flag = False
            self.camera_connected_flag = True

    def configure_v4l2_camera_settings_slot(self, focus, exposure):
        x_res = self.settings.value("system/system_settings/camera_res_width").toInt()[0]
        y_res = self.settings.value("system/system_settings/camera_res_height").toInt()[0]

        #vid_fmt_string = set_video_format_command + "width=" + str(x_res) + ",height=" + str(y_res) + ",pixelformat=1"

        #self.logger.debug("Vid String:  " + vid_fmt_string)

        #subprocess.Popen(vid_fmt_string.split(), stdout=self.dev_null_writer, stderr=self.dev_null_writer)

        subprocess.Popen(set_focus_mode_command.split(), stdout=self.dev_null_writer, stderr=self.dev_null_writer)
        subprocess.Popen((set_focus_value_command + str(focus)).split(), stdout=self.dev_null_writer,
                         stderr=self.dev_null_writer)

        subprocess.Popen(set_exposure_mode_command.split(), stdout=self.dev_null_writer, stderr=self.dev_null_writer)
        subprocess.Popen((set_exposure_value_command + str(exposure)).split(), stdout=self.dev_null_writer,
                         stderr=self.dev_null_writer)

    def show_needed_images(self):
        if self.video_output_widget_name == self.DETECTION_CAL:
            self.frame_grabber.set_process_continuous()
            self.show_detection_calibration()
        elif self.video_output_widget_name == self.SYSTEM_CAL:
            self.frame_grabber.set_process_continuous()
            self.show_system_calibration()
        elif self.video_output_widget_name == self.CYCLE_RUN:
            self.frame_grabber.set_process_continuous()
            self.show_cycle_run()

    def show_detection_calibration(self):
        self.setup_blob_params()

        frame = numpy.array([])

        if self.video_output_type == "Original Video":
            cropped = self.crop_image(self.raw_frame)
            frame = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)

        elif self.video_output_type == "Greyscale":
            frame = cv2.cvtColor(self.crop_image(self.raw_frame), cv2.COLOR_BGR2GRAY)

        elif self.video_output_type == "Binary Threshold":
            frame = cv2.cvtColor(self.crop_image(self.raw_frame), cv2.COLOR_BGR2GRAY)
            return_val, frame = cv2.threshold(frame, self.min_thresh, 255, cv2.THRESH_BINARY)

        elif self.video_output_type == "Masked Threshold":
            frame = cv2.cvtColor(self.raw_frame, cv2.COLOR_RGB2GRAY)

            mask_frame = numpy.zeros((self.y_res, self.x_res), numpy.uint8)
            cv2.circle(mask_frame, (self.x_center, self.y_center), (self.crop_dim_half - self.usable_offset), 255, -1)

            frame = cv2.bitwise_and(frame, mask_frame)
            frame = self.crop_image(frame)

        elif self.video_output_type == "Detected Threshold":
            frame = cv2.cvtColor(self.raw_frame, cv2.COLOR_RGB2GRAY)

            mask_frame = numpy.zeros((self.y_res, self.x_res), numpy.uint8)
            cv2.circle(mask_frame, (self.x_center, self.y_center), (self.crop_dim_half - self.usable_offset), 255, -1)

            frame = cv2.bitwise_and(frame, mask_frame)

            frame = self.masked_detect_and_overlay(frame, frame, "GRAY")

            frame = self.crop_image(frame)
        elif self.video_output_type == "Original w/ Detected":
            frame = cv2.cvtColor(self.raw_frame, cv2.COLOR_RGB2GRAY)

            mask_frame = numpy.zeros((self.y_res, self.x_res), numpy.uint8)
            cv2.circle(mask_frame, (self.x_center, self.y_center), (self.crop_dim_half - self.usable_offset), 255, -1)

            frame = cv2.bitwise_and(frame, mask_frame)

            frame = self.masked_detect_and_overlay(frame, self.raw_frame, "BGR")

            frame = self.crop_image(frame)

        try:
            self.images_displayed = False
            resized = cv2.resize(frame, (250, 250))

            self.settings_and_cal_qimage = self.convert_to_qimage(resized)
            self.requested_image_ready_signal.emit()

            while not self.images_displayed:
                if (not self.not_abort_flag) or (not self.video_being_used):
                    break
                self.msleep(10)
        except:
            self.logger.debug("failed to convert")

    def show_system_calibration(self):
        x_center = self.settings.value("system/system_calibration/crop_x_center").toInt()[0]
        y_center = self.settings.value("system/system_calibration/crop_y_center").toInt()[0]
        crop_dim_half = (self.settings.value("system/system_calibration/crop_dimension").toInt()[0] / 2)
        usable_offset = self.settings.value("system/system_calibration/usable_area_offset").toInt()[0]

        dist_x_center = self.settings.value("system/system_calibration/distance_cal_x").toInt()[0] + x_center
        dist_y_center = self.settings.value("system/system_calibration/distance_cal_y").toInt()[0] + y_center

        cv2.circle(self.raw_frame, (x_center, y_center), 3, (0, 0, 255), -1, cv2.CV_AA)
        cv2.circle(self.raw_frame, (x_center, y_center), crop_dim_half-1, (0, 0, 255), 1, cv2.CV_AA)
        cv2.circle(self.raw_frame, (x_center, y_center), (crop_dim_half - usable_offset), (0, 255, 255), 1, cv2.CV_AA)
        cv2.circle(self.raw_frame, (dist_x_center, dist_y_center), 3, (0, 102, 255), -1, cv2.CV_AA)

        frame = cv2.cvtColor(self.crop_image(self.raw_frame), cv2.COLOR_BGR2RGB)

        try:
            self.settings_and_cal_qimage = self.convert_to_qimage(cv2.resize(frame, (250, 250)))
            self.requested_image_ready_signal.emit()
        except:
            self.logger.debug("failed to convert")

    def show_cycle_run(self):
        if self.setup_params_once:
            self.setup_blob_params()
            self.setup_params_once = False

        if  not self.wait_for_image_req:
            self.wait_for_image_req = True

            try:
                frame = cv2.cvtColor(self.raw_frame, cv2.COLOR_BGR2GRAY)  # convert color image to grey
                # return_val, frame = cv2.threshold(frame, self.min_thresh, 255, cv2.cv.CV_THRESH_BINARY)  # apply binary threshold to image
                mask_frame = numpy.zeros((self.y_res, self.x_res), numpy.uint8)  # Setup a masking frame the size of the input frame with zeros
                cv2.circle(mask_frame, (self.x_center, self.y_center), (self.crop_dim_half - self.usable_offset), 255, -1)  # Fill the mask with 1's for a circle where the dish is in the image
                frame = cv2.bitwise_and(frame, mask_frame)  # Apply the mask to the input frame
                detected_frame = self.masked_detect_and_overlay(frame, self.raw_frame, "BGR")  # Send the masked frame to blob detection
                frame = self.crop_image(detected_frame)  # Crop image to size for display on gui


                self.cropped_only_raw = detected_frame

                resized = cv2.resize(frame, (200, 200))
                self.cycle_monitor_qimage = self.convert_to_qimage(resized)

                self.requested_image_ready_signal.emit()

            except:
                self.logger.debug("failed to convert")

    def masked_detect_and_overlay(self, input_frame, overlay_frame, overlay_type):
        detector = cv2.SimpleBlobDetector(self.current_params)
        self.keypoints = detector.detect(input_frame)
        self.number_embryos_detected_signal.emit(len(self.keypoints))

        if self.embryo_set_en:
            if overlay_type == "BGR":
                output_frame = overlay_frame
            else:
                output_frame = cv2.cvtColor(overlay_frame, cv2.COLOR_GRAY2BGR)

            self.valid_embryos = self.get_valid_embryos(self.keypoints)
            self.pickable_embryos = self.get_pickable_embryos(self.valid_embryos)

            output_frame = self.draw_embryos(output_frame, self.valid_embryos, RED)
            output_frame = self.draw_embryos(output_frame, self.pickable_embryos, GREEN)

        else:
            output_frame = cv2.drawKeypoints(overlay_frame, self.keypoints, color=(255, 0, 0))

        self.number_embryos_detected_signal.emit(len(self.pickable_embryos))
        return output_frame

    def setup_blob_params(self):
        if self.detection_profile_name == "Dechorionated":
            prefix = "d_"
        else:
            prefix = "c_"

        min_blob_dist = self.settings.value("system/detection_calibration/" + prefix + "min_blob_distance").toDouble()[0]
        min_repeat = self.settings.value("system/detection_calibration/" + prefix + "min_repeat").toInt()[0]
        blob_thresh_min = self.settings.value("system/detection_calibration/" + prefix + "blob_thresh_min").toInt()[0]
        blob_thresh_max = self.settings.value("system/detection_calibration/" + prefix + "blob_thresh_max").toInt()[0]
        blob_thresh_step = self.settings.value("system/detection_calibration/" + prefix + "blob_thresh_step").toInt()[0]
        blob_area_en = self.settings.value("system/detection_calibration/" + prefix + "blob_area_enabled").toInt()[0]
        blob_area_min = self.settings.value("system/detection_calibration/" + prefix + "blob_area_min").toDouble()[0]
        blob_area_max = self.settings.value("system/detection_calibration/" + prefix + "blob_area_max").toDouble()[0]
        blob_circ_en = self.settings.value("system/detection_calibration/" + prefix + "blob_circularity_enabled").toInt()[0]
        blob_circ_min = self.settings.value("system/detection_calibration/" + prefix + "blob_circularity_min").toDouble()[0]
        blob_circ_max = self.settings.value("system/detection_calibration/" + prefix + "blob_circularity_max").toDouble()[0]
        blob_conv_en = self.settings.value("system/detection_calibration/" + prefix + "blob_convexity_enabled").toInt()[0]
        blob_conv_min = self.settings.value("system/detection_calibration/" + prefix + "blob_convexity_min").toDouble()[0]
        blob_conv_max = self.settings.value("system/detection_calibration/" + prefix + "blob_convexity_max").toDouble()[0]
        blob_inertia_en = self.settings.value("system/detection_calibration/" + prefix + "blob_inertia_enabled").toInt()[0]
        blob_inertia_min = self.settings.value("system/detection_calibration/" + prefix + "blob_inertia_min").toDouble()[0]
        blob_inertia_max = self.settings.value("system/detection_calibration/" + prefix + "blob_inertia_max").toDouble()[0]


        self.current_params.minDistBetweenBlobs = min_blob_dist
        self.current_params.minRepeatability = min_repeat
        self.current_params.minThreshold = blob_thresh_min
        self.current_params.maxThreshold = blob_thresh_max
        self.current_params.thresholdStep = blob_thresh_step


        self.current_params.filterByColor = False

        if blob_area_en:
            self.current_params.filterByArea = True
            self.current_params.minArea = blob_area_min
            self.current_params.maxArea = blob_area_max
        else:
            self.current_params.filterByArea = False

        if blob_circ_en:
            self.current_params.filterByCircularity = True
            self.current_params.minCircularity = blob_circ_min
            self.current_params.maxCircularity = blob_circ_max
        else:
            self.current_params.filterByCircularity = False

        if blob_conv_en:
            self.current_params.filterByConvexity = True
            self.current_params.minConvexity = blob_conv_min
            self.current_params.maxConvexity = blob_conv_max
        else:
            self.current_params.filterByConvexity = False

        if blob_inertia_en:
            self.current_params.filterByInertia = True
            self.current_params.minInertiaRatio = blob_inertia_min
            self.current_params.maxInertiaRatio = blob_inertia_max
        else:
            self.current_params.filterByInertia = False

        self.embryo_set_en = self.settings.value("system/detection_calibration/" + prefix + "embryo_settings_enabled").toInt()[0]
        self.embryo_min_dist = self.settings.value("system/detection_calibration/" + prefix + "embryo_min_dist").toDouble()[0]
        self.embryo_min_size = self.settings.value("system/detection_calibration/" + prefix + "embryo_min_size").toDouble()[0]
        self.embryo_max_size = self.settings.value("system/detection_calibration/" + prefix + "embryo_max_size").toDouble()[0]


        # self.logger.info("Min Dist:" + str(self.embryo_min_dist))
        # self.logger.info("Min Size:" + str(self.embryo_min_size))
        # self.logger.info("Max Size:" + str(self.embryo_max_size))

        self.min_thresh = self.settings.value("system/detection_calibration/" + prefix + "min_binary_thresh").toInt()[0]
        #FIXME: thresholding testing
        self.min_thresh = blob_thresh_min
        self.x_res = self.settings.value("system/system_settings/camera_res_width").toInt()[0]
        self.y_res = self.settings.value("system/system_settings/camera_res_height").toInt()[0]
        self.x_center = self.settings.value("system/system_calibration/crop_x_center").toInt()[0]
        self.y_center = self.settings.value("system/system_calibration/crop_y_center").toInt()[0]
        self.crop_dim_half = (self.settings.value("system/system_calibration/crop_dimension").toInt()[0] / 2)
        self.usable_offset = self.settings.value("system/system_calibration/usable_area_offset").toInt()[0]

    def get_valid_embryos(self, keypoints):
        valid = []

        for point in self.keypoints:
                if (not isnan(point.pt[0])) and (not isnan(point.pt[1])) and (not isnan(point.size)):
                    valid.append([point.pt[0], point.pt[1], point.size])

        return valid

    def get_pickable_embryos(self, valid):
        pickable = []
        min_between_embryos = self.embryo_min_dist
        min_embryo_dia = self.embryo_min_size
        max_embryo_dia = self.embryo_max_size

        for embryo in valid:
            x = embryo[0]
            y = embryo[1]
            dia = embryo[2]

            if (dia >= min_embryo_dia) and (dia <= max_embryo_dia):
                found_too_close = False
                for comp_embryo in valid:
                    c_x = comp_embryo[0]
                    c_y = comp_embryo[1]
                    c_dia = comp_embryo[2]

                    if (x == c_x) and (y == c_y):
                        pass
                    elif (sqrt(pow(abs(x-c_x), 2) + pow(abs(y-c_y), 2))-(dia/2)-(c_dia/2)) < min_between_embryos:
                        found_too_close = True
                        break
                if not found_too_close:
                    pickable.append(embryo)

        return pickable

    @staticmethod
    def draw_embryos(frame, embryos, color):
        for embryo in embryos:
            cv2.circle(frame, (int(embryo[0]), int(embryo[1])), int(embryo[2]), color, -1, cv2.CV_AA)
        return frame

    @staticmethod
    def convert_to_qimage(input_matrix):
        return qimage2ndarray.array2qimage(input_matrix)

    def crop_image(self, input_matrix):
        x_center = self.settings.value("system/system_calibration/crop_x_center").toInt()[0]
        y_center = self.settings.value("system/system_calibration/crop_y_center").toInt()[0]
        crop_dim_half = (self.settings.value("system/system_calibration/crop_dimension").toInt()[0] / 2)
        x1 = x_center - crop_dim_half
        x2 = x_center + crop_dim_half
        y1 = y_center - crop_dim_half
        y2 = y_center + crop_dim_half

        cropped = input_matrix[y1:y2, x1:x2]

        return cropped

    def get_camera_frame(self):
        #self.raw_frame = cv2.imread('images/embryo_image.png', cv2.IMREAD_COLOR)
        return_val, self.raw_frame = self.video_camera.retrieve()
        if self.take_image:
            if self.image_count >= 12:
                filename = datetime.now().strftime("RawImage__%Y-%m-%d___%H-%M-%S.png")
                cv2.imwrite("/home/debian/screen_dumps/" + filename, self.raw_frame)
                self.take_image = False
            else:
                self.image_count += 1

    def on_general_camera_settings_changed_slot(self):
        self.settings.sync()
        self.reconnect_to_camera_flag = True

    def detection_calibration_preview_status_slot(self, enabled_state, which_image, which_profile):
        if enabled_state:
            self.setup_params_once = True

        self.video_being_used = enabled_state
        self.video_output_type = which_image
        self.video_output_widget_name = self.DETECTION_CAL
        self.detection_profile_name = which_profile

    def system_calibration_preview_status_slot(self, enabled_state):

        self.video_being_used = enabled_state
        self.video_output_widget_name = self.SYSTEM_CAL

    def cycle_run_changed_slot(self, enabled_state, which_profile):
        if enabled_state:
            self.detection_profile_name = which_profile
            self.take_image = True
            self.image_count = 0
            self.setup_params_once = True

        self.video_being_used = enabled_state
        self.video_output_widget_name = self.CYCLE_RUN

    def on_cycle_run_image_requested_slot(self):
        self.wait_for_image_req = False

    def images_displayed_slot(self):
        self.images_displayed = True

    def on_kill_threads_slot(self):
        self.not_abort_flag = False