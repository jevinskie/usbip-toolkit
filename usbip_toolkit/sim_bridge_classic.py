import socket
import sys
import time
from queue import Empty, Queue
from threading import Thread

from usbip_toolkit.proto import *
from usbip_toolkit.usb import *
from usbip_toolkit.util import get_tcp_server_socket

# real_print = print
# print = lambda *args, **kwargs: real_print(*args, **kwargs, flush=True)


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
            if all([b == 0 for b in buf]) and len(buf) > 64:
                continue
            print(f"d2h_raw: {buf.hex(' ')}")
            self.d2h_raw.put(buf)
        print("sim client closed socket")

    def h2d_loop(self):
        while True:
            bufs = self.h2d_raw.get()
            if not isinstance(bufs, list):
                bufs = [bufs]
            obuf = bytearray()
            for buf in bufs:
                smsg = len(buf).to_bytes(4, "big") + buf
                obuf += smsg
                print(f"h2d_raw: {buf.hex(' ')}")
                # time.sleep(0.01)
                self.client_sock.send(smsg)
            # self.client_sock.send(obuf)
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
            print(f"d2h_ip sock write: smsg_ty: {smsg_ty}")
            self.client_sock.send(buf)
            self.d2h_ip.task_done()

    def h2d_loop(self):
        while True:
            cmsg, cmsg_ty = read_usbip_client_packet(self.client_sock)
            if cmsg is None:
                break
            print(f"h2d_ip sock read: cmsg_ty: {cmsg_ty} cmsg: {cmsg}")
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
        self._odds = [False] * USB_MAX_ENDPOINTS
        self.busnum = 47
        self.devnum = 6
        self._setup_addr_done = False

    def d2h_raw_pop(self):
        res = self.d2h_raw.get()
        self.d2h_raw.task_done()
        return res

    def h2d_ip_pop(self):
        res = self.h2d_ip.get()
        self.h2d_ip.task_done()
        return res

    def serve(self):
        print("server running")
        self.sim_server.serve()
        self.usbip_server.serve()

        while True:
            cmsg, cmsg_ty = self.h2d_ip_pop()
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

    def odd(self, endpoint):
        res = self._odds[endpoint]
        self._odds[endpoint] = not res
        return res

    def reset_odd(self, endpoint):
        self._odds[endpoint] = False

    def setup_addr(self):
        dev = 0
        ep = 0
        setup_token = setup_token_packet(dev, ep)
        setup_data = setup_data_packet(Recip.DEVICE, Dir.OUT, Req.SET_ADDRESS, self.devnum, 0, 0)
        self.reset_odd(ep)
        self.odd(ep)
        self.h2d_raw.put([setup_token, setup_data])
        setup_resp = self.d2h_raw_pop()
        assert setup_resp == ack_packet()
        in_token = in_token_packet(0, 0)
        self.h2d_raw.put([sof_packet(self.frame_num), in_token])
        resp_data = self.d2h_raw_pop()
        resp_data_gold = data_packet(b"", odd=self.odd(ep))
        if resp_data != resp_data_gold:
            raise ValueError(f"resp actual: {resp_data.hex(' ')} gold: {resp_data_gold.hex(' ')}")
        self.h2d_raw.put(ack_packet())
        self._setup_addr_done = True

    def handle_control(self, urb):
        if len(urb.body.transfer_buffer):
            raise NotImplementedError("setup packet with extra data? NYET!")
        ep = 0
        is_in = urb.body.setup[0] & Dir.IN != 0
        # setup phase
        setup_token = setup_token_packet(urb.devid_devnum, ep)
        self.reset_odd(ep)
        setup_data = data_packet(urb.body.setup, odd=False)
        self.h2d_raw.put([setup_token, setup_data])
        setup_resp = self.d2h_raw_pop()
        print(f"setup_resp: {setup_resp.hex()}")
        if setup_resp != ack_packet():
            print("got bad setup_resp")
            smsg = RetSubmit.build({**cmd_ret_hdr(urb), "body": {"status": 1, "error_count": 1}})
            self.d2h_ip.put((smsg, USBIPServerPacketType.USBIPCommandReply))
            return
        setup_resp_data = b""
        if urb.body.transfer_buffer_length:
            # data phase
            print("good good setup_resp, sending in token(s) to device")
            in_token = in_token_packet(urb.devid_devnum, ep)
            while len(setup_resp_data) < urb.body.transfer_buffer_length:
                self.h2d_raw.put(in_token)
                full_buf = self.d2h_raw_pop()
                # fixme check PID and CRC
                buf = full_buf[1:-2]
                setup_resp_data += buf
                self.h2d_raw.put(ack_packet())
                if len(buf) != 64:
                    break
        print(f"setup_resp_data: {setup_resp_data.hex(' ')}")
        # status phase
        status_zlp = data_packet(b"", odd=True)
        if is_in:
            out_token = out_token_packet(urb.devid_devnum, ep)
            self.h2d_raw.put([out_token, status_zlp])
            self.reset_odd(ep)
            status_resp = self.d2h_raw_pop()
            print(f"status_resp: {status_resp.hex()}")
            if status_resp != ack_packet():
                print("got bad status_resp")
                smsg = RetSubmit.build(
                    {**cmd_ret_hdr(urb), "body": {"status": 1, "error_count": 1}}
                )
                self.d2h_ip.put((smsg, USBIPServerPacketType.USBIPCommandReply))
                return
        else:
            in_token = in_token_packet(urb.devid_devnum, ep)
            self.h2d_raw.put(in_token)
            zlp_resp = self.d2h_raw_pop()
            if zlp_resp != status_zlp:
                print(f"RUHROH: {zlp_resp} {status_zlp}")
            self.h2d_raw.put(ack_packet())
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

    def handle_bulk(self, urb):
        MAX_PKT_SZ = 512
        is_in = urb.direction == 1
        print(f"urb dir: {Dir(urb.body.setup[0])} len: {urb.body.transfer_buffer_length}")
        if is_in:
            obuf = bytearray()
        else:
            ibuf = bytearray(urb.body.transfer_buffer)
        len_rem = urb.body.transfer_buffer_length
        while len_rem > 0:
            obufs = []
            if is_in:
                token_pkt = in_token_packet(urb.devid_devnum, urb.ep)
                obufs.append(token_pkt)
            else:
                token_pkt = out_token_packet(urb.devid_devnum, urb.ep)
                obufs.append(token_pkt)
                buf = ibuf[:512]
                print(f"z buf: {buf.hex(' ')}")
                data_out_pkt = data_packet(buf, odd=self.odd(urb.ep))
                obufs.append(data_out_pkt)
                del ibuf[:512]
                len_rem -= len(buf)
            self.h2d_raw.put(obufs)
            if is_in:
                resp_data_pkt = self.d2h_raw_pop()
                # FIXME: check PID and CRC
                resp_data = resp_data_pkt[1:-2]
                len_rem -= len(resp_data)
                obuf += resp_data
                self.h2d_raw.put(ack_packet())
            else:
                resp = self.d2h_raw_pop()
                assert resp == ack_packet()
            print(f"len_rem: {len_rem}")
        smsg = RetSubmit.build(
            {
                **cmd_ret_hdr(urb),
                "body": {
                    "status": 0,
                    "error_count": 0,
                    "actual_length": len(obuf) if is_in else 0,
                    "transfer_buffer": obuf if is_in else b"",
                },
            }
        )
        self.d2h_ip.put((smsg, USBIPServerPacketType.USBIPCommandReply))

    def handle_iso(self, urb):
        raise NotImplementedError("iso transfers not implemented")

    def handle_interrupt(self, urb):
        raise NotImplementedError("interrrupt transfers not implemented")

    def handle_transfer(self, urb):
        if urb.ep == 0:
            self.handle_control(urb)
        elif urb.body.number_of_packets:
            self.handle_iso(urb)
        elif False:  # no way to detect transfer type without endpoint descriptor parsing??
            self.handle_interrupt(urb)
        else:
            self.handle_bulk(urb)

    def send_urb_to_sim(self, urb):
        # print(f"submit: {urb}")
        self.h2d_raw.put(sof_packet(self.frame_num))
        if not self._setup_addr_done:
            self.setup_addr()
        self.handle_transfer(urb)


if __name__ == "__main__":
    sim = USBIPSimBridgeServer_classic()
    sim.serve()
