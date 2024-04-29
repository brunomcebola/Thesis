"""
Module to compute relative pose between multiple cameras using ArUco markers.
"""

import cv2
import cv2.aruco as aruco
import numpy as np

# Define the dictionary and parameters
ARUCO_DICT = aruco.getPredefinedDictionary(aruco.DICT_6X6_50)
aruco_params = aruco.DetectorParameters()

# Camera intrinsic parameters (dummy values, replace with your calibration data)
camera_matrix = np.array([[1000, 0, 320], [0, 1000, 240], [0, 0, 1]])
dist_coeffs = np.zeros((5, 1))


def detect_markers_and_pose(image, camera_matrix, dist_coeffs):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    corners, ids, rejected = aruco.detectMarkers(gray, aruco_dict, parameters=aruco_params)

    rvecs, tvecs, _objPoints = aruco.estimatePoseSingleMarkers(
        corners, 0.05, camera_matrix, dist_coeffs
    )  # 0.05 is the marker size in meters
    return ids, rvecs, tvecs


def compute_relative_transformation(rvec1, tvec1, rvec2, tvec2):
    R1, _ = cv2.Rodrigues(rvec1)
    R2, _ = cv2.Rodrigues(rvec2)
    R_relative = R2 @ R1.T
    t_relative = tvec2 - (R_relative @ tvec1)
    return R_relative, t_relative


# Dummy data for illustration; replace with your actual images
images = [cv2.imread(f"camera{i}.jpg") for i in range(1, 5)]

poses = []
for img in images:
    ids, rvecs, tvecs = detect_markers_and_pose(img, camera_matrix, dist_coeffs)
    poses.append((ids, rvecs, tvecs))

# Assuming camera 0 is the reference
reference_ids, reference_rvecs, reference_tvecs = poses[0]

for i in range(1, len(images)):
    current_ids, current_rvecs, current_tvecs = poses[i]
    # Find common markers and compute transformations
    for id_idx, marker_id in enumerate(current_ids):
        if marker_id in reference_ids:
            ref_idx = np.where(reference_ids == marker_id)[0][0]
            R_rel, t_rel = compute_relative_transformation(
                reference_rvecs[ref_idx],
                reference_tvecs[ref_idx],
                current_rvecs[id_idx],
                current_tvecs[id_idx],
            )
            print(
                f"Relative pose from camera 0 to camera {i} using marker {marker_id}:", R_rel, t_rel
            )
