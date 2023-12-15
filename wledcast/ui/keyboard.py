import logging
import math
from multiprocessing import Event

import keyboard
import wx
from wxasync import WxAsyncApp

from wledcast.config import border_size, max_x, max_y
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
            border_size - capture_box.left,
            min(
                max_x - (capture_box.left + capture_box.width + border_size),
                delta_x,
            ),
        )
        delta_y = max(
            border_size - capture_box.top,
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

    def on_key_event(event):
        key = event.name
        if key in ["left", "right", "up", "down"]:
            ctrl = keyboard.is_pressed("ctrl")
            alt = keyboard.is_pressed("alt")

            if event.event_type == "down":
                action_type = "move" if ctrl else "resize" if alt else None
                if action_type:
                    perform_action(action_type, key)
                    update_speed(action_type)
            elif event.event_type == "up":
                # Stop the action and reset speed for both move and resize
                for action_type in ["move", "resize"]:
                    current_speed[action_type] = (
                        min_speed if action_type == "move" else min_speed
                    )

        elif key == "esc" and event.event_type == "down":
            stop_event.set()
            wx.CallAfter(keyboard.unhook_all)
            wx.CallAfter(app.ExitMainLoop)

    keyboard.hook(on_key_event)

    return on_key_event
