from wledcast.wled.pixel_writer import PixelWriter
import numpy as np
import time
import sys

pw = PixelWriter('clock.local')
# pw = PixelWriter('wled-matrix.local')
rgb_array = np.tile((0,0,255), (105, 1, 3))
pw.update_pixels(np.array(rgb_array))

from wledcast.mapper import LEDMapper, generator
mapping = generator.ring(
    length = 60,
    diameter = 16.6,
    angle = -90,
    reverse = False,
    crop = 0)
mapping2 = generator.matrix(
    width = 8,
    height = 8,
    firstled = 'topleft')
print('Mapping', mapping)
led_mapper = LEDMapper(mapping)
print('Bbox', led_mapper.get_bbox())
print('Size', led_mapper.get_size())
scale = 8
led_mapper.render_ascii(scalex=scale, scaley=scale/2)

# rgb_array = np.full((105, 1, 3), (0,0,0))
# pw.update_pixels(np.array(rgb_array))
while True:
    start = time.time()
    for j in range(3):
        color = [255, 255, 255]
        color[j] = 0
        for i in range(0, 17+2+1):
            array_size = (i, i, 3)
            # print(i, array_size)
            rgb_array = np.full(array_size, color, dtype=np.uint8)
            rgb_array = led_mapper.map_pixels(rgb_array)
            led_mapper.render_ascii(scalex=scale, scaley=scale/2, rgb_array=rgb_array)
            pw.update_pixels(np.array(rgb_array))
            spent = time.time()-start
            time.sleep(max(0, 1/10))
            print(f'fps = {1/spent} - {spent}s')
