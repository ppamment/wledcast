from dataclasses import dataclass

@dataclass
class Box:
    left: int
    top: int
    width: int
    height: int

    def getSize(self):
        return self.width, self.height

    def getCenter(self):
        return self.left + self.width // 2, self.top + self.height // 2

    def getTopLeft(self):
        return self.left, self.top

    def getPosition(self):
        return self.getTopLeft()
