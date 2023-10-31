"""
This module holds the tools to aquire data from the realsense cameras.

Classes:
--------


"""
import os
import calendar

from utils import print_warning, BaseNamespace, ArgSource
from intel import Camera, StreamType, CameraUnavailableError

WEEK_DAYS = list(calendar.day_abbr)


class OutputFolderError(Exception):
    """
    Exception raised when the output folder does not exist.
    """


class AquireNamespace(BaseNamespace):
    """
    This class holds the arguments for the aquire mode.

    It can be initialized with explicit arguments or with a dictionary.

    Attributes:
    -----------
        - output_folder (str):
            The path to the output folder.
        - op_times (list[tuple[int, int, int]]):
            The time interval in which the cameras will be capturing data for each day of the week.
        - cameras (list[Camera]):
            The list with the cameras to be used.
    """

    def __init__(
        self,
        source: ArgSource,
        output_folder: str,
        serial_numbers: list[str] | None = None,
        stream_types: list[StreamType] | None = None,
        # names: list[str] | None = None,
        # stream_configs: list[dict[str, StreamConfig]] | None = None,
        # op_times: tuple[int, int] | list[tuple[str, int, int]] | None = None,
        **kwargs,
    ):
        """
        AquireNamespace constructor.

        Args:
        -----
            - source: Origin of the arguments.
            - output_folder: The path to the output folder.
            - serial_numbers: The serial numbers of the cameras to be used.
            - stream_types: The stream types to be used.
            - kwargs: The remaining arguments (to allow for the use of **vars(args))
        """

        # type definitions
        self.output_folder: str
        self.op_times: list[tuple[int, int, int]]

        del kwargs

        super().__init__(source)

        if self.source == ArgSource.CMD:
            # output folder (argparser ensure it is a non-empty string)
            if not os.path.exists(output_folder):
                raise OutputFolderError(f"Output folder does not exist ({output_folder}).")

            self.output_folder = output_folder

            # serial_numbers (argparser ensures it is either None or a list with only one element)
            #   if None then all available cameras will be used
            #   if list then specified serial number must match an available camera
            if serial_numbers is None:
                print_warning("No specific camera specified. Using all connected cameras.")
                serial_numbers = Camera.get_available_cameras()
                if len(serial_numbers) == 0:
                    raise CameraUnavailableError("No available cameras.")
            elif not Camera.is_camera_available(serial_numbers[0]):
                raise CameraUnavailableError(f"Camera {serial_numbers[0]} is not available.")

            # stream types (argparser ensures it is either None or a list with only one element)
            #   if None then depth stream will be used to all cameras
            #   if list then specified stream type will be used to all cameras
            if stream_types is None:
                print_warning("No stream type specified. Setting depth as stream of all cameras.")
                stream_types = [StreamType.DEPTH] * len(serial_numbers)
            else:
                stream_types = stream_types * len(serial_numbers)

            # stream configs (argparser ensures it is None)
            # default configs will be used for all cameras based on their models
            print_warning("Using default stream configs for all cameras based on their models.")
            stream_configs = [
                Camera.get_default_config(Camera.get_camera_model(sn)) for sn in self.serial_numbers
            ]

            # names (argparser ensures it is None)
            # cameras' names will be their serial numbers
            print_warning("Using serial number as name for all cameras.")

            # create list of camera instances
            self.cameras = [
                Camera(sn, st, sc)
                for sn, st, sc in zip(serial_numbers, stream_types, stream_configs)
            ]

            # op times (argparser ensures it is None)
            # cameras will be capturing data all the time
            print_warning("Cameras will be capturing data all the time.")
            self.op_times = [(i, 0, 24) for i in range(7)]

        elif self.source == ArgSource.YAML:
            pass

    # TODO: change to direct access
    def __str__(self) -> str:
        string = ""

        string += f"\tOutput folder: '{self.output_folder}'\n"
        string += (
            f"\tOperation time: {[(WEEK_DAYS[op[0]], op[1], op[2]) for op in self.op_times]}\n"
        )
        string += "\tCameras:"
        for camera in self.cameras:
            string += "\n"
            string += f"\t\tName:{camera}\n"
            string += f"\t\tSerial number:{camera}\n"
            string += f"\t\tStream type:{camera}\n"
            for key, value in camera():
                string += f"\t\t{key.capitalize()} stream config:{str(value)}\n"

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

# cameras: list[Camera] = []
# for i in range(nb_of_cams):
#     dev = devices[i]
#     serial_number = dev.get_info(rs.camera_info.serial_number)
#     print("serial number: ", serial_number)
#     cameras.append(
#         Camera(serial_number, StreamType.DEPTH, StreamConfig(640, 480, 30, rs.format.z16))
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
