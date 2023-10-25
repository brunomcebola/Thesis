"""
This module holds the tools to aquire data from the realsense cameras.

Classes:
--------


"""
import os
from utils import print_error, BaseNamespace, ArgSource

from camera import Camera


class AquireNamespace(BaseNamespace):
    """
    This class holds the arguments for the aquire mode.

    It can be initialized with explicit arguments or with a dictionary.

    Attributes:
    -----------
        - source:
            Indicates wheter the args come from the command line of from a YAML file.
        - output:
            The path to the output folder.
        - cameras:
            The serial numbers of the cameras to be used.
        - stream:
            The type of stream to be captured by each camera.
        - config:
            The configuration of the stream to be captured by each camera.
        - op_time:
            The time interval in which the cameras will be capturing data.
        - source:
            Indicates wheter the args come from a YAML file of from the command line.
        - kwargs:
            Used as dumpster for extra arguments passed from mappings.
    """

    def __init__(
        self,
        source: ArgSource,
        output_folder: str,
        cameras: list[str] | None = None,
        # stream_types: list[StreamType] = None,
        # stream_configs: list[tuple[StreamConfig | None, StreamConfig | None]] = None,
        # op_times: list[tuple[int, int]] = None,
        **kwargs,
    ):
        del kwargs

        super().__init__(source)

        if self.source == ArgSource.CMD:
            # output folder
            if not os.path.exists(output_folder):
                print_error(f"Output folder does not exist ({output_folder}).")
                exit(1)

            self.output_folder = output_folder

            # cameras
            if cameras is None:
                cameras = Camera.get_available_cameras()
                if len(cameras) == 0:
                    print_error("No available cameras.")
                    exit(1)
                self.cameras = cameras
            elif Camera.is_camera_available(cameras[0]):
                self.cameras = cameras
            else:
                print_error(f"Camera {cameras[0]} is not available.")
                exit(1)

        elif self.source == ArgSource.YAML:
            pass


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
