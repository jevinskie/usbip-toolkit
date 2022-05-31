import asyncio
from collections import namedtuple
from itertools import count

import reactivex as rx
import reactivex.operators as ops
from reactivex.scheduler.eventloop import AsyncIOScheduler
from reactivex.subject import Subject

from usbip_toolkit.proto import *

EchoItem = namedtuple("EchoItem", ["future", "data"])


class USBIPSimBridgeServer:
    def __init__(self, usbip_port: int = 3240, sim_port: int = 2443):
        self.usbip_port = usbip_port
        self.sim_port = sim_port
        self.counter = count()

    def serve(self):
        loop = asyncio.get_event_loop()
        proxy = Subject()
        source = self.tcp_echo_server(proxy, loop)
        aio_scheduler = AsyncIOScheduler(loop=loop)

        source.pipe(ops.map(lambda i: i._replace(data="echo: {}".format(i.data)))).subscribe(
            proxy, scheduler=aio_scheduler
        )

        loop.run_forever()
        print("done")
        loop.close()

    def tcp_echo_server(self, sink, loop):
        def on_subscribe(observer, scheduler):
            async def handle_echo(reader, writer):
                print("new client connected")
                while True:
                    data = await reader.readline()
                    data = data.decode("utf-8")
                    if not data:
                        break

                    future = asyncio.Future()
                    observer.on_next(EchoItem(future=future, data=data))
                    await future
                    writer.write(future.result().encode("utf-8"))

                print("Close the client socket")
                writer.close()

            def on_next(i):
                i.future.set_result(i.data)

            print("starting server")
            server = asyncio.start_server(handle_echo, "127.0.0.1", 8888)
            loop.create_task(server)

            sink.subscribe(
                on_next=on_next, on_error=observer.on_error, on_completed=observer.on_completed
            )

        return rx.create(on_subscribe)
