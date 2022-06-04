import socket
import sys
import time
from queue import Empty, Queue
from threading import Thread

from usbip_toolkit.proto import *
from usbip_toolkit.usb import *
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
            print(f"d2h_raw: {buf.hex(' ')}", flush=True)
            self.d2h_raw.put(buf)
        print("sim client closed socket")

    def h2d_loop(self):
        while True:
            bufs = self.h2d_raw.get()
            if not isinstance(bufs, list):
                bufs = [bufs]
            obuf = bytearray()
            for buf in bufs:
                obuf += len(buf).to_bytes(4, "big")
                obuf += buf
                print(f"h2d_raw: {buf.hex(' ')}", flush=True)
            self.client_sock.send(obuf)
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
        print("waiting for usbip clinent connection")
        self.serv_sock.listen(1)
        self.client_sock, _ = self.serv_sock.accept()
        print("got usbip client conection")
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
            buf, smsg_ty = self.d2h_ip.get()
            print(f"smsg_ty: {smsg_ty}")
            self.client_sock.send(buf)
            self.d2h_ip.task_done()

    def h2d_loop(self):
        while True:
            cmsg, cmsg_ty = read_usbip_client_packet(self.client_sock)
            if cmsg is None:
                break
            print(f"cmsg_ty: {cmsg_ty} cmsg: {cmsg}")
            self.h2d_ip.put((cmsg, cmsg_ty))
        print("usbip client closed socket")


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
        self._frame_num = 0
        self._odd = False
        self.busnum = 47
        self.devnum = 43
        self._setup_addr_done = False

    def serve(self):
        print("server running")
        self.sim_server.serve()
        self.usbip_server.serve()

        while True:
            cmsg, cmsg_ty = self.h2d_ip.get()
            if cmsg_ty == USBIPClientPacketType.USBIPOperationRequest:
                if cmsg.code == UBSIPCode.REQ_IMPORT:
                    smsg = OpImportReply.build(
                        {
                            "status": 0,
                            "body": {
                                "udev": {
                                    "path": "",
                                    "busid": f"{self.busnum}-{self.devnum}.0",
                                    "busnum": self.busnum,
                                    "devnum": self.devnum,
                                    "speed": 3,
                                    "idVendor": 0x16D0,
                                    "idProduct": 0x0F3B,
                                    "bcdDevice": 0,
                                    "bDeviceClass": 0,
                                    "bDeviceSubClass": 0,
                                    "bDeviceProtocol": 0,
                                    "bConfigurationValue": 0,
                                    "bNumConfigurations": 1,
                                    "bNumInterfaces": 1,
                                }
                            },
                        }
                    )
                    self.d2h_ip.put((smsg, USBIPServerPacketType.USBIPOperationReply))
                else:
                    raise NotImplementedError(repr(cmsg.code))
            elif cmsg_ty == USBIPClientPacketType.USBIPCommandRequest:
                if cmsg.command == UBSIPCommandEnum.CMD_SUBMIT:
                    self.send_urb_to_sim(cmsg)
                elif cmsg.command == UBSIPCommandEnum.CMD_UNLINK:
                    print("got unlink!")
                    break

        print("server done")

    @property
    def frame_num(self):
        res = self._frame_num
        self._frame_num = (res + 1) & ((1 << 11) - 1)
        return res

    @property
    def odd(self):
        res = self._odd
        self._odd = not res
        return res

    def reset_odd(self):
        self._odd = False

    def setup_addr(self):
        setup_token = setup_token_packet(0, 0)
        setup_data = setup_data_packet(Recip.DEVICE, Dir.OUT, Req.SET_ADDRESS, self.devnum, 0, 0)
        self.reset_odd()
        self.h2d_raw.put(
            [sof_packet(self.frame_num), sof_packet(self.frame_num), setup_token, setup_data]
        )
        setup_resp = self.d2h_raw.get()
        assert setup_resp == ack_packet()
        in_token = in_token_packet(0, 0)
        self.h2d_raw.put([sof_packet(self.frame_num), in_token])
        resp_data = self.d2h_raw.get()
        print(f"setup_addr resp_data: {resp_data.hex(' ')}")
        self.h2d_raw.put(ack_packet())
        self._setup_addr_done = True

    def send_urb_to_sim(self, urb):
        print(f"submit: {urb}")
        if not self._setup_addr_done:
            self.setup_addr()
        if urb.ep == 0:
            if len(urb.body.transfer_buffer):
                raise NotImplementedError("setup packet with extra data?")
            setup_token = setup_token_packet(urb.devid & 0xFFFF, 0)
            setup_data = data_packet(urb.body.setup, odd=False)
            # setup_data = data_packet(bytes.fromhex("80 06 00 01 00 00 12 00"), odd=False)
            self.reset_odd()
            self.h2d_raw.put([sof_packet(self.frame_num), setup_token, setup_data])
            setup_resp = self.d2h_raw.get()
            print(f"setup_resp: {setup_resp.hex()}")
            if setup_resp != ack_packet():
                print("got bad setup_resp")
                smsg = RetSubmit.build(
                    {**cmd_ret_hdr(urb), "body": {"status": 1, "error_count": 1}}
                )
                self.d2h_ip.put((smsg, USBIPServerPacketType.USBIPCommandReply))
            else:
                print("good good setup_resp, sending in token to device")
                in_token = in_token_packet(urb.devid & 0xFFFF, 0)
                print(f"in_token: {in_token.hex()}")
                self.h2d_raw.put([sof_packet(self.frame_num), in_token])
                # fixme check PID and CRC
                setup_resp_data = self.d2h_raw.get()[1:-2]
                print(f"setup_resp_data: {setup_resp_data.hex(' ')}")
                self.h2d_raw.put([ack_packet()])
                smsg = RetSubmit.build(
                    {
                        **cmd_ret_hdr(urb),
                        "body": {
                            "status": 0,
                            "error_count": 0,
                            "actual_length": len(setup_resp_data),
                            "transfer_buffer": setup_resp_data,
                        },
                    }
                )
                self.d2h_ip.put((smsg, USBIPServerPacketType.USBIPCommandReply))
        else:
            raise NotImplementedError


if __name__ == "__main__":
    sim = USBIPSimBridgeServer_classic()
    sim.serve()
