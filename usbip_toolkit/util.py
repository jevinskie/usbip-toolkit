import trio


def bit_reverse(val, nbits):
    rval = 0
    for i in range(nbits):
        bit_shift = nbits - i - 1
        bit_mask = 1 << bit_shift
        masked = val & bit_mask
        rval |= (masked >> bit_shift) << i
    return rval


class ExactReceiver:
    def __init__(self, stream: trio.abc.ReceiveStream, max_frame_length: int = 16384):
        assert not stream or isinstance(stream, trio.abc.ReceiveStream)

        self.stream = stream
        self.max_frame_length = max_frame_length

        self._buf = bytearray()

    def __bool__(self):
        return bool(self._buf)

    async def receive_exactly(self, n: int) -> bytes:
        while len(self._buf) < n:
            await self._receive()

        return self._frame(n)

    async def _receive(self):
        if len(self._buf) > self.max_frame_length:
            raise ValueError("frame too long")

        more_data = await self.stream.receive_some(1024)
        if more_data == b"":
            if self._buf:
                raise ValueError("incomplete frame")
            raise trio.EndOfChannel

        self._buf += more_data

    def _frame(self, idx: int) -> bytes:
        frame = self._buf[:idx]
        del self._buf[:idx]
        return frame


class LengthPrefixedTransceiver(ExactReceiver):
    async def receive(self):
        nbytes = int.from_bytes(await self.receive_exactly(4), "big")
        return await self.receive_exactly(nbytes)

    async def send(self, bufs):
        if not isinstance(bufs, list):
            bufs = [bufs]
        obuf = b""
        for buf in bufs:
            obuf += len(buf).to_bytes(4, "big") + buf
        await self.stream.send_all(obuf)

    def __aiter__(self):
        return self

    async def __anext__(self):
        data = await self.receive()
        if data:
            return data
        else:
            raise StopAsyncIteration
