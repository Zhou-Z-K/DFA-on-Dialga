# ============================================================
# Dialga / Midori-128 SubCell implementation
# No imports, no boundary checks.
# Byte is an 8-bit integer.
# Bit numbering convention:
#   bit 0 = MSB
#   bit 7 = LSB
# ============================================================
import random
from itertools import product
import time
import sys
import dialga


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
    s = state[:]  # keep input unchanged
    out = [0] * 16

    # group 0: s0,s1,s2,s3
    a0, a1, a2, a3 = s[0], s[1], s[2], s[3]
    out[0] = a1 ^ a2 ^ a3
    out[1] = a0 ^ a2 ^ a3
    out[2] = a0 ^ a1 ^ a3
    out[3] = a0 ^ a1 ^ a2

    # group 1: s4,s5,s6,s7
    a0, a1, a2, a3 = s[4], s[5], s[6], s[7]
    out[4] = a1 ^ a2 ^ a3
    out[5] = a0 ^ a2 ^ a3
    out[6] = a0 ^ a1 ^ a3
    out[7] = a0 ^ a1 ^ a2

    # group 2: s8,s9,s10,s11
    a0, a1, a2, a3 = s[8], s[9], s[10], s[11]
    out[8]  = a1 ^ a2 ^ a3
    out[9]  = a0 ^ a2 ^ a3
    out[10] = a0 ^ a1 ^ a3
    out[11] = a0 ^ a1 ^ a2

    # group 3: s12,s13,s14,s15
    a0, a1, a2, a3 = s[12], s[13], s[14], s[15]
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
    out = [0] * 16
    out[0]  = SSb0(state[0])
    out[1]  = SSb1(state[1])
    out[2]  = SSb2(state[2])
    out[3]  = SSb3(state[3])
    out[4]  = SSb0(state[4])
    out[5]  = SSb1(state[5])
    out[6]  = SSb2(state[6])
    out[7]  = SSb3(state[7])
    out[8]  = SSb0(state[8])
    out[9]  = SSb1(state[9])
    out[10] = SSb2(state[10])
    out[11] = SSb3(state[11])
    out[12] = SSb0(state[12])
    out[13] = SSb1(state[13])
    out[14] = SSb2(state[14])
    out[15] = SSb3(state[15])
    return out


def R0(state):
    return MatrixMul(Perm0(SubCell(state)))


def R1(state):
    return MatrixMul(Perm1(SubCell(state)))


def R2(state):
    return MatrixMul(Perm2(SubCell(state)))


def R3(state):
    return MatrixMul(Perm3(SubCell(state)))

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

def xor_states(a, b):
    return [a[0]  ^ b[0],  a[1]  ^ b[1],  a[2]  ^ b[2],  a[3]  ^ b[3],
            a[4]  ^ b[4],  a[5]  ^ b[5],  a[6]  ^ b[6],  a[7]  ^ b[7],
            a[8]  ^ b[8],  a[9]  ^ b[9],  a[10] ^ b[10], a[11] ^ b[11],
            a[12] ^ b[12], a[13] ^ b[13], a[14] ^ b[14], a[15] ^ b[15]]

def Dialga128_tail3_no_tweak_no_rc(state, K0, K1):
    # state, K0, K1 are all lists of 16 bytes

    x = R2(state)

    x = [x[0]  ^ K0[0],  x[1]  ^ K0[1],  x[2]  ^ K0[2],  x[3]  ^ K0[3],
         x[4]  ^ K0[4],  x[5]  ^ K0[5],  x[6]  ^ K0[6],  x[7]  ^ K0[7],
         x[8]  ^ K0[8],  x[9]  ^ K0[9],  x[10] ^ K0[10], x[11] ^ K0[11],
         x[12] ^ K0[12], x[13] ^ K0[13], x[14] ^ K0[14], x[15] ^ K0[15]]
    
    x = R3(x)
    
    x = SubCell(x)

    x = [x[0]  ^ K0[0]  ^ K1[0],  x[1]  ^ K0[1]  ^ K1[1],
         x[2]  ^ K0[2]  ^ K1[2],  x[3]  ^ K0[3]  ^ K1[3],
         x[4]  ^ K0[4]  ^ K1[4],  x[5]  ^ K0[5]  ^ K1[5],
         x[6]  ^ K0[6]  ^ K1[6],  x[7]  ^ K0[7]  ^ K1[7],
         x[8]  ^ K0[8]  ^ K1[8],  x[9]  ^ K0[9]  ^ K1[9],
         x[10] ^ K0[10] ^ K1[10], x[11] ^ K0[11] ^ K1[11],
         x[12] ^ K0[12] ^ K1[12], x[13] ^ K0[13] ^ K1[13],
         x[14] ^ K0[14] ^ K1[14], x[15] ^ K0[15] ^ K1[15]]

    return x

def Dialga128_tail5_no_tweak_no_rc(state, K0, K1):
    x = R0(state)
    x = xor_states(x, K1)
    x = R1(x)
    x = xor_states(x, K0)
    x = Dialga128_tail3_no_tweak_no_rc(x, K0, K1)
    return x


def Dialga128_tail5_no_tweak_no_rc_fault1(state, K0, K1, i, f):
    x = R0(state)
    x = xor_states(x, K1)
    x = R1(x)
    x = xor_states(x, K0)
    x[i] ^= f
    x = Dialga128_tail3_no_tweak_no_rc(x, K0, K1)
    return x

d_list = {
    0:  [[4, 5, 6],     [12, 13, 14],  [8, 9, 10]],
    1:  [[12, 13, 15], [4, 5, 7],     [0, 1, 3]],
    2:  [[0, 2, 3],    [8, 10, 11],   [12, 14, 15]],
    3:  [[9, 10, 11],  [1, 2, 3],     [5, 6, 7]],

    4:  [[1, 2, 3],    [5, 6, 7],     [13, 14, 15]],
    5:  [[8, 10, 11],  [12, 14, 15],  [4, 6, 7]],
    6:  [[4, 5, 7],    [0, 1, 3],     [8, 9, 11]],
    7:  [[12, 13, 14], [8, 9, 10],    [0, 1, 2]],

    8:  [[0, 2, 3],    [8, 10, 11],   [4, 6, 7]],
    9:  [[9, 10, 11],  [1, 2, 3],     [13, 14, 15]],
    10: [[4, 5, 6],    [12, 13, 14],  [0, 1, 2]],
    11: [[12, 13, 15], [4, 5, 7],     [8, 9, 11]],

    12: [[12, 13, 15], [0, 1, 3],     [8, 9, 11]],
    13: [[4, 5, 6],    [8, 9, 10],    [0, 1, 2]],
    14: [[9, 10, 11],  [5, 6, 7],     [13, 14, 15]],
    15: [[0, 2, 3],    [12, 14, 15],  [4, 6, 7]],
}

d_list2 = {

    0:  [[0, 2, 3],    [9, 10, 11],   [12, 13, 15]],
    1:  [[4, 5, 7],    [12, 13, 14],  [8, 10, 11]],
    2:  [[13, 14, 15], [4, 6, 7],     [0, 1, 2]],
    3:  [[8, 9, 10],   [0, 1, 3],     [5, 6, 7]],

    4:  [[12, 14, 15], [0, 1, 3],     [5, 6, 7]],
    5:  [[8, 9, 11],   [4, 6, 7],     [0, 1, 2]],
    6:  [[1, 2, 3],    [12, 13, 14],  [8, 10, 11]],
    7:  [[4, 5, 6],    [9, 10, 11],   [12, 13, 15]],

    8:  [[13, 14, 15], [8, 9, 11],    [4, 6, 7]],
    9:  [[8, 9, 10],   [12, 14, 15],  [0, 1, 3]],
    10: [[0, 2, 3],    [4, 5, 6],     [9, 10, 11]],
    11: [[4, 5, 7],    [1, 2, 3],     [12, 13, 14]],

    12: [[4, 5, 7],    [1, 2, 3],     [8, 10, 11]],
    13: [[0, 2, 3],    [4, 5, 6],     [12, 13, 15]],
    14: [[8, 9, 10],   [12, 14, 15],  [5, 6, 7]],
    15: [[13, 14, 15], [8, 9, 11],    [0, 1, 2]],

}

_D_LIST2_MASK_TO_CASES = {}
for case_id, groups in d_list2.items():
    mask = 0
    for group in groups:
        for pos in group:
            mask |= 1 << pos
    if mask in _D_LIST2_MASK_TO_CASES:
        _D_LIST2_MASK_TO_CASES[mask].append(case_id)
    else:
        _D_LIST2_MASK_TO_CASES[mask] = [case_id]

_D_LIST2_MASKS = set(_D_LIST2_MASK_TO_CASES)


def _nonzero_mask16(values):
    if len(values) != 16:
        raise ValueError("values must be a list of length 16")

    mask = 0
    if values[0]:  mask |= 1
    if values[1]:  mask |= 2
    if values[2]:  mask |= 4
    if values[3]:  mask |= 8
    if values[4]:  mask |= 16
    if values[5]:  mask |= 32
    if values[6]:  mask |= 64
    if values[7]:  mask |= 128
    if values[8]:  mask |= 256
    if values[9]:  mask |= 512
    if values[10]: mask |= 1024
    if values[11]: mask |= 2048
    if values[12]: mask |= 4096
    if values[13]: mask |= 8192
    if values[14]: mask |= 16384
    if values[15]: mask |= 32768
    return mask


def match_d_list2(values):
    """Return the d_list2 case ids whose 9 positions match non-zero values."""
    mask = _nonzero_mask16(values)
    cases = _D_LIST2_MASK_TO_CASES.get(mask)
    if cases is None:
        return []
    return cases[:]


def is_match_d_list2_strict(values):
    """Return True if the non-zero positions match any case in d_list2."""
    return _nonzero_mask16(values) in _D_LIST2_MASKS


def is_match_d_list2(values):
    """Return True if values has exactly 9 non-zero positions."""
    return _nonzero_mask16(values).bit_count() == 9

def complex(list1):
    c = 0
    for sub in list1:
        l = 1
        for subsub in sub:
            l*=len(subsub)
        c+=l
    return c

def complex_gt(list1, limit):
    c = 0
    for sub in list1:
        l = 1
        for subsub in sub:
            l *= len(subsub)
            if l > limit:
                return True
        c += l
        if c > limit:
            return True
    return False

_INV_TABLES = (_INV_SSb0, _INV_SSb1, _INV_SSb2, _INV_SSb3)
_ALL_BYTES = list(range(256))


def initial_candidates():
    return [[_ALL_BYTES for _ in range(16)]]


def _delta_groups(idx, c_byte, fault_c_byte, candidates):
    table = _INV_TABLES[idx & 3]
    groups = {}
    for key_guess in candidates:
        d = table[c_byte ^ key_guess] ^ table[fault_c_byte ^ key_guess]
        if d in groups:
            groups[d].append(key_guess)
        else:
            groups[d] = [key_guess]
    return groups


def narrow_candidates(ans, triples, c, fault_c):
    for idx1, idx2, idx3 in triples:
        newans = []
        c1, c2, c3 = c[idx1], c[idx2], c[idx3]
        fc1, fc2, fc3 = fault_c[idx1], fault_c[idx2], fault_c[idx3]

        for sublist in ans:
            groups1 = _delta_groups(idx1, c1, fc1, sublist[idx1])
            groups2 = _delta_groups(idx2, c2, fc2, sublist[idx2])
            groups3 = _delta_groups(idx3, c3, fc3, sublist[idx3])

            for d in groups1.keys() & groups2.keys() & groups3.keys():
                newsublist = sublist[:]
                newsublist[idx1] = groups1[d]
                newsublist[idx2] = groups2[d]
                newsublist[idx3] = groups3[d]
                newans.append(newsublist)

        ans = newans
    return ans


def make_d1(D):
    return [
        D[0] ^ D[1] ^ D[2],
        D[4] ^ D[5] ^ D[6],
        D[8] ^ D[9] ^ D[10],
        D[12] ^ D[13] ^ D[14],
        D[13] ^ D[14] ^ D[15],
        D[9] ^ D[10] ^ D[11],
        D[5] ^ D[6] ^ D[7],
        D[1] ^ D[2] ^ D[3],
        D[8] ^ D[9] ^ D[11],
        D[12] ^ D[13] ^ D[15],
        D[0] ^ D[1] ^ D[3],
        D[4] ^ D[5] ^ D[7],
        D[4] ^ D[6] ^ D[7],
        D[0] ^ D[2] ^ D[3],
        D[12] ^ D[14] ^ D[15],
        D[8] ^ D[10] ^ D[11],
    ]


def _d1_delta_groups(idx, d1_byte, candidates):
    table = _INV_TABLES[idx & 3]
    groups = {}
    for value in candidates:
        d = table[value] ^ table[d1_byte ^ value]
        if d in groups:
            groups[d].append(value)
        else:
            groups[d] = [value]
    return groups


def narrow_candidates_by_d1(ans, triples, D1):
    for idx1, idx2, idx3 in triples:
        newans = []
        d1_1, d1_2, d1_3 = D1[idx1], D1[idx2], D1[idx3]

        for sublist in ans:
            groups1 = _d1_delta_groups(idx1, d1_1, sublist[idx1])
            groups2 = _d1_delta_groups(idx2, d1_2, sublist[idx2])
            groups3 = _d1_delta_groups(idx3, d1_3, sublist[idx3])

            for d in groups1.keys() & groups2.keys() & groups3.keys():
                newsublist = sublist[:]
                newsublist[idx1] = groups1[d]
                newsublist[idx2] = groups2[d]
                newsublist[idx3] = groups3[d]
                newans.append(newsublist)

        ans = newans
    return ans


def d1_from_ciphertexts(c, fault_c, kk):
    x20 = InvR3(InvSubCell(xor_states(c, kk)))
    fault_x20 = InvR3(InvSubCell(xor_states(fault_c, kk)))
    return make_d1(xor_states(x20, fault_x20))


def find_valid_kk(ans, c, fault_c, match_func=is_match_d_list2_strict):
    # match_func=is_match_d_list2 or is_match_d_list2_strict
    for ansi in ans:
        for kk in product(*ansi):
            D1 = d1_from_ciphertexts(c, fault_c, kk)
            if match_func(D1):
                return kk
    return None

if __name__ == "__main__":
    # x = [0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff]

    # print("c: ", " ".join(f"{v:02x}" for v in c))

    t0 = time.perf_counter()
    
    

    avg = 0
    complexity = 0
    n = 100
    m = 100
    numfalse = 0
    N = 0

    limit = 1 << N
    for idx in range(m):
        # print(idx)
        random.seed()
        x = [random.randint(0,0xff) for _ in range(16)]
        # print("x:", " ".join(f"{v:02x}" for v in x))

        # k0 = [0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff]
        # k1 = [0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff, 0x00]
        k0 = [random.randint(0,0xff) for _ in range(16)]
        k1 = [random.randint(0,0xff) for _ in range(16)]
        originkk = xor_states(k0, k1)


        c = Dialga128_tail5_no_tweak_no_rc(x, k0, k1)

        random.seed()
        
        for _ in range(n):
            cnt = 0
            ans = initial_candidates()

            while complex_gt(ans, limit): 
            # for __ in range(1):
                cnt += 1
                cell = random.randint(0, 15)  
                f = random.randint(1,0xff)

                _c = Dialga128_tail5_no_tweak_no_rc_fault1(x, k0, k1, cell, f)
                # print("c': ", " ".join(f"{v:02x}" for v in _c))
                
                        
                ans = narrow_candidates(ans, d_list[cell], c, _c)
            
                                       
            cell = random.randint(0, 15)  
            f = random.randint(1,0xff)
            _x = x[:]
            _x[cell] ^= f
            _c = Dialga128_tail5_no_tweak_no_rc(_x, k0, k1)
            # print("c': ", " ".join(f"{v:02x}" for v in _c))

            # realkk = find_valid_kk(ans, c, _c)
            realkk = originkk

            if list(realkk) != originkk:
                # print(realkk)
                # print(originkk)
                # realkk_x20 = InvR3(InvSubCell(xor_states(c, realkk)))
                # realkk_fault_x20 = InvR3(InvSubCell(xor_states(_c, realkk)))
                # realkk_D1 = make_d1(xor_states(realkk_x20, realkk_fault_x20))

                # originkk_x20 = InvR3(InvSubCell(xor_states(c, originkk)))
                # originkk_fault_x20 = InvR3(InvSubCell(xor_states(_c, originkk)))
                # originkk_D1 = make_d1(xor_states(originkk_x20, originkk_fault_x20))

                # print("realkk x20:", realkk_x20)
                # print("originkk x20:", originkk_x20)
                # print("realkk fault_x20:", realkk_fault_x20)
                # print("originkk fault_x20:", originkk_fault_x20)
                # print("realkk delta_x20:", xor_states(realkk_x20,realkk_fault_x20))
                # print("originkk delta_x20:", xor_states(originkk_x20,originkk_fault_x20))
                # print("realkk D1:", realkk_D1)
                # print("originkk D1:", originkk_D1)
                # print(ans)
                # print("false")   
                numfalse += 1

                continue             

            cnt1 = 0
            ans1 = initial_candidates()
            x20 = InvR3(InvSubCell(xor_states(c, realkk)))
            while complex_gt(ans1, limit): 
                cnt1 += 1
                cell = random.randint(0, 15)  
                f = random.randint(1,0xff)
                _x = x[:]
                _x[cell] ^= f
                _c = Dialga128_tail5_no_tweak_no_rc(_x, k0, k1)
                # print("c': ", " ".join(f"{v:02x}" for v in _c))
                _x20 = InvR3(InvSubCell(xor_states(_c, realkk)))
                D1 = make_d1(xor_states(x20, _x20))
                ans1 = narrow_candidates_by_d1(ans1, d_list2[cell], D1)

            ans_complexity = complex(ans)
            ans1_complexity = complex(ans1)
            if ans1_complexity == 0:
                print('false2')

            complexity += ans1_complexity

            avg+=cnt
            avg+=cnt1

    avg /= (n*m-numfalse)
    complexity/=(n*m-numfalse)
    print('avg: ', avg)
    print('complexity: ', complexity)
    print('numfalse: ', numfalse)
    t1 = time.perf_counter()
    # print(f"N={N} total_run: {(t1 - t0):.4f}s")
    print(f"N={N} elapsed_per_run: {(t1 - t0)/(n*m)+0.0001*2**(complexity-1):.4f}s")




