"""
Module for testing
"""

from intel import Camera, StreamType, StreamConfig
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


c = Camera("135522077203", StreamType.DEPTH, Camera.DEFAULTS["D435"], "c1")

c.start()

frame = c.get_frames()
print(frame)

c.stop()

# print(Camera.DEFAULTS)
