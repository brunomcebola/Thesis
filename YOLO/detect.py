" This is a test file to test the functionality of the RealSenseCamera class and the YOLO model."

import cv2
import numpy as np
from ultralytics import YOLO

import src.intel as intel

# Load model
model = YOLO("yolov8n.pt")

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
    intel.StreamType.COLOR,
)

camera.start_streaming()

try:
    while True:

        frames = camera.frames_queue.get()

        depth_image = frames[0].data
        color_image = frames[1].data

        # img2 = np.zeros((depth_image.shape[0], depth_image.shape[1], 3))
        # img2[:, :, 0] = depth_image  # same value in each channel
        # img2[:, :, 1] = depth_image
        # img2[:, :, 2] = depth_image

        # print(np.min(img2))
        # print(np.min(color_image))

        depth_image = cv2.applyColorMap(
            cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET
        )
        results = model.predict(source=depth_image)

        depth_image = cv2.resize(depth_image, (640, 480))
        color_image = cv2.resize(color_image, (640, 480))

        for box in results[0].boxes:
            depth_image = cv2.rectangle(
                depth_image,
                (int(box.xyxy[0][0]), int(box.xyxy[0][1])),
                (int(box.xyxy[0][2]), int(box.xyxy[0][3])),
                (0, 0, 255),
                2,
            )

        images = np.hstack((color_image, depth_image))

        cv2.imshow("RealSense", images)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:

    # Stop streaming
    camera.stop_streaming()

    cv2.destroyAllWindows()

    print("End of program")
