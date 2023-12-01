import win32gui
import win32con
import win32api
from pynput import keyboard

pen_width = 6
def create_border_window(rect):
    # Define window class
    class_name = 'BorderWindowClass'
    hInstance = win32api.GetModuleHandle()
    wndClass = win32gui.WNDCLASS()
    wndClass.lpfnWndProc = {win32con.WM_PAINT: on_paint}
    wndClass.hInstance = hInstance
    wndClass.lpszClassName = class_name
    win32gui.RegisterClass(wndClass)

    # Create the window
    style = win32con.WS_POPUP
    hwnd = win32gui.CreateWindowEx(
        win32con.WS_EX_TOPMOST | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT,
        class_name,
        'Border Window',
        style,
        rect[0] - pen_width, # note the  -(a//-b) for ceil division
        rect[1] - pen_width,
        rect[2] - rect[0] + pen_width*2,
        rect[3] - rect[1] + pen_width*2,
        0,
        0,
        hInstance,
        None
    )
    # Set the window to be transparent with a specific color
    win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(0, 0, 0), 0, win32con.LWA_COLORKEY)

    # Show the window
    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
    return hwnd

def on_paint(hwnd, msg, wparam, lparam):
    hdc, paintStruct = win32gui.BeginPaint(hwnd)
    brush = win32gui.CreateSolidBrush(win32api.RGB(0,0,0))
    win32gui.SelectObject(hdc, brush)

    rect = win32gui.GetClientRect(hwnd)
    for i in range(6):
        # Draw 5 1px rectangles in from the edge of rect starting colour 255,0,0 getting 1/5 brighter as they move inward
        # first create and select the pen
        pen = win32gui.CreatePen(win32con.PS_INSIDEFRAME, 1, win32api.RGB(255, (1-i)*40, (1-i)*40))
        old_pen = win32gui.SelectObject(hdc, pen)
        win32gui.Rectangle(hdc, rect[0] + i, rect[1] + i, rect[2] - i, rect[3] - i)

        win32gui.SelectObject(hdc, old_pen)
        win32gui.DeleteObject(pen)
    win32gui.DeleteObject(brush)
    win32gui.EndPaint(hwnd, paintStruct)
    return 0

def move_window(hwnd, rect:list[int]):
    win32gui.MoveWindow(hwnd, rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1], True)

def init_keybindings(hwnd, capture_rect) -> keyboard.Listener:
    print("Ctrl + arrow keys moves the capture area")
    print("Alt + arrow keys resizes the capture area")
    print("Ctrl+c closes the program")

    keys_pressed = []
    aspect = (capture_rect[2] - capture_rect[0]) / (capture_rect[3] - capture_rect[1])

    move_px_max = 60
    move_px_min = 10
    maxX= win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
    maxY = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
    move_px = move_px_min

    def on_press(key):
        nonlocal move_px
        try:

            if key in [keyboard.Key.ctrl_l, keyboard.Key.ctrl_r, keyboard.Key.ctrl]:
                if not keyboard.Key.ctrl in keys_pressed:
                    keys_pressed.append(keyboard.Key.ctrl)
                    return
                elif key.char == "c":
                    listener.stop()

            if key in [keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt, keyboard.Key.alt_gr]:
                if not keyboard.Key.alt in keys_pressed:
                    keys_pressed.append(keyboard.Key.alt)
                    return


            if key in keys_pressed and key in [keyboard.Key.right, keyboard.Key.left, keyboard.Key.up, keyboard.Key.down]:
                # accelerate on hold
                move_px = min(move_px + 3, move_px_max)

            # alt + arrow key resizes the capture area
            if keyboard.Key.alt in keys_pressed:
                if key == keyboard.Key.right:
                    capture_rect[2] += move_px  # Increase width
                    capture_rect[3] += int(move_px / aspect)
                    if not keyboard.Key.right in keys_pressed:
                        keys_pressed.append(keyboard.Key.right)
                elif key == keyboard.Key.left and capture_rect[2] > capture_rect[0] + 2 * move_px and capture_rect[3] > capture_rect[1] + 2 * move_px:
                    capture_rect[2] -= move_px  # Decrease width
                    capture_rect[3] -= int(move_px / aspect)
                    if not keyboard.Key.left in keys_pressed:
                        keys_pressed.append(keyboard.Key.left)
                elif key == keyboard.Key.up and capture_rect[3] > capture_rect[1] + 2 * move_px and capture_rect[2] > capture_rect[0] + 2 * move_px:
                    capture_rect[3] -= move_px  # Decrease height
                    capture_rect[2] -= int(move_px * aspect)
                    if not keyboard.Key.up in keys_pressed:
                        keys_pressed.append(keyboard.Key.up)
                elif key == keyboard.Key.down:
                    capture_rect[3] += move_px  # Increase height
                    capture_rect[2] += int(move_px * aspect)
                    if not keyboard.Key.down in keys_pressed:
                        keys_pressed.append(keyboard.Key.down)
                else:
                    return
            # Ctrl + arrow key moves the capture area
            elif keyboard.Key.ctrl in keys_pressed:
                if key == keyboard.Key.right:
                    capture_rect[0] += move_px  # Move right
                    capture_rect[2] += move_px  # Move right
                    if not keyboard.Key.right in keys_pressed:
                        keys_pressed.append(keyboard.Key.right)
                elif key == keyboard.Key.left:
                    capture_rect[0] -= move_px  # Move left
                    capture_rect[2] -= move_px  # Move Left
                    if not keyboard.Key.left in keys_pressed:
                        keys_pressed.append(keyboard.Key.left)
                elif key == keyboard.Key.up:
                    capture_rect[1] -= move_px  # Move up
                    capture_rect[3] -= move_px  # Move up
                    if not keyboard.Key.up in keys_pressed:
                        keys_pressed.append(keyboard.Key.up)
                elif key == keyboard.Key.down:
                    capture_rect[1] += move_px  # Move down
                    capture_rect[3] += move_px  # Move down
                    if not keyboard.Key.down in keys_pressed:
                        keys_pressed.append(keyboard.Key.down)
                else:
                    return

            # make sure we don't move outside the screen
            if capture_rect[0] < 0:
                capture_rect[2] -= capture_rect[0]
                capture_rect[0] = 0
            if capture_rect[1] < 0:
                capture_rect[3] -= capture_rect[1]
                capture_rect[1] = 0
            if capture_rect[2] > maxX:
                capture_rect[0] -= capture_rect[2] - maxX
                capture_rect[2] = maxX
            if capture_rect[3] > maxY:
                capture_rect[1] -= capture_rect[3] - maxY
                capture_rect[3] = maxY

            move_window(hwnd, capture_rect)

        except AttributeError:
            pass

    def on_release(key):
        nonlocal move_px
        try:
            if key in [keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
                keys_pressed.remove(keyboard.Key.ctrl)
            elif key in keys_pressed:
                keys_pressed.remove(key)
                move_px = move_px_min
        except ValueError:
            pass

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)

    return listener