from usbip_toolkit.util import bit_reverse


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
