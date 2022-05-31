import asyncio
from itertools import count

import aioreactive as rx
from expression import pipe

from usbip_toolkit.proto import *


class USBIPSimBridgeServer_aioreactive:
    def __init__(self, usbip_port: int = 3240, sim_port: int = 2443):
        self.usbip_port = usbip_port
        self.sim_port = sim_port
        self.counter = count()

    def serve(self):
        loop = asyncio.get_event_loop()
        print("loop running")
        self.tcp_echo_server(loop)
        loop.run_forever()
        print("done")
        loop.close()

    def tcp_echo_server(self, loop):
        async def handle_echo(reader, writer):
            print("new client connected")
            while True:
                data = await reader.readline()
                data = data.decode("utf-8")
                if not data:
                    break

                writer.write(data.upper().encode("utf-8"))

            print("Close the client socket")
            writer.close()

        print("starting server")
        server = asyncio.start_server(handle_echo, "127.0.0.1", 8888)
        loop.create_task(server)
