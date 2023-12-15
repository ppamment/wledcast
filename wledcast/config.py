import argparse
import json
import os

import aiofiles
import pymonctl

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
    "--live-preview",
    default=False,
    help="Show a live preview of the WLED output  the computer screen",
    action="store_true",
)
# parser.add_argument(
#     "--capture-method",
#     type=str,
#     default="mss",
#     help="Default mss works well on all platforms. dxcam is faster but only supports windows on primary monitor",
#     choices=["dxcam", "mss"],
# )
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
    "--monitor",
    nargs="?",
    const=-1,
    type=int,
    help="Monitor the WLED output to the screen",
)
parser.add_argument(
    "--border-size",
    default=10,
    type=int,
    help="Width in px of border around the casting area. Defaults to 10px",
)
parser.add_argument(
    "--output-resolution",
    type=str,
    default=None,
    help="Output resolution of the WLED instance to cast to",
)
parser.add_argument(
    "--workers",
    type=int,
    default=3,
    help="Number of caoture workers. Defaults to 3 which is fine unless fps is very high",
)
args = parser.parse_args()

border_size: int = int(args.border_size)
filter_config_path = os.path.join(os.path.dirname(__file__), "filter.json")

with open(filter_config_path, "r") as f:
    filters = json.load(f)


async def save_filter_config():
    async with aiofiles.open(filter_config_path, "w") as f:
        await f.write(json.dumps(filters, indent=4))


max_x = max_y = 0
for monitor in pymonctl.getAllMonitorsDict().values():
    max_x += monitor["size"].width
    max_y = max(max_y, monitor["size"].height)
