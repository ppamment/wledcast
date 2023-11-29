# Screencast your monitor to WLED

A python application that uses the windows GDI interface to capture your screen and stream it realtime to any WLED device

This was mostly created with the idea of casting to an LED matrix in mind, but there's no reason you couldn't cast a strip of screen to an LED strip.

## Features
- Autodiscovery of WLED devices on your network
- Pick a window to cast
- The aspect ratio of the wled configuration is autodiscovered. The largest central area of this aspect ratio sent to the LEDs so as not to distort the image
- Filters for saturation, contrast, brightness, sharpness and rgb balance are included. The default values work well for my 16x16 matrices from Aliexoress, but experiment as there is no doubt variation
- Realtime keyboard control for capture area. Arrow keys to move it around, Ctrl + Up/down to enlarge or shrink.
- There are 4 capture implementations I tried in screen_capture.py, The GDI one is fast enough at around 20hz and unlike the directx implementations supports sealessly moving between screens or capturing from multiple at once. dxcam is slightly faster but does not.

## Installation
Create and activate a conda/venv, If you don't know what that is, I recommend [micromamba](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html)  as it's very lightweight and fast:

`micromamba create -n wledcast -c conda-forge python=3.10`
`micromamba activate wledcast`

Clone the repo
`git clone https://github.com/ppamment/wledcast.git`

Install dependencies
`pip install -r requirements.txt`

Run the thing:
`python main.py`

Licence