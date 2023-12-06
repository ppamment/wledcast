import time
import threading
import argparse
from collections import deque
import logging
import sys

import win32gui

from pixel_writer import PixelWriter
import screen_capture
import user_interface as ui
import wled_discovery
from image_processor import config

logging.basicConfig(filename='debug.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
default_fps = 30

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--fps", type=int, default=default_fps, help="Target FPS")
    parser.add_argument("--title", type=str, default=None, help="Cast window whose title contains this string")
    args = parser.parse_args()
    # Discover WLED instances
    wled_instances = wled_discovery.discover(2)

    # Ask user which WLED instance to cast to
    selected_wled_host = wled_discovery.select_instance(wled_instances) if len(wled_instances) > 1 else wled_instances[0]
    # Determine the shape of the LED pixel matrix from WLED
    led_matrix_shape = wled_discovery.get_matrix_shape(selected_wled_host)
    # get the coordinates to capture, use a list to make it mutable
    hwnd = screen_capture.select_window(title=args.title)

    # get the capture coordinates: [left, top, right, bottom]
    capture_rect = screen_capture.get_capture_rect(hwnd, led_matrix_shape)
    # draw a border around the captured area on screen
    gui_hwnd = ui.create_border_window(capture_rect)
    stop_event = threading.Event()
    keyboard_listener = ui.init_keybindings(gui_hwnd, capture_rect, stop_event)
    # Initialize the pixel writer
    pixel_writer = PixelWriter(selected_wled_host)

    try:
        frame_times = deque(maxlen=10)
        def cast():
            while not stop_event.is_set():
                start = time.time()
                # Capture the selected screen
                rgb_array = screen_capture.capture_window_content(capture_rect, led_matrix_shape)
                if rgb_array is None:
                    print("**Dropped frame**".ljust(40))
                    continue
                # Update the LED matrix via WLED in real-time
                pixel_writer.update_pixels(rgb_array)
                end = time.time()
                dt = end - start
                # Chill if we're moving too fast
                if dt < 1/args.fps:
                    time.sleep(1/args.fps - dt)

                frame_times.append(end)

            win32gui.PostQuitMessage(0)

        cast_thread = threading.Thread(target=cast, daemon=True)
        terminal_thread = threading.Thread(target=ui.start_terminal_ui, args=(config, frame_times, capture_rect, stop_event), daemon=True)
        terminal_thread.start()
        cast_thread.start()
        keyboard_listener.start()

    except KeyboardInterrupt:
        print("\nScreen casting stopped by user...")
    except Exception as e:
        print(f"Unexpected error: {e}")

    def cleanup():
        win32gui.DestroyWindow(gui_hwnd)
        keyboard_listener.stop()
        cast_thread.join()
        terminal_thread.join()
        keyboard_listener.join()


    shutting_down = False
    while True:
        if stop_event.is_set() and not shutting_down:
            shutting_down = True
            print("Shutting down...")
            cleanup()
        msg = win32gui.GetMessage(None, 0, 0)
        if msg[0] > 0:
            win32gui.TranslateMessage(msg[1])
            win32gui.DispatchMessage(msg[1])
        elif msg[0] == 0:
            break
        time.sleep(0.1)

if __name__ == "__main__":
    main()
