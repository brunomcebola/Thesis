import cv2
import intel

camera = intel.Camera(
    intel.CameraType.D435i,
    intel.CameraMode.Depth,
    intel.CameraResolution.Depth1280x720,
    intel.CameraFrameRate.Depth30,
)