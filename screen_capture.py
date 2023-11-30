from typing import Any
import time

import cv2
import win32gui
import win32ui
import win32con
import ctypes

import dxcam
import numpy as np
from PIL import Image, ImageGrab
import d3dshot
import image_processor


def _get_window_list() -> list[dict[str, int]]:
    # Create a dictionary to store the titles and handles of open windows
    window_list: list[dict[str, Any]] = []

    def window_enum_handler(hwnd, _):
        # Check if the window is a top-level window
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                window_list.append({"title": title, "hwnd": hwnd})

    win32gui.EnumWindows(window_enum_handler, None)

    return window_list


def select_window() -> int:
    # Get the list of open windows
    windows = _get_window_list()  # Get the list of windows as {title: id}
    # Ask the user to select a window from a list numbered from 1 upwards
    for i, window in enumerate(windows):
        print(f"{i + 1}: {window['title']}")
    choice = int(input("Enter the number of the window to capture: ")) - 1
    if choice < 0 or choice >= len(windows):
        print("Invalid selection. Please try again.")
        return select_window()

    return windows[choice]["hwnd"]

def get_capture_rect(hwnd, target_resolution):
    client = win32gui.GetClientRect(hwnd)
    client_left_top = win32gui.ClientToScreen(hwnd, (0, 0))
    client_rect = [
        client_left_top[0],
        client_left_top[1],
        client_left_top[0] + client[2],
        client_left_top[1] + client[3],
    ]
    width = client_rect[2] - client_rect[0]
    height = client_rect[3] - client_rect[1]
    # crop the largest area in client_rect that matches the aspect ratio of resolution
    target_aspect_ratio = target_resolution[0] / target_resolution[1]

    # Calculate the aspect ratio of the client rectangle
    client_aspect_ratio = width / height

    # Check if the aspect ratio of the client rectangle matches the aspect ratio of the resolution
    if client_aspect_ratio > target_aspect_ratio:
        # Crop the width of the client rectangle to match the aspect ratio of the resolution
        new_width = int(height * target_aspect_ratio)
        center_x = (client_rect[0] + client_rect[2]) // 2
        client_rect[0] = center_x - (new_width // 2)
        client_rect[2] = center_x + (new_width // 2)
    else:
        # Crop the height of the client rectangle to match the aspect ratio of the resolution
        new_height = int(width / target_aspect_ratio)
        center_y = (client_rect[1] + client_rect[3]) // 2
        client_rect[1] = center_y - (new_height // 2)
        client_rect[3] = center_y + (new_height // 2)

    return client_rect

def capture_window_content( window_rect: list[int], resolution: tuple[int, int]) -> np.ndarray | None:
    try:
        return capture_win32(window_rect, resolution)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        return None

def capture_win32(window_rect, resolution):
    start = time.time()
    left, top, right, bottom = window_rect
    width, height = right - left, bottom - top

    # Get the screen's device context
    screen_hwnd = win32gui.GetDesktopWindow()

    # Retrieve the device context (DC) for the entire virtual screen.
    screen_dc = win32gui.GetWindowDC(screen_hwnd)
    ##print("device", hwndDevice)

    mfcDC = win32ui.CreateDCFromHandle(screen_dc)
    try:
        saveDC = mfcDC.CreateCompatibleDC()
        saveBitMap = win32ui.CreateBitmap()
        # Above line is assumed to never raise an exception.
        try:
            try:
                saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            except (win32ui.error, OverflowError) as e:
                print("Error: ", e)
            saveDC.SelectObject(saveBitMap)
            try:
                saveDC.BitBlt((0, 0), (width, height), mfcDC, (left, top), win32con.SRCCOPY)
            except win32ui.error as e:
                print("Error: ", e)
        except win32ui.error as e:
            print("Error: ", e)
    finally:
        mfcDC.DeleteDC()

    # Convert the bitmap to a NumPy array
    bmp_info = saveBitMap.GetInfo()
    bmp_str = saveBitMap.GetBitmapBits(True)
    rgb_array = np.frombuffer(bmp_str, dtype='uint8')
    rgb_array.shape = (bmp_info['bmHeight'], bmp_info['bmWidth'], 4)
    rgb_array = rgb_array[:, :, 2::-1]

    # Release resources
    win32gui.DeleteObject(saveBitMap.GetHandle())
    win32gui.ReleaseDC(screen_hwnd, screen_dc)

    a = time.time()
    downscaled_array = cv2.resize(rgb_array, resolution, interpolation=cv2.INTER_AREA)
    b = time.time()
    processed_array = image_processor.apply_filters_cv2(downscaled_array)
    c = time.time()

    print(f"\rCapture: {(a-start)*1000:.1f}ms, Downscale: {(b-a)*1000:.1f}ms, Filter: {(c-b)*1000:.1f}ms")
    print(f"\rTotal Image capturing: {(c-start)*1000:.1f}ms")

    return processed_array

# def capture_pillow(window_rect, resolution):
#     # Use Pillow to capture the image
#     start = time.time()
#     image = ImageGrab.grab(bbox=tuple(window_rect))
#     a = time.time()
#
#     image = image.resize(resolution, Image.Resampling.BOX)
#     b = time.time()
#
#     image = image_processor.apply_filters_pillow(image)
#     c = time.time()
#     rgb_array = np.array(image)
#     d = time.time()
#
#     print(f"\rCapture: {(a - start) * 1000:.1f}ms, Downscale: {(b - a) * 1000:.1f}ms, Filter: {(c - b) * 1000:.1f}ms. array: {(d - c) * 1000:.1f}ms")
#     print(f"\rTotal Image capturing: {(c - start) * 1000:.1f}ms")
#
#     return rgb_array

# dshot = d3dshot.create(capture_output="numpy")
# def capture_d3dshot(window_rect, resolution):
#     start = time.time()
#     rgb_array = dshot.screenshot(region=window_rect)
#     a = time.time()
#     downscaled_array = cv2.resize(rgb_array, resolution, interpolation=cv2.INTER_AREA)
#     b = time.time()
#     rgb_array = image_processor.apply_filters_cv2(downscaled_array)
#     c = time.time()
#     print(f"\rCapture: {(a - start) * 1000:.1f}ms, Downscale: {(b - a) * 1000:.1f}ms, Filter: {(c - b) * 1000:.1f}ms")
#     print(f"\rTotal Image capturing: {(c - start) * 1000:.1f}ms")
#
#
# camera = dxcam.create()
# def capture_dxcam(window_rect, resolution):
#     start = time.time()
#     rgb_array = camera.grab(region=window_rect)
#     a = time.time()
#     downscaled_array = cv2.resize(rgb_array, resolution, interpolation=cv2.INTER_AREA)
#     b = time.time()
#     rgb_array = image_processor.apply_filters_cv2(downscaled_array)
#     c = time.time()
#     print(f"\rCapture: {(a - start) * 1000:.1f}ms, Downscale: {(b - a) * 1000:.1f}ms, Filter: {(c - b) * 1000:.1f}ms")
#     print(f"\rTotal Image capturing: {(c - start) * 1000:.1f}ms")
#
#     return rgb_array