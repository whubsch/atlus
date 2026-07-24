"""Functions and tools to process raw opening hours strings."""

import regex

from .objects import DayRange, OpeningHours, RuleSet, TimeSpan
from .resources import (
    closed_comp,
    comma_day_comp,
    daily_comp,
    day_24_comp,
    day_expand,
    day_order,
    filler_comp,
    rule_split_comp,
    time_range_split_comp,
    time_start_comp,
    time_token_comp,
    weekday_comp,
    weekend_comp,
)


def _normalize(value: str) -> str:
    """Normalize punctuation/whitespace before parsing.

    Args:
        value (str): The raw string to normalize.

    Returns:
        str: The normalized string.
    """
    value = value.replace("&", ",").replace("and", ",")
    # collapse horizontal whitespace only -- newlines are meaningful rule
    # separators and are handled by rule_split_comp
    value = regex.sub(r"[ \t]+", " ", value)
    return value.strip(" .,")


def _parse_days(day_part: str) -> list[DayRange]:
    """Parse the "day" portion of a rule segment into a list of DayRange.

    Args:
        day_part (str): The substring believed to contain day information.

    Returns:
        list[DayRange]: The parsed day ranges. Empty means "every day".
    """
    day_part = filler_comp.sub(" ", day_part)
    day_part = regex.sub(r"\s+", " ", day_part).strip(" ,")
    if not day_part:
        return []

    if daily_comp.search(day_part):
        return []
    if weekday_comp.search(day_part):
        return [DayRange(start="Mo", end="Fr")]
    if weekend_comp.search(day_part):
        return [DayRange(start="Sa", end="Su")]

    ranges: list[DayRange] = []
    for token in regex.split(r"\s*,\s*", day_part):
        token = token.strip(" .")
        if not token:
            continue
        parts = time_range_split_comp.split(token, maxsplit=1)
        parts = [p.strip(" .") for p in parts if p.strip(" .")]
        if len(parts) == 2:
            start_code = day_expand.get(parts[0].upper())
            end_code = day_expand.get(parts[1].upper())
            if start_code is None or end_code is None:
                raise ValueError(f"Unrecognized day range: {token!r}")
            ranges.append(DayRange(start=start_code, end=end_code))
        elif len(parts) == 1:
            code = day_expand.get(parts[0].upper())
            if code is None:
                raise ValueError(f"Unrecognized day: {token!r}")
            ranges.append(DayRange(start=code))
        else:
            raise ValueError(f"Unrecognized day token: {token!r}")

    return ranges


def _parse_single_time(token: str) -> tuple[int, int, bool]:
    """Parse a single clock time token.

    Args:
        token (str): A single time value, e.g. "8am", "08:00", "noon".

    Returns:
        tuple[int, int, bool]: The hour (0-24), minute, and whether the
        value is unambiguously resolved (has a meridiem, or an explicit
        24-hour style with a colon).

    Raises:
        ValueError: If the token cannot be parsed as a time.
    """
    token = token.strip().lower()
    if token == "noon":
        return 12, 0, True
    if token == "midnight":
        return 24, 0, True

    match = time_token_comp.match(token)
    if not match:
        raise ValueError(f"Unrecognized time: {token!r}")

    hour = int(match.group(1))
    minute = int(match.group(3) or 0)
    meridiem = match.group(4)
    has_colon = match.group(2) is not None

    if meridiem:
        meridiem = meridiem.replace(".", "")
        if meridiem == "pm" and hour != 12:
            hour += 12
        elif meridiem == "am" and hour == 12:
            hour = 0
        return hour, minute, True

    if has_colon:
        # explicit HH:MM with no am/pm is treated as already 24-hour
        return hour, minute, True

    # bare digit, e.g. "9" or "5" -- ambiguous, needs resolution later
    return hour, minute, False


def _resolve_pair(
    start: tuple[int, int, bool], end: tuple[int, int, bool]
) -> tuple[str, str]:
    """Resolve a pair of (possibly ambiguous) times into 24-hour strings.

    Args:
        start (tuple[int, int, bool]): The start hour, minute, and resolved flag.
        end (tuple[int, int, bool]): The end hour, minute, and resolved flag.

    Returns:
        tuple[str, str]: The resolved "HH:MM" start and end strings.
    """
    sh, sm, s_ok = start
    eh, em, e_ok = end

    if not s_ok and not e_ok:
        # bare "9-5" style: assume typical business hours (AM to PM)
        if sh == 12:
            sh = 0
        if eh != 12:
            eh += 12
    elif s_ok and not e_ok:
        candidate_pm = eh if eh == 12 else eh + 12
        candidate_am = 0 if eh == 12 else eh
        eh = candidate_pm if candidate_pm > sh else candidate_am
    elif e_ok and not s_ok:
        # prefer PM for the start time (it must come before the resolved
        # end time); fall back to AM if PM would put start after end
        candidate_pm = sh if sh == 12 else sh + 12
        candidate_am = 0 if sh == 12 else sh
        sh = candidate_pm if candidate_pm < eh else candidate_am

    return f"{sh:02d}:{sm:02d}", f"{eh:02d}:{em:02d}"


def _parse_time_span(token: str) -> TimeSpan:
    """Parse a single time range token, e.g. "8am-5pm" or "08:00-12:00".

    Args:
        token (str): The time range token.

    Returns:
        TimeSpan: The parsed time span.

    Raises:
        ValueError: If the token isn't a valid time range.
    """
    parts = [p for p in time_range_split_comp.split(token.strip(), maxsplit=1) if p]
    if len(parts) != 2:
        raise ValueError(f"Unrecognized time range: {token!r}")

    start = _parse_single_time(parts[0])
    end = _parse_single_time(parts[1])
    start_str, end_str = _resolve_pair(start, end)
    return TimeSpan(start=start_str, end=end_str)


def _parse_times(time_part: str) -> list[TimeSpan]:
    """Parse the "time" portion of a rule segment into a list of TimeSpan.

    Args:
        time_part (str): The substring believed to contain time information.

    Returns:
        list[TimeSpan]: The parsed time spans.
    """
    tokens = [t for t in regex.split(r"\s*,\s*", time_part.strip(" ,")) if t]
    return [_parse_time_span(token) for token in tokens]


def _split_comma_days(text: str) -> list[str]:
    """Split a top-level segment on commas that introduce a new day group.

    A comma only starts a new rule segment if the text since the last split
    point already contains time/status information -- otherwise, it's just
    another day being added to the same day list (e.g. "Mo,We").

    Args:
        text (str): The top-level segment to split.

    Returns:
        list[str]: The resulting sub-segments.
    """
    results = []
    last = 0
    for match in comma_day_comp.finditer(text):
        candidate = text[last : match.start()]
        if time_start_comp.search(candidate):
            results.append(text[last : match.start()])
            last = match.end()
    results.append(text[last:])
    return [segment for segment in results if segment.strip()]


def _split_day_time(segment: str) -> tuple[str, str]:
    """Split a rule segment into its day portion and time/status portion.

    Args:
        segment (str): A single rule segment.

    Returns:
        tuple[str, str]: The day portion and the time/status portion.
    """
    match = time_start_comp.search(segment)
    if not match:
        # no digits/status keywords found -- treat whole thing as days,
        # implying it's open with no specified times (unusual, but handled)
        return segment.strip(), ""
    return segment[: match.start()].strip(), segment[match.start() :].strip()


def _parse_segment(segment: str) -> RuleSet:
    """Parse a single rule segment into a RuleSet.

    Args:
        segment (str): A single rule segment (days plus times/status).

    Returns:
        RuleSet: The parsed rule.
    """
    day_part, time_part = _split_day_time(segment)
    days = _parse_days(day_part)

    if closed_comp.search(time_part):
        return RuleSet(days=days, closed=True)
    if day_24_comp.search(time_part):
        return RuleSet(days=days, is_24h=True)

    times = _parse_times(time_part)
    return RuleSet(days=days, times=times)


def _rule_signature(rule: RuleSet) -> tuple:
    """Build a hashable signature representing a rule's status/times.

    Args:
        rule (RuleSet): The rule to summarize.

    Returns:
        tuple: A hashable value equal for rules that should be merged.
    """
    return (rule.closed, rule.is_24h, tuple((t.start, t.end) for t in rule.times))


def _expand_days(day_ranges: list[DayRange]) -> list[str]:
    """Expand a list of DayRange into individual day codes.

    Args:
        day_ranges (list[DayRange]): The day ranges to expand. An empty
            list is treated as applying to every day of the week.

    Returns:
        list[str]: The individual two-letter day codes covered.
    """
    if not day_ranges:
        return list(day_order)

    days: list[str] = []
    for day_range in day_ranges:
        start_idx = day_order.index(day_range.start.value)
        end_idx = day_order.index(day_range.end.value) if day_range.end else start_idx
        if end_idx >= start_idx:
            days.extend(day_order[start_idx : end_idx + 1])
        else:
            # range wraps around the end of the week, e.g. Sa-Mo
            days.extend(day_order[start_idx:] + day_order[: end_idx + 1])
    return days


def _collapse_days_to_ranges(days: set[str]) -> list[DayRange]:
    """Collapse a set of day codes into the minimal list of DayRange.

    Args:
        days (set[str]): The day codes to collapse.

    Returns:
        list[DayRange]: The days grouped into contiguous ranges, in week order.
    """
    ordered = [day for day in day_order if day in days]
    if not ordered:
        return []

    ranges: list[DayRange] = []
    run_start = run_prev = ordered[0]
    for day in ordered[1:]:
        if day_order.index(day) == day_order.index(run_prev) + 1:
            run_prev = day
            continue
        ranges.append(
            DayRange(start=run_start)
            if run_start == run_prev
            else DayRange(start=run_start, end=run_prev)
        )
        run_start = run_prev = day
    ranges.append(
        DayRange(start=run_start)
        if run_start == run_prev
        else DayRange(start=run_start, end=run_prev)
    )
    return ranges


def _coalesce_rules(rules: list[RuleSet]) -> list[RuleSet]:
    """Merge rules that share identical hours, and sort by week order.

    This lets out-of-order, per-day input (e.g. a Thursday-first weekly
    schedule) collapse into compact, correctly-ordered OSM ranges like
    `Mo-Th 17:00-21:30`.

    Args:
        rules (list[RuleSet]): The individually-parsed rules, in input order.
            Later rules win if the same day appears more than once.

    Returns:
        list[RuleSet]: The merged rules, sorted by first day of the week.
    """
    day_to_rule: dict[str, RuleSet] = {}
    for rule in rules:
        for day in _expand_days(rule.days):
            day_to_rule[day] = rule

    sig_to_days: dict[tuple, set[str]] = {}
    sig_to_rule: dict[tuple, RuleSet] = {}
    for day, rule in day_to_rule.items():
        sig = _rule_signature(rule)
        sig_to_days.setdefault(sig, set()).add(day)
        sig_to_rule[sig] = rule

    merged = [
        RuleSet(
            days=_collapse_days_to_ranges(days),
            times=sig_to_rule[sig].times,
            closed=sig_to_rule[sig].closed,
            is_24h=sig_to_rule[sig].is_24h,
        )
        for sig, days in sig_to_days.items()
    ]
    merged.sort(key=lambda rule: day_order.index(rule.days[0].start.value))
    return merged


def get_hours(value: str) -> str:
    """Process opening hours strings into the OSM `opening_hours` format.

    ```python
    >>> get_hours("Mo-Fr 08:00-12:00,13:00-17:30")
    "Mo-Fr 08:00-12:00,13:00-17:30"
    >>> get_hours("Monday to Friday 9am-5pm, Saturday 9am-12pm")
    "Mo-Fr 09:00-17:00; Sa 09:00-12:00"
    >>> get_hours("Closed")
    "off"
    ```

    Args:
        value (str): The opening hours string to process.

    Returns:
        str: The formatted opening hours string.

    Raises:
        ValueError: If the string cannot be parsed.
    """
    normalized = _normalize(value)
    if not normalized:
        raise ValueError("Empty opening hours string.")

    if closed_comp.fullmatch(normalized.strip()):
        return "off"
    if day_24_comp.fullmatch(normalized.strip()):
        return "24/7"

    top_segments = [s for s in rule_split_comp.split(normalized) if s.strip()]
    segments = [sub for top in top_segments for sub in _split_comma_days(top)]
    rules = [_parse_segment(segment) for segment in segments]

    # only coalesce/reorder when every rule specifies explicit days -- if any
    # rule applies to the whole week (e.g. "daily"), leave the input order
    # alone since day semantics may be intentionally layered
    if rules and all(rule.days for rule in rules):
        rules = _coalesce_rules(rules)

    return OpeningHours(rules=rules).to_osm()
