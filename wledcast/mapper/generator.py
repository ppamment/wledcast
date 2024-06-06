from typing import List, Tuple
import math

def matrix(width: int, height: int, firstled: str = 'topleft') -> List[Tuple[int, int]]:
    """
    Generate a mapping for an LED matrix without serpentine pattern.

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
        # # FIXME: `radius +` offsets the bbox to ((0,0), (x,y)), but the center is no more (0,0)
        # (radius + radius * math.cos(math.radians(angle + i * angle_increment)),
        #  radius + radius * math.sin(math.radians(angle + i * angle_increment)))
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



# Example usage
if __name__ == "__main__":
    width = 5
    height = 3
    firstled = 'topleft'
    led_matrix = matrix(width, height, firstled)
    print('Matrix', led_matrix)

    length = 12
    diameter = 10
    crop = 3
    firstled = 'topleft'
    reverse = True
    led_ring = ring(length, diameter, crop, firstled, reverse)
    print('Ring', led_ring)
