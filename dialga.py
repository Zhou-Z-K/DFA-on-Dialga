# ============================================================
# Dialga / Midori-128 SubCell implementation
# No imports, no boundary checks.
# Byte is an 8-bit integer.
# Bit numbering convention:
#   bit 0 = MSB
#   bit 7 = LSB
# ============================================================



CF = [
    [0x24, 0x3f, 0x6a, 0x88, 0x85, 0xa3, 0x08, 0xd3, 0x13, 0x19, 0x8a, 0x2e, 0x03, 0x70, 0x73, 0x44],
    [0xa4, 0x09, 0x38, 0x22, 0x29, 0x9f, 0x31, 0xd0, 0x08, 0x2e, 0xfa, 0x98, 0xec, 0x4e, 0x6c, 0x89],
    [0x45, 0x28, 0x21, 0xe6, 0x38, 0xd0, 0x13, 0x77, 0xbe, 0x54, 0x66, 0xcf, 0x34, 0xe9, 0x0c, 0x6c],
    [0xc0, 0xac, 0x29, 0xb7, 0xc9, 0x7c, 0x50, 0xdd, 0x3f, 0x84, 0xd5, 0xb5, 0xb5, 0x47, 0x09, 0x17],
    [0x92, 0x16, 0xd5, 0xd9, 0x89, 0x79, 0xfb, 0x1b, 0xd1, 0x31, 0x0b, 0xa6, 0x98, 0xdf, 0xb5, 0xac],
    [0x2f, 0xfd, 0x72, 0xdb, 0xd0, 0x1a, 0xdf, 0xb7, 0xb8, 0xe1, 0xaf, 0xed, 0x6a, 0x26, 0x7e, 0x96],
    [0xba, 0x7c, 0x90, 0x45, 0xf1, 0x2c, 0x7f, 0x99, 0x24, 0xa1, 0x99, 0x47, 0xb3, 0x91, 0x6c, 0xf7],
    [0x08, 0x01, 0xf2, 0xe2, 0x85, 0x8e, 0xfc, 0x16, 0x63, 0x69, 0x20, 0xd8, 0x71, 0x57, 0x4e, 0x69],
    [0xa4, 0x58, 0xfe, 0xa3, 0xf4, 0x93, 0x3d, 0x7e, 0x0d, 0x95, 0x74, 0x8f, 0x72, 0x8e, 0xb6, 0x58],
    [0x71, 0x8b, 0xcd, 0x58, 0x82, 0x15, 0x4a, 0xee, 0x7b, 0x54, 0xa4, 0x1d, 0xc2, 0x5a, 0x59, 0xb5]
]

CM = [
    [0x9c, 0x30, 0xd5, 0x39, 0x2a, 0xf2, 0x60, 0x13, 0xc5, 0xd1, 0xb0, 0x23, 0x28, 0x60, 0x85, 0xf0],
    [0xca, 0x41, 0x79, 0x18, 0xb8, 0xdb, 0x38, 0xef, 0x8e, 0x79, 0xdc, 0xb0, 0x60, 0x3a, 0x18, 0x0e]
]


CB = [
    [0x6c, 0x9e, 0x0e, 0x8b, 0xb0, 0x1e, 0x8a, 0x3e, 0xd7, 0x15, 0x77, 0xc1, 0xbd, 0x31, 0x4b, 0x27],
    [0x78, 0xaf, 0x2f, 0xda, 0x55, 0x60, 0x5c, 0x60, 0xe6, 0x55, 0x25, 0xf3, 0xaa, 0x55, 0xab, 0x94],
    [0x57, 0x48, 0x98, 0x62, 0x63, 0xe8, 0x14, 0x40, 0x55, 0xca, 0x39, 0x6a, 0x2a, 0xab, 0x10, 0xb6],
    [0xb4, 0xcc, 0x5c, 0x34, 0x11, 0x41, 0xe8, 0xce, 0xa1, 0x54, 0x86, 0xaf, 0x7c, 0x72, 0xe9, 0x93],
    [0xb3, 0xee, 0x14, 0x11, 0x63, 0x6f, 0xbc, 0x2a, 0x2b, 0xa9, 0xc5, 0x5d, 0x74, 0x18, 0x31, 0xf6],
    [0xce, 0x5c, 0x3e, 0x16, 0x9b, 0x87, 0x93, 0x1e, 0xaf, 0xd6, 0xba, 0x33, 0x6c, 0x24, 0xcf, 0x5c],
    [0x7a, 0x32, 0x53, 0x81, 0x28, 0x95, 0x86, 0x77, 0x3b, 0x8f, 0x48, 0x98, 0x6b, 0x4b, 0xb9, 0xaf],
    [0xc4, 0xbf, 0xe8, 0x1b, 0x66, 0x28, 0x21, 0x93, 0x61, 0xd8, 0x09, 0xcc, 0xfb, 0x21, 0xa9, 0x91]
]


# 4-bit core S-box Sb0
_SB0 = [
    0xC, 0xA, 0xD, 0x3,
    0xE, 0xB, 0xF, 0x7,
    0x8, 0x9, 0x1, 0x5,
    0x0, 0x2, 0x4, 0x6,
]

# inverse 4-bit S-box
_INV_SB0 = [0] * 16
for i in range(16):
    _INV_SB0[_SB0[i]] = i


def _byte_to_bits(x):
    # returns [x0, x1, ..., x7], where x0 is MSB
    return [(x >> 7) & 1,
            (x >> 6) & 1,
            (x >> 5) & 1,
            (x >> 4) & 1,
            (x >> 3) & 1,
            (x >> 2) & 1,
            (x >> 1) & 1,
             x       & 1]


def _bits_to_byte(bits):
    return ((bits[0] << 7) |
            (bits[1] << 6) |
            (bits[2] << 5) |
            (bits[3] << 4) |
            (bits[4] << 3) |
            (bits[5] << 2) |
            (bits[6] << 1) |
             bits[7])


def _bits_to_nibble(bits4):
    return ((bits4[0] << 3) |
            (bits4[1] << 2) |
            (bits4[2] << 1) |
             bits4[3])


def _nibble_to_bits(n):
    return [(n >> 3) & 1,
            (n >> 2) & 1,
            (n >> 1) & 1,
             n       & 1]


def _sb0_bits(bits4):
    return _nibble_to_bits(_SB0[_bits_to_nibble(bits4)])


def _inv_sb0_bits(bits4):
    return _nibble_to_bits(_INV_SB0[_bits_to_nibble(bits4)])


# ------------------------------------------------------------
# Four 8-bit S-boxes
# ------------------------------------------------------------

def SSb0(x):
    x0, x1, x2, x3, x4, x5, x6, x7 = _byte_to_bits(x)

    n0 = _sb0_bits([x4, x1, x6, x3])
    n1 = _sb0_bits([x0, x5, x2, x7])

    y_bits = [
        n1[0], n0[1], n1[2], n0[3],
        n0[0], n1[1], n0[2], n1[3],
    ]
    return _bits_to_byte(y_bits)


def SSb1(x):
    x0, x1, x2, x3, x4, x5, x6, x7 = _byte_to_bits(x)

    n0 = _sb0_bits([x1, x6, x7, x0])
    n1 = _sb0_bits([x5, x2, x3, x4])

    y_bits = [
        n0[3], n0[0], n1[1], n1[2],
        n1[3], n1[0], n0[1], n0[2],
    ]
    return _bits_to_byte(y_bits)


def SSb2(x):
    x0, x1, x2, x3, x4, x5, x6, x7 = _byte_to_bits(x)

    n0 = _sb0_bits([x2, x3, x4, x1])
    n1 = _sb0_bits([x6, x7, x0, x5])

    y_bits = [
        n1[2], n0[3], n0[0], n0[1],
        n0[2], n1[3], n1[0], n1[1],
    ]
    return _bits_to_byte(y_bits)


def SSb3(x):
    x0, x1, x2, x3, x4, x5, x6, x7 = _byte_to_bits(x)

    n0 = _sb0_bits([x7, x4, x1, x2])
    n1 = _sb0_bits([x3, x0, x5, x6])

    y_bits = [
        n1[1], n0[2], n0[3], n1[0],
        n0[1], n1[2], n1[3], n0[0],
    ]
    return _bits_to_byte(y_bits)


# Precompute the four 8-bit S-boxes once.  The bit-level definitions above
# are kept as the specification source, but hot paths use table lookups.
_SSB0 = [SSb0(x) for x in range(256)]
_SSB1 = [SSb1(x) for x in range(256)]
_SSB2 = [SSb2(x) for x in range(256)]
_SSB3 = [SSb3(x) for x in range(256)]
_SSB_TABLES = (_SSB0, _SSB1, _SSB2, _SSB3)


def SSb0(x):
    return _SSB0[x]


def SSb1(x):
    return _SSB1[x]


def SSb2(x):
    return _SSB2[x]


def SSb3(x):
    return _SSB3[x]


# ------------------------------------------------------------
# Build inverse lookup tables
# ------------------------------------------------------------

_INV_SSb0 = [0] * 256
_INV_SSb1 = [0] * 256
_INV_SSb2 = [0] * 256
_INV_SSb3 = [0] * 256

for x in range(256):
    _INV_SSb0[SSb0(x)] = x
    _INV_SSb1[SSb1(x)] = x
    _INV_SSb2[SSb2(x)] = x
    _INV_SSb3[SSb3(x)] = x


def invSSb0(x):
    return _INV_SSb0[x]


def invSSb1(x):
    return _INV_SSb1[x]


def invSSb2(x):
    return _INV_SSb2[x]


def invSSb3(x):
    return _INV_SSb3[x]


# ------------------------------------------------------------
# Optional unified wrappers
# ------------------------------------------------------------

def SSb(idx, x):
    if idx == 0:
        return SSb0(x)
    if idx == 1:
        return SSb1(x)
    if idx == 2:
        return SSb2(x)
    return SSb3(x)


def invSSb(idx, x):
    if idx == 0:
        return invSSb0(x)
    if idx == 1:
        return invSSb1(x)
    if idx == 2:
        return invSSb2(x)
    return invSSb3(x)

# ============================================================
# Dialga byte permutations and MatrixMul
# State is a list of 16 bytes:
#   state[0], state[1], ..., state[15]
# No imports, no boundary checks.
# Permutation convention follows the paper:
#   new[i] = old[pi[i]]
# ============================================================

# byte permutations pi0, pi1, pi2, pi3
PI0 = [7, 0, 13, 10, 5, 2, 15, 8, 4, 3, 14, 9, 6, 1, 12, 11]
PI1 = [13, 0, 10, 7, 11, 6, 12, 1, 2, 15, 5, 8, 4, 9, 3, 14]
PI2 = [7, 13, 10, 0, 6, 12, 11, 1, 5, 15, 8, 2, 4, 14, 9, 3]
PI3 = [13, 8, 6, 3, 14, 11, 5, 0, 12, 9, 7, 2, 15, 10, 4, 1]

# extra permutation pi_m (used in MS)
PIM = [0, 10, 5, 15, 14, 4, 11, 1, 9, 3, 12, 6, 7, 13, 2, 8]


def permute(state, pi):
    return [state[pi[0]],  state[pi[1]],  state[pi[2]],  state[pi[3]],
            state[pi[4]],  state[pi[5]],  state[pi[6]],  state[pi[7]],
            state[pi[8]],  state[pi[9]],  state[pi[10]], state[pi[11]],
            state[pi[12]], state[pi[13]], state[pi[14]], state[pi[15]]]


def Perm0(state):
    return permute(state, PI0)


def Perm1(state):
    return permute(state, PI1)


def Perm2(state):
    return permute(state, PI2)


def Perm3(state):
    return permute(state, PI3)


def MS(state):
    return permute(state, PIM)


# ============================================================
# MatrixMul
# For each group of 4 consecutive bytes:
#   (s[4i], s[4i+1], s[4i+2], s[4i+3])
# apply:
#   [0 1 1 1]
#   [1 0 1 1]
#   [1 1 0 1]
#   [1 1 1 0]
# over XOR.
# ============================================================

def MatrixMul(state):
    out = [0] * 16

    # group 0: s0,s1,s2,s3
    a0, a1, a2, a3 = state[0], state[1], state[2], state[3]
    out[0] = a1 ^ a2 ^ a3
    out[1] = a0 ^ a2 ^ a3
    out[2] = a0 ^ a1 ^ a3
    out[3] = a0 ^ a1 ^ a2

    # group 1: s4,s5,s6,s7
    a0, a1, a2, a3 = state[4], state[5], state[6], state[7]
    out[4] = a1 ^ a2 ^ a3
    out[5] = a0 ^ a2 ^ a3
    out[6] = a0 ^ a1 ^ a3
    out[7] = a0 ^ a1 ^ a2

    # group 2: s8,s9,s10,s11
    a0, a1, a2, a3 = state[8], state[9], state[10], state[11]
    out[8]  = a1 ^ a2 ^ a3
    out[9]  = a0 ^ a2 ^ a3
    out[10] = a0 ^ a1 ^ a3
    out[11] = a0 ^ a1 ^ a2

    # group 3: s12,s13,s14,s15
    a0, a1, a2, a3 = state[12], state[13], state[14], state[15]
    out[12] = a1 ^ a2 ^ a3
    out[13] = a0 ^ a2 ^ a3
    out[14] = a0 ^ a1 ^ a3
    out[15] = a0 ^ a1 ^ a2

    return out


# ============================================================
# Optional round skeletons (without key/tweak/constant xor)
# Assume you already have SSb0..SSb3 defined.
# ============================================================

def SubCell(state):
    s0, s1, s2, s3 = _SSB0, _SSB1, _SSB2, _SSB3
    return [
        s0[state[0]],  s1[state[1]],  s2[state[2]],  s3[state[3]],
        s0[state[4]],  s1[state[5]],  s2[state[6]],  s3[state[7]],
        s0[state[8]],  s1[state[9]],  s2[state[10]], s3[state[11]],
        s0[state[12]], s1[state[13]], s2[state[14]], s3[state[15]],
    ]


def R0(state):
    s0, s1, s2, s3 = _SSB0, _SSB1, _SSB2, _SSB3
    a0, a1, a2, a3 = s3[state[7]], s0[state[0]], s1[state[13]], s2[state[10]]
    b0, b1, b2, b3 = s1[state[5]], s2[state[2]], s3[state[15]], s0[state[8]]
    c0, c1, c2, c3 = s0[state[4]], s3[state[3]], s2[state[14]], s1[state[9]]
    d0, d1, d2, d3 = s2[state[6]], s1[state[1]], s0[state[12]], s3[state[11]]
    return [
        a1 ^ a2 ^ a3, a0 ^ a2 ^ a3, a0 ^ a1 ^ a3, a0 ^ a1 ^ a2,
        b1 ^ b2 ^ b3, b0 ^ b2 ^ b3, b0 ^ b1 ^ b3, b0 ^ b1 ^ b2,
        c1 ^ c2 ^ c3, c0 ^ c2 ^ c3, c0 ^ c1 ^ c3, c0 ^ c1 ^ c2,
        d1 ^ d2 ^ d3, d0 ^ d2 ^ d3, d0 ^ d1 ^ d3, d0 ^ d1 ^ d2,
    ]


def R1(state):
    s0, s1, s2, s3 = _SSB0, _SSB1, _SSB2, _SSB3
    a0, a1, a2, a3 = s1[state[13]], s0[state[0]], s2[state[10]], s3[state[7]]
    b0, b1, b2, b3 = s3[state[11]], s2[state[6]], s0[state[12]], s1[state[1]]
    c0, c1, c2, c3 = s2[state[2]], s3[state[15]], s1[state[5]], s0[state[8]]
    d0, d1, d2, d3 = s0[state[4]], s1[state[9]], s3[state[3]], s2[state[14]]
    return [
        a1 ^ a2 ^ a3, a0 ^ a2 ^ a3, a0 ^ a1 ^ a3, a0 ^ a1 ^ a2,
        b1 ^ b2 ^ b3, b0 ^ b2 ^ b3, b0 ^ b1 ^ b3, b0 ^ b1 ^ b2,
        c1 ^ c2 ^ c3, c0 ^ c2 ^ c3, c0 ^ c1 ^ c3, c0 ^ c1 ^ c2,
        d1 ^ d2 ^ d3, d0 ^ d2 ^ d3, d0 ^ d1 ^ d3, d0 ^ d1 ^ d2,
    ]


def R2(state):
    s0, s1, s2, s3 = _SSB0, _SSB1, _SSB2, _SSB3
    a0, a1, a2, a3 = s3[state[7]], s1[state[13]], s2[state[10]], s0[state[0]]
    b0, b1, b2, b3 = s2[state[6]], s0[state[12]], s3[state[11]], s1[state[1]]
    c0, c1, c2, c3 = s1[state[5]], s3[state[15]], s0[state[8]], s2[state[2]]
    d0, d1, d2, d3 = s0[state[4]], s2[state[14]], s1[state[9]], s3[state[3]]
    return [
        a1 ^ a2 ^ a3, a0 ^ a2 ^ a3, a0 ^ a1 ^ a3, a0 ^ a1 ^ a2,
        b1 ^ b2 ^ b3, b0 ^ b2 ^ b3, b0 ^ b1 ^ b3, b0 ^ b1 ^ b2,
        c1 ^ c2 ^ c3, c0 ^ c2 ^ c3, c0 ^ c1 ^ c3, c0 ^ c1 ^ c2,
        d1 ^ d2 ^ d3, d0 ^ d2 ^ d3, d0 ^ d1 ^ d3, d0 ^ d1 ^ d2,
    ]


def R3(state):
    s0, s1, s2, s3 = _SSB0, _SSB1, _SSB2, _SSB3
    a0, a1, a2, a3 = s1[state[13]], s0[state[8]], s2[state[6]], s3[state[3]]
    b0, b1, b2, b3 = s2[state[14]], s3[state[11]], s1[state[5]], s0[state[0]]
    c0, c1, c2, c3 = s0[state[12]], s1[state[9]], s3[state[7]], s2[state[2]]
    d0, d1, d2, d3 = s3[state[15]], s2[state[10]], s0[state[4]], s1[state[1]]
    return [
        a1 ^ a2 ^ a3, a0 ^ a2 ^ a3, a0 ^ a1 ^ a3, a0 ^ a1 ^ a2,
        b1 ^ b2 ^ b3, b0 ^ b2 ^ b3, b0 ^ b1 ^ b3, b0 ^ b1 ^ b2,
        c1 ^ c2 ^ c3, c0 ^ c2 ^ c3, c0 ^ c1 ^ c3, c0 ^ c1 ^ c2,
        d1 ^ d2 ^ d3, d0 ^ d2 ^ d3, d0 ^ d1 ^ d3, d0 ^ d1 ^ d2,
    ]




def xor_states(a, b):
    return [a[0]  ^ b[0],  a[1]  ^ b[1],  a[2]  ^ b[2],  a[3]  ^ b[3],
            a[4]  ^ b[4],  a[5]  ^ b[5],  a[6]  ^ b[6],  a[7]  ^ b[7],
            a[8]  ^ b[8],  a[9]  ^ b[9],  a[10] ^ b[10], a[11] ^ b[11],
            a[12] ^ b[12], a[13] ^ b[13], a[14] ^ b[14], a[15] ^ b[15]]


def xor3(a, b, c):
    return [a[0]  ^ b[0]  ^ c[0],  a[1]  ^ b[1]  ^ c[1],
            a[2]  ^ b[2]  ^ c[2],  a[3]  ^ b[3]  ^ c[3],
            a[4]  ^ b[4]  ^ c[4],  a[5]  ^ b[5]  ^ c[5],
            a[6]  ^ b[6]  ^ c[6],  a[7]  ^ b[7]  ^ c[7],
            a[8]  ^ b[8]  ^ c[8],  a[9]  ^ b[9]  ^ c[9],
            a[10] ^ b[10] ^ c[10], a[11] ^ b[11] ^ c[11],
            a[12] ^ b[12] ^ c[12], a[13] ^ b[13] ^ c[13],
            a[14] ^ b[14] ^ c[14], a[15] ^ b[15] ^ c[15]]


def xor4(a, b, c, d):
    return [a[0]  ^ b[0]  ^ c[0]  ^ d[0],
            a[1]  ^ b[1]  ^ c[1]  ^ d[1],
            a[2]  ^ b[2]  ^ c[2]  ^ d[2],
            a[3]  ^ b[3]  ^ c[3]  ^ d[3],
            a[4]  ^ b[4]  ^ c[4]  ^ d[4],
            a[5]  ^ b[5]  ^ c[5]  ^ d[5],
            a[6]  ^ b[6]  ^ c[6]  ^ d[6],
            a[7]  ^ b[7]  ^ c[7]  ^ d[7],
            a[8]  ^ b[8]  ^ c[8]  ^ d[8],
            a[9]  ^ b[9]  ^ c[9]  ^ d[9],
            a[10] ^ b[10] ^ c[10] ^ d[10],
            a[11] ^ b[11] ^ c[11] ^ d[11],
            a[12] ^ b[12] ^ c[12] ^ d[12],
            a[13] ^ b[13] ^ c[13] ^ d[13],
            a[14] ^ b[14] ^ c[14] ^ d[14],
            a[15] ^ b[15] ^ c[15] ^ d[15]]


def InvSubCell(state):
    return [
        invSSb0(state[0]),  invSSb1(state[1]),
        invSSb2(state[2]),  invSSb3(state[3]),

        invSSb0(state[4]),  invSSb1(state[5]),
        invSSb2(state[6]),  invSSb3(state[7]),

        invSSb0(state[8]),  invSSb1(state[9]),
        invSSb2(state[10]), invSSb3(state[11]),

        invSSb0(state[12]), invSSb1(state[13]),
        invSSb2(state[14]), invSSb3(state[15]),
    ]


def inv_permute(state, pi):
    # inverse of paper convention new[i] = old[pi[i]]
    out = [0] * 16
    out[pi[0]]  = state[0]
    out[pi[1]]  = state[1]
    out[pi[2]]  = state[2]
    out[pi[3]]  = state[3]
    out[pi[4]]  = state[4]
    out[pi[5]]  = state[5]
    out[pi[6]]  = state[6]
    out[pi[7]]  = state[7]
    out[pi[8]]  = state[8]
    out[pi[9]]  = state[9]
    out[pi[10]] = state[10]
    out[pi[11]] = state[11]
    out[pi[12]] = state[12]
    out[pi[13]] = state[13]
    out[pi[14]] = state[14]
    out[pi[15]] = state[15]
    return out


def InvPerm0(state):
    return inv_permute(state, PI0)


def InvPerm1(state):
    return inv_permute(state, PI1)


def InvPerm2(state):
    return inv_permute(state, PI2)


def InvPerm3(state):
    return inv_permute(state, PI3)


def InvR0(state):
    # R0 = MatrixMul o Perm0 o SubCell
    # MatrixMul is involutive.
    return InvSubCell(InvPerm0(MatrixMul(state)))


def InvR1(state):
    return InvSubCell(InvPerm1(MatrixMul(state)))


def InvR2(state):
    return InvSubCell(InvPerm2(MatrixMul(state)))


def InvR3(state):
    return InvSubCell(InvPerm3(MatrixMul(state)))


_R_FUNCS = (R0, R1, R2, R3)
_INV_R_FUNCS = (InvR0, InvR1, InvR2, InvR3)


def R(idx, state):
    return _R_FUNCS[idx & 3](state)


def InvR(idx, state):
    return _INV_R_FUNCS[idx & 3](state)


def zero_rc(n):
    z = [0] * 16
    out = []
    for _ in range(n):
        out.append(z[:])
    return out


def Dialga128_encrypt(P, T, key):
    # Full Dialga-128:
    # alpha = 5 forward iterations
    # beta  = 4 backward iterations
    alpha = 5
    beta = 4


    K0 = key[0:16]
    K1 = key[16:32]
    K = [K0, K1]

    # --------------------------------------------------------
    # Initial whitening
    # Sd = P xor T xor K0 xor K1
    # St = T
    # --------------------------------------------------------
    Sd = xor4(P, T, K0, K1)
    St = T[:]

    # --------------------------------------------------------
    # Rf
    # Each iteration: two data rounds + one tweak update
    # --------------------------------------------------------
    for i in range(1, alpha + 1):
        if i == 1:
            St_new = xor_states(St, K[(i - 1) & 1])
        else:
            St_new = xor_states(R((i - 1) & 3, St), K[(i - 1) & 1])

        Sd = R((2 * i - 2) & 3, Sd)
        Sd = xor3(Sd, K[i & 1], CF[2 * (i - 1)])

        Sd = R((2 * i - 1) & 3, Sd)
        Sd = xor3(Sd, St_new, CF[2 * i - 1])

        St = St_new

    # --------------------------------------------------------
    # Rm
    # Middle reflection layer
    # --------------------------------------------------------
    Sd = R((2 * alpha) & 3, Sd)
    Sd = xor4(Sd, K[(alpha - 1) & 1], CM[0], SubCell(St))

    St_new = InvR((alpha - 1) & 3, xor_states(St, K[(alpha - 1) & 1]))

    Sd = R((2 * alpha + 1) & 3, Sd)
    Sd = xor3(Sd, MS(St_new), CM[1])

    St = St_new

    # --------------------------------------------------------
    # Rb
    # Each iteration: two data rounds + one inverse tweak update
    # --------------------------------------------------------
    for i in range(1, beta + 1):
        key_idx = (alpha - i - 1) & 1
        r_idx = (alpha - i - 1) & 3

        if i == beta:
            St_new = xor_states(St, K[key_idx])
        else:
            St_new = InvR(r_idx, xor_states(St, K[key_idx]))

        Sd = R((2 * (alpha + i)) & 3, Sd)
        Sd = xor3(Sd, K[key_idx], CB[2 * (i - 1)])

        Sd = R((2 * (alpha + i) + 1) & 3, Sd)
        Sd = xor3(Sd, MS(St_new), CB[2 * i - 1])

        St = St_new

    # --------------------------------------------------------
    # Final SubCell and whitening
    # C = SubCell(Sd) xor K0 xor K1
    # --------------------------------------------------------
    Sd = SubCell(Sd)
    C = xor3(Sd, K0, K1)

    return C



if __name__ == "__main__":
    import time
    import random
    p = [0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff]

    k = [0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff,
         0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff, 0x00]
    
    t = [0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0x00, 0xff, 0x11]

    c = Dialga128_encrypt(p, t, k)
    # print("c:", " ".join(f"{v:02x}" for v in c))

    m = 1<<16
    t0 = time.perf_counter()
    for idx in range(m):
        random.seed(idx)
        x = [random.randint(0,0xff) for _ in range(16)]
        k = [random.randint(0,0xff) for _ in range(32)]
        c = Dialga128_encrypt(p, t, k)

    t1 = time.perf_counter()
    print(f"time: {(t1 - t0)/m:.8f}s")
