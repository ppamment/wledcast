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
