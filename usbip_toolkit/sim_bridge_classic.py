import socket
import time
from queue import Queue
from threading import Thread

from usbip_toolkit.proto import *
from usbip_toolkit.util import get_tcp_server_socket


class SimServer:
    def __init__(self, d2h_raw: Queue, h2d_raw: Queue, port: int = 2443):
        self.d2h_raw = d2h_raw
        self.h2d_raw = h2d_raw
        self.port = port
        self.serv_sock = get_tcp_server_socket(port)
        self.accept_thread = None
        self.d2h_thread = None
        self.h2d_thread = None

    def wait_for_connection(self):
        print("waiting for sim client connection")
        self.serv_sock.listen(1)
        self.client_sock, _ = self.serv_sock.accept()
        print("got sim client connection")
        self.d2h_thread = Thread(target=self.d2h_loop, name="d2h_raw", daemon=True)
        self.h2d_thread = Thread(target=self.h2d_loop, name="h2d_raw", daemon=True)
        self.d2h_thread.start()
        self.h2d_thread.start()
        self.accept_thread = None

    def serve(self):
        print("starting sim server")
        self.accept_thread = Thread(target=self.wait_for_connection, name="sim_wait", daemon=False)
        self.accept_thread.start()
        print("ended sim server")

    def d2h_loop(self):
        while True:
            nbytes_buf = self.client_sock.recv(4)
            if not nbytes_buf:
                break
            nbytes = int.from_bytes(nbytes_buf, "big")
            buf = self.client_sock.recv(nbytes)
            if not buf:
                break
            self.d2h_raw.put(buf)
        print("sim client closed socket")

    def h2d_loop(self):
        while True:
            buf = self.h2d_raw.get()
            lpbuf = len(buf).to_bytes(4, "big") + buf
            self.client_sock.send(lpbuf)
            self.h2d_raw.task_done()


class USBIPServer:
    def __init__(self, d2h_ip: Queue, h2d_ip: Queue, port: int = 3240):
        self.d2h_ip = d2h_ip
        self.h2d_ip = h2d_ip
        self.port = port
        self.serv_sock = get_tcp_server_socket(port)
        self.accept_thread = None
        self.d2h_thread = None
        self.h2d_thread = None

    def wait_for_connection(self):
        print("waiting for usbip client connection")
        self.serv_sock.listen(1)
        self.client_sock, _ = self.serv_sock.accept()
        print("got usbip client connection")
        self.d2h_thread = Thread(target=self.d2h_loop, name="d2h_ip", daemon=True)
        self.h2d_thread = Thread(target=self.h2d_loop, name="h2d_ip", daemon=True)
        self.d2h_thread.start()
        self.h2d_thread.start()
        self.accept_thread = None

    def serve(self):
        print("starting usbip server")
        self.accept_thread = Thread(target=self.wait_for_connection, name="ip_wait", daemon=False)
        self.accept_thread.start()
        print("ended usbip server")

    def d2h_loop(self):
        while True:
            pkt = read_usbip_packet(self.client_sock)
            print(f"d2h_ip pkt: {pkt}")
            self.d2h_ip.put(pkt)
        print("usbip client closed socket")

    def h2d_loop(self):
        while True:
            self.client_sock.send(self.h2d_ip.get())
            self.h2d_ip.task_done()


class USBIPSimBridgeServer_classic:
    def __init__(self, usbip_port: int = 3240, sim_port: int = 2443):
        self.usbip_port = usbip_port
        self.sim_port = sim_port
        self.d2h_raw = Queue()
        self.h2d_raw = Queue()
        self.d2h_ip = Queue()
        self.h2d_ip = Queue()
        self.sim_server = SimServer(self.d2h_raw, self.h2d_raw, sim_port)
        self.usbip_server = USBIPServer(self.d2h_ip, self.h2d_ip, usbip_port)

    def serve(self):
        print("server running")
        self.sim_server.serve()
        self.usbip_server.serve()
        print("server done")


if __name__ == "__main__":
    sim = USBIPSimBridgeServer_classic()
    sim.serve()
