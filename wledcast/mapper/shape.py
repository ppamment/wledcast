import yaml
from typing import List, Tuple
import math

def map_controller(controller_id, positions, force=False):
    """
    Map positions to controller_id.
    """
    # print('Mapping to', controller_id, len(list(filter(bool, (len(p) < 3 for p in positions)))))
    for i in range(len(positions)):
        if len(positions[i]) < 3:
            positions[i] = positions[i] + (controller_id,)
    return positions  # positions is now a mapping
    # mapping = ()
    # for position in positions:
    #     if force:
    #         position = position[:2]
    #     # Add controller_id if not already existing
    #     if len(position) < 3:
    #         mapping += ((position[0], position[1], controller_id),)
    # print(mapping)
    # return mapping  # a mapping is positions with controller_id

def load(filename):  # TODO: Move to module mapper
    """
    Return a mapping from the given yaml file name.
    """
    def create(item):
        fn = next(iter(item.keys()))
        args = item[fn]
        if not args:
            raise IndentationError(f'No args for "{fn}", please check indentation: {item}')
        # id = args.get('id', fn)  # TODO
        # if 'id' in args:
        #     del args['id']
        controller = args.get('controller', {})
        if 'controller' in args:
            del args['controller']
        disabled = args.get('disabled', False)
        if 'disabled' in args:
            del args['disabled']
        children = args.get('items', None)
        if 'items' in args:
            del args['items']

        if disabled:
            return []

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


# Shapes: an array of (x, y) positions.

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


# Transformers: always take `mapping` as first argument

def scale(mapping, factor=1):
    """
    Return a scaled mapping by the given factor.
    
    :param mapping: List of tuples representing the (x, y) positions of each LED.
    :param factor: Scale factor for the mapping. Default is 1 (no scaling).
    :return: Scaled mapping.
    """
    scaled_mapping = []
    for i, pixel in enumerate(mapping):
        try:
            # Pixel already mapped with controller_id
            pixel_x, pixel_y, controller_id = pixel
            scaled_mapping.append((pixel_x * factor, pixel_y * factor, controller_id))
        except ValueError:
            # Pixel not yet mapped
            pixel_x, pixel_y = pixel
            scaled_mapping.append((pixel_x * factor, pixel_y * factor))

    return scaled_mapping

def translate(mapping, x=0, y=0):  # TODO: Also rotate_centroid() and rotate_reframe() ?
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

def rotate(mapping, angle):
    """
    Return a rotated mapping by a given angle in degrees.

    :param mapping: A list of tuples representing the (x, y) position of each LED.
    :param angle: The angle to rotate the mapping, in degrees.
    :return: A rotated mapping.
    """
    angle_rad = math.radians(angle)
    cos_angle = math.cos(angle_rad)
    sin_angle = math.sin(angle_rad)

    rotated_mapping = []
    for i, pixel in enumerate(mapping):
        try: # Handle pixels with and without controller_id
            # Pixel already mapped
            pixel_x, pixel_y, controller_id = pixel
            new_x = pixel_x * cos_angle - pixel_y * sin_angle
            new_y = pixel_x * sin_angle + pixel_y * cos_angle
            rotated_mapping.append((new_x, new_y, controller_id))
        except ValueError:
            # Pixel not yet mapped
            pixel_x, pixel_y = pixel
            new_x = pixel_x * cos_angle - pixel_y * sin_angle
            new_y = pixel_x * sin_angle + pixel_y * cos_angle
            rotated_mapping.append((new_x, new_y))

    return rotated_mapping

# def rotate_adjusted(mapping, angle):
#     from wledcast.mapper import Mapping
#     mapping = rotate(mapping, angle)
#     bbox = Mapping(map_controller('none', mapping, force=True)).bbox  # FIXME: hackish
#     offset_x, offset_y = -min(bbox[0]), -min(bbox[1])
#     print(bbox, offset_x, offset_y)
#     return translate(mapping, x=offset_x, y=offset_y)

# def rotate_centroid(mapping, angle):
#     """
#     Return a mapping rotated around its centroid by a given angle in degrees.

#     :param mapping: A list of tuples representing the (x, y) position of each LED.
#     :param angle: The angle to rotate the mapping, in degrees.
#     :return: A rotated mapping.
#     """
#     # Calculate the centroid
#     n = len(mapping)
#     centroid_x = sum(x for x, y, *rest in mapping) / n
#     centroid_y = sum(y for x, y, *rest in mapping) / n

#     # Convert angle to radians
#     angle_rad = math.radians(angle)
#     cos_angle = math.cos(angle_rad)
#     sin_angle = math.sin(angle_rad)

#     rotated_mapping = []
#     for pixel in mapping:
#         try:  # Handle pixels with and without controller_id
#             # Pixel already mapped
#             pixel_x, pixel_y, controller_id = pixel
#             # Translate pixel to origin
#             trans_x = pixel_x - centroid_x
#             trans_y = pixel_y - centroid_y
#             # Rotate pixel
#             new_x = trans_x * cos_angle - trans_y * sin_angle
#             new_y = trans_x * sin_angle + trans_y * cos_angle
#             # Translate pixel back
#             new_x += centroid_x
#             new_y += centroid_y
#             rotated_mapping.append((new_x, new_y, controller_id))
#         except ValueError:
#             # Pixel not yet mapped
#             pixel_x, pixel_y = pixel
#             # Translate pixel to origin
#             trans_x = pixel_x - centroid_x
#             trans_y = pixel_y - centroid_y
#             # Rotate pixel
#             new_x = trans_x * cos_angle - trans_y * sin_angle
#             new_y = trans_x * sin_angle + trans_y * cos_angle
#             # Translate pixel back
#             new_x += centroid_x
#             new_y += centroid_y
#             rotated_mapping.append((new_x, new_y))

#     return rotated_mapping

def include(file):
    return load(file)
