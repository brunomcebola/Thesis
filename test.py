"""
Module for testing
"""
import pyrealsense2.pyrealsense2 as rs
from camera import Camera, StreamType, StreamConfig

c1 = Camera(
    "123",
    "135522077203",
    StreamType.DEPTH,
    {StreamType.DEPTH: StreamConfig(rs.format.z16, (640, 480), 30)},
)

del c1

c2 = Camera(
    "123",
    "135522077203",
    StreamType.DEPTH,
    {StreamType.DEPTH: StreamConfig(rs.format.z16, (640, 480), 30)},
)

# print(Camera.DEFAULTS)
