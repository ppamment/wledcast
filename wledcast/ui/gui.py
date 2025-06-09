import logging

import wx

from wledcast.config import border_size, max_x, max_y
from wledcast.model import Box

logger = logging.getLogger(__name__)


class TransparentWindow(wx.Frame):
    def __init__(self, parent, title, capture_box: Box):
        self.capture_box = capture_box
        self.capture_box.left = capture_box.left + border_size // 2
        self.capture_box.top = capture_box.top + border_size // 2
        adjusted_width = min(
            max_x - self.capture_box.left - 2 * border_size, capture_box.width
        )
        adjusted_height = min(
            max_y - self.capture_box.top - 2 * border_size, capture_box.height
        )
        adjustment_factor = min(
            adjusted_width / capture_box.width, adjusted_height / capture_box.height
        )
        adjusted_width = int(capture_box.width * adjustment_factor)
        adjusted_height = int(capture_box.height * adjustment_factor)
        self.capture_box.width = adjusted_width
        self.capture_box.height = adjusted_height
        pos = (capture_box.left - border_size, capture_box.top - border_size)
        size = (
            capture_box.width + 2 * border_size,
            capture_box.height + 2 * border_size,
        )
        logger.info(f"Capture box (adjusted): {capture_box}")
        logger.info(f"TransparentWindow: {Box(*pos, *size)}")
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

    def OnMouseDown(self, event):
        try:
            self.CaptureMouse()
        except Exception as e:
            logger.info(f"Failed to capture mouse: {e}")
            return
        
        try:
            self.dragging = True
            self.dragStartPos = event.GetPosition()
        except Exception as e:
            logger.info(f"Error after mouse capture: {e}")
            # Ensure mouse is released if we captured it but failed after
            try:
                if self.HasCapture():
                    self.ReleaseMouse()
            except:
                pass

    def OnRightMouseDown(self, event):
        try:
            self.CaptureMouse()
        except Exception as e:
            logger.info(f"Failed to capture mouse: {e}")
            return
        
        try:
            self.resizing = True
            self.dragStartPos = event.GetPosition()
        except Exception as e:
            logger.info(f"Error after mouse capture: {e}")
            # Ensure mouse is released if we captured it but failed after
            try:
                if self.HasCapture():
                    self.ReleaseMouse()
            except:
                pass

    def OnMouseUp(self, event):
        # Always try to release mouse first, then handle other cleanup
        try:
            if self.HasCapture():
                self.ReleaseMouse()
        except Exception as e:
            logger.info(f"Failed to release mouse: {e}")
        finally:
            # Always reset state regardless of mouse release success
            self.dragging = False
            self.resizing = False

    def OnMouseMove(self, event):
        if self.dragging:
            x, y = self.ClientToScreen(event.GetPosition())
            newpos = (
                max(0, min(max_x - self.GetSize().width, x - self.dragStartPos.x)),
                max(0, min(max_y - self.GetSize().height, y - self.dragStartPos.y)),
            )
            self.capture_box.left = newpos[0] + border_size
            self.capture_box.top = newpos[1] + border_size
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
            self.capture_box.width = newsize[0] - 2 * border_size
            self.capture_box.height = newsize[1] - 2 * border_size
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
            wx.Pen(wx.Colour(255, 0, 0, 1), border_size, wx.PENSTYLE_SOLID)
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
        pen = wx.Pen(wx.Colour(255, 0, 0, 1), border_size)
        dc.SetPen(pen)  # Red pen for the border
        dc.DrawRectangle(0, 0, width, height)
        pen.Destroy()

    def OnSize(self, event):
        # Recreate the shape bitmap when the window is resized
        self.CreateShapeBitmap(event.GetSize())
        event.Skip()

    def Destroy(self):
        # Ensure mouse is released before destroying window
        try:
            if self.HasCapture():
                self.ReleaseMouse()
        except:
            pass  # Ignore any errors during cleanup
        return super().Destroy()
