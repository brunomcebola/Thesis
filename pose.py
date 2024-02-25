" This is a test file to test the functionality of the RealSenseCamera class and the YOLO model."

import cv2
import numpy as np
from ultralytics import YOLO
import pyrealsense2 as rs

import src.intel as intel

# Load model
model = YOLO("yolov8n-pose.pt")

camera = intel.RealSenseCamera(
    "939622075103",
    [
        intel.StreamConfig(
            intel.StreamType.DEPTH,
            intel.StreamFormat.Z16,
            intel.StreamResolution.X640_Y480,
            intel.StreamFPS.FPS_30,
        ),
        intel.StreamConfig(
            intel.StreamType.COLOR,
            intel.StreamFormat.BGR8,
            intel.StreamResolution.X640_Y480,
            intel.StreamFPS.FPS_30,
        ),
    ],
)

align_to = rs.stream.color # type: ignore
align = rs.align(align_to) # type: ignore

camera.start_streaming()

try:
    while True:

        frames = camera.frames_queue.get()

        depth_image = frames[0].data
        color_image = frames[1].data

        results = model.predict(source=color_image, classes=[0])

        depth_image = cv2.applyColorMap(
            cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET
        )

        depth_image = cv2.resize(depth_image, (640, 480))
        color_image = cv2.resize(color_image, (640, 480))

        for person_skel in results[0].keypoints.xy:
            if len(person_skel):
                for point in person_skel:
                    if point[0] > 0 and point[1] > 0:
                        color_image = cv2.circle(
                            color_image,
                            (int(point[0]), int(point[1])),
                            5,
                            (0, 0, 255)
                        )

        # for keypoint in results[0].keypoints[0].xy[0]:
            # color_image = cv2.rectangle(
            #     color_image,
            #     (int(box.xyxy[0][0]), int(box.xyxy[0][1])),
            #     (int(box.xyxy[0][2]), int(box.xyxy[0][3])),
            #     (0, 0, 255),
            #     2,
            # )
            # if len(keypoint.xy[0]) > 0:
            #     for
            #     color_image = cv2.circle(
            #         color_image,
            #         (int(keypoint.xy[0][0]), int(keypoint.xy[0][1])),
            #         5,
            #         (0, 0, 255),
            #         -1,
            #     )
            # print(keypoint)

        images = np.hstack((color_image, depth_image))

        cv2.imshow("RealSense", images)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:

    # Stop streaming
    camera.stop_streaming()

    cv2.destroyAllWindows()

    print("End of program")