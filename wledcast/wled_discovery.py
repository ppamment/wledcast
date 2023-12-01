import socket
import requests
import time

from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange, ServiceInfo

def discover(timeout=5):
    # Discover WLED instances on the local network
    def check_wled_on_ip(info: ServiceInfo):
        address = socket.inet_ntoa(info.addresses[0])
        port = info.port
        try:
            response = requests.get(f"http://{address}:{port}/win", timeout=0.1)
            if response.status_code == 200:
                services.append(address)
        except requests.exceptions.RequestException as e:
            pass  # Service didn't respond to /win or there was another error

    zeroconf = Zeroconf()
    services = []

    def on_service_state_change(zeroconf, service_type, name, state_change):
        if state_change == ServiceStateChange.Added:
            info = zeroconf.get_service_info(service_type, name)
            if info:
                check_wled_on_ip(info)

    with ServiceBrowser(zeroconf, "_http._tcp.local.", handlers=[on_service_state_change]):
        time.sleep(timeout)

    if not services:
        print("No WLED instances found on the network.")
        exit(1)
    return services

def select_instance(instances):
    # Ask user which WLED instance to cast to
    if not instances:
        print("No WLED instances available to select.")
        return None
    print("Please select a WLED instance to cast to:")
    for i, instance in enumerate(instances):
        print(f"{i+1}. {instance}")
    selected_index = int(input("Enter the number of your selection: ")) - 1
    if selected_index < 0 or selected_index >= len(instances):
        print("Invalid selection. Please try again.")
        return select_instance(instances)

    return instances[selected_index]

def get_matrix_shape(host) -> tuple[int, int]:
    # Determine the shape of the LED pixel matrix from WLED
    try:
        response = requests.get(
            f"http://{host}:80/json/state")
        data = response.json()
        seg_data = data.get("seg")
        if seg_data is None or not seg_data:
            print(f"Error: The WLED instance did not return the expected 'seg' data. Response data: {data}")
            exit(1)
        # Find the first segment that is turned on
        on_segment = next((seg for seg in seg_data if seg.get('on')), None)
        if on_segment is None:
            print(f"Error: Make sure you have at least one segment turned on and try again. Response data: {data}")
            exit(1)
        width = on_segment.get('stop') - on_segment.get('start')
        height = on_segment.get('stopY') - on_segment.get('startY')

        return (width, height)
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with the WLED instance: {e}")
        exit(1)
