"""
This module holds the tools to aquire data from the realsense cameras.

Classes:
--------


"""
from types import SimpleNamespace
import pyrealsense2.pyrealsense2 as rs

from camera import Camera, StreamType, StreamConfig


class AquireNamespace(SimpleNamespace):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        print(self.__dict__.get("ttt"))

        self.__dict__.update(a=1)


# STORAGE_PATH = os.getenv("STORAGE_PATH")

# if STORAGE_PATH is None:
#     exit("STORAGE_PATH is not set in .env file.")
# elif not os.path.exists(STORAGE_PATH):
#     exit(f"STORAGE_PATH set in .env file does not exist ({STORAGE_PATH}) .")

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
