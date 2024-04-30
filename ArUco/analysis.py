"""
Detecting ArUco markers in an image
"""

import cv2
import numpy as np


def preprocess_image(img):
    """
    Enhance the image to make the markers more visible
    """
    # Sharpen image
    kernel = np.array([[1, 1, 1], [1, 1, 1], [1, 1, 1]])
    # img = cv2.filter2D(img, -1, kernel)

    # Correcting brightness and contrast (if necessary)
    # img = cv2.convertScaleAbs(img, alpha=1.5, beta=20)

    return img


ARUCO_DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_50)

aruco_params = cv2.aruco.DetectorParameters()
aruco_params.adaptiveThreshConstant = 7
aruco_params.minMarkerPerimeterRate = 0.03
aruco_params.maxMarkerPerimeterRate = 4.0
aruco_params.polygonalApproxAccuracyRate = 0.05

aruco_detector = cv2.aruco.ArucoDetector(ARUCO_DICT, aruco_params)


input_images = [
    preprocess_image(cv2.rotate(cv2.imread(f"photos/rpi{i}_1.png"), cv2.ROTATE_180))
    for i in range(1, 5)
]
infered_data = []
output_images = []

for image in input_images:
    RESULT = aruco_detector.detectMarkers(image)
    if RESULT is not None:
        (corners, ids, rejected) = RESULT
        infered_data.append((corners, ids, rejected))

        IMAGE_W_MARKERS = cv2.aruco.drawDetectedMarkers(image, corners, ids)
        output_images.append(IMAGE_W_MARKERS)


horizontal1 = np.hstack(output_images[:2])
horizontal2 = np.hstack(output_images[2:])

vertical = np.vstack([horizontal1, horizontal2])

cv2.imshow("Grid", vertical)
cv2.waitKey()
