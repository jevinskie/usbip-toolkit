from itertools import count

import trio

from usbip_toolkit.proto import *
from usbip_toolkit.util import LengthPrefixedReceiver


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
            nursery.start_soon(self.serve_usbip_async)
            nursery.start_soon(self.serve_utmi_async)
        print("serve_async end")

    def serve(self):
        trio.run(self.serve_async)

    async def utmi_server(self, server_stream):
        ident = next(self.counter)
        print(f"utmi_server {ident}: started")
        framed_server_stream = LengthPrefixedReceiver(server_stream)
        try:
            async for data in framed_server_stream:
                print(f"utmi_server {ident}: received data {data.hex()}")

                smsg = b"\x00"
                await server_stream.send_all(smsg)
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
