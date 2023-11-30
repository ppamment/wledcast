import time
import threading

import win32gui

import wled_discovery
import screen_capture
import user_interface as ui
from pixel_writer import PixelWriter

target_fps = 25

def main():
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
    keyboard_listener = ui.init_keybindings(gui_hwnd, capture_rect)
    # Initialize the pixel writer
    pixel_writer = PixelWriter(selected_wled_host)

    stop_casting_event = threading.Event()
    frame_times = []
    def cast():
        with keyboard_listener:
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
                if dt < 1/target_fps:
                    time.sleep(1/target_fps - dt)

                frame_times.append(end)
                if len(frame_times) == 10:
                    # print FPS every 10 frames: 10 / time for last 10 frames
                    print(f"\rFPS: {10 / (frame_times[-1] - frame_times[0]):.2f}. Casting area: ({capture_rect[0]}, {capture_rect[1]}) to ({capture_rect[2]}, {capture_rect[3]}", end='')
                    # reset the frame times
                    frame_times.clear()

    cast_thread = threading.Thread(target=cast)
    cast_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nScreen casting stopped by user...")

    stop_casting_event.set()
    win32gui.DestroyWindow(gui_hwnd)

if __name__ == "__main__":
    main()
