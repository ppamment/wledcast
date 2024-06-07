# Programmatic mapping declaration:
from wledcast.mapper import generator, Mapping
mapping = generator.ring(
    length = 60,
    diameter = 15,
    angle = -90,
    reverse = False,
    crop = 0)
mapping = generator.translate(mapping, x=15/2, y=15/2)
mapping = Mapping(mapping)

# YAML mapping declaration
from wledcast.mapper import Mapping
mapping = Mapping.load('dev-mapping-clock.yaml')
print(mapping)
mapping.display()
# mapping.display('svg')

# PixelWriter
from wledcast.wled.pixel_writer import PixelWriter
pw = PixelWriter('clock.local')

# Growing square mapped to mapping
from wledcast.mapper import test
test.growing_square(mapping, pw)
