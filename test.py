"""
Module for testing
"""
import pyrealsense2.pyrealsense2 as rs
from intel import Camera, StreamType, StreamConfig, DepthFrame
import utils

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

b = utils.BaseNamespace(utils.ArgSource.CMD)

f = DepthFrame("ola")
f.operation()

# print(Camera.DEFAULTS)
