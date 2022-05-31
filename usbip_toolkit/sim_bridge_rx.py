import socket
from itertools import count

import reactivex as rx
from reactivex import operators as ops

from usbip_toolkit.proto import *


class USBIPSimBridgeServer_rx:
    def __init__(self, usbip_port: int = 3240, sim_port: int = 2443):
        self.usbip_port = usbip_port
        self.sim_port = sim_port
        self.counter = count()

    def serve(self):
        print("server running")
        self.tcp_echo_server()
        print("server done")

    def tcp_echo_server(self):
        print("starting server")
