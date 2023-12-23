import asyncio
import logging
import time
from argparse import Namespace
from collections import deque
from multiprocessing import Event, Pool, Value

from wx import Frame
from wxasync import StartCoroutine

from wledcast import config
from wledcast.capture import capture_screen, image_processor
from wledcast.model import Box, Size
from wledcast.wled.pixel_writer import PixelWriter

logger = logging.getLogger(__name__)

# Initialize the pixel writer
frame_times = deque(maxlen=20)

async def async_sleep(duration):
    await asyncio.get_running_loop().run_in_executor(None, time.sleep, duration)


def cast(
    writer: PixelWriter,
    capture_box: Box,
    led_matrix_shape: Size,
    capture_method: str,
    live_preview: bool,
    filters: dict,
):
    # Capture the selected screen
    rgb_array = capture_screen.capture(capture_box, capture_method)
    if rgb_array is None:
        logger.info("**Dropped frame**".ljust(40))
        return
    # Process the image
    rgb_array = image_processor.process_raw_image(rgb_array, led_matrix_shape, filters)
    if live_preview:
        image_processor.show_preview(rgb_array, led_matrix_shape)
    # Update the LED matrix via WLED in real-time
    writer.update_pixels(rgb_array)

    return time.time()


def start_async(
    host: str,
    capture_box: Box,
    led_matrix_shape: Size,
    args: Namespace,
    stop_event: Event,
    window: Frame,
):
    writer = PixelWriter(host)
    async def loop():
        with Pool(args.workers) as pool:
            while not stop_event.is_set():
                pool.apply_async(
                    cast,
                    args=(
                        writer,
                        capture_box,
                        led_matrix_shape,
                        "mss",
                        args.live_preview,
                        config.filters,
                    ),
                    callback=lambda x: frame_times.append(x) if x is not None else None,
                )
                await async_sleep(1 / args.fps) # asyncio.sleep is only accurate to ~15ms!

    return StartCoroutine(loop(), window)
