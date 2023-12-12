import asyncio
import logging
from multiprocessing import Event

from wxasync import WxAsyncApp

from wledcast import config
from wledcast.capture import capture_screen
from wledcast.model import Box, Size
from wledcast.ui import gui, keyboard, terminal
from wledcast.wled import caster, discovery

logging.basicConfig(
    level=logging.INFO if config.args.debug else logging.ERROR,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def async_main(selected_wled_host: str, led_matrix_shape: Size, capture_box: Box):
    app = WxAsyncApp(sleep_duration=0.001)

    logger.info("Starting GUI")
    border = gui.TransparentWindow(None, "wledcast", capture_box)
    border.Show()
    app.SetTopWindow(border)

    stop_event = Event()
    logger.info("Setting up keybinds")
    keyboard.setup_keybinds(app, border, capture_box, stop_event)

    logger.info("Starting teminal interface")
    terminal.start_async(caster.frame_times, capture_box, stop_event, border)

    logger.info("Starting casting")
    caster.start_async(
        selected_wled_host,
        capture_box,
        led_matrix_shape,
        config.args,
        stop_event,
        border,
    )

    await app.MainLoop()
    print("BYEBYE!")
    border.Close()
    border.Destroy()
    app.Destroy()


def main():
    if config.args.host is not None:
        selected_wled_host = config.args.host
    else:
        # Discover WLED instances
        wled_instances = discovery.discover(config.args.search_timeout)
        if len(wled_instances) == 0:
            return 1

        # Ask user which WLED instance to cast to
        selected_wled_host = (
            discovery.select_instance(wled_instances)
            if len(wled_instances) > 1
            else wled_instances[0]
        )

    if (
        config.args.output_resolution is not None
        and type(config.args.output_resolution.split("x")) is tuple
    ):
        w, h = config.args.output_resolution.split("x")
        led_matrix_shape = Size(int(w), int(h))
    else:
        # Determine the shape of the LED pixel matrix from WLED
        led_matrix_shape = discovery.get_matrix_shape(selected_wled_host)

    logger.info(
        f"Matrix shape: width={led_matrix_shape.width}, height={led_matrix_shape}"
    )

    # get the coordinates to capture, they are stored in a mutable Box which can be modified by the UI
    window = capture_screen.select_window(
        monitor=config.args.monitor, title=config.args.title
    )
    logger.info(f"Selected {window}")

    # get the capture coordinates: dict[left, top, width, height]
    capture_box = capture_screen.get_capture_box(window, led_matrix_shape)
    logger.info(
        f"Capture area: top={capture_box.top}, left={capture_box.left}, width={capture_box.width}, height={capture_box.height}"
    )
    asyncio.run(async_main(selected_wled_host, led_matrix_shape, capture_box))


if __name__ == "__main__":
    main()
