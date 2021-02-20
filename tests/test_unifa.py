
# Copyright (c) 2021 Idein Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice (including the next
# paragraph) shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from videocore6.assembler import qpu
from videocore6.driver import Driver

import numpy as np


@qpu
def qpu_unifa(asm):

    reg_n = rf0
    reg_src0 = rf1
    reg_src1 = rf2
    reg_dst = rf3
    reg_inc = rf4
    reg_tmp = rf5

    nop(sig=ldunifrf(reg_n))
    nop(sig=ldunifrf(reg_src0))
    nop(sig=ldunifrf(reg_src1))
    nop(sig=ldunifrf(reg_dst))

    eidx(r0)
    shl(r0, r0, 2)
    add(reg_src0, reg_src0, r0)
    add(reg_src1, reg_src1, r0)
    add(reg_dst, reg_dst, r0)

    shl(reg_inc, 4, 4)

    # Address is taken from element zero.
    mov(unifa, reg_src0)
    # Three delays are required for the data to be ready.
    nop()
    nop()
    sub(r0, reg_n, 1, cond='pushz')
    L.l0
    nop(sig=ldunifa)
    b(R.l0, cond='na0')
    mov(tmud, r5)
    mov(tmua, reg_dst).add(reg_dst, reg_dst, reg_inc)
    sub(r0, r0, 1, cond='pushz')

    # Ordinary uniform and sideband uniform simultaneous reads.
    b(R.l1, cond='always').unif_addr(reg_src0)
    mov(unifa, reg_src1)
    sub(r0, reg_n, 1, cond='pushz')
    nop()
    L.l1
    nop(sig=ldunif)
    mov(tmud, r5, sig=ldunifa)
    mov(tmua, reg_dst).add(reg_dst, reg_dst, reg_inc)
    b(R.l1, cond='na0')
    mov(tmud, r5)
    mov(tmua, reg_dst).add(reg_dst, reg_dst, reg_inc)
    sub(r0, r0, 1, cond='pushz')

    nop(sig=thrsw)
    nop(sig=thrsw)
    nop()
    nop()
    nop(sig=thrsw)
    nop()
    nop()
    nop()


def test_unifa():

    n = 521

    with Driver() as drv:

        code = drv.program(qpu_unifa)
        unif = drv.alloc(4, dtype='uint32')
        src0 = drv.alloc(n, dtype='uint32')
        src1 = drv.alloc(n, dtype='uint32')
        dst = drv.alloc((n * 3, 16), dtype='uint32')

        rng = np.random.default_rng()
        src0[:] = rng.integers(1, 2 ** 32 - 1, size=n)
        src1[:] = rng.integers(1, 2 ** 32 - 1, size=n)
        dst[:, :] = 0

        unif[0] = n
        unif[1] = src0.addresses()[0]
        unif[2] = src1.addresses()[0]
        unif[3] = dst.addresses()[0, 0]

        drv.execute(code, unif.addresses()[0])

        for i in range(n):
            assert all(dst[i, :] == src0[i])
            assert all(dst[n + i * 2 + 0, :] == src0[i])
            assert all(dst[n + i * 2 + 1, :] == src1[i])
