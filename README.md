# Budget Traveller with Coupons

A Python project for finding the least expensive directed route from city 1 to city N, with at most K intermediate stops and up to C half-price coupons. Coupon prices are rounded down.

## Files

- `main.py` — solver, CSV input/output, random graph generator, and animated visualization.
- `sample_flights.csv` — sample input graph for Option 2.
- `sample_cases.txt` — example input and expected answer.
- `requirements.txt` — visualization dependencies.

## Setup

Python 3.9 or newer is recommended.

```bash
python -m pip install -r requirements.txt
python main.py
```

Choose one of the three modes in the menu:

1. **Manual input:** enter `N M`, then `K C`, then M lines of `u v price`.
2. **CSV input:** use a CSV with headers `source,destination,price`; then enter `N` and `K C`.
3. **Generate graph:** enter `N` and `K C`. A guaranteed valid route is generated and saved to `generated_flights.csv`.

The program prints the minimum cost (or `-1`) and route, and writes `result.csv` with selected flights marked by `x`. Coupon flights are also marked by `x` in the `coupon_used` column. A graph window animates the selected route; coupon flights are highlighted in gold.

## Sample CSV format

```csv
source,destination,price
1,2,500
2,4,300
4,5,100
```

Cities are numbered from 1 through N. A stop is an intermediate city, so a route with at most K stops can contain at most K+1 flights. Flight prices must be nonnegative integers.
