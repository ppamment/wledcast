import logging
import math
from multiprocessing import Event

import keyboard
import wx
from wxasync import WxAsyncApp

from wledcast.config import border_size, max_x, max_y, min_desktop_x, min_desktop_y
from wledcast.model import Box

logger = logging.getLogger(__name__)


def setup_keybinds(
    app: WxAsyncApp, frame: wx.Frame, capture_box: Box, stop_event: Event
) -> callable:
    logger.info("Setting up keybinds")
    aspect_ratio = frame.GetSize().GetWidth() / frame.GetSize().GetHeight()
    # Movement and resizing speeds
    speed_increment = 3
    min_speed = 1
    max_speed = 50

    # Current speed and timers for movement and resizing
    current_speed = {"move": min_speed, "resize": min_speed}

    def adjust_position(delta_x: int, delta_y: int):
        delta_x = max(
            min_desktop_x + border_size - capture_box.left,
            min(
                max_x - (capture_box.left + capture_box.width + border_size),
                delta_x,
            ),
        )
        delta_y = max(
            min_desktop_y + border_size - capture_box.top,
            min(
                max_y - (capture_box.top + capture_box.height + border_size),
                delta_y,
            ),
        )
        capture_box.left += delta_x
        capture_box.top += delta_y
        logger.info(f"Capture area: {capture_box}")
        # wx.CallAfter(frame.capturing.SetPosition, (capture_box.left, capture_box.top))
        wx.CallAfter(
            frame.SetPosition,
            (capture_box.left - border_size, capture_box.top - border_size),
        )

    def adjust_size(step: int):
        delta_w = (
            step * aspect_ratio if capture_box.width > capture_box.height else step
        )
        delta_h = (
            step / aspect_ratio if capture_box.width < capture_box.height else step
        )
        delta_w_bounded = max(
            1 - capture_box.width,
            min(delta_w, max_x - (capture_box.left + capture_box.width + border_size)),
        )
        delta_h_bounded = max(
            1 - capture_box.height,
            min(delta_h, max_y - (capture_box.top + capture_box.height + border_size)),
        )
        h_w_bounded_scale = min(delta_h_bounded / delta_h, delta_w_bounded / delta_w)
        delta_w_final = math.floor(h_w_bounded_scale * delta_w)
        delta_h_final = math.floor(h_w_bounded_scale * delta_h)
        logger.info(f"delta_w_total: {delta_w_final}, delta_h_total: {delta_h_final}")
        logger.info(f"capture_box_before: {capture_box}")
        capture_box.width += delta_w_final
        capture_box.height += delta_h_final
        logger.info(f"capture_box_after: {capture_box}")
        wx.CallAfter(
            frame.SetSize,
            (capture_box.width + border_size * 2, capture_box.height + border_size * 2),
        )
        # wx.CallAfter(frame.capturing.SetSize, (capture_box.width, capture_box.height))
        logger.info(
            f"new frame size: {(capture_box.width+border_size, capture_box.height+border_size)}"
        )

    def perform_action(action_type, key):
        # Determine the action based on the key and whether it's a move or resize action
        delta = current_speed[action_type]

        if action_type == "move":
            if key == "left":
                adjust_position(-delta, 0)
            elif key == "right":
                adjust_position(delta, 0)
            elif key == "up":
                adjust_position(0, -delta)
            elif key == "down":
                adjust_position(0, delta)
        elif action_type == "resize":
            if key in ["left", "up"]:
                adjust_size(-delta)
            elif key in ["right", "down"]:
                adjust_size(delta)

    def update_speed(action_type):
        # Accelerate the movement or resizing speed
        if current_speed[action_type] < max_speed:
            current_speed[action_type] += speed_increment

    def move_resize_handler(action_type, key):
        perform_action(action_type, key)
        update_speed(action_type)

    def on_key_release(event):
        if event.event_type == 'up' and event.name in ['left', 'right', 'up', 'down']:
            # Reset the speed for both move and resize actions
            for action_type in ['move', 'resize']:
                current_speed[action_type] = min_speed

    # Register the key release handler
    keyboard.hook(on_key_release)

    # Bind hotkeys for moving and resizing
    keyboard.add_hotkey('ctrl+left', lambda: move_resize_handler("move", "left"), suppress=True)
    keyboard.add_hotkey('ctrl+right', lambda: move_resize_handler("move", "right"), suppress=True)
    keyboard.add_hotkey('ctrl+up', lambda: move_resize_handler("move", "up"), suppress=True)
    keyboard.add_hotkey('ctrl+down', lambda: move_resize_handler("move", "down"), suppress=True)

    keyboard.add_hotkey('alt+left', lambda: move_resize_handler("resize", "left"), suppress=True)
    keyboard.add_hotkey('alt+right', lambda: move_resize_handler("resize", "right"), suppress=True)
    keyboard.add_hotkey('alt+up', lambda: move_resize_handler("resize", "up"), suppress=True)
    keyboard.add_hotkey('alt+down', lambda: move_resize_handler("resize", "down"), suppress=True)

    # Function to handle escape key
    def on_escape():
        stop_event.set()
        wx.CallAfter(keyboard.unhook_all)
        wx.CallAfter(app.ExitMainLoop)

    keyboard.add_hotkey('esc', on_escape, suppress=True)

    return lambda: keyboard.unhook_all()  # Return a callable to unhook all hotkeys
