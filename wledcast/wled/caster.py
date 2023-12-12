import logging
import time
from argparse import Namespace
from collections import deque
from threading import Thread, Event

from wledcast.capture import capture_screen, image_processor
from wledcast.model import Box, Size
from wledcast.wled.pixel_writer import PixelWriter

logger = logging.getLogger(__name__)

# Initialize the pixel writer
frame_times = deque(maxlen=10)
def cast(writer: PixelWriter, capture_box: Box, led_matrix_shape: Size, args: Namespace, stop_event: Event):
    while not stop_event.is_set():
        start = time.time()
        # Capture the selected screen
        rgb_array = capture_screen.capture(
            capture_box, led_matrix_shape, args.capture_method
        )
        if rgb_array is None:
            logger.info("**Dropped frame**".ljust(40))
            continue
        if args.live_preview:
            image_processor.show_preview(rgb_array, led_matrix_shape)
        # Update the LED matrix via WLED in real-time
        writer.update_pixels(rgb_array)
        end = time.time()
        dt = end - start
        # Frame rate limiter
        if dt < 1 / args.fps:
            time.sleep(1 / args.fps - dt)

        frame_times.append(end)
    return 0

def create_thread(host: str, capture_box: Box, led_matrix_shape: Size, args: Namespace, stop_event: Event):
    writer = PixelWriter(host)
    return Thread(target=cast, args=(writer, capture_box, led_matrix_shape, args, stop_event))