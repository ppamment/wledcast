import argparse
import json
import logging
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
    help="Number of capture workers. Defaults to 3 which is fine unless fps is very high",
)
args = parser.parse_args()

border_size: int = int(args.border_size)
filter_config_path = os.path.join(os.path.dirname(__file__), "filter.json")

with open(filter_config_path, "r") as f:
    filters = json.load(f)

logger = logging.getLogger(__name__)


async def save_filter_config():
    async with aiofiles.open(filter_config_path, "w") as f:
        await f.write(json.dumps(filters, indent=4))


# Calculate actual virtual desktop bounds considering monitor positions
try:
    monitors = pymonctl.getAllMonitorsDict()
    if not monitors:
        # Fallback to a reasonable default if no monitors detected
        max_x, max_y = 1920, 1080
        logger.warning("No monitors detected, using fallback resolution 1920x1080")
    else:
        # Find the actual bounding box of all monitors
        min_x = min_y = float('inf')
        max_x_bound = max_y_bound = float('-inf')
        
        for i, monitor in enumerate(monitors.values()):
            # Handle Point objects for position
            pos = monitor.get("position", None)
            size = monitor.get("size", None)
            
            # Extract coordinates from Point/Size objects or use defaults
            if hasattr(pos, 'x') and hasattr(pos, 'y'):
                left = pos.x
                top = pos.y
            else:
                left = top = 0
                
            if hasattr(size, 'width') and hasattr(size, 'height'):
                width = size.width
                height = size.height
            else:
                width, height = 1920, 1080
            
            # Calculate monitor boundaries
            right = left + width
            bottom = top + height
            
            
            # Update bounding box
            min_x = min(min_x, left)
            min_y = min(min_y, top)
            max_x_bound = max(max_x_bound, right)
            max_y_bound = max(max_y_bound, bottom)
        
        # Store the actual coordinate bounds for UI constraints
        # Don't convert to dimensions - keep as coordinate bounds
        max_x = max_x_bound
        max_y = max_y_bound
        # Also store minimums for constraints
        min_desktop_x = min_x
        min_desktop_y = min_y
        
        logger.info(f"Virtual desktop bounds: {max_x}x{max_y} (monitors from {min_x},{min_y} to {max_x_bound},{max_y_bound})")

except Exception as e:
    # Fallback if monitor detection fails
    max_x, max_y = 1920, 1080
    min_desktop_x = min_desktop_y = 0
    logger.warning(f"Monitor detection failed ({e}), using fallback resolution 1920x1080")

