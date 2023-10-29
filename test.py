"""
Module for testing
"""
import pyrealsense2.pyrealsense2 as rs
from intel import Camera, StreamType, StreamConfig
import utils

from abc import ABC, abstractmethod

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

class t(utils.BaseNamespace):
    def __init__(self, source: utils.ArgSource):
        super().__init__(source)
        print("init")

b = utils.BaseNamespace(utils.ArgSource.CMD)

# print(Camera.DEFAULTS)
