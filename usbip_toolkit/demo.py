from itertools import count

import trio

from usbip_toolkit.proto import *


class DemoServer:
    def __init__(self, port: int = 3240):
        self.port = port
        self.counter = count()

    async def serve_async(self):
        await trio.serve_tcp(self.demo_server, self.port)

    def serve(self):
        trio.run(self.serve_async)

    async def demo_server(self, server_stream):
        ident = next(self.counter)
        print(f"demo_server {ident}: started")
        try:
            i = 0
            async for data in server_stream:
                print(f"demo_server {ident}: received data {data.hex()}")
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
            print(f"demo_server {ident}: connection closed")
        except Exception as exc:
            print(f"demo_server {ident}: crashed: {exc!r}")
