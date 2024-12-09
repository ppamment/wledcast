import yaml

write_mock = lambda pixels: None

class Controller:
    def __init__(self, write = write_mock): #, positions = []):
        self.write = write
        self.positions = []

    def __str__(self):
        return f'Controller: {len(self.positions)} pixels, write: {self.write}'

def load(filename) -> dict:
    """
    Return a dict of controllers from the given yaml file name.
    """
    with open(filename, 'r') as file:
        yaml_data = yaml.safe_load(file)

    controllers = {}
    if 'controller' in yaml_data:
        controller_data = yaml_data['controller']
        for item in controller_data:
            controller_type = next(iter(item.keys()))
            args = item[controller_type]
            try:
                controller_id = args.get('id', args['host'])
                if args['id']:
                    del args['id']
            except KeyError as e:
                raise KeyError(f'controller must specify {e}')
            if controller_id in controllers:
                raise ValueError(f'duplicate id for controller {controller_id}')
            write_function = globals()[controller_type](**args)
            controllers[controller_id] = Controller(write=write_function)

    return controllers


def ddp(host):
    from wledcast.wled.pixel_writer import PixelWriter
    pw = PixelWriter(host)
    return pw.update_pixels
