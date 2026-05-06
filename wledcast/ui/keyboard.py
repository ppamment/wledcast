import logging
import math
from multiprocessing import Event

import wx
from wxasync import WxAsyncApp
from pynput import keyboard

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

    # Function to handle escape key
    def on_escape():
        stop_event.set()
        if hotkey_listener:
            wx.CallAfter(hotkey_listener.stop)
        if key_listener:
            wx.CallAfter(key_listener.stop)
        wx.CallAfter(app.ExitMainLoop)

    # Track currently pressed modifier keys
    ctrl_pressed = False
    alt_pressed = False

    # Handle key press including repeats for acceleration behavior
    def on_key_press(key):
        nonlocal ctrl_pressed, alt_pressed
        
        try:
            # Track modifier keys
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                ctrl_pressed = True
            elif key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                alt_pressed = True
            elif key == keyboard.Key.esc:
                on_escape()
                return
            
            # Handle directional keys with modifiers - this triggers on every repeat!
            direction_map = {
                keyboard.Key.left: "left",
                keyboard.Key.right: "right", 
                keyboard.Key.up: "up",
                keyboard.Key.down: "down"
            }
            
            if key in direction_map:
                direction = direction_map[key]
                
                if ctrl_pressed:
                    move_resize_handler("move", direction)
                    return
                elif alt_pressed:
                    move_resize_handler("resize", direction)
                    return
                    
        except Exception as e:
            # Ignore errors in key handling
            pass
        

    def on_key_release(key):
        nonlocal ctrl_pressed, alt_pressed
        
        try:
            # Track modifier keys
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                ctrl_pressed = False
            elif key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                alt_pressed = False
            
            # Reset speed when arrow keys are released
            if key in [keyboard.Key.left, keyboard.Key.right, keyboard.Key.up, keyboard.Key.down]:
                for action_type in ['move', 'resize']:
                    current_speed[action_type] = min_speed
                    
        except Exception as e:
            # Ignore errors in key release handling
            pass

    # Use simple escape hotkey for non-directional keys
    hotkeys = {
        '<esc>': on_escape,
    }

    # Set up global hotkey listener for escape
    try:
        hotkey_listener = keyboard.GlobalHotKeys(hotkeys)
        hotkey_listener.start()
        logger.info("Global hotkeys enabled")
    except Exception as e:
        logger.warning(f"Global hotkeys failed to initialize: {e}")
        hotkey_listener = None

    # Set up key listener for directional keys and acceleration
    try:
        key_listener = keyboard.Listener(
            on_press=on_key_press,
            on_release=on_key_release,
            suppress=False,
        )
        key_listener.start()
    except Exception as e:
        logger.warning(f"Key listener failed: {e}")
        key_listener = None

    # Return cleanup function
    def cleanup():
        try:
            if hotkey_listener:
                hotkey_listener.stop()
            if key_listener:
                key_listener.stop()
        except Exception:
            pass

    return cleanup
