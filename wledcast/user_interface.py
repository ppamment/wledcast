import wx

from .model import Box


def get_virtual_desktop_size() -> (int, int):
    total_width = 0
    total_height = 0
    for i in range(wx.Display.GetCount()):
        display = wx.Display(i)
        rect = display.GetGeometry()
        total_width += rect.GetWidth()
        total_height = max(total_height, rect.GetHeight())
    return total_width, total_height


class TransparentWindow(wx.Frame):
    border_size = 5

    def __init__(self, parent, title, pos, size, capture_box: Box):
        self.capture_box = capture_box
        pos = (pos[0] - self.border_size, pos[1] - self.border_size)
        size = (size[0] + 2 * self.border_size, size[1] + 2 * self.border_size)
        super().__init__(
            parent,
            title=title,
            style=wx.FRAME_SHAPED | wx.STAY_ON_TOP,
            pos=pos,
            size=size,
        )
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)  # Needed for shaped windows
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)  # Resize event
        self.CreateShapeBitmap(size)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnMouseUp)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightMouseDown)
        self.Bind(wx.EVT_RIGHT_UP, self.OnMouseUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMove)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnter)

        self.dragging = False
        self.resizing = False
        self.dragStartPos = None
        self.max_x, self.max_y = get_virtual_desktop_size()

    def OnMouseDown(self, event):
        self.CaptureMouse()
        self.dragging = True
        self.dragStartPos = event.GetPosition()

    def OnRightMouseDown(self, event):
        self.CaptureMouse()
        self.resizing = True
        self.dragStartPos = event.GetPosition()

    def OnMouseUp(self, event):
        if self.HasCapture():
            self.ReleaseMouse()
        self.dragging = False
        self.resizing = False

    def OnMouseMove(self, event):
        if self.dragging:
            x, y = self.ClientToScreen(event.GetPosition())
            newpos = (
                max(0, min(self.max_x - self.GetSize()[0], x - self.dragStartPos.x)),
                max(0, min(self.max_y - self.GetSize()[1], y - self.dragStartPos.y)),
            )
            self.capture_box.left = newpos[0] + self.border_size
            self.capture_box.top = newpos[1] + self.border_size
            self.Move(newpos)
        elif self.resizing:
            x, y = self.ClientToScreen(event.GetPosition())
            newsize = (
                int(
                    self.GetSize()[0]
                    / self.GetSize()[1]
                    * max(1, y - self.GetPosition().y)
                ),
                max(1, y - self.GetPosition().y),
            )
            self.capture_box.width = newsize[0] - 2 * self.border_size
            self.capture_box.height = newsize[1] - 2 * self.border_size
            self.SetSize(newsize)

    def OnMouseLeave(self, event):
        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))

    def OnMouseEnter(self, event):
        self.SetCursor(wx.Cursor(wx.CURSOR_SIZENWSE))

    def CreateShapeBitmap(self, size):
        # Create a bitmap where the border is opaque and the center is transparent
        bitmap = wx.Bitmap(size[0], size[1], 32)
        dc = wx.MemoryDC(bitmap)
        dc.SetBackground(
            wx.Brush(wx.Colour(255, 0, 0, 1), wx.BRUSHSTYLE_TRANSPARENT)
        )  # Fully transparent brush
        dc.Clear()
        dc.SetPen(
            wx.Pen(wx.Colour(255, 0, 0, 1), self.border_size, wx.PENSTYLE_SOLID)
        )  # Red pen for the border
        dc.SetBrush(
            wx.Brush(wx.Colour(255, 0, 0, 1), wx.BRUSHSTYLE_TRANSPARENT)
        )  # Fully transparent brush
        dc.DrawRectangle(0, 0, size[0], size[1])
        del dc  # Need to delete the DC before setting shape
        self.SetShape(wx.Region(bitmap, wx.Colour(0, 0, 0, 0)))

    def OnPaint(self, event):
        # Custom drawing for the border
        dc = wx.PaintDC(self)
        width, height = self.GetClientSize()
        dc.SetBrush(wx.TRANSPARENT_BRUSH)  # Transparent brush for the interior
        pen = wx.Pen(wx.Colour(255, 0, 0, 1), self.border_size)
        dc.SetPen(pen)  # Red pen for the border
        dc.DrawRectangle(0, 0, width, height)
        pen.Destroy()

    def OnSize(self, event):
        # Recreate the shape bitmap when the window is resized
        self.CreateShapeBitmap(event.GetSize())
        event.Skip()




