# YAML mapping declaration
from wledcast.mapper import shape, Mapping
mapping = Mapping.load('dev-mapping.yaml')
print('Mapping', mapping)
mapping.display()

# Image zoom mapped to mapping
from wledcast.mapper import test
test.image_zoom(mapping, '/Users/damien/Downloads/rubik-rotating.gif')
# test.image_zoom(mapping, '/Users/damien/Documents/xLights/ASSETS/Fratel-logo.jpg')
