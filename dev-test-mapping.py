# YAML mapping declaration
from wledcast.mapper import Mapping, source
mapping = Mapping.load('dev-mapping.yaml')
print(mapping)
mapping.display()
# mapping.display('svg')
# import sys; sys.exit()

# Growing square mapped to mapping
source.run(
    fps=60,
    mapping=mapping,
    # generator=source.growing_square(side_size=max(mapping.size)))
    # generator=source.image_zoom('/Users/damien/Downloads/rubik-rotating.gif', size=mapping.size))
    generator=source.filter(source.screen(to_size=mapping.size)))

# Growing square mapped to mapping (deprecated)
# from wledcast.mapper import test
# test.growing_square(mapping)
# # test.image_zoom(mapping, '/Users/damien/Downloads/rubik-rotating.gif')
