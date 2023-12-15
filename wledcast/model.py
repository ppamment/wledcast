from dataclasses import dataclass

from pywinbox import Size


@dataclass
class Box:
    left: int
    top: int
    width: int
    height: int

    def getSize(self) -> Size:
        return Size(self.width, self.height)

    def getTopLeft(self):
        return self.left, self.top

    def getPosition(self):
        return self.getTopLeft()
