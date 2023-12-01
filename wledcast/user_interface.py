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

            if key in [keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt, keyboard.Key.alt_gr]:
                if not keyboard.Key.alt in keys_pressed:
                    keys_pressed.append(keyboard.Key.alt)
                    return

            # accelerate on hold
            if key in [keyboard.Key.right, keyboard.Key.left, keyboard.Key.up, keyboard.Key.down]:
                if key in keys_pressed:
                    move_px = min(move_px + 3, move_px_max)
                else:
                    keys_pressed.append(key)

            # alt + arrow key resizes the capture area
            if keyboard.Key.alt in keys_pressed:
                if key == keyboard.Key.right:
                    capture_rect[2] += move_px  # Increase width
                    capture_rect[3] += int(move_px / aspect)
                elif key == keyboard.Key.left and capture_rect[2] > capture_rect[0] + 2 * move_px and capture_rect[3] > capture_rect[1] + 2 * move_px:
                    capture_rect[2] -= move_px  # Decrease width
                    capture_rect[3] -= int(move_px / aspect)
                elif key == keyboard.Key.up and capture_rect[3] > capture_rect[1] + 2 * move_px and capture_rect[2] > capture_rect[0] + 2 * move_px:
                    capture_rect[3] -= move_px  # Decrease height
                    capture_rect[2] -= int(move_px * aspect)
                elif key == keyboard.Key.down:
                    capture_rect[3] += move_px  # Increase height
                    capture_rect[2] += int(move_px * aspect)
                else:
                    return
            # Ctrl + arrow key moves the capture area
            if keyboard.Key.ctrl in keys_pressed:
                if key == keyboard.Key.right:
                    capture_rect[0] += move_px  # Move right
                    capture_rect[2] += move_px  # Move right
                elif key == keyboard.Key.left:
                    capture_rect[0] -= move_px  # Move left
                    capture_rect[2] -= move_px  # Move Left
                elif key == keyboard.Key.up:
                    capture_rect[1] -= move_px  # Move up
                    capture_rect[3] -= move_px  # Move up
                elif key == keyboard.Key.down:
                    capture_rect[1] += move_px  # Move down
                    capture_rect[3] += move_px  # Move down
                elif key.char == "c":
                    listener.stop()
                    return False
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
            elif key in [keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt, keyboard.Key.alt_gr]:
                keys_pressed.remove(keyboard.Key.alt)
            elif key in keys_pressed:
                keys_pressed.remove(key)
                move_px = move_px_min
        except ValueError:
            pass

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)

    return listener

# config = {
#     "sharpen": 0.3,
#     "saturation": 1.1,
#     "brightness": 0.17,
#     "contrast": 1.4,
#     "balance": {
#         "r": 1,
#         "g": 0.85,
#         "b": 0.45
#     }
# }
#
# def edit_config(screen, config):
#     def update_form():
#         # Update form values from config
#         form_data["sharpen"].value = str(config["sharpen"])
#         form_data["saturation"].value = str(config["saturation"])
#         form_data["brightness"].value = str(config["brightness"])
#         form_data["contrast"].value = str(config["contrast"])
#         form_data["balance_r"].value = str(config["balance"]["r"])
#         form_data["balance_g"].value = str(config["balance"]["g"])
#         form_data["balance_b"].value = str(config["balance"]["b"])
#
#     def save_config():
#         # Save form values to config
#         try:
#             config["sharpen"] = float(form_data["sharpen"].value)
#             config["saturation"] = float(form_data["saturation"].value)
#             config["brightness"] = float(form_data["brightness"].value)
#             config["contrast"] = float(form_data["contrast"].value)
#             config["balance"]["r"] = float(form_data["balance_r"].value)
#             config["balance"]["g"] = float(form_data["balance_g"].value)
#             config["balance"]["b"] = float(form_data["balance_b"].value)
#         except ValueError:
#             pass  # Handle invalid float conversion
#
#     def exit_app():
#         raise StopApplication("User requested exit")
#
#     frame = Frame(screen, int(screen.height * 2 // 3), int(screen.width * 2 // 3), hover_focus=True, title="Edit Configuration")
#     layout = Layout([1], fill_frame=True)
#     frame.add_layout(layout)
#
#     # Create form fields
#     form_data = {
#         "sharpen": Text("Sharpen:", "sharpen"),
#         "saturation": Text("Saturation:", "saturation"),
#         "brightness": Text("Brightness:", "brightness"),
#         "contrast": Text("Contrast:", "contrast"),
#         "balance_r": Text("Balance R:", "balance_r"),
#         "balance_g": Text("Balance G:", "balance_g"),
#         "balance_b": Text("Balance B:", "balance_b"),
#     }
#
#     for name, field in form_data.items():
#         layout.add_widget(field)
#
#     layout.add_widget(Button("Save", save_config))
#     layout.add_widget(Button("Exit", exit_app))
#
#     frame.fix()
#
#     update_form()
#
#     while True:
#         screen.draw_next_frame(repeat=False)
#         event = screen.get_event()
#         if isinstance(event, KeyboardEvent):
#             if event.key_code in [Screen.KEY_ESCAPE, ord('q'), ord('Q')]:
#                 return
#             else:
#                 frame.process_event(event)
#
# Screen.wrapper(edit_config, arguments=[config])