# Programmatic mapping declaration:
from wledcast.mapper import shape, controller, Mapping
mapping = shape.matrix(
    width = 8,
    height = 8,
    firstled = 'topleft')
mapping = shape.map_controller('none', mapping)
mapping = Mapping(
    mapping,
    controllers={'none': controller.Controller(controller.ddp('wled-matrix.local'))})
# mapping.controllers['none'] = controller.Controller(controller.ddp('wled-matrix.local'))
print(mapping)
# An image to display
import numpy as np
i = max(mapping.size)
array_size = (i, i, 3)
rgb_array = np.full(array_size, (255, 255, 255), dtype=np.uint8)
# Display using Controller
mapping.controllers['none'].write(rgb_array)
# Display using PixelWriter
from wledcast.wled.pixel_writer import PixelWriter
pw = PixelWriter('wled-matrix.local')
pw.update_pixels(rgb_array)
import time
time.sleep(1)


# YAML mapping declaration
mapping = Mapping.load('dev-mapping-matrix-8x8.yaml', controllers={'none': controller.Controller(controller.ddp('wled-matrix.local'))})
print('Mapping', mapping)
mapping.display()
# Growing square mapped to mapping
from wledcast.mapper import test
test.growing_square(mapping)
