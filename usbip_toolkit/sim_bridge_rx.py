import os
import socket
import time
from itertools import count

import reactivex
import reactivex as rx
from reactivex import operators as ops
from reactivex.scheduler import ThreadPoolScheduler

from usbip_toolkit.proto import *
from usbip_toolkit.util import get_tcp_server_socket

pool_scheduler = ThreadPoolScheduler(os.cpu_count())


class SimServer:
    def __init__(self, port: int = 2443):
        self.port = port
        self.serv_sock = get_tcp_server_socket(port)

    def wait_for_connection(self):
        print("waiting for connection")
        self.serv_sock.listen(1)
        self.client_sock, _ = self.serv_sock.accept()

    def serve(self):
        print("starting server")

        def rx_loop(observer, scheduler):
            self.wait_for_connection()
            while True:
                buf = self.client_sock.recv(1024)
                if buf:
                    observer.on_next(buf)
                else:
                    print("got empty buf completing")
                    self.client_sock = None
                    break
            observer.on_completed()

        # self.source = rx.create(rx_loop).pipe(ops.observe_on(pool_scheduler))
        self.source = rx.create(rx_loop).pipe(ops.subscribe_on(pool_scheduler))

        foo = self.source.subscribe(
            on_next=lambda i: print("Received A {0}".format(i)),
            on_error=lambda e: print("Error Occurred: {0}".format(e)),
            on_completed=lambda: print("Done! A"),
        )

        def push_five_strings(observer, scheduler):
            observer.on_next("Alpha")
            time.sleep(2)
            observer.on_next("Beta")
            time.sleep(2)
            observer.on_next("Gamma")
            time.sleep(2)
            observer.on_next("Delta")
            time.sleep(2)
            observer.on_next("Epsilon")
            time.sleep(2)
            observer.on_completed()

        source2 = rx.create(push_five_strings)

        source2.pipe(ops.subscribe_on(pool_scheduler), ops.delay(3)).subscribe(
            on_next=lambda i: print("Received B {0}".format(i)),
            on_error=lambda e: print("Error Occurred: {0}".format(e)),
            on_completed=lambda: print("Done! B"),
        )


class USBIPServer:
    def __init__(self, port: int = 3240):
        self.port = port
        self.serv_sock = get_tcp_server_socket(port)


class USBIPSimBridgeServer_rx:
    def __init__(self, usbip_port: int = 3240, sim_port: int = 2443):
        self.usbip_port = usbip_port
        self.sim_port = sim_port
        self.sim_server = SimServer(sim_port)
        self.counter = count()

    def serve(self):
        print("server running")
        self.sim_server.serve()
        print("server done")
