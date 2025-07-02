#!/usr/bin/env python3
"""
collatz3.py – 3‑D "shrub" visualisation of Collatz‑type orbits
===============================================================

This extends the 2‑D turtle plot to a third dimension so the whole tree
spirals upward like a twisted bonsai.  It also supports an *experimental*
ternary analogue of the 3n+1 map, so you can flip between two dynamical
rules with a flag.

Binary rule (classic):
    n -> n/2           if n ≡ 0 (mod 2)
    n -> 3n + 1        if n ≡ 1 (mod 2)

Ternary rule (one plausible choice):
    n ->   n / 3             if n ≡ 0 (mod 3)
    n ->  (4n + 1) / 3       if n ≡ 1 (mod 3)
    n ->  (2n + 2) / 3       if n ≡ 2 (mod 3)
The ternary mapping is *not* proven to converge – we’re just poking it with a
stick to see what pictures jump out.

---------------------------------------------------------------
Usage
-----
    python collatz3.py [N_STARTS] [MAX_START] [mode]

    N_STARTS   number of random starting integers (default 3 000)
    MAX_START  exclusive upper bound for sampling (default 1 000 000)
    mode       "binary" (default)  or  "ternary"

Example
-------
    python collatz3.py 5000 200000 ternary

Controls
--------
* Turn angles in the *x–y* plane:
      even/0‑mod‑2/3  : +8.65°   (gentle left)
      odd /1‑mod‑2    : –16.0°   (sharper right)
      (you can tweak the constants below)
* *z* rises linearly with step length (scaled by VERTICAL_SCALE).
* Each path is drawn thin & translucent; one highlight trajectory is drawn
  thicker for context.

Dependencies
------------
matplotlib (for 3‑D) and numpy (for colour mapping); everything else is stdlib.
"""

from __future__ import annotations

import math
import random
import sys
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 – registers 3‑D proj

# -----------------------------------------------------------------------------
# User‑tweakable constants
# -----------------------------------------------------------------------------
LEFT_DEG = 8.65
RIGHT_DEG = 16.0
INITIAL_HEADING_DEG = -75.0     # slightly downward‑right to mimic poster
VERTICAL_SCALE = 0.6            # step_length * this  -> Δz
SEED = 42                       # RNG seed for reproducibility

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

Angle = float
Point3 = Tuple[float, float, float]

left_rad = math.radians(LEFT_DEG)
right_rad = math.radians(RIGHT_DEG)
init_heading = math.radians(INITIAL_HEADING_DEG)


def next_n(n: int, mode: str = "binary") -> int:
    """Return the next value of *n* under the chosen rule."""
    if mode == "binary":
        return n // 2 if n % 2 == 0 else 3 * n + 1
    elif mode == "ternary":
        r = n % 3
        if r == 0:
            return n // 3
        elif r == 1:
            return (4 * n + 1) // 3
        else:  # r == 2
            return (2 * n + 2) // 3
    else:
        raise ValueError("mode must be 'binary' or 'ternary'")


def collatz_path_3d(n: int, mode: str = "binary") -> Tuple[List[float], List[float], List[float]]:
    """Generate (xs, ys, zs) for the 3‑D turtle path of *n*."""
    x = y = z = 0.0
    angle_xy: Angle = init_heading

    xs = [x]
    ys = [y]
    zs = [z]

    while n != 1:
        nxt = next_n(n, mode)

        # decide turn direction from *current* parity / mod‑class, *not* nxt
        if mode == "binary":
            if n % 2 == 0:
                angle_xy += left_rad
            else:
                angle_xy -= right_rad
        else:  # ternary
            r = n % 3
            if r == 0:
                angle_xy += left_rad
            elif r == 1:
                angle_xy -= right_rad  # same magnitude for simplicity
            else:  # r == 2
                angle_xy += 0.5 * left_rad  # mild left turn

        # step length shrinks like 1 / ln(nxt + 1)
        step = 1.0 / math.log(nxt + 1.0)

        x += step * math.cos(angle_xy)
        y += step * math.sin(angle_xy)
        z += step * VERTICAL_SCALE

        xs.append(x)
        ys.append(y)
        zs.append(z)

        n = nxt

    return xs, ys, zs


# -----------------------------------------------------------------------------
# Main rendering routine
# -----------------------------------------------------------------------------

def plot_shrub(n_samples: int, max_start: int, mode: str = "binary") -> None:
    random.seed(SEED)
    starts = random.sample(range(2, max_start), n_samples)

    fig = plt.figure(figsize=(10, 8), dpi=150)
    ax: Axes3D = fig.add_subplot(111, projection="3d")

    # colour map by log(start)
    cmap = plt.cm.plasma
    logs = np.log(np.array(starts))
    clr_norm = (logs - logs.min()) / (np.ptp(logs) or 1.0)

    for idx, n in enumerate(starts):
        xs, ys, zs = collatz_path_3d(n, mode)
        ax.plot(xs, ys, zs,
                color=cmap(clr_norm[idx]),
                alpha=0.03,
                linewidth=0.5)

    # highlight one celebrity path for context (27 is iconic in binary)
    celeb = 27 if mode == "binary" else 31
    xs, ys, zs = collatz_path_3d(celeb, mode)
    ax.plot(xs, ys, zs, color="black", linewidth=2.0, alpha=0.9, zorder=5)

    ax.set_axis_off()
    ax.set_box_aspect([1, 1, 1])
    ax.view_init(elev=22, azim=-60)  # pleasant angle – tweak to taste
    plt.tight_layout()
    plt.show()


# -----------------------------------------------------------------------------
# Entry‑point
# -----------------------------------------------------------------------------

def main() -> None:
    try:
        n_samples = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
        max_start = int(float(sys.argv[2])) if len(sys.argv) > 2 else 1_000_000
        mode = sys.argv[3] if len(sys.argv) > 3 else "binary"
    except (ValueError, IndexError):
        sys.exit("Usage: python collatz3.py [N_STARTS] [MAX_START] [mode]")

    if mode not in {"binary", "ternary"}:
        sys.exit("mode must be 'binary' or 'ternary'")

    plot_shrub(n_samples, max_start, mode)


if __name__ == "__main__":
    main()

