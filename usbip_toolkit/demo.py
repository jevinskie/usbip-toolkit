from itertools import count

import trio


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
            async for data in server_stream:
                print(f"demo_server {ident}: received data {data.hex()}")
                smsg = bytes(1)
                await server_stream.send_all(smsg)
            print(f"demo_server {ident}: connection closed")
        except Exception as exc:
            print(f"demo_server {ident}: crashed: {exc!r}")
