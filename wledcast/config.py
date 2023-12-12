import logging
import argparse
import os
import json

import pymonctl
import wx


# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--fps", type=int, default=30, help="Target FPS")
parser.add_argument(
    "--title",
    type=str,
    default=None,
    help="Cast window whose title contains this string",
)
parser.add_argument(
    "--search-timeout",
    type=int,
    default=3,
    help="Seconds to wait for WLED instance discovery",
)
parser.add_argument(
    "--output-resolution",
    type=str,
    default=None,
    help="Specify the output resolution rather than discovering from WLED",
)
parser.add_argument(
    "--live-preview",
    default=False,
    help="Show a live preview of the WLED output  the computer screen",
    action="store_true",
)
parser.add_argument(
    "--capture-method",
    type=str,
    default="mss",
    help="Default mss works well on all platforms. dxcam is faster but only supports windows on primary monitor",
    choices=["dxcam", "mss"],
)
parser.add_argument(
    "--debug",
    default=False,
    help="Show debug messages",
    action="store_true",
)
parser.add_argument(
    "--host",
    default=None,
    type=str,
    help="Specify the IP address of the WLED instance to cast to",
)
parser.add_argument(
    '--monitor',
    nargs='?',
    const=-1,
    type=int,
    help="Monitor the WLED output to the screen"
)
parser.add_argument(
    '--border-size',
    default=10,
    type=int,
    help="Width in px of border around the casting area. Defaults to 10px"
)
args = parser.parse_args()

border_size: int = int(args.border_size)
filter_config_path = os.path.join(os.path.dirname(__file__), "filter.json")

def get_filter_config():
    with open(filter_config_path, "r") as f:
        config = json.load(f)
    return config

def save_filter_config(config):
    with open(filter_config_path, "w") as f:
        f.write(json.dumps(config))


max_x = max_y = 0
for monitor in pymonctl.getAllMonitorsDict().values():
    max_x += monitor["size"].width
    max_y = max(max_y, monitor["size"].height)
    if args.capture_method == "dxcam":
        # only first monitor for dxcam capture
        break
