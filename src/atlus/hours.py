"""Functions and tools to process raw opening hours and point-in-time strings.

This module handles two related but distinct OSM conventions:

- Ranged tags like `opening_hours`, parsed with `get_hours`.
- Point-in-time tags like `collection_times`/`service_times`, parsed with
  `get_times`.
"""

import regex

from .objects import (
    Day,
    DayRange,
    OpeningHours,
    PointRuleSet,
    PointTimes,
    RuleSet,
    TimeSpan,
)

EARLY_MORNING_CUTOFF_HOUR = 6
"""The latest hour (24-hour, exclusive) still considered a plausible
overnight closing time, e.g. "2am" or "5am" but not "2pm"."""
from .resources import (
    closed_comp,
    comma_day_comp,
    daily_comp,
    day_24_comp,
    day_comp,
    day_expand,
    day_index,
    day_present_comp,
    day_order,
    day_range_comp,
    filler_comp,
    holiday_name_comp,
    ignored_phrase_comp,
    month_comp,
    nth_weekday_comp,
    rule_split_comp,
    solar_time_comp,
    space_day_comp,
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
    # Replace Spanish "y" (and) and "de" (of/from) with comma, using word
    # boundaries to avoid matching letters within words
    value = regex.sub(r"\by\b", ",", value, flags=regex.IGNORECASE)
    value = regex.sub(r"\bde\b", "", value, flags=regex.IGNORECASE)
    # drop phrases that carry no day/time information of their own (e.g.
    # "Last Seating") before any other parsing happens
    value = ignored_phrase_comp.sub("", value)
    # collapse horizontal whitespace only -- newlines are meaningful rule
    # separators and are handled by rule_split_comp
    value = regex.sub(r"[ \t]+", " ", value)
    value = value.strip(" ,")
    # strip trailing periods only if NOT part of a.m./p.m. abbreviation
    # (i.e., not preceded by a single letter like "a." or "p.")
    while value.endswith(".") and not regex.search(
        r"[a-z]\.$", value, flags=regex.IGNORECASE
    ):
        value = value[:-1].rstrip(" .,")
    return value


def _reject_unsupported_calendar_refs(value: str) -> None:
    """Raise if the string references calendar/date-based rules that this
    package doesn't attempt to parse, rather than silently mangling them.

    This includes month names or specific dates (e.g. "Jan 1", "Dec 25"),
    named holidays (e.g. "Easter", "Thanksgiving"), and OSM's "nth weekday
    of month" notation (e.g. "Th[4]" for the fourth Thursday). These all
    require actual calendar logic, which is out of scope here -- input
    containing them should be handled manually instead of risking a
    silently incorrect result.

    Args:
        value (str): The string to check (normalized or raw).

    Raises:
        ValueError: If a calendar/date-based reference is detected.
    """
    for comp, kind in (
        (nth_weekday_comp, "an 'nth weekday of month' reference (e.g. 'Th[4]')"),
        (month_comp, "a month name or specific date (e.g. 'Jan 1')"),
        (holiday_name_comp, "a named holiday (e.g. 'Easter', 'Thanksgiving')"),
    ):
        match = comp.search(value)
        if match:
            raise ValueError(
                "Calendar/date-based rules aren't supported"
                f" -- found {kind}: {match.group()!r}."
            )


def _parse_days(day_part: str) -> list[DayRange]:
    """Parse the "day" portion of a rule segment into a list of DayRange.

    Args:
        day_part (str): The substring believed to contain day information.

    Returns:
        list[DayRange]: The parsed day ranges. Empty means "every day".
    """
    day_part = filler_comp.sub(" ", day_part)
    day_part = regex.sub(r"\s+", " ", day_part).strip(" ,-\u2013\u2014\u2015")
    if not day_part:
        return []

    if daily_comp.search(day_part):
        return []
    if weekday_comp.search(day_part):
        return [DayRange(start="Mo", end="Fr")]
    if weekend_comp.search(day_part):
        return [DayRange(start="Sa", end="Su")]

    ranges: list[DayRange] = []
    # a slash between day names is used as a list separator (e.g. "We/Sa"
    # meaning "We, Sa"), not a range -- treat it the same as a comma
    for token in regex.split(r"\s*[,/]\s*", day_part):
        token = token.strip(" .:")
        if not token:
            continue
        parts = time_range_split_comp.split(token, maxsplit=1)
        parts = [p.strip(" .:") for p in parts if p.strip(" .:")]
        if len(parts) == 2:
            start_code = day_expand.get(parts[0].upper())
            end_code = day_expand.get(parts[1].upper())
            if start_code is None or end_code is None:
                raise ValueError(f"Unrecognized day range: {token!r}")
            if start_code == end_code:
                # an explicit range that starts and ends on the same day
                # (e.g. "Domingo a domingo"/"Sunday to Sunday") is an
                # idiom for the full week, wrapping all the way around
                return []
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
        if meridiem.startswith("p") and hour != 12:
            hour += 12
        elif meridiem.startswith("a") and hour == 12:
            hour = 0
        return hour, minute, True

    if has_colon:
        # explicit HH:MM with no am/pm is treated as already 24-hour
        return hour, minute, True

    if hour > 12:
        # a bare hour above 12 (e.g. "17") can only be a 24-hour value --
        # there's no 12-hour reading of it, so it's already unambiguous
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


def _meridiem_letter(token: str) -> str | None:
    """Extract the explicit am/pm marker (if any) from a time token.

    Args:
        token (str): A single time token, e.g. "8:30p" or "4:30".

    Returns:
        str | None: "a" or "p" if the token has an explicit meridiem
        marker, otherwise None.
    """
    match = time_token_comp.match(token.strip().lower())
    if not match or not match.group(4):
        return None
    return match.group(4).replace(".", "")[0]


def _match_solar_time(token: str) -> str | None:
    """Check whether a token is one of OSM's solar-relative time keywords.

    Args:
        token (str): A single time value, e.g. "sunrise" or "08:00".

    Returns:
        str | None: The lowercased keyword ("dawn", "dusk", "sunrise", or
        "sunset") if the token is one of them, otherwise None.
    """
    token = token.strip().lower()
    return token if solar_time_comp.match(token) else None


def _parse_time_span(token: str) -> TimeSpan:
    """Parse a single time range token, e.g. "8am-5pm", "08:00-12:00", or
    "sunrise-sunset".

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

    start_solar = _match_solar_time(parts[0])
    end_solar = _match_solar_time(parts[1])

    if start_solar or end_solar:
        # solar keywords are relative and unambiguous on their own -- there's
        # no pair to resolve against, and no meaningful way to compare them
        # against a clock time to detect a "backwards" span, so each side is
        # handled independently and the overnight-span check is skipped
        if not start_solar:
            hour, minute, _ = _parse_single_time(parts[0])
            start_solar = f"{hour:02d}:{minute:02d}"
        if not end_solar:
            hour, minute, _ = _parse_single_time(parts[1])
            end_solar = f"{hour:02d}:{minute:02d}"
        return TimeSpan(start=start_solar, end=end_solar)

    start = _parse_single_time(parts[0])
    end = _parse_single_time(parts[1])
    start_str, end_str = _resolve_pair(start, end)

    # a colon-form start time with no explicit am/pm marker (e.g. the "4:30"
    # in "4:30-8:30p") is normally assumed to already be in 24-hour form,
    # but when it's paired with an explicit PM end time it's meant to share
    # that same meridiem -- adjust it to match, unless it's already noon.
    if (
        start[2]
        and _meridiem_letter(parts[0]) is None
        and _meridiem_letter(parts[1]) == "p"
        and 0 < start[0] < 12
    ):
        start_str = f"{start[0] + 12:02d}:{start[1]:02d}"

    # an end time earlier than the start time normally means the span
    # crosses midnight (e.g. "22:00-02:00"), which is valid OSM syntax --
    # but only when the end time actually falls in the late night/early
    # morning hours. An end time later in the day (e.g. "16:00-14:00")
    # is almost certainly a mistake rather than a ~22 hour overnight span.
    if end_str < start_str and int(end_str[:2]) >= EARLY_MORNING_CUTOFF_HOUR:
        raise ValueError(
            f"Invalid time range: {token.strip()!r} ends before it starts, "
            "and isn't a plausible overnight closing time"
        )

    return TimeSpan(start=start_str, end=end_str)


def _merge_time_spans(spans: list[TimeSpan]) -> list[TimeSpan]:
    """Merge adjacent time spans where one ends exactly when the next
    starts (e.g. "11:30-15:00,15:00-17:00" -> "11:30-17:00"), since such
    back-to-back windows represent one continuous open period.

    Args:
        spans (list[TimeSpan]): The time spans to merge, in input order.

    Returns:
        list[TimeSpan]: The merged time spans.
    """
    if not spans:
        return spans

    merged = [spans[0]]
    for span in spans[1:]:
        if span.start == merged[-1].end:
            merged[-1] = TimeSpan(start=merged[-1].start, end=span.end)
        else:
            merged.append(span)
    return merged


def _parse_times(time_part: str) -> list[TimeSpan]:
    """Parse the "time" portion of a rule segment into a list of TimeSpan.

    Args:
        time_part (str): The substring believed to contain time information.

    Returns:
        list[TimeSpan]: The parsed time spans.
    """
    tokens = [t for t in regex.split(r"\s*,\s*", time_part.strip(" ,")) if t]
    return _merge_time_spans([_parse_time_span(token) for token in tokens])


def _parse_point_time(token: str) -> str:
    """Parse a single point-in-time token into a 24-hour `HH:MM` string, or
    a solar keyword ("dawn", "dusk", "sunrise", "sunset").

    Unlike a time range, there's no second value to resolve an ambiguous
    bare-digit time against, so such values (e.g. "3" with no colon or
    am/pm marker) are taken at face value as an already-24-hour hour.

    Args:
        token (str): A single time value, e.g. "3pm", "15:00", "sunrise".

    Returns:
        str: The resolved "HH:MM" string, or the solar keyword as-is.

    Raises:
        ValueError: If the token cannot be parsed as a time.
    """
    solar = _match_solar_time(token)
    if solar:
        return solar
    hour, minute, _ = _parse_single_time(token)
    return f"{hour:02d}:{minute:02d}"


def _parse_point_times(time_part: str) -> list[str]:
    """Parse the "time" portion of a point-in-time rule segment into a
    sorted, de-duplicated list of "HH:MM" values.

    Args:
        time_part (str): The substring believed to contain time information.

    Returns:
        list[str]: The parsed, sorted point-in-time values.
    """
    tokens = [t for t in regex.split(r"\s*,\s*", time_part.strip(" ,")) if t]
    return sorted({_parse_point_time(token) for token in tokens})


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


def _split_space_days(text: str) -> list[str]:
    """Split a top-level segment on whitespace that introduces a new day
    group, when there's no punctuation separating adjacent rules at all
    (e.g. "Mo-Fr 08:00-21:00 Sa-Su 08:00-18:00").

    Like `_split_comma_days`, a day token only starts a new rule segment if
    the text since the last split point already looks like a complete
    day+time rule -- otherwise it's just part of the day range/phrase
    currently being read (e.g. the "Friday" in "Monday - Friday").

    Args:
        text (str): The top-level segment to split.

    Returns:
        list[str]: The resulting sub-segments.
    """
    results = []
    last = 0
    for match in space_day_comp.finditer(text):
        candidate = text[last : match.start()]
        if time_start_comp.search(candidate) and _has_day_info(candidate):
            results.append(text[last : match.start()])
            last = match.end()
    results.append(text[last:])
    return [segment for segment in results if segment.strip()]


def _has_day_info(segment: str) -> bool:
    """Check whether a segment contains any recognizable day reference.

    Args:
        segment (str): The segment to check.

    Returns:
        bool: True if the segment mentions a day name or a day-related
        keyword such as "weekdays" or "daily".
    """
    return bool(
        day_present_comp.search(segment)
        or weekday_comp.search(segment)
        or weekend_comp.search(segment)
        or daily_comp.search(segment)
    )


def _merge_day_time_lines(segments: list[str]) -> list[str]:
    """Merge consecutive top-level segments where days and times are split
    across separate lines (e.g. a day/day-range on its own line, followed by
    one or more lines with only the corresponding times -- as with a
    lunch/dinner split written on separate lines).

    A day-only line starts a new group, and any number of time-only lines
    that follow are attached to it (comma-joined) until the next day-only
    line or a fully self-contained day+time line appears. Segments that
    contain neither day nor time/status information (e.g. a stray section
    header like "Kitchen Hours:") are treated as noise and dropped.

    Args:
        segments (list[str]): The top-level segments, as split on rule
            separators (";" or newlines).

    Returns:
        list[str]: The segments, with day-only/time-only line groups merged
        and irrelevant noise lines removed.
    """
    merged: list[str] = []
    current_days: str | None = None
    current_times: list[str] = []

    def flush() -> None:
        nonlocal current_days, current_times
        if current_days is not None:
            body = ",".join(current_times)
            merged.append(f"{current_days} {body}".strip() if body else current_days)
        current_days = None
        current_times = []

    for segment in segments:
        has_time = bool(time_start_comp.search(segment))
        has_day = _has_day_info(segment)
        if not has_time and not has_day:
            # noise line (no day or time info) -- drop it
            continue
        if has_day and has_time:
            # a fully self-contained day+time line
            flush()
            merged.append(segment)
        elif has_day:
            # a day (range) on its own line, awaiting time(s) below
            flush()
            current_days = segment
        elif current_days is not None:
            # a time-only line -- attach to the day currently being built
            current_times.append(segment)
        elif merged:
            # a stray time-only continuation of the last completed rule
            merged[-1] = f"{merged[-1]},{segment}"
        else:
            merged.append(segment)

    flush()
    return merged


def _split_day_time(segment: str) -> tuple[str, str]:
    """Split a rule segment into its day portion and time/status portion.

    Args:
        segment (str): A single rule segment.

    Returns:
        tuple[str, str]: The day portion and the time/status portion.
    """
    stripped = segment.strip()

    # handle the reversed "Closed Monday - Wednesday" phrasing, where the
    # status keyword precedes the days it applies to instead of following
    # them -- swap the two parts so the days are parsed as days
    closed_match = closed_comp.match(stripped)
    if closed_match:
        remainder = stripped[closed_match.end() :].strip(" ,")
        if _has_day_info(remainder):
            return remainder, stripped[: closed_match.end()]

    match = time_start_comp.search(segment)
    if not match:
        # no digits/status keywords found -- treat whole thing as days,
        # implying it's open with no specified times (unusual, but handled)
        return segment.strip(), ""

    day_match = day_comp.search(segment)
    if day_match and day_match.start() > match.start():
        # the times come first, followed by the day(s) they apply to (e.g.
        # "08:00AM-06:00PM Monday-Friday") -- pull out the day range/name
        # from wherever it appears and treat everything else as the times
        clause_match = day_range_comp.match(segment, day_match.start())
        if clause_match:
            day_part = clause_match.group()
            time_part = segment[: clause_match.start()] + segment[clause_match.end() :]
            return day_part.strip(), time_part.strip()

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


def _merge_duplicate_day_rules(rules: list[RuleSet]) -> list[RuleSet]:
    """Merge consecutive rules that apply to the exact same day(s) and are
    both timed (e.g. two separately-written windows for the same days with
    no separator between them, like "Mo-Su 09:00-13:00 Mo-Su 16:30-20:30"),
    combining their time spans instead of letting the later one silently
    override the earlier one.

    Args:
        rules (list[RuleSet]): The individually-parsed rules, in input order.

    Returns:
        list[RuleSet]: The rules, with same-day timed duplicates merged.
    """
    merged: list[RuleSet] = []
    for rule in rules:
        prev = merged[-1] if merged else None
        if (
            prev is not None
            and not rule.closed
            and not rule.is_24h
            and not prev.closed
            and not prev.is_24h
            and rule.days == prev.days
        ):
            merged[-1] = RuleSet(
                days=prev.days, times=_merge_time_spans(prev.times + rule.times)
            )
        else:
            merged.append(rule)
    return merged


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
        if day_range.start == Day.PH:
            # PH (public holiday) is never part of the weekly cycle -- it
            # always stands alone
            days.append("PH")
            continue
        start_idx = day_index[day_range.start.value]
        end_idx = day_index[day_range.end.value] if day_range.end else start_idx
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
    # PH (public holiday) is never grouped into a weekly range -- collapse
    # the real weekdays first, then always append PH last, on its own
    has_ph = "PH" in days
    ordered = [day for day in day_order if day in days]

    ranges: list[DayRange] = []
    if ordered:
        run_start = run_prev = ordered[0]
        run_prev_idx = day_index[run_prev]
        for day in ordered[1:]:
            day_idx = day_index[day]
            if day_idx == run_prev_idx + 1:
                run_prev = day
                run_prev_idx = day_idx
                continue
            ranges.append(
                DayRange(start=run_start)
                if run_start == run_prev
                else DayRange(start=run_start, end=run_prev)
            )
            run_start = run_prev = day
            run_prev_idx = day_idx
        ranges.append(
            DayRange(start=run_start)
            if run_start == run_prev
            else DayRange(start=run_start, end=run_prev)
        )

    if has_ph:
        ranges.append(DayRange(start=Day.PH))

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
    merged.sort(
        key=lambda rule: day_index.get(rule.days[0].start.value, len(day_order))
    )
    return merged


def _parse_point_segment(segment: str) -> PointRuleSet | None:
    """Parse a single point-in-time rule segment into a PointRuleSet.

    Point-in-time tags like `collection_times`/`service_times` have no
    "closed" concept of their own -- a day with no scheduled times simply
    has no entry -- so a "closed"/"off" segment (e.g. "Sunday: Closed")
    carries no meaningful point time and is dropped entirely rather than
    raising or fabricating a value.

    Args:
        segment (str): A single rule segment (days plus point time(s)).

    Returns:
        PointRuleSet | None: The parsed rule, or None if the segment is a
        "closed"/"off" status with no actual times.
    """
    day_part, time_part = _split_day_time(segment)
    if closed_comp.search(time_part):
        return None
    days = _parse_days(day_part)
    times = _parse_point_times(time_part)
    return PointRuleSet(days=days, times=times)


def _merge_duplicate_point_day_rules(rules: list[PointRuleSet]) -> list[PointRuleSet]:
    """Merge consecutive rules that apply to the exact same day(s),
    combining their point times instead of letting the later one silently
    override the earlier one.

    Args:
        rules (list[PointRuleSet]): The individually-parsed rules, in input
            order.

    Returns:
        list[PointRuleSet]: The rules, with same-day duplicates merged.
    """
    merged: list[PointRuleSet] = []
    for rule in rules:
        prev = merged[-1] if merged else None
        if prev is not None and rule.days == prev.days:
            merged[-1] = PointRuleSet(
                days=prev.days, times=sorted(set(prev.times) | set(rule.times))
            )
        else:
            merged.append(rule)
    return merged


def _coalesce_point_rules(rules: list[PointRuleSet]) -> list[PointRuleSet]:
    """Merge rules that share identical point times, and sort by week order.

    Args:
        rules (list[PointRuleSet]): The individually-parsed rules, in input
            order. Later rules win if the same day appears more than once.

    Returns:
        list[PointRuleSet]: The merged rules, sorted by first day of the week.
    """
    day_to_rule: dict[str, PointRuleSet] = {}
    for rule in rules:
        for day in _expand_days(rule.days):
            day_to_rule[day] = rule

    sig_to_days: dict[tuple, set[str]] = {}
    sig_to_rule: dict[tuple, PointRuleSet] = {}
    for day, rule in day_to_rule.items():
        sig = tuple(rule.times)
        sig_to_days.setdefault(sig, set()).add(day)
        sig_to_rule[sig] = rule

    merged = [
        PointRuleSet(days=_collapse_days_to_ranges(days), times=sig_to_rule[sig].times)
        for sig, days in sig_to_days.items()
    ]
    merged.sort(
        key=lambda rule: day_index.get(rule.days[0].start.value, len(day_order))
    )
    return merged


def _validate_opening_hours_output(output: str) -> None:
    """Validate that the output is well-formed opening_hours syntax.

    Each rule must have both days and times (or be entirely off/24h).
    A rule like "Fr off; Sa-Su" (missing times on the last rule) is invalid.

    Args:
        output (str): The formatted opening_hours string.

    Raises:
        ValueError: If the output has malformed rules.
    """
    if not output or output == "off" or output == "24/7":
        return

    # Split into individual rules
    rules = [r.strip() for r in output.split(";") if r.strip()]

    for rule in rules:
        # Each rule should have either:
        # - days + times (e.g. "Mo-Fr 08:00-12:00")
        # - days + "off" (e.g. "Sa-Su off")
        # - days + "24/7" (e.g. "We 24/7")
        # - just times (e.g. "08:00-12:00")
        # - just "off" or "24/7"
        # But NOT just days with nothing else (e.g. "Sa-Su")

        # Check if it's a rule with days
        parts = rule.split()
        if len(parts) < 1:
            raise ValueError(f"Malformed rule in output: {rule!r}")

        # If first part looks like days (contains weekday abbreviations or ranges),
        # there must be a second part with times/off/24h
        if len(parts) >= 1 and _has_day_info(parts[0]):
            if len(parts) < 2:
                raise ValueError(
                    f"Incomplete rule (days without times) in output: {rule!r}"
                )


def _validate_point_times_output(output: str) -> None:
    """Validate that the output is well-formed point-in-time syntax.

    Each rule must have both days and times.
    A rule like "Mo-Fr 15:00; Sa" (missing times on the last rule) is invalid.

    Args:
        output (str): The formatted point-in-time string.

    Raises:
        ValueError: If the output has malformed rules.
    """
    if not output:
        raise ValueError("Empty point-in-time output")

    # Split into individual rules
    rules = [r.strip() for r in output.split(";") if r.strip()]

    for rule in rules:
        parts = rule.split()
        if len(parts) < 1:
            raise ValueError(f"Malformed rule in output: {rule!r}")

        # If first part looks like days, there must be times
        if len(parts) >= 1 and _has_day_info(parts[0]):
            if len(parts) < 2:
                raise ValueError(
                    f"Incomplete rule (days without times) in output: {rule!r}"
                )


def get_times(value: str) -> str:
    """Process point-in-time strings (e.g. `collection_times`,
    `service_times`) into the OSM format.

    ```python
    >>> get_times("Mo-Fr 15:00,18:00,19:00,23:00; Sa 15:00; Su 10:30,23:00")
    "Mo-Fr 15:00,18:00,19:00,23:00; Sa 15:00; Su 10:30,23:00"
    >>> get_times("Monday to Friday 3pm and 6pm")
    "Mo-Fr 15:00,18:00"
    >>> get_times("Mo-Fr sunrise,sunset")
    "Mo-Fr sunrise,sunset"
    >>> get_times("Monday-Friday: 4:15pm Saturday: 1:00pm Sunday: Closed")
    "Mo-Fr 16:15; Sa 13:00"
    ```

    Point-in-time tags have no "closed" concept of their own -- a day with
    no scheduled times simply has no entry -- so a "closed"/"off" rule
    (e.g. `"Sunday: Closed"`) is dropped entirely rather than raising or
    fabricating a value.

    The solar keywords `dawn`, `dusk`, `sunrise`, and `sunset` are accepted
    in place of a clock time, and are rendered in lowercase exactly as OSM
    expects.

    Calendar/date-based rules -- month names or specific dates, named
    holidays, and OSM's "nth weekday of month" notation (e.g. `"Th[4]"`)
    -- aren't supported. Rather than risk silently mangling them, any input
    containing one of these raises `ValueError` instead of returning a
    partial or incorrect result.

    Args:
        value (str): The point-in-time string to process.

    Returns:
        str: The formatted point-in-time string.

    Raises:
        ValueError: If the string cannot be parsed, or if it references a
            calendar/date-based rule that isn't supported.
    """
    normalized = _normalize(value)
    if not normalized:
        raise ValueError("Empty collection/service times string.")
    _reject_unsupported_calendar_refs(normalized)

    top_segments = [s for s in rule_split_comp.split(normalized) if s.strip()]
    top_segments = _merge_day_time_lines(top_segments)
    segments = [sub for top in top_segments for sub in _split_space_days(top)]
    segments = [sub for seg in segments for sub in _split_comma_days(seg)]
    rules = [
        rule
        for rule in (_parse_point_segment(segment) for segment in segments)
        if rule is not None
    ]
    rules = _merge_duplicate_point_day_rules(rules)

    if rules and all(rule.days for rule in rules):
        rules = _coalesce_point_rules(rules)

    output = PointTimes(rules=rules).to_osm()
    _validate_point_times_output(output)
    return output


def get_hours(value: str) -> str:
    """Process opening hours strings into the OSM `opening_hours` format.

    ```python
    >>> get_hours("Mo-Fr 08:00-12:00,13:00-17:30")
    "Mo-Fr 08:00-12:00,13:00-17:30"
    >>> get_hours("Monday to Friday 9am-5pm, Saturday 9am-12pm")
    "Mo-Fr 09:00-17:00; Sa 09:00-12:00"
    >>> get_hours("Closed")
    "off"
    >>> get_hours("Mo-Fr 09:00-17:00; PH off")
    "Mo-Fr 09:00-17:00; PH off"
    >>> get_hours("Mo-Fr sunrise-sunset")
    "Mo-Fr sunrise-sunset"
    ```

    The solar keywords `dawn`, `dusk`, `sunrise`, and `sunset` are accepted
    in place of a clock time (on either or both sides of a time span), and
    are rendered in lowercase exactly as OSM expects.

    `PH` (public holiday) is supported as a special, non-weekday indicator:
    it's recognized only as the exact token `PH` (no other aliases or
    forms), can never be part of an actual day range (e.g. `PH-Mo` is
    rejected), and always sorts after every other day/rule in the output,
    regardless of where it appeared in the input.

    Calendar/date-based rules -- month names or specific dates (e.g.
    `"Jan 1"`), named holidays (e.g. `"Easter"`, `"Thanksgiving"`), and
    OSM's "nth weekday of month" notation (e.g. `"Th[4]"` for the fourth
    Thursday) -- aren't supported. Rather than risk silently mangling them,
    any input containing one of these raises `ValueError` instead of
    returning a partial or incorrect result.

    Args:
        value (str): The opening hours string to process.

    Returns:
        str: The formatted opening hours string.

    Raises:
        ValueError: If the string cannot be parsed, or if it references a
            calendar/date-based rule that isn't supported.
    """
    normalized = _normalize(value)
    if not normalized:
        raise ValueError("Empty opening hours string.")
    _reject_unsupported_calendar_refs(normalized)

    stripped = normalized.strip()
    if closed_comp.fullmatch(stripped):
        return "off"
    if day_24_comp.fullmatch(stripped):
        return "24/7"

    top_segments = [s for s in rule_split_comp.split(normalized) if s.strip()]
    top_segments = _merge_day_time_lines(top_segments)
    segments = [sub for top in top_segments for sub in _split_space_days(top)]
    segments = [sub for seg in segments for sub in _split_comma_days(seg)]
    rules = [_parse_segment(segment) for segment in segments]
    rules = _merge_duplicate_day_rules(rules)

    # only coalesce/reorder when every rule specifies explicit days -- if any
    # rule applies to the whole week (e.g. "daily"), leave the input order
    # alone since day semantics may be intentionally layered
    if rules and all(rule.days for rule in rules):
        rules = _coalesce_rules(rules)

    output = OpeningHours(rules=rules).to_osm()
    _validate_opening_hours_output(output)
    return output
