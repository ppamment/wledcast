# YAML mapping declaration
from wledcast.mapper import Mapping
mapping = Mapping.load('dev-mapping.yaml')
print(mapping)
mapping.display()
# mapping.display('svg')
import sys; sys.exit()

# PixelWriter
from wledcast.wled.pixel_writer import PixelWriter
pw = PixelWriter('clock.local')

# Growing square mapped to mapping
from wledcast.mapper import test
test.growing_square(mapping, pw)
