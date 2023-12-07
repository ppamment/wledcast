import keyboard
import threading
import wx

from .model import Box
from .user_interface import get_virtual_desktop_size



def setup_keybinds(
    frame: wx.Frame, capture_box: Box, stop_event: threading.Event
) -> callable:
    max_x, max_y = get_virtual_desktop_size()
    aspect_ratio = frame.GetSize().GetWidth() / frame.GetSize().GetHeight()
    # Movement and resizing speeds
    speed_increment = 3
    min_speed = 2
    max_speed = 50

    # Current speed and timers for movement and resizing
    current_speed = {"move": min_speed, "resize": min_speed}

    def adjust_position(delta_x: int, delta_y: int):
        x, y = frame.GetPosition()
        width, height = frame.GetSize()
        new_x = max(0, min(max_x - width, x + delta_x))
        new_y = max(0, min(max_y - height, y + delta_y))
        capture_box.left += new_x - x
        capture_box.top += new_y - y
        wx.CallAfter(frame.SetPosition, (new_x, new_y))

    def adjust_size(delta_w, delta_h):
        width, height = frame.GetSize()
        if delta_w != 0:
            new_width = max(10, min(max_x, width + delta_w))
            new_height = max(10, min(max_y, int(new_width / aspect_ratio)))
        else:
            new_height = max(10, min(max_x, height + delta_h))
            new_width = max(10, min(max_y, int(new_height * aspect_ratio)))
        capture_box.width += new_width - width
        capture_box.height += new_height - height
        wx.CallAfter(frame.SetSize, (new_width, new_height))

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
            if key == "left":
                adjust_size(-delta, 0)
            elif key == "right":
                adjust_size(delta, 0)
            elif key == "up":
                adjust_size(0, -delta)
            elif key == "down":
                adjust_size(0, delta)

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
            wx.CallAfter(frame.Close)

    keyboard.hook(on_key_event)

    return on_key_event