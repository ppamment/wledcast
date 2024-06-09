# YAML mapping declaration
from wledcast.mapper import Mapping
mapping = Mapping.load('dev-mapping.yaml')
print(mapping)
mapping.display()
# mapping.display('svg')
# import sys; sys.exit()

# Growing square mapped to mapping
from wledcast.mapper import test
test.growing_square(mapping)
# test.image_zoom(mapping, '/Users/damien/Downloads/rubik-rotating.gif')
