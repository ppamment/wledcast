import logging
import threading

from wledcast import config
from wledcast.capture import capture_screen, image_processor
from wledcast.ui import gui, keyboard, terminal
from wledcast.wled import discovery, caster
import wx

logging.basicConfig(level=logging.INFO if config.args.debug else logging.ERROR, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


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

    # Determine the shape of the LED pixel matrix from WLED
    led_matrix_shape = discovery.get_matrix_shape(selected_wled_host)
    logger.info(f"Matrix shape: width={led_matrix_shape.width}, height={led_matrix_shape}")

    # get the coordinates to capture, they are stored in a mutable Box which can be modified by the UI
    window = capture_screen.select_window(monitor=config.args.monitor, title=config.args.title)
    logger.info(f"Selected {window}")

    # get the capture coordinates: dict[left, top, width, height]
    capture_box = capture_screen.get_capture_box(window, led_matrix_shape)
    logger.info(f"Capture area: top={capture_box.top}, left={capture_box.left}, width={capture_box.width}, height={capture_box.height}")

    app = wx.App()
    border = gui.TransparentWindow(None, "wledcast", capture_box)
    border.Show()

    stop_event = threading.Event()
    cast_thread = caster.create_thread(selected_wled_host, capture_box, led_matrix_shape, config.args, stop_event)
    terminal_thread = terminal.create_thread(image_processor.filters, caster.frame_times, capture_box, stop_event)
    keyboard.setup_keybinds(border, capture_box, stop_event)

    try:
        terminal_thread.start()
        cast_thread.start()

        app.MainLoop()
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1
    finally:
        print("Shutting down...")
        stop_event.set()
        cast_thread.join()
        terminal_thread.join()

if __name__ == "__main__":
    main()