import numpy as np
from typing import List, Tuple, Optional
from PIL import Image
import cairosvg
import io

class LEDMapper:
    def __init__(self, mapping: List[Tuple[int, int]]):
        """
        Initialize the LEDMapper with a given mapping.

        :param mapping: A list of tuples representing the ordered positions of each pixel
                        (x, y) in the LED display.
        """
        self.mapping = mapping

    def map_pixels(self, img: np.ndarray) -> np.ndarray:
        """
        Map the pixels from the image to the LED display based on the mapping.

        :param img: A numpy array representing the image.
        :return: A list of RGB tuples in the order defined by the mapping.
        """
        height, width, _ = img.shape
        mapped_pixels = []
        for (x, y) in self.mapping:
            # Ensure the coordinates are within the image bounds
            if 0 <= x < width and 0 <= y < height:
                r, g, b = img[int(y), int(x)]
                mapped_pixels.append((r, g, b))
            else:
                # Default to black if the coordinate is out of bounds
                mapped_pixels.append((0, 0, 0))

        return np.array(mapped_pixels)

    def get_bbox(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        Calculate the bounding box of the mapping.
        

        :return: A tuple containing the minimum and maximum coordinates of the bounding box ((min_x, min_y), (max_x, max_y)).
        """
        xs, ys = zip(*self.mapping)
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        return (min_x, min_y), (max_x, max_y)

    def get_size(self) -> Tuple[int, int]:
        """
        Calculate the size of the mapping.

        :return: A tuple containing the size of the mapping (width, height).
        """
        bbox = self.get_bbox()
        width = bbox[1][0] - bbox[0][0] + 1
        height = bbox[1][1] - bbox[0][1] + 1
        return width, height

    def render_ascii(self, scalex: float = 1, scaley: Optional[float] = None, rgb_array: Optional[np.ndarray] = None):
        """
        Creates and prints an ASCII string representing the mapping LEDs on screen.

        :param scalex: A scaling factor for the x-axis.
        :param scaley: A scaling factor for the y-axis. If None, the aspect ratio is maintained.
        """
        if scaley is None:
            scaley = scalex

        # Find the bounding box of the mapping
        bbox = self.get_bbox()
        width, height = self.get_size()

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
                label = str(index)
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
        print(ascii_art)

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

        # Create the SVG string
        svg_parts = [
            '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
            f'width="{(max_x + 1) * spacing}" height="{(max_y + 1) * spacing}">'
        ]

        for i, (x, y) in enumerate(self.mapping):
            cx = x * spacing + circle_radius
            cy = y * spacing + circle_radius
            svg_parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{circle_radius}" fill="lightblue" stroke="black" stroke-width="1" />'
            )
            svg_parts.append(
                f'<text x="{cx}" y="{cy}" font-size="{font_size}" text-anchor="middle" '
                f'alignment-baseline="middle" fill="black">{i}</text>'
            )

        svg_parts.append('</svg>')
        return "\n".join(svg_parts)

    def display_svg(self, scale:float = 1):
        """
        Display the SVG output using PIL.Image.show().
        """
        svg_data = self.render_svg(scale=scale)
        png_data = cairosvg.svg2png(bytestring=svg_data.encode('utf-8'))

        # Load the PNG data into a PIL image
        image = Image.open(io.BytesIO(png_data))

        # Show the image
        image.show()

# Example usage
if __name__ == "__main__":
    from PIL import Image

    # # Load an image and convert it to a numpy array
    # img = Image.open('path_to_your_image.jpg')
    # img_array = np.array(img)
    rgb_array = np.tile((0,0,255), (128, 128))

    # Define the mapping of the LED strip/ring/matrix
    mapping = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0),
               (0, 1), (1, 1), (2, 1), (3, 1), (4, 1)]

    # Create an LEDMapper instance
    led_mapper = LEDMapper(mapping)

    # Map the pixels
    rgb_array = led_mapper.map_pixels(rgb_array)
