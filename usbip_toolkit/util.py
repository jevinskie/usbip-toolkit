import socket
from re import S


def bit_reverse(val, nbits):
    rval = 0
    for i in range(nbits):
        bit_shift = nbits - i - 1
        bit_mask = 1 << bit_shift
        masked = val & bit_mask
        rval |= (masked >> bit_shift) << i
    return rval


def get_tcp_server_socket(port: int, hostname: str = "localhost") -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    s.bind(("localhost", port))
    return s
