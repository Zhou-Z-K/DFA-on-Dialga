import random
import time
import math
from itertools import product

# qarmav2_64_fig4.py

SBOX = [
    0x4, 0x7, 0x9, 0xB,
    0xC, 0x6, 0xE, 0xF,
    0x0, 0x5, 0x1, 0xD,
    0x8, 0x3, 0x2, 0xA
]

INV_SBOX = [0] * 16
for i, v in enumerate(SBOX):
    INV_SBOX[v] = i

TAU_INV = [
    0, 5, 15, 10,
    13, 8, 2, 7,
    11, 14, 4, 1,
    6, 3, 9, 12
]

TAU = [0] * 16
for i, p in enumerate(TAU_INV):
    TAU[p] = i


def check_state(s, name="state"):
    if len(s) != 16:
        raise ValueError(f"{name} must contain exactly 16 nibbles.")
    s = [int(x) for x in s]
    if any(x < 0 or x > 0xF for x in s):
        raise ValueError(f"{name} must contain only 4-bit nibbles.")
    return s


def xor_state(a, b):
    return [x ^ y for x, y in zip(a, b)]


def inv_sbox_layer(s):
    return [INV_SBOX[x] for x in s]


def tau(s):
    return [s[TAU[i]] for i in range(16)]


def tau_inverse(s):
    # Convention: output[i] = input[TAU_INV[i]]
    return [s[TAU_INV[i]] for i in range(16)]


def rho(x, e=1):
    """
    rho(x3 x2 x1 x0) = x2 x1 x0 x3.
    e denotes rho^e.
    """
    x &= 0xF
    e %= 4
    for _ in range(e):
        x = ((x & 0x7) << 1) | ((x >> 3) & 0x1)
    return x


def mix_columns(s):
    """
    QARMAv2-64 MixColumns M.

    M = circ(0, rho, rho^2, rho^3)
      = [ 0    rho  rho2 rho3
          rho3 0    rho  rho2
          rho2 rho3 0    rho
          rho  rho2 rho3 0    ]

    M is involutive, so this is also inverse MixColumns.
    """
    out = [0] * 16

    for c in range(4):
        z0 = s[c]
        z1 = s[4 + c]
        z2 = s[8 + c]
        z3 = s[12 + c]

        out[c]      = rho(z1, 1) ^ rho(z2, 2) ^ rho(z3, 3)
        out[4 + c]  = rho(z0, 3) ^ rho(z2, 1) ^ rho(z3, 2)
        out[8 + c]  = rho(z0, 2) ^ rho(z1, 3) ^ rho(z3, 1)
        out[12 + c] = rho(z0, 1) ^ rho(z1, 2) ^ rho(z2, 3)

    return out


def qarmav2_64_fig4_rounds(
    X_rm1,
    key_rm1=None,
    key_r=None,
    final_key=None,
    art_rm1=None,
    art_r=None,
    return_trace=False
):
    """
    Implement Fig. 4 suffix of QARMAv2-64:

        X^{r-1}
          -> S^{-1}
          -> M^{-1}=M
          -> tau^{-1}
          -> ARK
          -> ART
          -> S^{-1}
          -> M^{-1}=M
          -> tau^{-1}
          -> ARK
          -> ART
          -> S^{-1}
          -> ARK
          -> C

    Inputs are 16-nibble states in paper order:
        [x0, x1, x2, x3,
         x4, x5, x6, x7,
         x8, x9, x10, x11,
         x12, x13, x14, x15]

    For pure differential propagation, set all keys and ART masks to zero.
    """

    zero = [0] * 16

    X_rm1 = check_state(X_rm1, "X_rm1")
    key_rm1 = check_state(key_rm1 if key_rm1 is not None else zero, "key_rm1")
    key_r = check_state(key_r if key_r is not None else zero, "key_r")
    final_key = check_state(final_key if final_key is not None else zero, "final_key")
    art_rm1 = check_state(art_rm1 if art_rm1 is not None else zero, "art_rm1")
    art_r = check_state(art_r if art_r is not None else zero, "art_r")

    trace = {}

    trace["X_rm1"] = X_rm1

    Y_rm1 = inv_sbox_layer(X_rm1)
    Z_rm1 = mix_columns(Y_rm1)
    W_rm1 = tau_inverse(Z_rm1)
    U_rm1 = xor_state(W_rm1, key_rm1)
    X_r = xor_state(U_rm1, art_rm1)

    trace["Y_rm1"] = Y_rm1
    trace["Z_rm1"] = Z_rm1
    trace["W_rm1"] = W_rm1
    trace["U_rm1"] = U_rm1
    trace["X_r"] = X_r

    Y_r = inv_sbox_layer(X_r)
    Z_r = mix_columns(Y_r)
    W_r = tau_inverse(Z_r)
    U_r = xor_state(W_r, key_r)
    X_rp1 = xor_state(U_r, art_r)

    trace["Y_r"] = Y_r
    trace["Z_r"] = Z_r
    trace["W_r"] = W_r
    trace["U_r"] = U_r
    trace["X_rp1"] = X_rp1

    Y_rp1 = inv_sbox_layer(X_rp1)
    C = xor_state(Y_rp1, final_key)

    trace["Y_rp1"] = Y_rp1
    trace["C"] = C

    return (C, trace) if return_trace else C

def int_to_state(x):
    """
    Convert 64-bit integer to QARMAv2-64 state.
    x0 is the most significant nibble.
    """
    if x < 0 or x >= (1 << 64):
        raise ValueError("x must be a 64-bit integer.")
    return [(x >> (4 * (15 - i))) & 0xF for i in range(16)]


def inverse_backward_round(X, key=None, art=None):
    """
    One QARMAv2-64 inverse/backward round:

        X^i -> S^{-1} -> Y^i
            -> M^{-1}=M -> Z^i
            -> tau^{-1} -> W^i
            -> ARK -> U^i
            -> ART -> X^{i+1}

    For differential support verification, key and art can be all-zero.
    """
    zero = [0] * 16
    X = check_state(X, "X")
    key = check_state(key if key is not None else zero, "key")
    art = check_state(art if art is not None else zero, "art")

    Y = inv_sbox_layer(X)
    Z = mix_columns(Y)
    W = tau_inverse(Z)
    U = xor_state(W, key)
    X_next = xor_state(U, art)

    return X_next, {
        "X": X,
        "Y": Y,
        "Z": Z,
        "W": W,
        "U": U,
        "X_next": X_next,
    }


def qarmav2_64_fig5_rounds(
    X_rm2,
    key_rm2=None,
    key_rm1=None,
    key_r=None,
    final_key=None,
    art_rm2=None,
    art_rm1=None,
    art_r=None,
    return_trace=False,
):
    """
    Implement Fig. 5 suffix:

        X^{r-2}
          -> inverse round r-2
        X^{r-1}
          -> inverse round r-1
        X^r
          -> inverse round r
        X^{r+1}
          -> S^{-1}
          -> ARK
        C

    This is only the Fig. 5 part, not full QARMAv2-64.
    """

    zero = [0] * 16

    X_rm2 = check_state(X_rm2, "X_rm2")
    key_rm2 = check_state(key_rm2 if key_rm2 is not None else zero, "key_rm2")
    key_rm1 = check_state(key_rm1 if key_rm1 is not None else zero, "key_rm1")
    key_r = check_state(key_r if key_r is not None else zero, "key_r")
    final_key = check_state(final_key if final_key is not None else zero, "final_key")

    art_rm2 = check_state(art_rm2 if art_rm2 is not None else zero, "art_rm2")
    art_rm1 = check_state(art_rm1 if art_rm1 is not None else zero, "art_rm1")
    art_r = check_state(art_r if art_r is not None else zero, "art_r")

    trace = {}

    X_rm1, tr_rm2 = inverse_backward_round(X_rm2, key_rm2, art_rm2)
    X_r, tr_rm1 = inverse_backward_round(X_rm1, key_rm1, art_rm1)
    X_rp1, tr_r = inverse_backward_round(X_r, key_r, art_r)

    Y_rp1 = inv_sbox_layer(X_rp1)
    C = xor_state(Y_rp1, final_key)

    trace["round_rm2"] = tr_rm2
    trace["round_rm1"] = tr_rm1
    trace["round_r"] = tr_r
    trace["Y_rp1"] = Y_rp1
    trace["C"] = C

    return (C, trace) if return_trace else C


def state_to_int(s):
    s = check_state(s)
    x = 0
    for v in s:
        x = (x << 4) | v
    return x


def state_hex(s):
    return f"{state_to_int(s):016x}"


def random_state():
    return [random.randint(0, 0xF) for _ in range(16)]


d_list_qarmav2_64_fig4 = {
    0:  [[4, 11, 14], [6, 9, 12],  [7, 8, 13],  [-1, 1], [1, -1], [-1, 1]],
    1:  [[1, 4, 14],  [0, 5, 15],  [3, 6, 12],  [2, -1], [2, 1],  [2, 1]],
    2:  [[2, 7, 8],   [1, 4, 11],  [0, 5, 10],  [2, 1],  [2, 1],  [2, -1]],
    3:  [[3, 9, 12],  [2, 8, 13],  [0, 10, 15], [-1, 1], [1, -1], [-1, 1]],

    4:  [[5, 10, 15], [4, 11, 14], [7, 8, 13],  [1, -1], [-1, 1], [-1, 1]],
    5:  [[0, 5, 15],  [2, 7, 13],  [3, 6, 12],  [2, 1],  [2, -1], [2, 1]],
    6:  [[2, 7, 8],   [3, 6, 9],   [1, 4, 11],  [2, 1],  [2, -1], [2, 1]],
    7:  [[3, 9, 12],  [0, 10, 15], [1, 11, 14], [-1, 1], [-1, 1], [1, -1]],

    8:  [[5, 10, 15], [6, 9, 12],  [7, 8, 13],  [1, -1], [1, -1], [-1, 1]],
    9:  [[1, 4, 14],  [0, 5, 15],  [2, 7, 13],  [2, -1], [2, 1],  [2, -1]],
    10: [[3, 6, 9],   [1, 4, 11],  [0, 5, 10],  [2, -1], [2, 1],  [2, -1]],
    11: [[3, 9, 12],  [2, 8, 13],  [1, 11, 14], [-1, 1], [1, -1], [1, -1]],

    12: [[5, 10, 15], [4, 11, 14], [6, 9, 12],  [1, -1], [-1, 1], [1, -1]],
    13: [[1, 4, 14],  [2, 7, 13],  [3, 6, 12],  [2, -1], [2, -1], [2, 1]],
    14: [[2, 7, 8],   [3, 6, 9],   [0, 5, 10],  [2, 1],  [2, -1], [2, -1]],
    15: [[2, 8, 13],  [0, 10, 15], [1, 11, 14], [1, -1], [-1, 1], [1, -1]],
}


def state_xor_fault(s, cell, fault):
    out = s[:]
    out[cell] ^= fault
    return out


def qarmav2_64_fig4_fault(
    X_rm1,
    cell,
    fault,
    key_rm1=None,
    key_r=None,
    final_key=None,
    art_rm1=None,
    art_r=None,
):
    return qarmav2_64_fig4_rounds(
        state_xor_fault(X_rm1, cell, fault),
        key_rm1=key_rm1,
        key_r=key_r,
        final_key=final_key,
        art_rm1=art_rm1,
        art_r=art_r,
    )

def qarmav2_64_fig5_fault(
    X_rm2,
    cell,
    fault,
    key_rm2=None,
    key_rm1=None,
    key_r=None,
    final_key=None,
    art_rm1=None,
    art_r=None,
):
    return qarmav2_64_fig5_rounds(
        state_xor_fault(X_rm2, cell, fault),
        key_rm2=key_rm2,
        key_rm1=key_rm1,
        key_r=key_r,
        final_key=final_key,
        art_rm1=art_rm1,
        art_r=art_r,
    )


def candidate_complexity(ans):
    c = 0
    for sublist in ans:
        l = 1
        for candidates in sublist:
            l *= len(candidates)
        c += l
    return c


def candidate_complexity_gt(ans, limit):
    c = 0
    for sublist in ans:
        l = 1
        for candidates in sublist:
            l *= len(candidates)
            if l > limit:
                return True
        c += l
        if c > limit:
            return True
    return False


_ALL_NIBBLES = list(range(16))


def initial_l1_candidates():
    return [[_ALL_NIBBLES for _ in range(16)]]


def _l1_delta_groups(idx, c_nibble, fault_c_nibble, candidates):
    groups = {}
    for key_guess in candidates:
        d = SBOX[c_nibble ^ key_guess] ^ SBOX[fault_c_nibble ^ key_guess]
        if d in groups:
            groups[d].append(key_guess)
        else:
            groups[d] = [key_guess]
    return groups


def narrow_l1_candidates(ans, d_list_row, c, fault_c):
    triples = d_list_row[:3]
    rotations = d_list_row[3:]

    for (idx1, idx2, idx3), (rot2, rot3) in zip(triples, rotations):
        newans = []
        c1, c2, c3 = c[idx1], c[idx2], c[idx3]
        fc1, fc2, fc3 = fault_c[idx1], fault_c[idx2], fault_c[idx3]

        for sublist in ans:
            groups1 = _l1_delta_groups(idx1, c1, fc1, sublist[idx1])
            groups2 = _l1_delta_groups(idx2, c2, fc2, sublist[idx2])
            groups3 = _l1_delta_groups(idx3, c3, fc3, sublist[idx3])

            for d1 in groups1:
                d2 = rho(d1, rot2)
                d3 = rho(d1, rot3)
                if d2 not in groups2 or d3 not in groups3:
                    continue

                newsublist = sublist[:]
                newsublist[idx1] = groups1[d1]
                newsublist[idx2] = groups2[d2]
                newsublist[idx3] = groups3[d3]
                newans.append(newsublist)

        ans = newans
    return ans


def recover_l1_from_faults(c, faults, ans=None):
    if ans is None:
        ans = initial_l1_candidates()

    for cell, fault_c in faults:
        ans = narrow_l1_candidates(ans, d_list_qarmav2_64_fig4[cell], c, fault_c)
    return ans

d_list_qarmav2_64_fig4_simple = {
    0:  [[4, 11, 14], [6, 9, 12],  [7, 8, 13]],
    1:  [[1, 4, 14],  [0, 5, 15],  [3, 6, 12]],
    2:  [[2, 7, 8],   [1, 4, 11],  [0, 5, 10]],
    3:  [[3, 9, 12],  [2, 8, 13],  [0, 10, 15]],

    4:  [[5, 10, 15], [4, 11, 14], [7, 8, 13]],
    5:  [[0, 5, 15],  [2, 7, 13],  [3, 6, 12]],
    6:  [[2, 7, 8],   [3, 6, 9],   [1, 4, 11]],
    7:  [[3, 9, 12],  [0, 10, 15], [1, 11, 14]],

    8:  [[5, 10, 15], [6, 9, 12],  [7, 8, 13]],
    9:  [[1, 4, 14],  [0, 5, 15],  [2, 7, 13]],
    10: [[3, 6, 9],   [1, 4, 11],  [0, 5, 10]],
    11: [[3, 9, 12],  [2, 8, 13],  [1, 11, 14]],

    12: [[5, 10, 15], [4, 11, 14], [6, 9, 12]],
    13: [[1, 4, 14],  [2, 7, 13],  [3, 6, 12]],
    14: [[2, 7, 8],   [3, 6, 9],   [0, 5, 10]],
    15: [[2, 8, 13],  [0, 10, 15], [1, 11, 14]],
}

def match_d_list2(values):
    """Return the d_list2 case ids whose 9 positions match non-zero values."""
    if len(values) != 16:
        raise ValueError("values must be a list of length 16")

    nonzero_positions = {i for i, value in enumerate(values) if value != 0}
    if len(nonzero_positions) != 9:
        return []

    matched_cases = []
    for case_id, groups in d_list_qarmav2_64_fig4_simple.items():
        case_positions = {pos for group in groups for pos in group}
        if nonzero_positions == case_positions:
            matched_cases.append(case_id)

    return matched_cases


if False and __name__ == "__main__":
    X_rm1 = int_to_state(0x0123456789ABCDEF)

    # 示例 key。实际使用时按你的 key schedule 传入。
    L1 = int_to_state(0x0011223344556677)
    L1 = int_to_state(0x0011223344556677)
    L0 = int_to_state(0x8899AABBCCDDEEFF)

    C, trace = qarmav2_64_fig4_rounds(
        X_rm1,
        key_rm1=L1,
        key_r=L0,
        final_key=L1,
        art_rm1=[0] * 16,
        art_r=[0] * 16,
        return_trace=True
    )

    print("C =", state_hex(C))
    print("C state =", C)

    faults = []
    for cell, fault in [(0, 0x7), (1, 0x5), (2, 0x9), (3, 0x3)]:
        fault_c = qarmav2_64_fig4_fault(
            X_rm1,
            cell,
            fault,
            key_rm1=L1,
            key_r=L0,
            final_key=L1,
            art_rm1=[0] * 16,
            art_r=[0] * 16,
        )
        faults.append((cell, fault_c))

    ans = recover_l1_from_faults(C, faults)
    true_l1_remains = any(
        all(L1[i] in sublist[i] for i in range(16))
        for sublist in ans
    )
    print("L1 candidate complexity =", candidate_complexity(ans))
    print("True L1 remains =", true_l1_remains)


if __name__ == "__main__":
    n = 1
    m = 100
    N = 24
    
    t0 = time.perf_counter()
    avg = 0
    complexity = 0
    # numfalse = 0
    # flist = [0]
    limit = 1 << N

    for idx in range(m):
        random.seed(idx)
        X_rm1 = random_state()
        X_rm2 = random_state()
        L1 = random_state()
        L0 = random_state()


        C = qarmav2_64_fig4_rounds(
            X_rm1,
            key_rm1=L1,
            key_r=L0,
            final_key=L1,
            art_rm1=[0] * 16,
            art_r=[0] * 16,
        )

        random.seed()
        for _ in range(n):
            cnt = 0
            ans = initial_l1_candidates()

            while candidate_complexity_gt(ans, limit):
                cnt += 1
                cell = random.randint(0, 15)
                fault = random.randint(1, 0xF)

                fault_c = qarmav2_64_fig4_fault(
                    X_rm1,
                    cell,
                    fault,
                    key_rm1=L1,
                    key_r=L0,
                    final_key=L1,
                    art_rm1=[0] * 16,
                    art_r=[0] * 16,
                )

                ans = narrow_l1_candidates(
                    ans,
                    d_list_qarmav2_64_fig4[cell],
                    C,
                    fault_c,
                )

                if not ans:
                    break

            # true_l1_remains = any(
            #     all(L1[i] in sublist[i] for i in range(16))
            #     for sublist in ans
            # )
            # if not true_l1_remains:
            #     numfalse += 1
            #     continue
            L1_list = []
            cnt11 = 0
            for ansi in ans:
                for L1_rec in product(*ansi):
                    C1 = qarmav2_64_fig5_rounds(
                        X_rm2,
                        key_rm2=L0,
                        key_rm1=L1,
                        key_r=L0,
                        final_key=L1,
                        art_rm1=[0] * 16,
                        art_r=[0] * 16,
                    ) 
                    cell1 = random.randint(0, 15)
                    # print(cell)
                    fault1 = random.randint(1, 0xF)
                    fault1_C1 = qarmav2_64_fig5_fault(
                        X_rm2,
                        cell1,
                        fault1,
                        key_rm2=L0,                
                        key_rm1=L1,
                        key_r=L0,
                        final_key=L1,
                        art_rm1=[0] * 16,
                        art_r=[0] * 16,
                    ) 

                    C1_l0_input1 = mix_columns(tau([SBOX[C1[i] ^ L1_rec[i]] for i in range(16)]))
                    fault_C1_l0_input1 = mix_columns(tau([SBOX[fault1_C1[i] ^ L1_rec[i]] for i in range(16)]))
                    delta1 = xor_state(C1_l0_input1, fault_C1_l0_input1)
                    # print(delta)
                    flag1 = bool(match_d_list2(delta1))

                    fault = random.randint(1, 0xF)
                    fault_C1 = qarmav2_64_fig5_fault(
                        X_rm2,
                        cell,
                        fault,
                        key_rm2=L0,                
                        key_rm1=L1,
                        key_r=L0,
                        final_key=L1,
                        art_rm1=[0] * 16,
                        art_r=[0] * 16,
                    ) 

                    C1_l0_input = mix_columns(tau([SBOX[C1[i] ^ L1_rec[i]] for i in range(16)]))
                    fault_C1_l0_input = mix_columns(tau([SBOX[fault_C1[i] ^ L1_rec[i]] for i in range(16)]))
                    delta = xor_state(C1_l0_input, fault_C1_l0_input)
                    # print(delta)
                    flag = bool(match_d_list2(delta))                    
                    if flag and flag1:
                        cnt11+=1
                        L1_list.append(L1_rec)
            cnt111 = 0
            C1 = qarmav2_64_fig5_rounds(
                    X_rm2,
                    key_rm2=L0,
                    key_rm1=L1,
                    key_r=L0,
                    final_key=L1,
                    art_rm1=[0] * 16,
                    art_r=[0] * 16,
                )

            for L1_reduce in L1_list:
                cnt1 = 0
                ans1 = initial_l1_candidates()

                while candidate_complexity_gt(ans1, limit):
                    cnt1 += 1
                    cell = random.randint(0, 15)
                    fault = random.randint(1, 0xF)

                    fault_c = qarmav2_64_fig5_fault(
                        X_rm2,
                        cell,
                        fault,
                        key_rm2=L0,
                        key_rm1=L1,
                        key_r=L0,
                        final_key=L1,
                        art_rm1=[0] * 16,
                        art_r=[0] * 16,
                    )
                    C1_l0_input = mix_columns(tau([SBOX[C1[i] ^ L1_reduce[i]] for i in range(16)]))
                    fault_C1_l0_input = mix_columns(tau([SBOX[fault_c[i] ^ L1_reduce[i]] for i in range(16)]))
                    ans1 = narrow_l1_candidates(
                        ans1,
                        d_list_qarmav2_64_fig4[cell],
                        C1_l0_input,
                        fault_C1_l0_input,
                    )
                    if not ans1:
                        break

                complexity += candidate_complexity(ans1)
                if cnt1 > cnt111:
                    cnt111 = cnt1
            avg += (cnt+cnt111)
            # while len(flist) <= cnt:
            #     flist.append(0)
            # flist[cnt] += 1

    # total_success = n * m - numfalse
    avg /= n * m

    # if total_success:
    #     complexity /= total_success
    t1 = time.perf_counter()
    # print(f"N={N}, avg={avg}")
    print(f"N={N}, complexity={complexity}")
    # print(f"N={N}, numfalse={numfalse}")
    # print(f"N={N}, matchnum={cnt1}")
    print(f"N={N} elapsed (without final search): {t1 - t0:.2f}s")
    complexity_exp = math.log2(complexity) if complexity > 0 else float("-inf")
    print(f"complexity=2^{complexity_exp:.1f}, total={avg}")
    # print("fault frequencies:", flist)
