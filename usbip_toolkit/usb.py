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
