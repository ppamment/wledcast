import dxcam
import cv2

from . import image_processor

camera = dxcam.create()

def capture_dxcam(capture_box, resolution):
    global camera
    rgb_array = camera.grab(region=(capture_box.left, capture_box.top, capture_box.left +capture_box.width, capture_box.top + capture_box.height))
    downscaled_array = cv2.resize(rgb_array, resolution, interpolation=cv2.INTER_AREA)
    rgb_array = image_processor.apply_filters_cv2(downscaled_array)

    return rgb_array