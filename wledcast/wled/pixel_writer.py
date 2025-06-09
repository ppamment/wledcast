import socket

import numpy


class PixelWriter:
    DDP_MAX_DATALEN = 1200  # Maximum length of DDP data
    DDP_DESTINATION_ID = 1  # Hardcoded Destination ID

    def __init__(self, host):
        self.host = host
        self.sequence_id = 1  # Initialize sequence ID
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP socket

    def update_pixels(self, rgb_array: numpy.ndarray):
        # Update the LED matrix via WLED in real-time using DDP
        # Convert numpy array directly to bytes for better performance
        byte_data = rgb_array.flatten().tobytes()

        self._send_ddp_data(byte_data)

    def _create_ddp_packet(self, data, data_offset, is_last_packet=False):
        header = bytearray(10)
        header[0] = 0b01000000 | (0b00000001 if is_last_packet else 0)
        header[1] = self.sequence_id
        header[2] = 0x01  # Data type set to 01
        header[3] = self.DDP_DESTINATION_ID
        header[4:8] = data_offset.to_bytes(4, byteorder="big")
        header[8:10] = len(data).to_bytes(2, byteorder="big")
        return header + data

    def _send_ddp_data(self, rgb_data):
        data_offset = 0

        for i in range(0, len(rgb_data), self.DDP_MAX_DATALEN):
            packet_data = rgb_data[i : i + self.DDP_MAX_DATALEN]
            is_last_packet = i + self.DDP_MAX_DATALEN >= len(rgb_data)
            packet = self._create_ddp_packet(packet_data, data_offset, is_last_packet)
            self.socket.sendto(packet, (self.host, 4048))
            data_offset += len(packet_data)

        # Increment sequence ID for the next RGB dataset
        self.sequence_id = (self.sequence_id + 1) % 16

    def close_socket(self):
        self.socket.close()

    def __del__(self):
        self.close_socket()
