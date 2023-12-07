import threading
import time
from collections import deque

import keyboard
import screen_capture
import wx
from asciimatics.event import KeyboardEvent
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.widgets import Button, Frame, Label, Layout, Text


def get_virtual_desktop_size():
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

    def __init__(self, parent, title, pos, size, capture_box: screen_capture.Box):
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


def setup_keybinds(
    frame: wx.Frame, capture_box: screen_capture.Box, stop_event: threading.Event
) -> callable:
    max_x, max_y = get_virtual_desktop_size()
    aspect_ratio = frame.GetSize().GetWidth() / frame.GetSize().GetHeight()
    # Movement and resizing speeds
    speed_increment = 3
    min_speed = 2
    max_speed = 50

    # Current speed and timers for movement and resizing
    current_speed = {"move": min_speed, "resize": min_speed}

    def adjust_position(delta_x: int, delta_y: int):
        x, y = frame.GetPosition()
        width, height = frame.GetSize()
        new_x = max(0, min(max_x - width, x + delta_x))
        new_y = max(0, min(max_y - height, y + delta_y))
        capture_box.left += new_x - x
        capture_box.top += new_y - y
        wx.CallAfter(frame.SetPosition, (new_x, new_y))

    def adjust_size(delta_w, delta_h):
        width, height = frame.GetSize()
        if delta_w != 0:
            new_width = max(10, min(max_x, width + delta_w))
            new_height = max(10, min(max_y, int(new_width / aspect_ratio)))
        else:
            new_height = max(10, min(max_x, height + delta_h))
            new_width = max(10, min(max_y, int(new_height * aspect_ratio)))
        capture_box.width += new_width - width
        capture_box.height += new_height - height
        wx.CallAfter(frame.SetSize, (new_width, new_height))

    def perform_action(action_type, key):
        # Determine the action based on the key and whether it's a move or resize action
        delta = current_speed[action_type]

        if action_type == "move":
            if key == "left":
                adjust_position(-delta, 0)
            elif key == "right":
                adjust_position(delta, 0)
            elif key == "up":
                adjust_position(0, -delta)
            elif key == "down":
                adjust_position(0, delta)
        elif action_type == "resize":
            if key == "left":
                adjust_size(-delta, 0)
            elif key == "right":
                adjust_size(delta, 0)
            elif key == "up":
                adjust_size(0, -delta)
            elif key == "down":
                adjust_size(0, delta)

    def update_speed(action_type):
        # Accelerate the movement or resizing speed
        if current_speed[action_type] < max_speed:
            current_speed[action_type] += speed_increment

    def on_key_event(event):
        key = event.name
        if key in ["left", "right", "up", "down"]:
            ctrl = keyboard.is_pressed("ctrl")
            alt = keyboard.is_pressed("alt")

            if event.event_type == "down":
                action_type = "move" if ctrl else "resize" if alt else None
                if action_type:
                    perform_action(action_type, key)
                    update_speed(action_type)
            elif event.event_type == "up":
                # Stop the action and reset speed for both move and resize
                for action_type in ["move", "resize"]:
                    current_speed[action_type] = (
                        min_speed if action_type == "move" else min_speed
                    )

        elif key == "esc" and event.event_type == "down":
            stop_event.set()
            wx.CallAfter(frame.Close)

    return on_key_event


def config_editor(
    screen,
    config,
    frame_times: deque,
    capture_box: screen_capture.Box,
    stop_event: threading.Event,
):
    def update_form():
        # Update form values from config
        for key, value in config.items():
            form_data[key].value = str(value)

    def save_config():
        # Save form values to config
        try:
            for key, value in config.items():
                config[key] = float(form_data[key].value)
        except ValueError as exc:
            pass  # Handle invalid float conversion

    frame = Frame(
        screen,
        int(screen.height * 2 // 3),
        int(screen.width * 2 // 3),
        title="Edit Configuration",
    )
    frame.set_theme("green")
    layout = Layout([1], fill_frame=True)
    frame.add_layout(layout)

    layout.add_widget(
        Label("Use Ctrl + arrow keys or left mouse button move the capture area")
    )
    layout.add_widget(
        Label("Use Alt + arrow keys or right mouse button to resize the capture area")
    )
    layout.add_widget(Label("Esc to exit"))

    # print FPS: 10 / time for last 10 frames
    fps_label = Label(
        f"Casting {capture_box.width}x{capture_box.height} ({capture_box.left}, {capture_box.top}) to ({capture_box.left + capture_box.width}, {capture_box.top + capture_box.height}) at ~~~fps"
    )
    layout.add_widget(fps_label)

    # Create form fields
    form_data = {
        "sharpen": Text("Sharpen:", "sharpen"),
        "saturation": Text("Saturation:", "saturation"),
        "brightness": Text("Brightness:", "brightness"),
        "contrast": Text("Contrast:", "contrast"),
        "balance_r": Text("Balance R:", "balance_r"),
        "balance_g": Text("Balance G:", "balance_g"),
        "balance_b": Text("Balance B:", "balance_b"),
    }
    for name, field in form_data.items():
        layout.add_widget(field)
    layout.add_widget(Button("Save", save_config))

    frame.fix()
    update_form()

    # Create a scene with the frame
    scenes = [Scene([frame], -1)]
    screen.set_scenes(scenes)

    while not stop_event.is_set():
        if len(frame_times) >= 10:
            fps_label.text = f"Casting {capture_box.width}x{capture_box.height} ({capture_box.left}, {capture_box.top}) to ({capture_box.left + capture_box.width}, {capture_box.top + capture_box.height}) at {round(len(frame_times) / (frame_times[len(frame_times) - 1] - frame_times[0]), 1) if len(frame_times) > 0 else '~~'}fps.)"
        screen.draw_next_frame(repeat=False)
        event = screen.get_event()
        if isinstance(event, KeyboardEvent):
            frame.process_event(event)
        time.sleep(0.05)


def start_terminal_ui(
    config: dict,
    frame_times: deque,
    capture_box: screen_capture.Box,
    stop_event: threading.Event,
):
    def run(screen: Screen):
        config_editor(screen, config, frame_times, capture_box, stop_event)

    Screen.wrapper(run)
    return 0
