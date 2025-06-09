import logging
from typing import Union

import numpy as np
import pymonctl
import pywinctl

from wledcast.capture import capture_mss
from wledcast.config import border_size, max_x, max_y
from wledcast.model import Box

logger = logging.getLogger(__name__)


def select_from_list(
    items: list[Union[pywinctl.Window, pymonctl.Monitor]], description: str
) -> Union[pywinctl.Window, pymonctl.Monitor]:
    if len(items) == 1:
        logger.info(
            f"Only one {description} found: {getattr(items[0], description)}. Selecting it."
        )
        return items[0]

    for i, item in enumerate(items):
        print(f"{i + 1}: {getattr(item, description)}")
    try:
        choice = int(input("Enter the number of the item to capture: "))
        choice = choice - 1
    except ValueError:
        print("Invalid input. Please try again.")
        return select_from_list(items, description)
    if choice < 0 or choice >= len(items):
        print("Invalid selection. Please try again.")
        return select_from_list(items, description)
    logger.info(f"Selected {getattr(items[choice], description)}")
    return items[choice]


def select_window(
    monitor: int = None, title: str = None
) -> Union[pywinctl.Window, pymonctl.Monitor]:
    if monitor is not None:
        monitors = pymonctl.getAllMonitors()
        if 0 <= monitor < len(monitors):
            logger.info(f"Using monitor {monitor}")
            return monitors[monitor]
        elif monitor == -1 and len(monitors) > 0:
            return select_from_list(monitors, "name")
        else:
            logger.warning(f"Invalid monitor index {monitor}, found {len(monitors)} monitors")
    # Get the list of open windows
    windows: list[pywinctl.Window] = pywinctl.getAllWindows()
    logger.info(f"Found {len(windows)} windows total")

    if title:
        logger.info(f"Filtering by title: {title}")
        windows_matching_title = [
            window
            for window in windows
            if title in window.title and not window.isActive
        ]
        logger.info(f"Found {len(windows)} matching windows")
        if len(windows_matching_title) >= 1:
            logger.info(
                f"Selecting from {len(windows_matching_title)} windows matching title: {title}"
            )
            return select_from_list(windows_matching_title, "title")

    windows = [
        window
        for window in windows
        if not window.isMinimized
        and (not hasattr(window, "_parent") or not window.getParent())
        and window.title
    ]
    logger.info(f"Found {len(windows)} top level windows windows")

    if len(windows) >= 1:
        logger.info(f"Selecting from {len(windows)} windows")
        return select_from_list(windows, "title")

    monitors = pymonctl.getAllMonitors()
    logger.info(f"Found 0 visible windows, selecting from {len(monitors)} monitors")
    return select_from_list(monitors, "name")


def get_capture_box(
    window: Union[pywinctl.Window, pymonctl.Monitor], target_resolution
) -> Box:
    # Get the client rectangle of the window
    rect = (
        window.getClientFrame() if isinstance(window, pywinctl.Window) else window.rect
    )
    logger.info(f"Client rect: {rect}")

    client_box = Box(
        left=max(border_size, rect.left),
        top=max(border_size, rect.top),
        width=min(
            max_x - max(border_size, rect.left) - border_size,
            rect.right - max(border_size, rect.left) - border_size,
        ),
        height=min(
            max_y - max(border_size, rect.top) - border_size,
            rect.bottom - max(border_size, rect.top) - border_size,
        ),
    )

    # crop the largest area in client_rect that matches the aspect ratio of resolution
    target_aspect_ratio = target_resolution.width / target_resolution.height

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


def capture(
    window_box: Box
) -> Union[np.ndarray, None]:
    try:
        rgb_array = capture_mss.capture(window_box)

        return rgb_array
    except Exception as e:
        return None
