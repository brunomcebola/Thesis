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


c = Camera("135522077203", StreamType.DEPTH_N_COLOR, Camera.DEFAULTS["D435"], "c1")


c.start()

frame = c.get_frames()

# print(frame.get_depth_frame().get_distance(72, 1))
# print(np.asanyarray(frame.get_depth_frame().get_data()).shape)
# print(np.asanyarray(frame.get_color_frame().get_data()).shape)
# print()

# xyz = np.random.rand(100, 3)
# pcd = o3d.geometry.PointCloud()
# pcd.points = o3d.utility.Vector3dVector(xyz)
# o3d.io.write_point_cloud("./data.ply", pcd)

# ply = rs.save_to_ply("1.ply")

# # Set options to the desired values
# # In this example we'll generate a textual PLY with normals (mesh is already created by default)
# ply.set_option(rs.save_to_ply.option_ply_binary, False)
# ply.set_option(rs.save_to_ply.option_ply_normals, True)

# print("Saving to 1.ply...")
# # Apply the processing block to the frameset which contains the depth frame and the texture
# ply.process(frame)

c.stop()

print(frame.get_depth_frame().get_distance(72, 1))

with open('frame.pkl', 'wb') as outp:
    pickle.dump(frame, outp, pickle.HIGHEST_PROTOCOL)

with open('frame.pkl', 'rb') as inp:
    frame = pickle.load(inp)

print(frame.get_depth_frame().get_distance(72, 1))
# print(Camera.DEFAULTS)
