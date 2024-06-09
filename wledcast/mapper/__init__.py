"""
The mapper maps the pixels of a 2D image on a Mapping of 2D pixels (LEDs, etc).

Example:
```
mapping = Mapping.load('dev-mapping.yaml')
print(mapping.render_ascii())

img = Image.open('image.gif').resize((32,32)))
mapping.write(np.array(img))
```
"""

from . import shape, controller
import numpy as np
from PIL import Image
import cairosvg
from typing import List, Tuple, Optional
import io

class Mapping:
    def __init__(self, mapping: List[Tuple[int, int]], controllers: dict = {}):
        """
        Initialize the LEDMapper with a given mapping.

        :param mapping: A list of tuples representing the ordered positions of each pixel
                        (x, y) in the LED display.
        """
        self.controllers = controllers
        if not 'none' in controllers:
            self.controllers['none'] = controller.Controller(write = lambda pixels: None)
        for position in mapping:
            x, y, controller_id = position
            self.controllers[controller_id].positions.append((x,y))
            # FIXME: Ensure it is a np.ndarray() for performance ?
    
    def __str__(self):
        return f'Mapping: {sum(len(c.positions) for id, c in self.controllers.items())} pixels, size={self.size}, bbox={self.bbox}'

    @property
    def mapping(self) -> Tuple[int, int]:
        # FIXME: For dev leap: update all users of self.mapping and remove this property.
        from itertools import chain
        return chain(*(c.positions for c in self.controllers.values()))

    @property
    def bbox(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        Calculate the bounding box of the mapping.

        :return: A tuple containing the minimum and maximum coordinates of the bounding box ((min_x, min_y), (max_x, max_y)).
        """
        xs, ys = zip(*self.mapping)
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        return (min_x, min_y), (max_x, max_y)

    @property
    def size(self) -> Tuple[int, int]:
        """
        Calculate the size of the mapping.

        :return: A tuple containing the size of the mapping (width, height).
        """
        bbox = self.bbox
        width = bbox[1][0] - bbox[0][0] + 1
        height = bbox[1][1] - bbox[0][1] + 1
        return width, height

    def write(self, img):
        """
        Write image to physical mapping.
        """
        for id, controller in self.controllers.items():
            print(f'Writing {len(controller.positions)} pixels to', id, controller.write)
            controller.write(self.map(img, controller.positions))

    def map(self, img: np.ndarray, positions) -> np.ndarray:
        """
        Map the pixels from the image to the LED display based on the mapping.

        :param img: A numpy array representing the image.
        :return: A list of RGB tuples in the order defined by the mapping.
        """
        height, width, _ = img.shape
        mapped_pixels = []
        for (x, y) in positions:
            # Ensure the coordinates are within the image bounds
            if 0 <= x < width and 0 <= y < height:
                r, g, b = img[int(y), int(x)]
                mapped_pixels.append((r, g, b))
            else:
                # Default to black if the coordinate is out of bounds
                mapped_pixels.append((0, 0, 0))

        return np.array(mapped_pixels)

    def render_ascii(self, scale: float = 3, scalex: float = 2, scaley: float = 1, rgb_array: Optional[np.ndarray] = None):
        """
        Creates and prints an ASCII string representing the mapping LEDs on screen.

        :param scalex: A scaling factor for the x-axis.
        :param scaley: A scaling factor for the y-axis. If None, the aspect ratio is maintained.
        """
        scalex = scalex * scale
        scaley = scaley * scale

        # Find the bounding box of the mapping
        bbox = self.bbox
        width, height = self.size

        # Scale the width and height
        width = int(width * scalex)
        height = int(height * scaley)

        # Create an empty canvas
        canvas = [[' ' for _ in range(width)] for _ in range(height)]

        # Offset to translate positions to canvas coordinates
        x_offset = -bbox[0][0]
        y_offset = -bbox[0][1]

        # Place each LED on the canvas
        for index, (x, y) in enumerate(self.mapping):
            canvas_y = int((y + y_offset) * scaley)
            canvas_x = int((x + x_offset) * scalex)
            # Place the first digit of the index at the position of the LED
            if 0 <= canvas_y < height and 0 <= canvas_x < width:
                label = str(index)  # FIXME: wrong index (see render_svg() using per controller)
                for i, char in enumerate(label):
                    if rgb_array is not None:  # If rgb_array is provided, colorize the pixel according to the index
                        try:
                            color = tuple(rgb_array[index])
                            char = char if sum(color)>0 else "." #f"\033[38;2;{color[0]};{color[1]};{color[2]}m{char}\033[0m"
                        except IndexError:
                            pass
                    try:
                        canvas[canvas_y][canvas_x+i] = char
                    except IndexError:
                        pass

        # Convert the canvas to a string and print it
        ascii_art = '\n'.join(''.join(row) for row in canvas)
        return ascii_art

    def render_svg(self, scale: float = 1) -> str:
        """
        Render the mapping as an SVG string with scaling for distances between circles.

        :param scale: Scale factor for spacing between the circles.
        :return: An SVG string representing the LEDs.
        """
        # Determine the size of the SVG canvas
        max_x = max(x for x, y in self.mapping)
        max_y = max(y for x, y in self.mapping)

        # Circle properties
        circle_radius = 15  # Radius of the circle
        font_size = 10  # Font size for the text
        spacing = 2 * circle_radius * scale
        controller_labels = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

        # Create the SVG string
        svg_parts = [
            '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
            f'width="{(max_x + 1) * spacing}" height="{(max_y + 1) * spacing}">'
        ]

        for j, controller in enumerate(self.controllers.values()):
            for i, (x, y) in enumerate(controller.positions):
                prefix = controller_labels[j]
                cx = x * spacing + circle_radius
                cy = y * spacing + circle_radius
                svg_parts.append(
                    f'<circle cx="{cx}" cy="{cy}" r="{circle_radius}" fill="lightblue" stroke="black" stroke-width="1" />'
                )
                svg_parts.append(
                    f'<text x="{cx}" y="{cy}" font-size="{font_size}" text-anchor="middle" '
                    f'alignment-baseline="middle" fill="black">{prefix}{i}</text>'
                )

        svg_parts.append('</svg>')
        return "\n".join(svg_parts)

    def display(self, format:str='ascii', scale:float = 1, rgb_array: Optional[np.ndarray] = None):
        """
        Display the mapping.
        """
        if format == 'ascii':
            print(self.render_ascii(rgb_array=rgb_array))
        elif format == 'svg':
            svg_data = self.render_svg(scale=scale)
            png_data = cairosvg.svg2png(bytestring=svg_data.encode('utf-8'))  # Load the PNG data into a PIL image
            image = Image.open(io.BytesIO(png_data))
            image.show()  # Show the image
        else:
            raise ValueError("Invalid value for firstled. Choose from 'ascii' or 'svg'")

    @staticmethod
    def load(filename, controllers = {}):
        """
        Return an object Mapping containing the mapping specified in filename (YAML).
        """
        mapping = shape.load(filename)
        mapping = shape.map_controller('none', mapping)  # default unmapped positions to controller id 'none'
        for id, loaded_controller in controller.load(filename).items():
            controllers[id] = loaded_controller
        return Mapping(mapping, controllers)
