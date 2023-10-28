"""
Module for testing
"""
import pyrealsense2.pyrealsense2 as rs
from camera import Camera, StreamType, StreamConfig

c1 = Camera(
    "123",
    "135522077203",
    StreamType.DEPTH,
    {
        StreamType.DEPTH: StreamConfig(rs.format.z16, (640, 480), 30)
    },
)

try:
    c1.change_stream_configs(
        StreamType.COLOR,
        {StreamType.COLOR: StreamConfig(rs.format.rgb8, (640, 480), 30)},
    )
except Exception:
    print("err")

c1.start()
c1.stop()


# print(Camera.DEFAULTS)
