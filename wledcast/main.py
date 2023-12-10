import argparse
import logging
import threading
import time
from collections import deque

from . import image_processor
from . import keyboard_handler
from . import screen_capture
from . import terminal_interface
from . import user_interface as ui
from . import wled_discovery
from .pixel_writer import PixelWriter
import wx

logging.basicConfig(
    filename="debug.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def get_arguments():
    default_fps = 30
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--fps", type=int, default=default_fps, help="Target FPS")
    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Cast window whose title contains this string",
    )
    parser.add_argument(
        "--search-timeout",
        type=int,
        default=3,
        help="Seconds to wait for WLED instance discovery",
    )
    parser.add_argument(
        "--output-resolution",
        type=str,
        default=None,
        help="Specify the output resolution rather than discovering from WLED",
    )
    parser.add_argument(
        "--live-preview",
        default=False,
        help="Show a live preview of the WLED output  the computer screen",
        action="store_true",
    )
    parser.add_argument(
        "--dxcam",
        default=False,
        action="store_true",
        help="Use DirectX Capture (faster, but only for Windows and primary monitor)",
    )
    parser.add_argument(
        "--host",
        default=None,
        type=str,
        help="Specify the IP address of the WLED instance to cast to",
    )
    parser.add_argument(
        '--monitor',
        nargs='?',
        const=-1,
        type=int,
    )
    args = parser.parse_args()
    return args


def main():
    args = get_arguments()
    if args.dxcam:
        from dxcam_capture import capture_dxcam
        capture_function = capture_dxcam
    else:
        capture_function = None

    if args.host is not None:
        selected_wled_host = args.host
    else:
        # Discover WLED instances
        wled_instances = wled_discovery.discover(args.search_timeout)
        if len(wled_instances) == 0:
            return 1

        # Ask user which WLED instance to cast to
        selected_wled_host = (
            wled_discovery.select_instance(wled_instances)
            if len(wled_instances) > 1
            else wled_instances[0]
        )

    # Determine the shape of the LED pixel matrix from WLED
    led_matrix_shape = wled_discovery.get_matrix_shape(selected_wled_host)
    # get the coordinates to capture, use a list to make it mutable
    window = screen_capture.select_window(monitor=args.monitor, title=args.title)

    # get the capture coordinates: dict[left, top, width, height]
    capture_box = screen_capture.get_capture_box(window, led_matrix_shape)

    app = wx.App()
    ui_capture_border = ui.TransparentWindow(
        parent=None,
        title="wledcast",
        size=capture_box.getSize(),
        pos=capture_box.getPosition(),
        capture_box=capture_box,
    )
    ui_capture_border.Show()

    # Initialize the pixel writer
    frame_times = deque(maxlen=10)



    def cast():
        while not stop_event.is_set():
            start = time.time()
            # Capture the selected screen
            rgb_array = screen_capture.capture_window_content(
                capture_box, led_matrix_shape, capture_function
            )
            if rgb_array is None:
                print("**Dropped frame**".ljust(40))
                continue
            if args.live_preview:
                image_processor.show_preview(rgb_array, led_matrix_shape)
            # Update the LED matrix via WLED in real-time
            pixel_writer.update_pixels(rgb_array)
            end = time.time()
            dt = end - start
            # Frame rate limiter
            if dt < 1 / args.fps:
                time.sleep(1 / args.fps - dt)

            frame_times.append(end)
        return 0

    stop_event = threading.Event()
    pixel_writer = PixelWriter(selected_wled_host)
    cast_thread = threading.Thread(target=cast, daemon=True)
    terminal_thread = threading.Thread(
        target=terminal_interface.start_terminal_ui,
        args=(image_processor.config, frame_times, capture_box, stop_event),
        daemon=True,
    )
    keyboard_handler.setup_keybinds(ui_capture_border, capture_box, stop_event)

    try:
        terminal_thread.start()
        cast_thread.start()

        app.MainLoop()
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        stop_event.set()
        print("Shutting down...")
        cast_thread.join()
        terminal_thread.join()


if __name__ == "__main__":
    main()
