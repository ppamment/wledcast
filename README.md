A cross platform python application for capturing an area of your screen and streaming it to any WLED device over UDP using the DDP realtime protocol. Here it is casting to a 32x32 LED matrix. 



https://github.com/user-attachments/assets/ef07709c-d612-429a-a3a2-28bfc5f7d2c7




Maybe I just wasn't looking very hard, but I didn't find a simple tool already existing that does this.

This was mostly created with the idea of casting to an LED matrix in mind, but there's no reason you couldn't use it to cast to a strip or an alien covered in strips. 
You'd just need to use your imagination a bit more to work out what mapped where.

Looks great displaying a visualiser from whichever audio player you choose.

There are loads of cool visualisations/VJ set etc on youtube etc that look great too.

Issues and PRs are welcomed. This is still alpha at the moment. In my testing it is working on Windows 11 and Ubuntu 20.04 and 22.04. In my limited testing on MacOS, some accessibility features need to be enabled, but it did cast the screen to the LED matrix. The UI, however, was not really working. If someone needs to use it on MacOS, create an Issue, I'll see if I can borrow a mac for testing and spend a little time sorting it out. 

### Features
- Autodiscovers WLED devices on your network. Choose which to cast to.
- Pick a window to cast
- The aspect ratio of the wled configuration is autodiscovered and applied to the casting area
- Filters for saturation, contrast, brightness, sharpness and rgb balance are included. The values can be edited in the console menu on the fly while casting.
  Scale r, g, b down (ie less than 1) if you need sp you as not to have values overflow and clip. The default values work well for the 16x16 matrices from Aliexoress I have, but experiment as there is no doubt variation
- The area being cast is clearly displayed with a red border
- Move and scale the capture area with the keyboard  (Ctrl + arrows to move, Alt+arrows to scale). Alternatively left click on the red border to drag it around, right click and move up/down to scale.
- Decent performance - I get around 60-65fps with all filters enabled with the fps limiter off. This is really a little too fast for WS2812bs if you have a quite a few on a pin, so the fps is limited to 25 by default

### Options (none required)
| Option                   | Desctription                                                                                                      |
|:-------------------------|:------------------------------------------------------------------------------------------------------------------|
| --host HOST              | Skip network discovery and cast to this IP address                                                                |
| --title TITLE            | Cast the window whost title contains TITLE                                                                        |
| --monitor [NUMBER]       | Cast a monitor rather than a window. Optionally pass the monitor number, else you'll be asked                     |
| --output-resolution      | Skip resolution discovery from WLED and use this (format 64x32)                                                   |
| --live-preview           | Show the output in a preview pane on the computer                                                                 |
| --fps FPS                | Limit fps to FPS. 500 LEDS per GPIO is stable up to around 40Hz on and ESP32-WROOM for me but YMMV. Default 30    |
| --search-timeout TIMEOUT | Timeout for WLED network discovery, defaults to 3s. Increase if your latency is higher and devices are not found. |
| --workers [NUM]          | Number of workers capturing and sending data. Only increase if necessary to meet framerate.                       |
| --debug                  | Endable debug logs                                                                                                |

To implement:
     
### Installation
______
Requires Python >=3.10. Create and activate a conda/venv, If you aren't sure how, I recommend [micromamba (install here)](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html)  as it's very lightweight and fast:
```shell
micromamba create -n wledcast -c conda-forge python=3.11
micromamba activate wledcast
```

#### With pip (recommended)
```shell
pip install wledcast
wledcast
```

#### From source (developers/contributors)
Clone the repo, install the package (editable):
```shell
git clone https://github.com/ppamment/wledcast.git
cd wledcast
pip install -e .
wledcast
```

### Additional requirements
______

#### Windows - ImportError: DLL load failed
You probably need to install the Visual C++ 2015 runtime. You can find it here:

https://www.microsoft.com/en-us/download/details.aspx?id=53840

#### Linux - cannot build wxpython wheel
Install the GTK+ development package. On Ubuntu 22.04 it is available from apt:
```shell
sudo apt install libgtkmm-3.0-dev
```
You can also find wheels for various linux distros here: https://extras.wxpython.org/wxPython4/extras/linux/gtk3/
Copy the url and install it with pip, then retry installing wledcast.

### Licence
______
GPLv3, See the LICENCE file
