import socket
from itertools import count

import reactivex
import reactivex as rx
from reactivex import operators as ops

from usbip_toolkit.proto import *


class USBIPSimBridgeServer_rx:
    def __init__(self, usbip_port: int = 3240, sim_port: int = 2443):
        self.usbip_port = usbip_port
        self.sim_port = sim_port
        self.counter = count()
        self.serv_sock = serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        serv_sock.bind(("localhost", sim_port))
        serv_sock.listen(1)
        print("waiting for incomming connection")
        self.s, _ = serv_sock.accept()
        print("got connection")

    def serve(self):
        print("server running")
        self.tcp_echo_server()
        print("server done")

    def tcp_echo_server(self):
        print("starting server")

        def rx_loop(observer, scheduler):
            while True:
                buf = self.s.recv(1024)
                if buf:
                    observer.on_next(buf)
                else:
                    print("got empty buf completing")
                    observer.on_completed()
                    break

        source = rx.create(rx_loop)

        source.subscribe(
            on_next=lambda i: print("Received {0}".format(i)),
            on_error=lambda e: print("Error Occurred: {0}".format(e)),
            on_completed=lambda: print("Done!"),
        )
