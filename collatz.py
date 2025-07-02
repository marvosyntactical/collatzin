#!/usr/bin/env python3
"""
collatz3.py – 3‑D *time‑stacked* Collatz tree
===========================================

A revision of the earlier shrub script that gives the vertical axis real
meaning: **z rises one unit (scaled by ``Z_STEP``) per Collatz iteration**.
The height of a branch therefore encodes the stopping‑time of its starting
integer, while the left/right weaving in the x–y plane follows the familiar
8.65°/‑16° turtle rule.

Binary rule (classic):
    n → n/2            if n even
    n → 3 n + 1        if n odd

Ternary experimental rule (optional):
    n →   n/3                    if n ≡ 0 (mod 3)
    n → (4 n + 1)/3              if n ≡ 1 (mod 3)
    n → (2 n + 1)/3              if n ≡ 2 (mod 3)

Usage
-----
    python collatz3.py [N_STARTS] [MAX_START] [mode]

    N_STARTS   number of random starting integers (default 3 000)
    MAX_START  exclusive upper bound for sampling (default 1 000 000)
    mode       "binary" (default)  or  "ternary"
"""

from __future__ import annotations

import math
import random
import sys
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 – registers 3‑D projection

LEFT_DEG = 13.17                   # even (or 0‑mod‑3) left turn
RIGHT_DEG = 16.0                 # odd (or 1‑mod‑3) right turn
INITIAL_HEADING_DEG = -75.0      # initial direction in x–y plane
Z_STEP = 0.15                    # vertical rise per *iteration* ("time")
SEED = 42                         # RNG seed for repeatability

# Pre‑compute radians
_left   = math.radians(LEFT_DEG)
_right  = math.radians(RIGHT_DEG)
_init_h = math.radians(INITIAL_HEADING_DEG)

# ───────────────────────────────────────────────────────────────────────────────

def next_n(n: int, scheme: str = "binary") -> int:
    """Return the successor of *n* under the chosen Collatz‑type rule."""
    if scheme == "binary":
        return n // 2 if n % 2 == 0 else 3 * n + 1
    if scheme == "ternary":
        r = n % 3
        if r == 0:
            return n // 3
        if r == 1:
            return (4 * n + 1) // 3
        return (2 * n + 2) // 3
    raise ValueError("scheme must be 'binary' or 'ternary'")

# ───────────────────────────────────────────────────────────────────────────────
# Path generator – returns 3‑D polyline arrays
# ───────────────────────────────────────────────────────────────────────────────

def collatz_path_3d(n: int, scheme: str = "binary") -> Tuple[List[float], List[float], List[float]]:
    x = y = z = 0.0
    angle = _init_h
    xs, ys, zs = [x], [y], [z]
    step_count = 0

    while n != 1:
        nxt = next_n(n, scheme)

        # turn according to *current* residue class
        if scheme == "binary":
            angle += _left if n % 2 == 0 else -_right
        else:  # ternary
            r = n % 3
            angle += (_left if r == 0 else (-_right if r == 1 else 0.5 * _left))

        # step length for x–y shrinks like 1/ln(nxt)
        step_len = 1.0 / math.log(nxt + 1.0)
        x += step_len * math.cos(angle)
        y += step_len * math.sin(angle)

        step_count += 1
        z = step_count * Z_STEP  # ↑ time‑axis

        xs.append(x); ys.append(y); zs.append(z)
        n = nxt

    return xs, ys, zs

# ───────────────────────────────────────────────────────────────────────────────
# Plotting
# ───────────────────────────────────────────────────────────────────────────────

def plot_shrub(n_samples: int, max_start: int, scheme: str = "binary") -> None:
    hero = 837_799 if scheme == "binary" else 91

    random.seed(SEED)
    starts = random.sample(range(2, max_start), n_samples)
    if hero not in starts: starts += [hero]

    fig = plt.figure(figsize=(10, 8), dpi=150)
    ax: Axes3D = fig.add_subplot(111, projection="3d")

    # colour by log(start)
    # vals = np.log(np.array(starts))
    # colours = plt.cm.inferno((vals - vals.min()) / (np.ptp(vals) or 1))

    # color by start number magnitude
    norms   = (np.array(starts) - 2) / (max_start - 2)
    colours = plt.cm.gist_rainbow(norms)

    for idx, n in enumerate(starts):
        xs, ys, zs = collatz_path_3d(n, scheme)
        ax.plot(xs, ys, zs, color=colours[idx], alpha=0.5, linewidth=2.0/(n_samples/100))

    # spotlight a long trajectory for context
    # xs, ys, zs = collatz_path_3d(hero, scheme)
    # ax.plot(xs, ys, zs, color="black", linewidth=2.2, zorder=10)

    ax.set_axis_off()
    ax.set_box_aspect([1, 1, 1])
    ax.view_init(elev=25, azim=-35)  # default vantage; rotate interactively!
    plt.tight_layout()
    # plt.title(f"Collatz (scheme={scheme})")
    # help(plt.show)
    plt.show()

# ───────────────────────────────────────────────────────────────────────────────
# CLI entry‑point
# ───────────────────────────────────────────────────────────────────────────────

def main() -> None:
    try:
        n_samp  = int(sys.argv[1])       if len(sys.argv) > 1 else 1000
        max_n   = int(float(sys.argv[2])) if len(sys.argv) > 2 else 1_000_000
        scheme  = sys.argv[3]            if len(sys.argv) > 3 else "binary"
    except (ValueError, IndexError):
        sys.exit("Usage: python collatz3.py [N_STARTS] [MAX_START] [mode]")

    if scheme not in {"binary", "ternary"}:
        sys.exit("mode must be 'binary' or 'ternary'")

    plot_shrub(n_samp, max_n, scheme)


if __name__ == "__main__":
    main()

