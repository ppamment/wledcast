from typing import Union

from . import image_processor
from .model import Box

import mss
import numpy as np
import pywinctl
from PIL import Image


def select_window(title=None) -> pywinctl.Window:
    # Get the list of open windows
    windows: list[pywinctl.Window] = pywinctl.getAllWindows()
    windows = [
        window
        for window in windows
        if not window.isMinimized and not window.getParent() and window.title
    ]

    if title:
        windows = [window for window in windows if title in window.title]
    if len(windows) == 1:
        return windows[0]
    # Ask the user to select a window from a list numbered from 1 upwards
    for i, window in enumerate(windows):
        print(f"{i + 1}: {window.title}")
    choice = int(input("Enter the number of the window to capture: ")) - 1
    if choice < 0 or choice >= len(windows):
        print("Invalid selection. Please try again.")
        return select_window()

    return windows[choice]


def get_capture_box(window: pywinctl.Window, target_resolution) -> Box:
    # Get the client rectangle of the window
    client_box = Box(
        **{
            "left": window.box.left,
            "top": window.box.top,
            "width": window.box.width,
            "height": window.box.height,
        }
    )

    # crop the largest area in client_rect that matches the aspect ratio of resolution
    target_aspect_ratio = target_resolution[0] / target_resolution[1]

    # Calculate the aspect ratio of the client rectangle
    client_aspect_ratio = client_box.width / client_box.height

    # Check if the aspect ratio of the client rectangle matches the aspect ratio of the resolution
    if client_aspect_ratio > target_aspect_ratio:
        # Crop the width of the client rectangle to match the aspect ratio of the resolution
        new_width = int(client_box.height * target_aspect_ratio)
        center_x = client_box.left + (client_box.width // 2)
        client_box.left = center_x - (new_width // 2)
        client_box.width = new_width
    else:
        # Crop the height of the client rectangle to match the aspect ratio of the resolution
        new_height = int(client_box.width / target_aspect_ratio)
        center_y = client_box.top + (client_box.height // 2)
        client_box.top = center_y - (new_height // 2)
        client_box.height = new_height

    return client_box


def capture_window_content(
    window_box: Box, resolution: tuple[int, int], capture_function: Union[callable, None] = None
) -> Union[np.ndarray, None]:
    try:
        if capture_function is not None:
            return capture_function(window_box, resolution)
        # noinspection PyTypeChecker
        return capture_mss(window_box, resolution)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        return None


def capture_mss(window_box: Box, resolution):
    # Use mss to capture the image
    with mss.mss() as sct:
        sct_img = sct.grab(vars(window_box))
        image = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        image = image.resize(resolution, Image.Resampling.BOX)
        # image = image_processor.apply_filters_pillow(image)
        rgb_array = np.array(image)
        rgb_array = image_processor.apply_filters_cv2(
            rgb_array
        )  # apply filters after resizing
        return rgb_array
