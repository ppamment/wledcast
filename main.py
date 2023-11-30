import time

import win32gui

import wled_discovery
import screen_capture
import user_interface as ui
from pixel_writer import PixelWriter


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

    gui_hwnd = ui.create_border_window(capture_rect)
    keyboard_listener = ui.init_keybindings(gui_hwnd, capture_rect)

    # Initialize the pixel writer
    pixel_writer = PixelWriter(selected_wled_host)

    try:
        while True:
            msg = win32gui.PumpWaitingMessages()
                win32gui.TranslateMessage(msg)
                win32gui.DispatchMessage(msg)
            else:
                break

            start_time = time.time()

            # Capture the selected screen
            rgb_array = screen_capture.capture_window_content(capture_rect, led_matrix_shape)
            if rgb_array is None:
                continue
            # Update the LED matrix via WLED in real-time
            pixel_writer.update_pixels(rgb_array)

            end_time = time.time()

            elapsed_time = end_time - start_time
            # Delay to cap the update rate to 40Hz, accounting for the time taken by the operations
            time.sleep(max(1/20- elapsed_time, 0))
            # Update the terminal output for FPS
            fps_output = f"\rFPS: {1 / (time.time() - start_time):.2f}. Time for frame: {elapsed_time * 1000:.2f}ms"
            print(fps_output.ljust(80))
            capture_output = f"\rCapturing aread: ({capture_rect[0]}, {capture_rect[1]}) to ({capture_rect[2]}, {capture_rect[3]})"
            print(capture_output.ljust(80))
            print(f"\033[4A", end="")
    except KeyboardInterrupt:
        print("\nScreen casting stopped by user...")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

    win32gui.DestroyWindow(gui_hwnd)
    keyboard_listener.stop()
    keyboard_listener.join()

if __name__ == "__main__":
    main()
