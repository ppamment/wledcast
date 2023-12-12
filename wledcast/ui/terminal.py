import threading
import time
from collections import deque

from asciimatics.event import KeyboardEvent
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.widgets import Button, Frame, Label, Layout, Text

from wledcast import config
from wledcast.model import Box

def config_editor(
    screen,
    filter_config: dict[str, float],
    frame_times: deque,
    capture_box: Box,
    stop_event: threading.Event,
):
    def update_form():
        # Update form values from config
        for key, value in filter_config.items():
            form_data[key].value = str(value)

    def save_config():
        # Save form values to config
        try:
            for key, value in filter_config.items():
                filter_config[key] = float(form_data[key].value)
            config.save_filter_config(filter_config)
        except ValueError as exc:
            pass  # Handle invalid float conversion

    frame = Frame(
        screen,
        int(screen.height),
        int(screen.width),
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
    form_data = {k: Text(k.replace("_", " ").title()+":", k) for k in filter_config.keys()}

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
    filter_config: dict[str, float],
    frame_times: deque,
    capture_box: Box,
    stop_event: threading.Event,
):
    def run(screen: Screen):
        config_editor(screen, filter_config, frame_times, capture_box, stop_event)

    Screen.wrapper(run)
    return 0

def create_thread(filter_config: dict[str, float], frame_times: deque, capture_box: Box, stop_event: threading.Event):
    return threading.Thread(target=start_terminal_ui, args=(filter_config, frame_times, capture_box, stop_event))