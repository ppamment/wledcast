import numpy as np
from typing import List, Tuple, Optional

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

        :return: A tuple containing two tuples, representing the top-left and bottom-right corners of the bounding box.
        """
        if not self.mapping:
            return ((0, 0), (0, 0))

        xs, ys = zip(*self.mapping)
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        return ((min_x, min_y), (max_x, max_y))

    def get_size(self) -> Tuple[int, int]:
        """
        Calculate the size of the mapping.

        :return: A tuple representing the width and height of the self.mapping.
        """
        if not self.mapping:
            return (0, 0)

        bbox = self.get_bbox()
        width = bbox[1][0] - bbox[0][0] + 1
        height = bbox[1][1] - bbox[0][1] + 1

        return (width, height)

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


class Canvas:
    def __init__(self, width:int, height:int):
        pass


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
