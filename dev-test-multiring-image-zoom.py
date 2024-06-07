# Programmatic mapping declaration:
from wledcast.mapper import generator, Mapping
mapping = generator.matrix(width=0, height=0)
for (l, d) in ((60, 16.6), (48, 14.8), (40, 12.6), (32, 10.2), (24, 8.6), (16, 6.6), (12, 4.6), (8, 2.6), (1, 0)):
    mapping += generator.ring(
        length = l,
        diameter = d,
        angle = -90,
        reverse = False,
        crop = 0)
# Translate mapping (apply offset on positions)
for i, pixel in enumerate(mapping):
    x, y = pixel
    offset = 16.6/2
    mapping[i] = (offset+x, offset+y)
mapping = Mapping(mapping)

# YAML mapping declaration
mapping = Mapping.load('dev-mapping-multiring.yaml')
print('Mapping', mapping)
mapping.display()

# PixelWriter
from wledcast.wled.pixel_writer import PixelWriter
pw = PixelWriter('ring.local')

# Image zoom mapped to mapping
from wledcast.mapper import test
test.image_zoom(mapping, pw, '/Users/damien/Downloads/rubik-rotating.gif')
# test.image_zoom(mapping, pw, '/Users/damien/Documents/xLights/ASSETS/Fratel-logo.jpg')