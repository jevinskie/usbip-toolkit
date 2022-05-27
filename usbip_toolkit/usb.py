from enum import IntEnum

from usbip_toolkit.util import bit_reverse


class PID(IntEnum):
    TOK_OUT = 0b001
    TOK_IN = 0b1001
    TOK_SOF = 0b0101
    TOK_SETUP = 0b1101
    DAT_DATA0 = 0b0011
    DAT_DATA1 = 0b1011
    DAT_DATA2 = 0b0111
    DAT_MDATA = 0b1111
    SPC_PRE = 0b1100
    SPC_ERR = 0b1100
    SPC_SPLIT = 0b1000
    SPC_PING = 0b0100


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


def create_token_packet(pid, addr, endp):
    assert 0 <= pid <= 0xF
    pid_byte = ((pid ^ 0xF) << 4) | pid
    assert 0 <= addr <= 0x7F
    assert 0 <= endp <= 0xF
    mid_byte = ((endp & 1) << 7) | addr
    val4crc = bit_reverse((endp << 7) | addr, 11)
    crc_val = crc5(val4crc, 11)
    last_byte = (bit_reverse(crc_val, 5) << 3) | (endp >> 1)
    return bytes([pid_byte, mid_byte, last_byte])
