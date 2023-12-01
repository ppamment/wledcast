A python application that uses the Windows GDI interface to capture your screen (or a part) and stream it to any WLED device over UDP using the DDP realtime protocol.

Maybe I just wasn't lookig very hard, but I didn't find a simple tool already existing that does this.

This was mostly created with the idea of casting to an LED matrix in mind, but there's no reason you couldn't use it to cast to a strip or an alien covered in strips. 
You'd just need to use your imagination a bit more to work out what mapped where.

There are loads of cool visualisations on youtube etc that look good even at relatively

Issues and PRs are welcomed.

### Features
- Autodiscovers WLED devices on your network. Choose which to cast to.
- Pick a window to cast
- The aspect ratio of the wled configuration is autodiscovered and applied to the casting area
- Filters for saturation, contrast, brightness, sharpness and rgb balance are included. The values can be edited in filter.json during casting. 
  Scale r, g, b down (ie less than 1) if you need sp you as not to have values overflow and clip. The default values work well for the 16x16 matrices from Aliexoress I have, but experiment as there is no doubt variation
- The area being cast is clearly displayed with a red border
- Move and scale the capture area with keyboard arrows realtime
- Decent performance - I get around 60-65fps with all filters enabled with the fps limiter off. This is really a little too fast for the 512 pixels on each GPIO pin 

### Installation
______
It will soon be published to pypifor installation with pip.

Create and activate a conda/venv, If you aren't sure how, I recommend [micromamba](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html)  as it's very lightweight and fast:
```shell
micromamba create -n wledcast -c conda-forge python=3.10
micromamba activate wledcast
```


Clone the repo, install dependencies, run
```
git clone https://github.com/ppamment/wledcast.git
cd wledcast
python -m pip install -r requirements.txt
python main.py
```

### Licence
______
GPLv3, See the LICENCE file