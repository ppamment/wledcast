import time
import threading
import argparse

import asciimatics.exceptions
import asciimatics.exceptions as as_exc

import win32gui

from pixel_writer import PixelWriter
import screen_capture
import user_interface as ui
import wled_discovery
from image_processor import config

default_fps = 1000

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--fps", type=int, default=default_fps, help="Target FPS")
    args = parser.parse_args()
    # Discover WLED instances
    wled_instances = wled_discovery.discover(2)

    # Ask user which WLED instance to cast to
    selected_wled_host = wled_discovery.select_instance(wled_instances)
    # Determine the shape of the LED pixel matrix from WLED
    led_matrix_shape = wled_discovery.get_matrix_shape(selected_wled_host)
    # get the coordinates to capture, use a list to make it mutable
    hwnd = screen_capture.select_window()

    # get the capture coordinates: [left, top, right, bottom]
    capture_rect = screen_capture.get_capture_rect(hwnd, led_matrix_shape)
    # draw a border around the captured area on screen
    gui_hwnd = ui.create_border_window(capture_rect)
    stop_casting_event = threading.Event()
    keyboard_listener = ui.init_keybindings(gui_hwnd, capture_rect, stop_casting_event)
    # Initialize the pixel writer
    pixel_writer = PixelWriter(selected_wled_host)

    try:
        frame_times = []
        def cast():
            while not stop_casting_event.is_set():
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

        cast_thread = threading.Thread(target=cast)
        terminal_thread = threading.Thread(target=ui.start_terminal_ui, args=(config, frame_times, capture_rect))
        terminal_thread.start()
        cast_thread.start()
        keyboard_listener.start()


        while True:
            msg = win32gui.GetMessage(None, 0, 0)
            if msg[0] > 0:
                win32gui.TranslateMessage(msg[1])
                win32gui.DispatchMessage(msg[1])
            time.sleep(0.01)
    except KeyboardInterrupt:
        stop_casting_event.set()
        print("\nScreen casting stopped by user...")
    except as_exc.StopApplication:
        stop_casting_event.set()
        print("\nScreen casting stopped by user...")
    finally:
        win32gui.DestroyWindow(gui_hwnd)
        keyboard_listener.stop()
        stop_casting_event.set()
        terminal_thread.join()
        cast_thread.join()
        keyboard_listener.join()


if __name__ == "__main__":
    main()
