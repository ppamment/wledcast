import asyncio
import logging
from collections import deque
from multiprocessing import Event

import wx
from asciimatics.event import KeyboardEvent
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.widgets import Button, Frame, Label, Layout, Text
from wxasync import StartCoroutine

from wledcast import config
from wledcast.model import Box

logger = logging.getLogger(__name__)


async def config_editor_async(
    screen,
    frame_times: deque,
    capture_box: Box,
    stop_event: Event,
):
    logger.info("Starting config editor UI")

    def update_form():
        # Update form values from config
        for key, value in config.filters.items():
            form_data[key].value = str(value)

    def save_config():
        # Define an async function to save the config
        async def async_save():
            try:
                for key, value in config.filters.items():
                    config.filters[key] = float(form_data[key].value)
                await config.save_filter_config()
            except ValueError as exc:
                pass

        # This is a bit of a workaround as on_click cannot await async functions
        asyncio.create_task(async_save())

    logger.info(f"Creating frame, {screen.height}x{screen.width}")
    frame = Frame(
        screen,
        min(int(screen.height), 15),
        min(int(screen.width), 80),
        title="Edit Configuration",
    )
    frame.set_theme("green")
    logger.info("Creating layout")
    layout = Layout([1], fill_frame=True)
    frame.add_layout(layout)
    logger.info("Adding widgets")
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
        k: Text(k.replace("_", " ").title() + ":", k) for k in config.filters.keys()
    }

    for name, field in form_data.items():
        layout.add_widget(field)
    layout.add_widget(Button("Save", save_config))
    logger.info("Updating form")
    frame.fix()
    update_form()

    logger.info("Setting scenes")
    # Create a scene with the frame
    scenes = [Scene([frame], -1)]
    screen.set_scenes(scenes)
    screen.open()
    # Start the event loop
    while not stop_event.is_set():
        if len(frame_times) >= 10:
            fps_label.text = f"Casting {capture_box.width}x{capture_box.height} ({capture_box.left}, {capture_box.top}) to ({capture_box.left + capture_box.width}, {capture_box.top + capture_box.height}) at {round((len(frame_times)-1) / (frame_times[len(frame_times) - 1] - frame_times[0]), 1) if len(frame_times) > 0 else '~~'}fps.)"
        screen.draw_next_frame(repeat=False)
        event = screen.get_event()
        if isinstance(event, KeyboardEvent):
            frame.process_event(event)
        await asyncio.sleep(0.05)


def start_async(
    frame_times: deque, capture_box: Box, stop_event: Event, window: wx.Frame
):
    logger.info("Starting terminal UI")

    async def run(screen: Screen):
        await config_editor_async(screen, frame_times, capture_box, stop_event)

    return StartCoroutine(Screen.wrapper(run), window)
