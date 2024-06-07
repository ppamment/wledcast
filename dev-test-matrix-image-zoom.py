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
img = Image.open('/Users/damien/Downloads/rubik-rotating.gif')
# img = Image.open('/Users/damien/Documents/xLights/ASSETS/Fratel-logo.jpg')
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
                img.crop(border).resize((8,8)))
            rgb_array = led_mapper.map_pixels(rgb_array)
            led_mapper.render_ascii(scalex=scale, scaley=scale/2, rgb_array=rgb_array)
            pw.update_pixels(np.array(rgb_array))
            time.sleep(max(0, 1/(crop**.75)-(time.time()-start)))
            # time.sleep(max(0, 1/10-(time.time()-start)))
            spent = time.time()-start
            print(f'fps = {1/spent} - {spent}s - {border}')
        except (EOFError, ValueError):
            forward = not forward

# img.crop(border).show()
