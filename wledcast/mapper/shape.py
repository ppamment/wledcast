import yaml
from typing import List, Tuple
import math

def map_controller(controller_id, positions):
    # print('Mapping to', controller_id, len(list(filter(bool, (len(p) < 3 for p in positions)))))
    for i in range(len(positions)):
        if len(positions[i]) < 3:
            positions[i] = positions[i] + (controller_id,)
    return positions  # positions is now a mapping

def load(filename):
    """
    Return a mapping from the given yaml file name.
    """
    def create(item):
        fn = next(iter(item.keys()))
        args = item[fn]
        if not args:
            raise IndentationError(f'No args for "{fn}", please check indentation: {item}')
        controller = args.get('controller', {}) #, {'id': 'none'})
        if 'controller' in args:
            del args['controller']
        name = args.get('name', fn)
        if 'name' in args:
            del args['name']
        children = args.get('items', None)
        if 'items' in args:
            del args['items']

        positions = []
        if children:  # tranformer
            positions_children = []
            for child in children:
                positions_children += create(child)
            positions += create_transformer(fn, args, positions_children)
        else:  # shape
            positions += create_shape(fn, args)
        if controller:
            mapping = map_controller(controller['id'], positions)
        else:
            mapping = positions

        return mapping

    def create_transformer(fn, args, mapping):
        return globals()[fn](mapping=mapping, **args)

    def create_shape(fn, args):
        return globals()[fn](**args)

    with open(filename, 'r') as file:
        yaml_data = yaml.safe_load(file)

    mapping = []
    if 'mapping' in yaml_data:
        mapping_data = yaml_data['mapping']
        for item in mapping_data:
            mapping += create(item)

    return mapping


def matrix(width: int, height: int, firstled: str = 'topleft') -> List[Tuple[int, int]]:
    """
    Generate a mapping for an 2D LED matrix.

    :param width: The width of the matrix.
    :param height: The height of the matrix.
    :param firstled: The position of the first LED. Options are 'topleft', 'topright', 'bottomleft', 'bottomright'.
    :return: A list of tuples representing the position of each LED in the matrix.
    """
    mapping = []

    if firstled == 'topleft':
        for y in range(height):
            row = [(x, y) for x in range(width)]
            mapping.extend(row)
    elif firstled == 'topright':
        for y in range(height):
            row = [(x, y) for x in range(width-1, -1, -1)]
            mapping.extend(row)
    elif firstled == 'bottomleft':
        for y in range(height-1, -1, -1):
            row = [(x, y) for x in range(width)]
            mapping.extend(row)
    elif firstled == 'bottomright':
        for y in range(height-1, -1, -1):
            row = [(x, y) for x in range(width-1, -1, -1)]
            mapping.extend(row)
    else:
        raise ValueError("Invalid value for firstled. Choose from 'topleft', 'topright', 'bottomleft', 'bottomright'.")

    return mapping


def ring(length: int, diameter: int, angle: int = 0, reverse: bool = False, crop:int = 0) -> List[Tuple[float, float]]:
    """
    Generate a mapping for an LED ring.

    :param length: The number of LEDs in the circle.
    :param diameter: The diameter of the ring (unit agnostic).
    :param angle: The angle at which to start placing LEDs (in degrees).
                  Default is 0, starting at the top.
    :param reverse: Whether to reverse the order of the LEDs (counter-clockwise direction).
    :return: A list of tuples representing the (x, y) position of each LED in the ring.
    """
    radius = diameter / 2
    angle_increment = 360 / length  # Angle between LEDs

    # Generate the positions of the LEDs
    positions = [
        (radius * math.cos(math.radians(angle + i * angle_increment)),
         radius * math.sin(math.radians(angle + i * angle_increment)))
        for i in range(length)
    ]

    # Crop the positions to create an arc
    positions = positions[:length - crop]

    # Reverse the positions if needed
    if reverse:
        positions.reverse()

    return positions

def translate(mapping, x=0, y=0):
    """
    Return a translated mapping (apply offset x and y on positions).
    """
    translated_mapping = []
    for i, pixel in enumerate(mapping):
        try: # TODO: Factorize this in a helper
            # Pixel already mapped
            pixel_x, pixel_y, controller_id = pixel
            translated_mapping.append((pixel_x+x, pixel_y+y, controller_id))
        except ValueError:
            # Pixel not yet mapped
            pixel_x, pixel_y = pixel
            translated_mapping.append((pixel_x+x, pixel_y+y))

    return translated_mapping

def include(file):
    return load(file)

# Example usage
if __name__ == "__main__":
    width = 5
    height = 3
    firstled = 'topleft'
    led_matrix = matrix(width, height, firstled)
    # print('Matrix', led_matrix)

    length = 12
    diameter = 10
    crop = 3
    firstled = 'topleft'
    reverse = True
    led_ring = ring(length, diameter, crop, firstled, reverse)
    # print('Ring', led_ring)
