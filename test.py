"""
Module for testing
"""
import pyrealsense2.pyrealsense2 as rs
from camera import Camera, StreamType, StreamConfig

c = Camera(
    "123",
    "135522077203",
    StreamType.DEPTH_N_COLOR,
    {StreamType.DEPTH: StreamConfig(rs.format.z16, (640, 480), 30)},
)

# print(Camera.DEFAULTS)
