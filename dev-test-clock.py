# Programmatic mapping declaration:
from wledcast.mapper import shape, controller, Mapping
mapping = shape.ring(
    length = 60,
    diameter = 15,
    angle = -90,
    reverse = False,
    crop = 0)
mapping = shape.translate(mapping, x=15/2, y=15/2)
mapping = shape.map_controller('none', mapping)
mapping = Mapping(
    mapping,
    controllers={'none': controller.Controller(controller.ddp('clock.local'))})

# YAML mapping declaration
from wledcast.mapper import Mapping
mapping = Mapping.load('dev-mapping-clock.yaml')
print(mapping)
mapping.display()
# mapping.display('svg')

# Growing square mapped to mapping
from wledcast.mapper import test
test.growing_square(mapping)
