from enum import IntEnum

from usbip_toolkit._tables import _crc16_table
from usbip_toolkit.util import bit_reverse

USB_MAX_ENDPOINTS = 32

# fmt: off
class PID(IntEnum):
    TOK_OUT   = 0b0001 # 1
    TOK_IN    = 0b1001 # 9
    TOK_SOF   = 0b0101 # 5
    TOK_SETUP = 0b1101 # d
    DAT_DATA0 = 0b0011 # 3
    DAT_DATA1 = 0b1011 # b
    DAT_DATA2 = 0b0111 # 7
    DAT_MDATA = 0b1111 # f
    HND_ACK   = 0b0010 # 2
    HND_NACK  = 0b1010 # a
    HND_STALL = 0b1110 # e
    HND_NYET  = 0b0110 # 6
    SPC_PRE   = 0b1100 # c
    SPC_ERR   = 0b1100 # c
    SPC_SPLIT = 0b1000 # 8
    SPC_PING  = 0b0100 # 4


class Dir(IntEnum):
    OUT = 0x00
    IN  = 0x80


class Type(IntEnum):
    STANDARD = 0
    CLASS    = 1
    VENDOR   = 2
    RESERVED = 3


class Recip(IntEnum):
    DEVICE    = 0
    INTERFACE = 1
    ENDPOINT  = 2
    OTHER     = 3


class Req(IntEnum):
    GET_STATUS        = 0x00
    CLEAR_FEATURE     = 0x01
    SET_FEATURE       = 0x03
    SET_ADDRESS       = 0x05
    GET_DESCRIPTOR    = 0x06
    SET_DESCRIPTOR    = 0x07
    GET_CONFIGURATION = 0x08
    SET_CONFIGURATION = 0x09
    GET_INTERFACE     = 0x0A
    SET_INTERFACE     = 0x0B
    SYNCH_FRAME       = 0x0C
    SET_SEL           = 0x30
    SET_ISOCH_DELAY   = 0x31


class DescType(IntEnum):
    DEVICE           = 0x0100
    CONFIGURATION    = 0x0200
    STRING           = 0x0300
    INTERFACE        = 0x0400
    ENDPOINT         = 0x0500
    DEVICE_QUALIFIER = 0x0600
    OTHER_SPEED      = 0x0700

# fmt: on


def crc5(val, nbits):
    assert val.bit_length() <= nbits
    poly = 0x05 << (nbits - 5)
    crc = 0x1F << (nbits - 5)
    mask = (1 << nbits) - 1
    top_bit = 1 << (nbits - 1)

    for i in range(nbits):
        if (val ^ crc) & top_bit:
            crc = (crc << 1) & mask
            crc ^= poly
        else:
            crc = (crc << 1) & mask
        val = (val << 1) & mask
    crc >>= nbits - 5
    crc ^= 0x1F
    return crc


def crc16(buf):
    crc = 0xFFFF
    for b in buf:
        i = (crc ^ b) & 0xFF
        crc = (crc >> 8) ^ _crc16_table[(crc ^ b) & 0xFF]
    crc ^= 0xFFFF
    return bytes([crc & 0xFF, crc >> 8])


def pid_val(pid):
    assert 0 <= pid <= 0xF
    return ((pid ^ 0xF) << 4) | pid


def pid_byte(pid):
    return bytes([pid_val(pid)])


def bmRequestType_val(recip, ty, direction):
    return direction | (ty << 5) | recip


def bmRequestType_byte(recip, ty, direction):
    return bytes([bmRequestType_val(direction, ty, recip)])


def token_addr_packet(pid, addr, endp):
    assert 0 <= addr <= 0x7F
    assert 0 <= endp <= 0xF
    mid_byte = ((endp & 1) << 7) | addr
    val4crc = bit_reverse((endp << 7) | addr, 11)
    crc_val = crc5(val4crc, 11)
    last_byte = (bit_reverse(crc_val, 5) << 3) | (endp >> 1)
    return bytes([pid_val(pid), mid_byte, last_byte])


def out_token_packet(addr, endp):
    return token_addr_packet(PID.TOK_OUT, addr, endp)


def in_token_packet(addr, endp):
    return token_addr_packet(PID.TOK_IN, addr, endp)


def sof_packet(num):
    assert 0 <= num < (1 << 11)
    mid_byte = num & 0xFF
    val4crc = bit_reverse(num, 11)
    crc_val = crc5(val4crc, 11)
    last_byte = (bit_reverse(crc_val, 5) << 3) | (num >> 8)
    return bytes([pid_val(PID.TOK_SOF), mid_byte, last_byte])


def setup_token_packet(addr, endp):
    return token_addr_packet(PID.TOK_SETUP, addr, endp)


def data_packet(buf, odd=False):
    pb = pid_byte(PID.DAT_DATA1 if odd else PID.DAT_DATA0)
    return pb + buf + crc16(buf)


def ack_packet():
    return pid_byte(PID.HND_ACK)


def nack_packet():
    return pid_byte(PID.HND_NACK)


def stall_packet():
    return pid_byte(PID.HND_STALL)


def nyet_packet():
    return pid_byte(PID.HND_NYET)


def setup_data_packet(recip, direction, req, val, idx, sz, ty=Type.STANDARD):
    buf = (
        bmRequestType_byte(recip, ty, direction)
        + bytes([req])
        + val.to_bytes(2, "little")
        + idx.to_bytes(2, "little")
        + sz.to_bytes(2, "little")
    )
    return data_packet(buf, odd=False)
