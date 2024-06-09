import numpy as np
from PIL import Image
import time

def run(generator, mapping, fps=30, display=True):
    """
    Run the generator and map frames on mapping at fps.
    """
    for frame in generator:
        start = time.time()
        if display:
            mapping.display(rgb_array=mapping.map(frame, mapping.mapping))  # FIXME: make out what's happening really
        mapping.write(frame)
        time.sleep(max(0, 1/fps-(time.time()-start)))
        spent = time.time()-start
        print(f'fps = {1/spent} ({fps}), {spent}s')
        # yield frame

def filter(generator,  # FIXME: filter() should be appliable per controller, or better: per shape
        sharpen=0.1,   #        because each controller/shape can have different physical LEDs with their own bias
        saturation=1.0,
        brightness=0.5,
        contrast=2.0,
        balance_r=0.75,
        balance_g=0.8,
        balance_b=0.85
    ):
    """
    Filter generator frames according arguments.
    """
    from wledcast.capture import image_processor
    filters = {
        "sharpen": sharpen,
        "saturation": saturation,
        "brightness": brightness,
        "contrast": contrast,
        "balance_r": balance_r,
        "balance_g": balance_g,
        "balance_b": balance_b
    }
    for frame in generator:
        yield image_processor.apply_filters_cv2(frame, filters)

def screen(to_size, monitor=0):
    """
    Generate frames from monitor (screencast).
    """
    from wledcast.capture import capture_screen
    from wledcast.model import Box, Size
    import cv2
    to_size = Size(*(round(x) for x in to_size))
    window = capture_screen.select_window(monitor=monitor)  # FIXME: monitor=config.args.monitor, title=config.args.title
    capture_box = capture_screen.get_capture_box(window, to_size)
    while True:
        rgb_array = capture_screen.capture(capture_box)
        rgb_array = cv2.resize(rgb_array, to_size, interpolation=cv2.INTER_AREA)
        yield rgb_array

def growing_square(side_size):
    """
    Generate hues of a growing square.
    """
    side_size = round(side_size)
    while True:
        for j in range(3):
            color = [255, 255, 255]
            color[j] = 0
            for i in (*range(0, side_size), *reversed(range(0, side_size))):
                array_size = (i, i, 3)
                yield np.full(array_size, color, dtype=np.uint8)

def image_zoom(image_filename, size):
    """
    Generate frames from image that is zooming in and out.
    """
    size = tuple(int(x) for x in size)  # TODO: Use shape.resize()
    img = Image.open(image_filename)
    width, height = img.size
    crops = list(range(1, int(min(width, height)/2), 1)) + [min(width, height)/2]
    crops = [(min(width, height)-100)/2]
    i = 0
    forward = True
    while True:
        for crop in crops + list(reversed(crops)):
            i = i + (1 if forward else -1)
            try:
                img.seek(i)
                start = time.time()
                border = tuple(int(x) for x in (width/2-crop, height/2-crop, width/2+crop, height/2+crop))
                yield np.array(img.crop(border).resize(size))
            except (EOFError, ValueError):
                forward = not forward
            # img.crop(border).show()

# def resize(generator, rgb_array, size):  # TODO: Implement and move this to shape.resize()
#     size = tuple(int(x) for x in size)
#     yield np.array(img.crop(border).resize(size))
