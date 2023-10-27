"""
Module for testing
"""
import pyrealsense2.pyrealsense2 as rs
from camera import Camera, StreamType, StreamFormat

c = Camera(
    "135522077203", "135522077203", StreamType.DEPTH, StreamFormat(1280, 720, 30, rs.format.z16)
)
c.start_pipeline()
c.stop_pipeline()

s = StreamFormat(1280, 720, 30, rs.format.z16)

