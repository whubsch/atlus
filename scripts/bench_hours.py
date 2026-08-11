"""Benchmark `get_hours`/`get_times` and their stages.

Run before and after a change to compare:

```sh
python scripts/bench_hours.py --save baseline.json
# ...make changes...
python scripts/bench_hours.py --compare baseline.json
```
"""

import argparse
import json
import time
from pathlib import Path

from src.atlus.hours import (
    _normalize,
    _parse_days,
    _parse_point_times,
    _parse_times,
    get_hours,
    get_times,
)

HOURS = [
    "Monday to Friday 9am-5pm, Saturday 9am-12pm",
    "Mo-Fr 08:00-17:00",
    "Mon-Fri 9:00 AM - 5:00 PM; Sat 10-2; Sun closed",
    "Daily 7am-11pm",
    "Weekdays 9-5; Weekends 10-4",
    "Tu,Th 09:00-12:00,13:00-17:00",
    "M-F 6a-9p Sa 8a-8p Su 10a-6p",
    "Mo-Sa 11:00-22:00; Su 12:00-21:00",
]
"""Representative opening_hours inputs."""

TIMES = [
    "Mo-Fr 15:00,18:00,19:00,23:00; Sa 15:00; Su 10:30,23:00",
    "Monday through Friday 3pm and 6pm",
    "Mo-Fr 09:00",
    "Tu,Th 08:30,17:45",
]
"""Representative point-in-time inputs."""

DAY_PARTS = ["Monday to Friday", "Mo-Fr", "Weekdays", "Tu,Th", "M-F", "Sa/Su", "Daily"]
TIME_PARTS = ["9am-5pm", "08:00-17:00", "9:00 AM - 5:00 PM", "10-2", "6a-9p"]
POINT_PARTS = ["15:00,18:00,19:00,23:00", "3pm", "08:30,17:45", "09:00"]


def _time(fn, args: list, repeat: int, number: int) -> float:
    """Return the best per-call time in microseconds, ignoring failures."""
    runs = []
    for _ in range(repeat):
        start = time.perf_counter()
        for _ in range(number):
            for arg in args:
                try:
                    fn(arg)
                except Exception:  # noqa: BLE001 - timing only, errors are input-dependent
                    pass
        runs.append((time.perf_counter() - start) / (number * len(args)) * 1e6)
    return min(runs)


def run(repeat: int = 5, number: int = 200) -> dict[str, float]:
    """Benchmark each stage of the hours pipeline."""
    return {
        "_normalize": _time(_normalize, HOURS, repeat, number),
        "_parse_days": _time(_parse_days, DAY_PARTS, repeat, number),
        "_parse_times": _time(_parse_times, TIME_PARTS, repeat, number),
        "_parse_point_times": _time(_parse_point_times, POINT_PARTS, repeat, number),
        "get_hours": _time(get_hours, HOURS, repeat, number),
        "get_times": _time(get_times, TIMES, repeat, number),
    }


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

    ok = sum(1 for h in HOURS if get_hours(h))
    print(f"\nsanity: {ok}/{len(HOURS)} hours inputs parsed")


if __name__ == "__main__":
    main()
