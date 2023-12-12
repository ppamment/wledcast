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

    def getCenter(self):
        return self.left + self.width // 2, self.top + self.height // 2

    def getTopLeft(self):
        return self.left, self.top

    def getPosition(self):
        return self.getTopLeft()

    def contract(self, delta: int):
        return Box(
            self.left + delta,
            self.top + delta,
            self.width - delta*2,
            self.height - delta*2
        )
