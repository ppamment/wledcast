import logging

import mss
import numpy as np
from PIL import Image

from wledcast.model import Box

logger = logging.getLogger(__name__)


def capture(window_box: Box) -> np.ndarray:
    # Use mss to capture the image
    with mss.mss() as cap:
        img = cap.grab(vars(window_box))
        image = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
        # image.resize(resolution, Image.Resampling.BOX)
        rgb_array = np.array(image)

        return rgb_array
