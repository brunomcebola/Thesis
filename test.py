import src.intel as intel
import cv2
import numpy as np

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

camera.start_streaming()

try:
    while True:

        frames = camera.frames_queue.get()

        # Convert images to numpy arrays
        depth_image = frames[0].data
        color_image = frames[1].data


        # plot depth and color aligned

        depth_image = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

        depth_image = cv2.resize(depth_image, (640, 480))
        color_image = cv2.resize(color_image, (640, 480))

        images = np.hstack((color_image, depth_image))

        cv2.imshow("RealSense", images)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:

    # Stop streaming
    camera.stop_streaming()

    cv2.destroyAllWindows()

    print("End of program")