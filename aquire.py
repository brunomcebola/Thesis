"""
This module holds the tools to aquire data from the realsense cameras.

Classes:
--------
- AquireNamespace: Holds the arguments for the aquire mode.

Exceptions:
-----------
- OutputFolderError: Exception raised when errors related to the out_folder occur.
- OperationTimeError: Exception raised when errors related to the operation time occur.
- SerialNumberError: Exception raised when errors related to the serial number occur.
- NamesError: Exception raised when errors related to the names occur.
- StreamTypeError: Exception raised when errors related to the stream type occur.
- StreamConfigError: Exception raised when errors related to the stream config occur.
"""
import os
import calendar
from types import SimpleNamespace

import intel
import utils

WEEK_DAYS = list(calendar.day_name)
SHORT_WEEK_DAYS = list(calendar.day_abbr)


class OutputFolderError(Exception):
    """
    Exception raised when errors related to the out_folder occur.
    """


class OperationTimeError(Exception):
    """
    Exception raised when errors related to the operation time occur.

    It returns a tuple with information about the error.

    Tuple Structure:
    ----------------
        - error_message (str): A human-readable error message providing more
          details about the issue.
        - error_index (int | None): The index of the invalid operation time.

    Usage:
    ------
        try:
           # Code that may raise the exception
        except OperationTimeError as e:
           error_message, error_index = e.args
    """

    def __init__(self, error_message, error_index: int | None = None):
        super().__init__(error_message, error_index)


class SerialNumberError(Exception):
    """
    Exception raised when errors related to the serial number occur.
    """


class NamesError(Exception):
    """
    Exception raised when errors related to the names occur.
    """


class StreamTypeError(Exception):
    """
    Exception raised when errors related to the stream type occur.
    """


class StreamConfigError(Exception):
    """
    Exception raised when errors related to the stream config occur.
    """


class AquireNamespace(SimpleNamespace):
    """
    This class holds the arguments for the aquire mode.

    It can be initialized with explicit arguments or with a dictionary.

    Attributes:
    -----------
        - output_folder (str):
            The path to the output folder.
        - op_times (list[tuple[int, int]]):
            The time interval in which the cameras will be capturing data
            for each day of the week (Monday to Sunday).
        - cameras (list[intel.Camera]):
            The list with the cameras to be used.
    """

    def __init__(
        self,
        output_folder: str,
        op_times: list[tuple[int, int]] | None = None,
        serial_numbers: list[str] | None = None,
        names: list[str] | None = None,
        stream_types: list[intel.StreamType] | None = None,
        stream_configs: list[dict[intel.StreamType, intel.StreamConfig]] | None = None,
    ):
        """
        AquireNamespace constructor.

        Args:
        -----
            - output_folder: The path to the output folder.
            - op_times: The time interval in which the cameras will be capturing data
              for each day of the week (Monday to Sunday).
                - If None then cameras will be capturing data all the time.
                - If list with 1 element then the specified time interval will be used for all days.
                - If list with 7 elements then each element will be used for each day.
            - serial_numbers: The serial numbers of the cameras to be used.
                - If None then all connected cameras will be used.
                - If list with n elements then the specified cameras will be used.
            - names: The names of the cameras to be used.
                - If None then the cameras' serial numbers will be used as names.
                - If list with the same len as the serial_numbers list then the specified names
                  will be used.
            - stream_types: The stream types of the cameras to be used.
                - If None then depth stream will be used for all cameras.
                - If list with 1 element then the specified stream will be used for all cameras.
                - If list with the same len as the serial_numbers list then the specified streams
                  will be used.

        Raises:
        -------
            - OutputFolderError:
                - If the output folder does not exist.
            - OperationTimeError:
                - If the operation time is not a list with 1 or 7 elements.
                - If the operation time is not expressed in the format (int, int).
                - If the start hour is not a value between 0 and 23.
                - If the stop hour is not a value between 1 and 24.
                - If the start hour is greater than the stop hour.
            - SerialNumberError:
                - If the serial numbers are not unique.
            - NamesError:
                - If the number of names is not equal to the number of cameras, when cameras are
                specified.
            - StreamTypeError:
                - If the number of stream types is not equal to the number of cameras, when cameras
                are specified.
            - StreamConfigError:
                - If the number of stream configs is not equal to the number of cameras, when
                cameras are specified.
            - intel.CameraUnavailableError:
                - If no cameras are available.
                - If the specified cameras are not available.
            - intel.StreamConfigError:
                - If the specified stream config is not valid for the specified camera model.


        Examples:
        ---------
            >>> aquire_namespace = AquireNamespace(
            ...     output_folder="./",
            ...     op_times=[(8, 12)],
            ...     serial_numbers=["123456789", "987654321"],
            ...     names=["front", "back"],
            ...     stream_types=[StreamType.DEPTH, StreamType.COLOR],
            ... )
            >>> print(aquire_namespace)
            # TODO: add output
            # TODO: add examples

        """

        # type definitions
        self.output_folder: str = ""
        self.op_times: list[tuple[int, int]] = []
        self.cameras: list[intel.Camera] = []

        # output_folder validations
        output_folder = output_folder.strip()

        if output_folder == "":
            raise OutputFolderError("The output folder cannot be a empty string.")

        if not os.path.exists(output_folder):
            raise OutputFolderError(f"The output folder '{output_folder}' does not exist.")

        self.output_folder = output_folder

        # op_times validations
        if op_times is None:
            utils.print_warning(
                "No operation time specified. Cameras will be capturing data all the time."
            )

            op_times = [(int(0), int(24))] * 7

        elif len(op_times) == 1:
            utils.print_warning("Using the same operation time for all days.")

            op_times = op_times * 7

        elif len(op_times) != 7:
            raise OperationTimeError(
                "The specified operation time must be a list with 1 or 7 elements.",
            )

        for i, op_time in enumerate(op_times):
            if len(op_time) != 2:
                raise OperationTimeError(
                    "The operation time must be expressed in the format "
                    + "(int, int). Ex: (8, 12) => 8:00 - 12:00.",
                    i,
                )

            if op_time[0] not in range(24):
                raise OperationTimeError(
                    "The start hour must be a value between 0 and 23.",
                    i,
                )

            if op_time[1] not in range(1, 25):
                raise OperationTimeError(
                    "The stop hour must be a value between 1 and 24.",
                    i,
                )

            if op_time[0] >= op_time[1]:
                raise OperationTimeError(
                    "The start hour must be smaller than the stop hour.",
                    i,
                )

        self.op_times = op_times

        # serial_numbers validations
        original_nb_serial_numbers = len(serial_numbers) if serial_numbers is not None else 0

        if serial_numbers is None:
            utils.print_warning("No camera specified. Using all connected cameras.")

            serial_numbers = intel.Camera.get_available_cameras()

            if len(serial_numbers) == 0:
                raise intel.CameraUnavailableError("No available cameras.")

        if len(set(serial_numbers)) != len(serial_numbers):
            raise SerialNumberError("Duplicate serial numbers specified.")

        serial_numbers = [sn.strip() for sn in serial_numbers]

        # names validations
        if names is None:
            utils.print_warning("No names specified. Using serial numbers as camera names.")

            names = serial_numbers

        elif original_nb_serial_numbers == 0:
            utils.print_warning(
                "No cameras especified. Ignoring names and using serial numbers instead."
            )

            names = serial_numbers

        elif len(names) != len(serial_numbers):
            raise NamesError("The number of names must be equal to the number of cameras.")

        # stream_types validations
        if stream_types is None:
            utils.print_warning("No stream type specified. Setting depth as stream of all cameras.")

            stream_types = [intel.StreamType.DEPTH] * len(serial_numbers)

        elif len(stream_types) == 1:
            utils.print_warning("Using the specified stream type for all cameras.")

            stream_types = stream_types * len(serial_numbers)

        elif original_nb_serial_numbers == 0:
            utils.print_warning(
                "No cameras especified. Ignoring stream types and using depth for all "
                + "cameras instead."
            )

            stream_types = [intel.StreamType.DEPTH] * len(serial_numbers)

        elif len(stream_types) != len(serial_numbers):
            raise StreamTypeError(
                "The number of stream types must be equal to the number of cameras."
            )

        # stream configs validations
        if stream_configs is None:
            utils.print_warning(
                "No stream configs specified. Using default stream configs for each camera model."
            )

            stream_configs = [
                intel.Camera.get_default_config(intel.Camera.get_camera_model(sn))
                for sn in serial_numbers
            ]

        elif len(stream_configs) == 1:
            utils.print_warning("Using the specified stream config for all cameras.")

            stream_configs = stream_configs * len(serial_numbers)

        elif original_nb_serial_numbers == 0:
            utils.print_warning(
                "No cameras especified. Ignoring stream configs and using default stream configs "
                + "for each camera model instead."
            )

            stream_configs = [
                intel.Camera.get_default_config(intel.Camera.get_camera_model(sn))
                for sn in serial_numbers
            ]

        elif len(stream_configs) != len(serial_numbers):
            raise StreamConfigError(
                "The number of stream configs must be equal to the number of cameras."
            )

        # create list of camera instances
        self.cameras = [
            intel.Camera(sn, st, sc, nm)
            for sn, st, sc, nm in zip(serial_numbers, stream_types, stream_configs, names)
        ]

    # TODO: change to direct access
    def __str__(self) -> str:
        string = ""

        string += f"\tOutput folder: '{self.output_folder}'\n"
        string += f"\tOperation time: {[(SHORT_WEEK_DAYS[i], op[0], op[1]) for i, op in enumerate(self.op_times)]}\n"  # pylint: disable=line-too-long
        string += "\tCameras:"
        for camera in self.cameras:
            string += "\n"
            string += f"\t\tName:{camera.name}\n"
            string += f"\t\tSerial number:{camera.serial_number}\n"
            string += f"\t\tStream type:{camera.stream_type}\n"
            for key, value in camera.stream_configs.items():
                string += f"\t\t{key.name.capitalize()} stream config:{str(value)}\n"

        # align elements
        string = string.split(("Cameras:"))
        lines = string[1].split("\t\t")

        max_title = max([len(line.split(":")[0]) for line in lines])

        lines = [
            f":  {' ' * (max_title - len(line.split(':')[0]))}".join(line.split(":"))
            for line in lines
        ]

        lines = "\t\t".join(lines)

        return (string[0] + "Cameras:" + lines).rstrip()


# STOP_FLAG = False
# import time
# import logging

# def aquire():
#     logging.basicConfig(
#         filename="thread_output.log", level=logging.INFO, format="%(asctime)s - %(message)s"
#     )

#     while not STOP_FLAG:
#         logging.info("aquire")
#         time.sleep(1)

#     logging.info("adeus")


# STORAGE_PATH = os.getenv("STORAGE_PATH")


# context = rs.context()
# devices = context.query_devices()
# nb_of_cams = devices.size()
# if nb_of_cams == 0:
#     exit("No realsense cameras found.")

# cameras: list[intel.Camera] = []
# for i in range(nb_of_cams):
#     dev = devices[i]
#     serial_number = dev.get_info(rs.camera_info.serial_number)
#     print("serial number: ", serial_number)
#     cameras.append(
#         intel.Camera(serial_number, StreamType.DEPTH, StreamConfig(640, 480, 30, rs.format.z16))
#     )

#     # check if folder exists and if not create it
#     if not os.path.exists(STORAGE_PATH + serial_number):
#         os.makedirs(STORAGE_PATH + serial_number)
#         print("created folder: ", STORAGE_PATH + serial_number)
#     else:
#         print("folder already exists: ", STORAGE_PATH + serial_number)


# cameras[0].start_pipeline()

# t = []

# for i in range(6000):
#     ti = time.time()
#     frames = cameras[0].get_frames()
#     tf = time.time()
#     t.append(int(round((tf - ti) * 1000)))
#     time.sleep(0.1)

# print(np.average(t))
