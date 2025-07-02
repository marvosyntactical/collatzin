import random, math, matplotlib.pyplot as plt

def collatz_path(n, left_deg=5.65, right_deg=8.0):
    """Return the x-, y-coordinate lists for the Collatz path of a single number.

    Parameters
    ----------
    n : int
        Starting integer > 1.
    left_deg, right_deg : float
        Turning angles (degrees) for even (left) and odd (right) moves.
    """
    x, y = 0.0, 0.0            # turtle starts at origin
    angle = 0.0                # pointing along +x
    xs, ys = [x], [y]

    while n != 1:
        if n % 2 == 0:         # even → n/2, small left turn
            angle += math.radians(left_deg)
            n //= 2
        else:                  # odd → 3n+1, stronger right turn
            angle -= math.radians(right_deg)
            n = 3 * n + 1

        # step length shrinks with log of current value
        step = 1.0 / math.log(n + 1.0)
        x += step * math.cos(angle)
        y += step * math.sin(angle)
        xs.append(x)
        ys.append(y)

    return xs, ys

# --- generate paths ---------------------------------------------------------
random.seed(42)
N_STARTS   = 5000            # keep it light for the demo
MAX_START  = 1_000_000

starts = random.sample(range(2, MAX_START), N_STARTS)

plt.figure(figsize=(14, 7), dpi=150)

# light, wispy background paths
for n in starts:
    xs, ys = collatz_path(n)
    plt.plot(xs, ys, alpha=0.04, linewidth=0.5)

# highlight the famous longest path below one million: 837 799
special = 837_799
xs, ys = collatz_path(special)
plt.plot(xs, ys, linewidth=1.5)

# minimal styling ------------------------------------------------------------
plt.axis('equal')
plt.axis('off')
plt.tight_layout()
plt.show()

