import imp
import os
import socket
import time
from itertools import count
from multiprocessing import pool

import reactivex as rx
import reactivex.run as rxrun
from reactivex import operators as ops
from reactivex.scheduler import ThreadPoolScheduler
from reactivex.scheduler.scheduler import Scheduler

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

        def rx_loop(observer: rx.Observer, scheduler: Scheduler):
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
            observer.dispose()

        # self.source = rx.create(rx_loop).pipe(ops.observe_on(pool_scheduler))
        self.source = rx.create(rx_loop).pipe(ops.subscribe_on(pool_scheduler))

        # foo = self.source.subscribe(
        #     on_next=lambda i: print("Received A {0}".format(i)),
        #     on_error=lambda e: print("Error Occurred: {0}".format(e)),
        #     on_completed=lambda: print("Done! A"),
        # )

        def push_five_strings(observer, scheduler):
            # print("push 5 dstart")
            # time.sleep(5)
            # print("on a")
            observer.on_next("Alpha")
            # time.sleep(2)
            # print("on b")
            observer.on_next("Beta")
            # time.sleep(2)
            # print("on c")
            observer.on_next("Gamma")
            # time.sleep(2)
            # print("on d")
            observer.on_next("Delta")
            # time.sleep(2)
            # print("on e")
            observer.on_next("Epsilon")
            # time.sleep(2)
            # print("push 5 completed posting")
            observer.on_completed()
            # print("push 5 completed posted")

        source2 = rx.create(push_five_strings)

        s2 = source2.pipe(ops.observe_on(pool_scheduler))

        def push_five_other_strings(observer, scheduler):
            observer.on_next("aardvark")
            observer.on_next("babboon")
            observer.on_next("gibbon")
            observer.on_next("dingo")
            observer.on_next("elephant")
            observer.on_completed()

        source3 = rx.create(push_five_other_strings)

        s3 = source2.pipe(ops.subscribe_on(pool_scheduler), ops.delay(3))
        # s2 = source2.pipe(ops.subscribe_on(pool_scheduler), ops.delay(3)).subscribe(
        #     on_next=lambda i: print("Received B {0}".format(i)),
        #     on_error=lambda e: print("Error Occurred: {0}".format(e)),
        #     on_completed=lambda: print("Done! B"),
        # )
        # combo = rx.compose()
        # combo = self.source.pipe(ops.merge(s2))
        combo = rx.merge(self.source, s2).pipe(ops.observe_on(pool_scheduler))
        # combo = rx.merge(s2, s3)
        # combo_s = rx.create(combo)

        combo.subscribe(
            on_next=lambda i: print("Received C {0}".format(i)),
            on_error=lambda e: print("Error Occurred: {0}".format(e)),
            on_completed=lambda: print("Done! C"),
        )
        # print(f"foo: {foo}")
        # foo.dispose()
        rxrun.run(combo)

        print("ended server")


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


if __name__ == "__main__":
    sim = USBIPSimBridgeServer_rx()
    sim.serve()
