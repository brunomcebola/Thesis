""" Generate ArUco markers using OpenCV """

aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_50)
markerSize = 500  # Adjust based on actual size needed, considering print resolution

for markerId in range(50):  # Generate 5 markers
    markerImage = aruco.generateImageMarker(aruco_dict, markerId, markerSize)
    cv2.imwrite(f"ArUco markers/marker{markerId}.png", markerImage)
