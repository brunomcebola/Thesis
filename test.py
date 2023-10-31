"""
Module for testing
"""

import pyrealsense2.pyrealsense2 as rs
from intel import Camera, StreamType, StreamConfig
import utils
import numpy as np
import open3d as o3d
import pickle

# c1 = Camera(
#     "135522077203",
#     StreamType.DEPTH,
#     {StreamType.DEPTH: StreamConfig(rs.format.z16, (640, 480), 30)},
#     "c1",
# )

# print("created")

# try:
#     c1.change_stream_configs(
#         StreamType.COLOR,
#         {StreamType.COLOR: StreamConfig(rs.format.rgb8, (640, 480), 30)},
#     )
# except Exception:
#     print("err")

# c1.start()
# c1.stop()

print("ola")

c = Camera("135522071130", StreamType.DEPTH_N_COLOR, Camera.get_default_config("D435"), "c1")

print(c.stream_type)
print(c.stream_types)

c.stream_type = StreamType.COLOR

print(c.stream_type)
print(c.stream_types)
