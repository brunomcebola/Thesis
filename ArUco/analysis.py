"""
Detecting ArUco markers in an image
"""

import cv2
import numpy as np

aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_50)
aruco_params = cv2.aruco.DetectorParameters()
aruco_detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)


input_images = [cv2.rotate(cv2.imread(f"photos/rpi{i}_1.png"), cv2.ROTATE_180) for i in range(1, 5)]
infered_data = []
output_images = []

for image in input_images:
    (corners, ids, rejected) = aruco_detector.detectMarkers(image)
    infered_data.append((corners, ids, rejected))

    image = cv2.aruco.drawDetectedMarkers(image, corners, ids)
    output_images.append(image)


horizontal1 = np.hstack(output_images[:2])
horizontal2 = np.hstack(output_images[2:])

vertical = np.vstack([horizontal1, horizontal2])

cv2.imshow('Grid', vertical)
cv2.waitKey()
