def bit_reverse(val, nbits):
    rval = 0
    for i in range(nbits):
        bit_shift = nbits - i - 1
        bit_mask = 1 << bit_shift
        masked = val & bit_mask
        rval |= (masked >> bit_shift) << i
    return rval
