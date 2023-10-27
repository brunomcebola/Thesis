"""
Module for testing
"""
import pyrealsense2.pyrealsense2 as rs
from camera import Camera, StreamType, StreamFormat

c = Camera(
    "123",
    "123",
    StreamType.DEPTH,
    {StreamType.DEPTH: StreamFormat(rs.format.z16, (640, 480), 30)},
)

print(Camera.DEFAULTS)
