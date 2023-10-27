"""
This module holds the tools to aquire data from the realsense cameras.

Classes:
--------


"""
import os
import time
import logging
import calendar

from utils import print_error, print_warning, BaseNamespace, ArgSource
from camera import Camera, StreamType, StreamConfig

WEEK_DAYS = list(calendar.day_abbr)

# TODO: change exit to raise
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


        - serial_numbers (list[str]):
            The serial numbers of the cameras to be used.
        - names (list[str]):
            The names of the cameras to be used.
        - stream_types (list[StreamType]):
            The type of stream to be captured by each camera.
        - stream_configs (list[dict[str, StreamConfig]]):
            The configuration of the stream to be captured by each camera.

        - kwargs:
            Used as a dumpster for extra arguments passed from mappings.
    """

    def __init__(
        self,
        source: ArgSource,
        output_folder: str,
        serial_numbers: list[str] | None = None,
        # names: list[str] | None = None,
        stream_types: list[StreamType] | None = None,
        # stream_configs: list[dict[str, StreamConfig]] | None = None,
        # op_times: tuple[int, int] | list[tuple[str, int, int]] | None = None,
        **kwargs,
    ):
        # type definitions
        self.output_folder: str
        self.op_times: list[tuple[int, int, int]]



        del kwargs

        super().__init__(source)

        if self.source == ArgSource.CMD:
            # output folder (argparser ensure it is a non-empty string)
            if not os.path.exists(output_folder):
                print_error(f"Output folder does not exist ({output_folder}).")
                exit(1)

            self.output_folder = output_folder

            # serial_numbers (argparser ensures it is either None or a list with only one element)
            #   if None then all available cameras will be used
            #   if list then specified serial number must match an available camera
            if serial_numbers is None:
                serial_numbers = Camera.get_available_cameras()
                if len(serial_numbers) == 0:
                    print_error("No available cameras.")
                    exit(1)
                print_warning(
                    f"No specific camera specified. Using all available cameras: {serial_numbers}."
                )
                self.serial_numbers = serial_numbers
            elif Camera.is_camera_available(serial_numbers[0]):
                self.serial_numbers = serial_numbers
            else:
                print_error(f"Camera {serial_numbers[0]} is not available.")
                exit(1)

            # stream types (argparser ensures it is either None or a list with only one element)
            #   if None then depth stream will be used to all cameras
            #   if list then specified stream type will be used to all cameras
            if stream_types is None:
                print_warning("No stream type specified. Setting depth as stream of all cameras.")
                self.stream_types = [StreamType.DEPTH] * len(self.serial_numbers)
            else:
                self.stream_types = stream_types * len(self.serial_numbers)

            # names (argparser ensures it is None)
            # cameras' names will be their serial numbers
            print_warning("Using serial number as name for all cameras.")
            self.names = list(self.serial_numbers)

            # stream configs (argparser ensures it is None)
            # default configs will be used for all cameras based on their models
            print_warning("Using default stream configs for all cameras based on their models.")
            self.stream_configs = [
                Camera.get_camera_default_config(Camera.get_camera_model(sn))
                for sn in self.serial_numbers
            ]

            # op times (argparser ensures it is None)
            # cameras will be capturing data all the time
            print_warning("Cameras will be capturing data all the time.")
            self.op_times = [(i, 0, 24) for i in range(7)]

        elif self.source == ArgSource.YAML:
            pass

    def __str__(self) -> str:
        string = ""

        string += f"\tOutput folder: '{self.output_folder}'\n"
        string += (
            f"\tOperation time: {[(WEEK_DAYS[op[0]], op[1], op[2]) for op in self.op_times]}\n"
        )
        string += "\tCameras:"
        for name, sn, stream, config in zip(
            self.names, self.serial_numbers, self.stream_types, self.stream_configs
        ):
            string += "\n"
            string += f"\t\tName:{name}\n"
            string += f"\t\tSerial number:{sn}\n"
            string += f"\t\tStream type:{stream}\n"
            for key, value in config.items():
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
