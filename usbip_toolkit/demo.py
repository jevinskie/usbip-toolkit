from itertools import count

import aiostream
import trio

from usbip_toolkit.proto import *
from usbip_toolkit.util import LengthPrefixedTransceiver


class UTMIServerCombiner:
    def __init__(self, framed_server_stream, host_to_device_rx):
        self.framed_server_stream = framed_server_stream
        self.host_to_device_rx = host_to_device_rx

    def __aiter__(self):
        return self

    async def __anext__(self):
        pass


class DemoServer:
    def __init__(self, port: int = 3240):
        self.port = port
        self.counter = count()

    async def serve_usbip_async(self):
        await trio.serve_tcp(self.usbip_server, self.port)

    async def serve_utmi_async(self):
        await trio.serve_tcp(self.utmi_server, 2443)

    async def serve_async(self):
        # await trio.serve_tcp(self.demo_server, self.port)
        print("serve_async begin")
        async with trio.open_nursery() as nursery:
            self.host_to_device_tx, self.host_to_device_rx = trio.open_memory_channel(0)
            self.device_to_host_tx, self.device_to_host_rx = trio.open_memory_channel(0)
            nursery.start_soon(self.serve_usbip_async)
            nursery.start_soon(self.serve_utmi_async)
        print("serve_async end")

    def serve(self):
        trio.run(self.serve_async)

    async def utmi_server(self, server_stream):
        ident = next(self.counter)
        print(f"utmi_server {ident}: started")
        framed_server_stream = LengthPrefixedTransceiver(server_stream)
        combo = aiostream.stream.map(framed_server_stream, lambda x: x, self.host_to_device_rx)
        try:
            async for data in combo:
                print(f"utmi_server {ident}: received data {data.hex()}")

                smsg = b"\x00"
                await framed_server_stream.send(smsg)
            print(f"utmi_server {ident}: connection closed")
        except Exception as exc:
            print(f"utmi_server {ident}: crashed: {exc!r}")

    async def usbip_server(self, server_stream):
        ident = next(self.counter)
        print(f"demo_server {ident}: started")
        try:
            i = 0
            async for data in server_stream:
                print(f"usbip_server {ident}: received data {data.hex()}")
                if i == 0:
                    cmsg = OpRequest.parse(data)
                    print(f"cmsg: {cmsg}")
                    if cmsg.code == UBSIPCode.REQ_IMPORT:
                        smsg = OpImportReply.build(
                            {
                                "status": 0,
                                "udev": {
                                    "path": "",
                                    "busid": "00-0.0",
                                    "busnum": 0,
                                    "devnum": 0,
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
                                },
                            }
                        )
                else:
                    # cmd = CmdSubmitHdr.parse(data)
                    cmd = USBIPCommand.parse(data)
                    print(f"cmd: {cmd}")
                    smsg = bytes(1)
                    print(f"smsg: {smsg.hex()}")
                await server_stream.send_all(smsg)
                i += 1
            print(f"usbip_server {ident}: connection closed")
        except Exception as exc:
            print(f"usbip_server {ident}: crashed: {exc!r}")
