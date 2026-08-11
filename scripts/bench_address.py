"""Benchmark `get_address` and its stages.

Run before and after a parser change to compare:

```sh
python scripts/bench_address.py --save baseline.json
# ...make changes...
python scripts/bench_address.py --compare baseline.json
```
"""

import argparse
import json
import statistics
import time
from pathlib import Path

from src.atlus.atlus import (
    _apply_field_processors,
    _parse_address,
    abbrs,
    clean_address,
    get_address,
)
from src.atlus.objects import Address

SAMPLE = [
    "345 Maple Rd, Countryside PA 24680-0198",
    "100 S Michigan Ave, Apt 2500, Chicago Illinois",
    "27520 Hwy 98, Daphne AL 36526",
    "33 W 42nd Street",
    "1470 South Washington Street, North Attleboro MA",
    "500-600 Broadway, New York NY 10012",
    "222 NW Pineapple Ave Suite A, Beachville, SC 75309",
    "8 Embarcadero Plz, San Francisco CA 94111",
]
"""Representative spread: ZIP+4, units, highways, directionals, ranges."""


def _time(fn, args: list, repeat: int, number: int) -> float:
    """Return the best per-call time in microseconds."""
    runs = []
    for _ in range(repeat):
        start = time.perf_counter()
        for _ in range(number):
            for arg in args:
                fn(arg)
        runs.append((time.perf_counter() - start) / (number * len(args)) * 1e6)
    return min(runs)


def run(repeat: int = 5, number: int = 200) -> dict[str, float]:
    """Benchmark each stage of the address pipeline."""
    parsed = [_parse_address(s)[0] for s in SAMPLE]
    processed = [_apply_field_processors(p) for p in parsed]

    results = {
        "clean_address": _time(clean_address, SAMPLE, repeat, number),
        "abbrs": _time(abbrs, SAMPLE, repeat, number),
        "_parse_address": _time(_parse_address, SAMPLE, repeat, number),
        "_apply_field_processors": _time(
            _apply_field_processors, parsed, repeat, number
        ),
        "validate_and_dump": _time(
            lambda d: Address.model_validate(d).model_dump(
                exclude_none=True, by_alias=True
            ),
            processed,
            repeat,
            number,
        ),
        "get_address": _time(get_address, SAMPLE, repeat, number),
    }
    return results


def report(results: dict[str, float], baseline: dict[str, float] | None) -> None:
    """Print a table of results, optionally against a saved baseline."""
    header = f"{'stage':<26}{'now':>12}"
    if baseline:
        header += f"{'baseline':>12}{'change':>12}"
    print(header)
    print("-" * len(header))
    for key, value in results.items():
        line = f"{key:<26}{value:>9.1f} us"
        if baseline and key in baseline:
            old = baseline[key]
            speedup = old / value if value else float("inf")
            line += f"{old:>9.1f} us{speedup:>11.2f}x"
        print(line)


def main() -> None:
    """Parse args and run the benchmark."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--save", type=Path, help="write results to a JSON file")
    parser.add_argument("--compare", type=Path, help="compare against a JSON file")
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument("--number", type=int, default=200)
    args = parser.parse_args()

    results = run(repeat=args.repeat, number=args.number)

    baseline = None
    if args.compare and args.compare.exists():
        baseline = json.loads(args.compare.read_text())

    report(results, baseline)

    if args.save:
        args.save.write_text(json.dumps(results, indent=2))
        print(f"\nsaved to {args.save}")

    accuracy = statistics.mean(
        1.0 if get_address(s)[0].get("addr:street") else 0.0 for s in SAMPLE
    )
    print(f"\nsanity: {accuracy:.0%} of sample produced addr:street")


if __name__ == "__main__":
    main()
