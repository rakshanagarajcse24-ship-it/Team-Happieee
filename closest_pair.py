#!/usr/bin/env python3
"""
Closest Pair of Points: Brute-Force vs Divide-and-Conquer
=========================================================

Usage examples
--------------
    echo 200 | python closest_pair.py                 # run + plots
    python closest_pair.py --n 500 --seed 42 --int    # integer coordinates
    python closest_pair.py --n 30 --animate           # also animate the recursion
    python closest_pair.py --n 1000 --verify          # stress-test agreement
    python closest_pair.py --n 200 --no-show          # save PNGs only (headless)

Input  : N (from stdin, or --n). The N points are generated randomly.
Output : line 1 -> Brute-Force result, line 2 -> Divide-and-Conquer result,
         line 3 -> execution time of each algorithm in ms.
"""

import argparse
import math
import os
import random
import sys
import time
from typing import List, Optional, Tuple

Point = Tuple[float, float]
Result = Optional[Tuple[float, Point, Point]]  # (distance, p, q) or None if N < 2


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def dist(p: Point, q: Point) -> float:
    return math.hypot(p[0] - q[0], p[1] - q[1])


def fmt_num(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else f"{v:.4f}"


def fmt_pt(p: Point) -> str:
    return f"({fmt_num(p[0])}, {fmt_num(p[1])})"


def generate_points(n: int, coord_range: float, integer: bool, rng: random.Random) -> List[Point]:
    """Generate n random points (integer or floating point). Duplicates are allowed."""
    if integer:
        r = int(coord_range)
        return [(rng.randint(-r, r), rng.randint(-r, r)) for _ in range(n)]
    return [(rng.uniform(-coord_range, coord_range), rng.uniform(-coord_range, coord_range))
            for _ in range(n)]


# --------------------------------------------------------------------------- #
# Algorithm 1: Brute force  O(N^2)
# --------------------------------------------------------------------------- #
def brute_force(points: List[Point]) -> Result:
    n = len(points)
    if n < 2:
        return None
    best_d = math.inf
    best_pair = (points[0], points[1])
    for i in range(n - 1):
        pi = points[i]
        for j in range(i + 1, n):
            d = dist(pi, points[j])
            if d < best_d:
                best_d, best_pair = d, (pi, points[j])
    return best_d, best_pair[0], best_pair[1]


# --------------------------------------------------------------------------- #
# Algorithm 2: Divide and conquer  O(N log N)
# --------------------------------------------------------------------------- #
def _merge_by_y(a: List[Point], b: List[Point]) -> List[Point]:
    out, i, j = [], 0, 0
    while i < len(a) and j < len(b):
        if a[i][1] <= b[j][1]:
            out.append(a[i]); i += 1
        else:
            out.append(b[j]); j += 1
    out.extend(a[i:]); out.extend(b[j:])
    return out


def _rec(px: List[Point], lo: int, hi: int, ctx: dict, depth: int):
    """
    Solve for px[lo:hi] (sorted by x).
    Returns (best, ys) where best = (d, p, q) and ys = the same points sorted by y.
    ctx collects visualisation info (top-level split + optional event log).
    """
    events = ctx.get("events")
    n = hi - lo

    # Base case: 2 or 3 points -> brute force (also handles duplicates / collinear)
    if n <= 3:
        sub = px[lo:hi]
        best_d, bp = math.inf, (sub[0], sub[1])
        for i in range(n - 1):
            for j in range(i + 1, n):
                d = dist(sub[i], sub[j])
                if d < best_d:
                    best_d, bp = d, (sub[i], sub[j])
        ys = sorted(sub, key=lambda p: p[1])
        if events is not None:
            events.append(("base", lo, hi, None, best_d, bp, None))
        return (best_d, bp[0], bp[1]), ys

    mid = (lo + hi) // 2
    mid_x = px[mid][0]
    if events is not None:
        events.append(("split", lo, hi, mid_x, None, None, None))

    left, ys_l = _rec(px, lo, mid, ctx, depth + 1)
    right, ys_r = _rec(px, mid, hi, ctx, depth + 1)
    ys = _merge_by_y(ys_l, ys_r)

    best = left if left[0] <= right[0] else right
    delta = best[0]

    # Strip: points within delta of the dividing line, ordered by y
    strip = [p for p in ys if abs(p[0] - mid_x) < delta]
    for i in range(len(strip)):
        j = i + 1
        # At most ~7 neighbours need checking (packing argument)
        while j < len(strip) and strip[j][1] - strip[i][1] < best[0]:
            d = dist(strip[i], strip[j])
            if d < best[0]:
                best = (d, strip[i], strip[j])
            j += 1

    if depth == 0:
        ctx["mid_x"] = mid_x
        ctx["delta"] = delta        # strip half-width used at the top level (width 2*delta)
    if events is not None:
        events.append(("merge", lo, hi, mid_x, best[0], (best[1], best[2]), delta))
    return best, ys


def divide_and_conquer(points: List[Point], ctx: Optional[dict] = None) -> Result:
    if len(points) < 2:
        return None
    ctx = {} if ctx is None else ctx
    px = sorted(points, key=lambda p: (p[0], p[1]))
    ctx["px"] = px
    best, _ = _rec(px, 0, len(px), ctx, 0)
    return best


# --------------------------------------------------------------------------- #
# Timing / verification / benchmarking
# --------------------------------------------------------------------------- #
def timed(fn, *args, repeat: int = 1):
    """Return (result, best_time_ms) over `repeat` runs."""
    best_t, res = math.inf, None
    for _ in range(repeat):
        t0 = time.perf_counter()
        res = fn(*args)
        best_t = min(best_t, (time.perf_counter() - t0) * 1000.0)
    return res, best_t


def distances_agree(r1: Result, r2: Result, tol: float = 1e-9) -> bool:
    if r1 is None or r2 is None:
        return r1 is None and r2 is None
    return math.isclose(r1[0], r2[0], rel_tol=tol, abs_tol=tol)


def verify(trials: int, max_n: int, seed: int) -> bool:
    """Randomised cross-check including degenerate inputs."""
    rng = random.Random(seed)
    ok = True
    # fixed corner cases
    corner = [
        [], [(1, 1)], [(0, 0), (3, 4)],
        [(2, 2), (2, 2)],                                  # duplicate, N = 2
        [(1, 1), (5, 5), (1, 1), (9, 9)],                  # duplicate among others
        [(i, 0) for i in range(10)],                       # collinear, same y
        [(0, i * 2) for i in range(10)],                   # collinear, same x
        [(i, i) for i in range(10)],                       # diagonal
        [(3, 3)] * 6,                                      # all identical
        [(0, 0), (1, 0), (0, 1), (1, 1)],                  # unit square
    ]
    for pts in corner:
        if not distances_agree(brute_force(pts), divide_and_conquer(pts)):
            print(f"  MISMATCH on corner case: {pts}")
            ok = False
    for t in range(trials):
        n = rng.randint(0, max_n)
        mode = t % 4
        if mode == 0:
            pts = generate_points(n, 1000, False, rng)
        elif mode == 1:
            pts = generate_points(n, 10, True, rng)       # many duplicates / shared coords
        elif mode == 2:
            pts = [(rng.randint(0, 50), 7) for _ in range(n)]   # horizontal line
        else:
            pts = [(rng.uniform(0, 1e-3), rng.uniform(0, 1e6)) for _ in range(n)]  # skewed
        if not distances_agree(brute_force(pts), divide_and_conquer(pts)):
            print(f"  MISMATCH (trial {t}, n={n})")
            ok = False
    return ok


def benchmark(sizes: List[int], coord_range: float, seed: int, repeat: int = 3):
    rng = random.Random(seed)
    bf_times, dc_times, all_agree = [], [], True
    for n in sizes:
        pts = generate_points(n, coord_range, False, rng)
        r1, t1 = timed(brute_force, pts, repeat=repeat)
        r2, t2 = timed(divide_and_conquer, pts, repeat=repeat)
        agree = distances_agree(r1, r2)
        all_agree &= agree
        bf_times.append(t1); dc_times.append(t2)
        print(f"  N={n:<7d} brute={t1:10.3f} ms   d&c={t2:9.3f} ms   agree={agree}")
    return bf_times, dc_times, all_agree


# --------------------------------------------------------------------------- #
# Visualisation
# --------------------------------------------------------------------------- #
def plot_points(ax, points, bf: Result, dc: Result, ctx: dict):
    xs = [p[0] for p in points]; ys = [p[1] for p in points]
    ax.scatter(xs, ys, s=14, c="#888888", zorder=2, label=f"Points (N={len(points)})")
    if "mid_x" in ctx:
        mx, dl = ctx["mid_x"], ctx["delta"]
        ax.axvline(mx, color="green", linestyle="--", linewidth=1.3, zorder=1,
                   label="Dividing line")
        ax.axvspan(mx - dl, mx + dl, color="green", alpha=0.12, zorder=0,
                   label=f"Strip (width 2d = {2 * dl:.4g})")
    if bf:
        ax.plot([bf[1][0], bf[2][0]], [bf[1][1], bf[2][1]], color="red", linewidth=2.5,
                marker="o", markersize=8, zorder=4, label=f"Brute-Force  d={bf[0]:.6f}")
    if dc:
        ax.plot([dc[1][0], dc[2][0]], [dc[1][1], dc[2][1]], color="blue", linewidth=1.5,
                linestyle=":", marker="x", markersize=10, zorder=5,
                label=f"Divide&Conquer  d={dc[0]:.6f}")
    ax.set_title("Closest pair of points")
    ax.set_xlabel("x"); ax.set_ylabel("y")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(alpha=0.25)


def plot_runtime(ax, sizes, bf_times, dc_times):
    ax.plot(sizes, bf_times, "o-", color="red", label="Brute-Force  O(N²)")
    ax.plot(sizes, dc_times, "s-", color="blue", label="Divide & Conquer  O(N log N)")
    ax.set_xlabel("N (number of points)"); ax.set_ylabel("Running time (ms)")
    ax.set_title("Running time vs N")
    ax.legend(); ax.grid(alpha=0.3)


def animate_recursion(points, ctx, out_dir, show):
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation

    events, px = ctx["events"], ctx["px"]
    xs = [p[0] for p in points]; ys = [p[1] for p in points]
    fig, ax = plt.subplots(figsize=(8, 6))

    def draw(k):
        ax.clear()
        kind, lo, hi, mid_x, d, pair, delta = events[k]
        ax.scatter(xs, ys, s=18, c="#bbbbbb", zorder=2)
        seg = px[lo:hi]
        ax.scatter([p[0] for p in seg], [p[1] for p in seg], s=30, c="orange", zorder=3)
        ax.axvspan(px[lo][0], px[hi - 1][0], color="orange", alpha=0.10)
        if mid_x is not None:
            ax.axvline(mid_x, color="green", linestyle="--")
        if kind == "merge":
            ax.axvspan(mid_x - delta, mid_x + delta, color="green", alpha=0.2)
        if pair is not None:
            ax.plot([pair[0][0], pair[1][0]], [pair[0][1], pair[1][1]],
                    color="blue", linewidth=2, marker="o")
        label = {"split": "SPLIT", "base": "BASE CASE", "merge": "MERGE (check strip)"}[kind]
        extra = f"  best d={d:.4f}" if d is not None else ""
        ax.set_title(f"Step {k + 1}/{len(events)}: {label}  [{lo}:{hi}]{extra}")
        ax.grid(alpha=0.25)

    anim = FuncAnimation(fig, draw, frames=len(events), interval=500, repeat=False)
    try:
        path = os.path.join(out_dir, "animation.gif")
        anim.save(path, writer="pillow", fps=2)
        print(f"Saved animation -> {path}")
    except Exception as e:  # pillow missing, etc.
        print(f"(Could not save GIF: {e})")
    if show:
        plt.show()
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def read_n(arg_n: Optional[int]) -> int:
    if arg_n is not None:
        return arg_n
    if sys.stdin.isatty():
        sys.stderr.write("Enter N: ")
    tok = sys.stdin.read().split()
    if not tok:
        sys.exit("No input for N.")
    try:
        return int(tok[0])
    except ValueError:
        sys.exit("N must be an integer.")


def report(name: str, res: Result) -> str:
    if res is None:
        return f"{name}: N/A (need at least 2 points)"
    return f"{name}: {res[0]:.6f} {fmt_pt(res[1])} {fmt_pt(res[2])}"


def main():
    ap = argparse.ArgumentParser(description="Closest pair: brute force vs divide & conquer")
    ap.add_argument("--n", type=int, help="number of points (otherwise read from stdin)")
    ap.add_argument("--seed", type=int, default=None, help="random seed (reproducible runs)")
    ap.add_argument("--range", type=float, default=100.0, dest="rng_range",
                    help="coordinates drawn from [-range, range] (default 100)")
    ap.add_argument("--int", action="store_true", dest="integer", help="use integer coordinates")
    ap.add_argument("--sizes", type=int, nargs="+",
                    default=[100, 200, 500, 1000, 2000, 3000, 4000],
                    help="N values for the running-time graph")
    ap.add_argument("--verify", action="store_true", help="run randomised agreement tests")
    ap.add_argument("--animate", action="store_true",
                    help="animate recursive split/merge (use small N, e.g. <= 40)")
    ap.add_argument("--no-plots", action="store_true", help="skip all plots/benchmark")
    ap.add_argument("--no-show", action="store_true", help="save images, do not open windows")
    ap.add_argument("--out", default="output", help="directory for saved images")
    args = ap.parse_args()

    n = read_n(args.n)
    if n < 0:
        sys.exit("N must be non-negative.")
    rng = random.Random(args.seed)
    points = generate_points(n, args.rng_range, args.integer, rng)

    # ---- run both algorithms (timing runs carry no logging overhead) ----
    bf, t_bf = timed(brute_force, points)
    dc, t_dc = timed(divide_and_conquer, points)
    ctx: dict = {}
    divide_and_conquer(points, ctx)  # untimed run that records strip/divider info

    print(report("Brute-Force", bf))
    print(report("Divide-and-Conquer", dc))
    print(f"Execution time: Brute-Force = {t_bf:.3f} ms, Divide-and-Conquer = {t_dc:.3f} ms")

    if n < 2:
        print("Note: fewer than 2 points, no pair exists.", file=sys.stderr)
    agree = distances_agree(bf, dc)
    print(f"Distances agree: {agree}", file=sys.stderr)

    if args.verify:
        print("\nRunning randomised verification ...", file=sys.stderr)
        ok = verify(trials=400, max_n=300, seed=args.seed or 0)
        print(f"Verification {'PASSED' if ok else 'FAILED'}", file=sys.stderr)

    if args.no_plots:
        return

    import matplotlib
    if args.no_show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(args.out, exist_ok=True)

    print("\nBenchmarking ...", file=sys.stderr)
    bf_times, dc_times, all_ok = benchmark(args.sizes, args.rng_range, args.seed or 0)
    print(f"Agreement across all benchmark sizes: {all_ok}", file=sys.stderr)

    # Figure 1: points + closest pairs + divider + strip
    if n >= 2:
        fig1, ax1 = plt.subplots(figsize=(8, 7))
        plot_points(ax1, points, bf, dc, ctx)
        fig1.tight_layout()
        fig1.savefig(os.path.join(args.out, "closest_pair.png"), dpi=150)

    # Figure 2: running time vs N
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    plot_runtime(ax2, args.sizes, bf_times, dc_times)
    fig2.tight_layout()
    fig2.savefig(os.path.join(args.out, "runtime.png"), dpi=150)
    print(f"Saved plots in ./{args.out}/", file=sys.stderr)

    if args.animate and n >= 2:
        ctx_anim = {"events": []}
        divide_and_conquer(points, ctx_anim)
        animate_recursion(points, ctx_anim, args.out, show=not args.no_show)

    if not args.no_show:
        plt.show()


if __name__ == "__main__":
    main()