import numpy as np
from PIL import Image
import time

def growing_square(mapping, pixel_writer, fps=60):
    square_size = 1+round(max(mapping.size))
    while True:
        for j in range(3):
            color = [255, 255, 255]
            color[j] = 0
            for i in (*range(0, square_size), *reversed(range(0, square_size))):
                start = time.time()
                array_size = (i, i, 3)
                rgb_array = np.full(array_size, color, dtype=np.uint8)
                rgb_array = mapping.map(rgb_array)
                mapping.display(rgb_array=rgb_array)
                pixel_writer.update_pixels(np.array(rgb_array))
                time.sleep(max(0, 1/fps))
                spent = time.time()-start
                print(f'fps = {1/spent} - {spent}s')

def image_zoom(mapping, pixel_writer, image_filename):
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
                rgb_array = np.array(
                    img.crop(border).resize(int(x) for x in mapping.size))
                rgb_array = mapping.map(rgb_array)
                mapping.display(rgb_array=rgb_array)
                pixel_writer.update_pixels(np.array(rgb_array))
                time.sleep(max(0, 1/(crop**.75)-(time.time()-start)))
                # time.sleep(max(0, 1/10-(time.time()-start)))
                spent = time.time()-start
                print(f'fps = {1/spent} - {spent}s - {border}')
            except (EOFError, ValueError):
                forward = not forward
    # img.crop(border).show()
