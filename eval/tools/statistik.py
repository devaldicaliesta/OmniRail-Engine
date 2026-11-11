#!/usr/bin/env python3
"""Interval Wilson, uji McNemar eksak, dan kappa Cohen.

    python3 eval/tools/statistik.py
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Hashable, Sequence

Z_95 = 1.959963984540054


def wilson(k: int, n: int, z: float = Z_95) -> tuple[float, float]:
    if n <= 0:
        raise ValueError("n harus > 0")
    if not 0 <= k <= n:
        raise ValueError("k harus di antara 0 dan n")
    p = k / n
    z2 = z * z
    pusat = (p + z2 / (2 * n)) / (1 + z2 / n)
    lebar = (z / (1 + z2 / n)) * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))
    return max(0.0, pusat - lebar), min(1.0, pusat + lebar)


def mcnemar_eksak(b: int, c: int) -> float:
    if b < 0 or c < 0:
        raise ValueError("b dan c tidak boleh negatif")
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    ekor = sum(math.comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2 * ekor)


def cohen_kappa(label_a: Sequence[Hashable], label_b: Sequence[Hashable]) -> float:
    if len(label_a) != len(label_b) or not label_a:
        raise ValueError("kedua daftar label harus sama panjang dan tidak kosong")
    n = len(label_a)
    teramati = sum(a == b for a, b in zip(label_a, label_b)) / n
    hit_a, hit_b = Counter(label_a), Counter(label_b)
    harapan = sum(hit_a[k] * hit_b[k] for k in hit_a) / (n * n)
    if harapan == 1:
        return 1.0
    return (teramati - harapan) / (1 - harapan)


def main() -> None:
    print("Lebar interval Wilson 95% (setengah lebar, poin persentase)\n")
    print("| n | p = 0,80 | p = 0,90 | p = 0,95 | p = 0,98 |")
    print("| --- | --- | --- | --- | --- |")
    for n in (50, 100, 150, 300, 1000):
        sel = []
        for p in (0.80, 0.90, 0.95, 0.98):
            lo, hi = wilson(round(p * n), n)
            sel.append(f"±{(hi - lo) / 2 * 100:.1f}")
        print(f"| {n} | " + " | ".join(sel) + " |")


if __name__ == "__main__":
    main()
