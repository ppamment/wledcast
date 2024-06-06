from wledcast.wled.pixel_writer import PixelWriter
import numpy as np
import time
import sys

pw = PixelWriter('wled-matrix.local')

from wledcast.mapper import LEDMapper, generator
mapping = generator.matrix(
    width = 8,
    height = 8,
    firstled = 'topleft')
print('Mapping', mapping)
led_mapper = LEDMapper(mapping)
print('Bbox', led_mapper.get_bbox())
print('Size', led_mapper.get_size())
scale = 8
led_mapper.render_ascii(scalex=scale, scaley=scale/2)

while True:
    for j in range(3):
        color = [255, 255, 255]
        color[j] = 0
        for i in range(0, 8+1):
            start = time.time()
            array_size = (i, i, 3)
            rgb_array = np.full(array_size, color, dtype=np.uint8)
            rgb_array = led_mapper.map_pixels(rgb_array)
            led_mapper.render_ascii(scalex=scale, scaley=scale/2, rgb_array=rgb_array)
            pw.update_pixels(np.array(rgb_array))
            time.sleep(max(0, 1/60-(time.time()-start)))
            spent = time.time()-start
            print(f'fps = {1/spent} - {spent}s')
