import logging

import dxcam

from wledcast.model import Box

logger = logging.getLogger(__name__)


camera = dxcam.create()


def capture(capture_box: Box):
    global camera
    rgb_array = camera.grab(
        region=(
            capture_box.left,
            capture_box.top,
            capture_box.left + capture_box.width,
            capture_box.top + capture_box.height,
        )
    )
    return rgb_array
