from wledcast.mapper import Mapping, controller, shape
mapping = []
for (l, d) in ((60, 16.6), (48, 14.8), (40, 12.6), (32, 10.2), (24, 8.6), (16, 6.6), (12, 4.6), (8, 2.6), (1, 0)):
    mapping += shape.ring(
        length = l,
        diameter = d,
        angle = -90)
mapping = shape.translate(mapping, x=16.6/2, y=16.6/2)
mapping = shape.map_controller('none', mapping)
mapping = Mapping(
    mapping,
    controllers={'none': controller.Controller(controller.ddp('ring.local'))})
print(mapping)
mapping.display()

# YAML mapping declaration
mapping = Mapping.load('dev-mapping-multiring.yaml')
print('Mapping', mapping)
mapping.display()

# PixelWriter
from wledcast.wled.pixel_writer import PixelWriter
pw = PixelWriter('ring.local')

# Growing square mapped to mapping
from wledcast.mapper import test
test.growing_square(mapping)
