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

from PIL import Image
img = Image.open('/Users/damien/Documents/xLights/ASSETS/Fratel-logo.jpg')
width, height = img.size

while True:
    crops = list(range(1, int(max(width, height)/2), 1)) + [max(width, height)/2]
    for crop in crops + list(reversed(crops)):
        start = time.time()
        border = (width/2-crop, height/2-crop, width/2+crop, height/2+crop)
        rgb_array = np.array(
            img.crop(border).resize((8,8)))
        rgb_array = led_mapper.map_pixels(rgb_array)
        led_mapper.render_ascii(scalex=scale, scaley=scale/2, rgb_array=rgb_array)
        pw.update_pixels(np.array(rgb_array))
        time.sleep(max(0, 1/(crop**.75)-(time.time()-start)))
        # time.sleep(max(0, 1/10-(time.time()-start)))
        spent = time.time()-start
        print(f'fps = {1/spent} - {spent}s - {border}')

# img.crop(border).show()
