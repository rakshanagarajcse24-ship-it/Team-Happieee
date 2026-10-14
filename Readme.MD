# Closest Pair of Points: Brute-Force vs Divide-and-Conquer

Two implementations of the closest-pair problem with verification, benchmarking and visualization.

| Algorithm | Time complexity | Idea |
|---|---|---|
| Brute-Force | O(N²) | Check every pair |
| Divide-and-Conquer | O(N log N) | Split by x, recurse, then scan a 2d-wide strip sorted by y (≤ 7 neighbours each) |

## Setup
```bash
pip install -r requirements.txt
```

## Run
```bash
echo 200 | python closest_pair.py                  # N from stdin, random float points
python closest_pair.py --n 500 --seed 42 --int     # integer coordinates, reproducible
python closest_pair.py --n 30 --animate            # animate splitting/merging (saves GIF)
python closest_pair.py --n 1000 --verify           # randomised agreement tests
python closest_pair.py --n 200 --no-show           # headless: only save PNGs
```
Options: `--range R`, `--sizes N1 N2 ...` (benchmark sizes), `--no-plots`, `--out DIR`.

## Output
```
Brute-Force: 1.057471 (-96.6619, -97.0880) (-95.8364, -96.4271)
Divide-and-Conquer: 1.057471 (-96.6619, -97.0880) (-95.8364, -96.4271)
Execution time: Brute-Force = 2.094 ms, Divide-and-Conquer = 0.380 ms
```
Extra diagnostics (agreement checks, benchmark table) go to stderr. Images are saved in `output/`:
`closest_pair.png` (points, both closest pairs, dividing line, strip), `runtime.png`, `animation.gif`.

## Corner cases handled
N = 0, 1 (reports "N/A"), N = 2, duplicate points (distance 0), all-identical points,
collinear points, shared x or y coordinates, highly skewed distributions.
When several pairs tie for the minimum, the two algorithms may report different pairs,
but the **distances always agree** (`--verify` checks this).