"""Test functions for opening hours parsing."""

# python3.12 -m pytest --cov=src --cov-report=html tests/*

import pytest
from pydantic import ValidationError

from src.atlus.hours import (
    _normalize,
    _parse_days,
    _parse_segment,
    _parse_single_time,
    _parse_time_span,
    _parse_times,
    _resolve_pair,
    _split_day_time,
    get_hours,
)
from src.atlus.objects import Day, DayRange, OpeningHours, RuleSet, TimeSpan

# ---------------------------------------------------------------------------
# Object model tests
# ---------------------------------------------------------------------------


def test_day_values() -> None:
    """Test Day enum values are the two-letter OSM codes."""
    assert Day.MO.value == "Mo"
    assert Day.SU.value == "Su"


def test_day_index() -> None:
    """Test Day.index returns week position."""
    assert Day.MO.index == 0
    assert Day.SU.index == 6


def test_day_range_single_day() -> None:
    """Test DayRange.to_osm with a single day."""
    assert DayRange(start=Day.MO).to_osm() == "Mo"


def test_day_range_same_start_end() -> None:
    """Test DayRange.to_osm collapses identical start/end."""
    assert DayRange(start=Day.MO, end=Day.MO).to_osm() == "Mo"


def test_day_range_full_range() -> None:
    """Test DayRange.to_osm with a day range."""
    assert DayRange(start=Day.MO, end=Day.FR).to_osm() == "Mo-Fr"


def test_time_span_to_osm() -> None:
    """Test TimeSpan.to_osm formatting."""
    assert TimeSpan(start="08:00", end="17:30").to_osm() == "08:00-17:30"


def test_time_span_invalid_format() -> None:
    """Test TimeSpan rejects malformed time strings."""
    with pytest.raises(ValidationError):
        TimeSpan(start="8:00", end="17:30")


def test_time_span_allows_overnight() -> None:
    """Test TimeSpan allows end before start (crosses midnight)."""
    assert TimeSpan(start="22:00", end="02:00").to_osm() == "22:00-02:00"


def test_rule_set_basic() -> None:
    """Test RuleSet.to_osm with days and times."""
    rule = RuleSet(
        days=[DayRange(start=Day.MO, end=Day.FR)],
        times=[TimeSpan(start="08:00", end="12:00")],
    )
    assert rule.to_osm() == "Mo-Fr 08:00-12:00"


def test_rule_set_multiple_times() -> None:
    """Test RuleSet.to_osm with multiple time spans."""
    rule = RuleSet(
        days=[DayRange(start=Day.MO, end=Day.FR)],
        times=[
            TimeSpan(start="08:00", end="12:00"),
            TimeSpan(start="13:00", end="17:30"),
        ],
    )
    assert rule.to_osm() == "Mo-Fr 08:00-12:00,13:00-17:30"


def test_rule_set_multiple_days() -> None:
    """Test RuleSet.to_osm with multiple individual days."""
    rule = RuleSet(
        days=[DayRange(start=Day.MO), DayRange(start=Day.WE)],
        times=[TimeSpan(start="08:00", end="12:00")],
    )
    assert rule.to_osm() == "Mo,We 08:00-12:00"


def test_rule_set_closed() -> None:
    """Test RuleSet.to_osm for a closed rule."""
    rule = RuleSet(days=[DayRange(start=Day.SU)], closed=True)
    assert rule.to_osm() == "Su off"


def test_rule_set_24h() -> None:
    """Test RuleSet.to_osm for a 24-hour rule."""
    rule = RuleSet(days=[DayRange(start=Day.MO, end=Day.SU)], is_24h=True)
    assert rule.to_osm() == "Mo-Su 24/7"


def test_rule_set_no_days_means_every_day() -> None:
    """Test RuleSet.to_osm omits day prefix when days is empty."""
    rule = RuleSet(times=[TimeSpan(start="09:00", end="17:00")])
    assert rule.to_osm() == "09:00-17:00"


def test_rule_set_rejects_multiple_modes() -> None:
    """Test RuleSet rejects being both closed and having times."""
    with pytest.raises(ValidationError):
        RuleSet(
            days=[DayRange(start=Day.MO)],
            times=[TimeSpan(start="08:00", end="12:00")],
            closed=True,
        )


def test_opening_hours_single_rule() -> None:
    """Test OpeningHours.to_osm with a single rule."""
    oh = OpeningHours(
        rules=[
            RuleSet(
                days=[DayRange(start=Day.MO, end=Day.FR)],
                times=[TimeSpan(start="08:00", end="17:30")],
            )
        ]
    )
    assert oh.to_osm() == "Mo-Fr 08:00-17:30"


def test_opening_hours_multiple_rules() -> None:
    """Test OpeningHours.to_osm joins rules with semicolons."""
    oh = OpeningHours(
        rules=[
            RuleSet(
                days=[DayRange(start=Day.MO, end=Day.FR)],
                times=[
                    TimeSpan(start="08:00", end="12:00"),
                    TimeSpan(start="13:00", end="17:30"),
                ],
            ),
            RuleSet(
                days=[DayRange(start=Day.SA)],
                times=[TimeSpan(start="08:00", end="12:00")],
            ),
        ]
    )
    assert oh.to_osm() == "Mo-Fr 08:00-12:00,13:00-17:30; Sa 08:00-12:00"


def test_opening_hours_rejects_empty() -> None:
    """Test OpeningHours rejects an empty rule list."""
    with pytest.raises(ValidationError):
        OpeningHours(rules=[])


# ---------------------------------------------------------------------------
# Internal parsing helper tests
# ---------------------------------------------------------------------------


def test_normalize_collapses_whitespace() -> None:
    """Test _normalize collapses repeated whitespace."""
    assert _normalize("Mo-Fr   08:00-12:00") == "Mo-Fr 08:00-12:00"


def test_normalize_strips_trailing_punctuation() -> None:
    """Test _normalize strips trailing punctuation."""
    assert _normalize(" Mo-Fr 08:00-12:00. ") == "Mo-Fr 08:00-12:00"


def test_split_day_time_basic() -> None:
    """Test _split_day_time separates day text from time text."""
    day_part, time_part = _split_day_time("Mo-Fr 08:00-12:00")
    assert day_part == "Mo-Fr"
    assert time_part == "08:00-12:00"


def test_split_day_time_closed() -> None:
    """Test _split_day_time recognizes 'closed' as the time portion."""
    day_part, time_part = _split_day_time("Sunday closed")
    assert day_part == "Sunday"
    assert time_part == "closed"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Mo", [DayRange(start=Day.MO)]),
        ("Mo-Fr", [DayRange(start=Day.MO, end=Day.FR)]),
        ("Mo,We", [DayRange(start=Day.MO), DayRange(start=Day.WE)]),
        ("Monday", [DayRange(start=Day.MO)]),
        ("Monday-Friday", [DayRange(start=Day.MO, end=Day.FR)]),
        ("Mon to Fri", [DayRange(start=Day.MO, end=Day.FR)]),
        ("weekdays", [DayRange(start=Day.MO, end=Day.FR)]),
        ("weekends", [DayRange(start=Day.SA, end=Day.SU)]),
        ("daily", []),
        ("every day", []),
        ("", []),
    ],
)
def test_parse_days(text: str, expected: list[DayRange]) -> None:
    """Test _parse_days handles common day expressions."""
    assert _parse_days(text) == expected


def test_parse_days_invalid() -> None:
    """Test _parse_days raises on unrecognized day text."""
    with pytest.raises(ValueError, match="Unrecognized day"):
        _parse_days("Blursday")


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("8am", (8, 0, True)),
        ("8pm", (20, 0, True)),
        ("12am", (0, 0, True)),
        ("12pm", (12, 0, True)),
        ("8:00am", (8, 0, True)),
        ("8:30pm", (20, 30, True)),
        ("08:00", (8, 0, True)),
        ("17:30", (17, 30, True)),
        ("noon", (12, 0, True)),
        ("midnight", (24, 0, True)),
        ("9", (9, 0, False)),
        ("5", (5, 0, False)),
    ],
)
def test_parse_single_time(token: str, expected: tuple[int, int, bool]) -> None:
    """Test _parse_single_time resolves a variety of time formats."""
    assert _parse_single_time(token) == expected


def test_parse_single_time_invalid() -> None:
    """Test _parse_single_time raises on unparsable input."""
    with pytest.raises(ValueError, match="Unrecognized time"):
        _parse_single_time("banana")


def test_resolve_pair_both_ambiguous() -> None:
    """Test _resolve_pair assumes AM-PM business hours when unresolved."""
    assert _resolve_pair((9, 0, False), (5, 0, False)) == ("09:00", "17:00")


def test_resolve_pair_both_resolved() -> None:
    """Test _resolve_pair passes through already-resolved times."""
    assert _resolve_pair((8, 0, True), (17, 30, True)) == ("08:00", "17:30")


def test_resolve_pair_start_resolved_end_ambiguous() -> None:
    """Test _resolve_pair infers PM end time from an AM start."""
    assert _resolve_pair((8, 0, True), (5, 0, False)) == ("08:00", "17:00")


def test_resolve_pair_end_resolved_start_ambiguous() -> None:
    """Test _resolve_pair infers AM start time from a PM end."""
    assert _resolve_pair((9, 0, False), (17, 0, True)) == ("09:00", "17:00")


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("08:00-12:00", TimeSpan(start="08:00", end="12:00")),
        ("8am-5pm", TimeSpan(start="08:00", end="17:00")),
        ("9-5", TimeSpan(start="09:00", end="17:00")),
        ("9:30am to 5:30pm", TimeSpan(start="09:30", end="17:30")),
        ("22:00-02:00", TimeSpan(start="22:00", end="02:00")),
    ],
)
def test_parse_time_span(token: str, expected: TimeSpan) -> None:
    """Test _parse_time_span across common formats."""
    assert _parse_time_span(token) == expected


def test_parse_times_multiple() -> None:
    """Test _parse_times splits multiple comma-separated spans."""
    result = _parse_times("08:00-12:00,13:00-17:30")
    assert result == [
        TimeSpan(start="08:00", end="12:00"),
        TimeSpan(start="13:00", end="17:30"),
    ]


def test_parse_segment_basic() -> None:
    """Test _parse_segment builds a full RuleSet from a segment."""
    rule = _parse_segment("Mo-Fr 08:00-12:00,13:00-17:30")
    assert rule.to_osm() == "Mo-Fr 08:00-12:00,13:00-17:30"


def test_parse_segment_closed() -> None:
    """Test _parse_segment handles a closed day."""
    rule = _parse_segment("Sunday closed")
    assert rule.to_osm() == "Su off"


def test_parse_segment_24h() -> None:
    """Test _parse_segment handles a 24-hour day."""
    rule = _parse_segment("Mo-Su 24 hours")
    assert rule.to_osm() == "Mo-Su 24/7"


# ---------------------------------------------------------------------------
# get_hours() end-to-end tests
# ---------------------------------------------------------------------------


def test_get_hours_doc_example_single_interval() -> None:
    """Test the basic Mo-Fr example from the OSM docs."""
    assert get_hours("Mo-Fr 08:00-12:00,13:00-17:30") == (
        "Mo-Fr 08:00-12:00,13:00-17:30"
    )


def test_get_hours_doc_example_multiple_days() -> None:
    """Test the Mo,We example from the OSM docs."""
    assert get_hours("Mo,We 08:00-12:00") == "Mo,We 08:00-12:00"


def test_get_hours_doc_example_multiple_rules() -> None:
    """Test the multi-rule Mo-Fr/Sa example from the OSM docs."""
    assert get_hours("Mo-Fr 08:00-12:00,13:00-17:30; Sa 08:00-12:00") == (
        "Mo-Fr 08:00-12:00,13:00-17:30; Sa 08:00-12:00"
    )


def test_get_hours_full_day_names() -> None:
    """Test full day names and 'to' as a range separator."""
    assert get_hours("Monday to Friday 08:00-17:00") == "Mo-Fr 08:00-17:00"


def test_get_hours_am_pm() -> None:
    """Test 12-hour am/pm times."""
    assert get_hours("Mon-Fri 8am-5pm") == "Mo-Fr 08:00-17:00"


def test_get_hours_bare_hours() -> None:
    """Test bare digit hours with no am/pm are treated as business hours."""
    assert get_hours("Mon-Fri 9-5") == "Mo-Fr 09:00-17:00"


def test_get_hours_multiple_semicolon_rules() -> None:
    """Test semicolon-separated rules with different day groups."""
    result = get_hours("Mon-Fri 9am-5pm; Sat 9am-12pm; Sun closed")
    assert result == "Mo-Fr 09:00-17:00; Sa 09:00-12:00; Su off"


def test_get_hours_comma_separated_day_groups() -> None:
    """Test comma-separated day groups (not just time spans) split correctly.

    Mon and Tue share identical hours, so they're coalesced into "Mo-Tu".
    """
    result = get_hours("Mon 9am-5pm, Tue 9am-5pm, Wed closed")
    assert result == "Mo-Tu 09:00-17:00; We off"


def test_get_hours_weekdays_keyword() -> None:
    """Test the 'weekdays' keyword expands to Mo-Fr."""
    assert get_hours("Weekdays 9am-5pm") == "Mo-Fr 09:00-17:00"


def test_get_hours_weekends_keyword() -> None:
    """Test the 'weekends' keyword expands to Sa-Su."""
    assert get_hours("Weekends 10am-4pm") == "Sa-Su 10:00-16:00"


def test_get_hours_daily_keyword_omits_days() -> None:
    """Test 'daily' produces a rule with no day prefix."""
    assert get_hours("Daily 9am-9pm") == "09:00-21:00"
    assert get_hours("9 am-9 pm") == "09:00-21:00"
    assert get_hours("Open daily 9am-9pm") == "09:00-21:00"
    assert get_hours("Open daily 9-9") == "09:00-21:00"
    assert get_hours("9 am to 9 pm") == "09:00-21:00"


def test_get_hours_every_day_keyword() -> None:
    """Test 'every day' behaves the same as 'daily'."""
    assert get_hours("Open every day 9am-9pm") == "09:00-21:00"


def test_get_hours_closed_only() -> None:
    """Test a bare 'Closed' string."""
    assert get_hours("Closed") == "off"


def test_get_hours_24_hours_only() -> None:
    """Test a bare '24 hours' string."""
    assert get_hours("Open 24 hours") == "24/7"
    assert get_hours("24/7") == "24/7"


def test_get_hours_noon_and_midnight() -> None:
    """Test 'noon' and 'midnight' are recognized as times."""
    assert get_hours("Mon-Fri noon-midnight") == "Mo-Fr 12:00-24:00"


def test_get_hours_lunch_break() -> None:
    """Test a schedule with a midday break, matching the OSM doc example."""
    result = get_hours("Mon-Fri 8am-noon, 1pm-5:30pm")
    assert result == "Mo-Fr 08:00-12:00,13:00-17:30"


def test_get_hours_overnight_span() -> None:
    """Test a time span that crosses midnight."""
    assert get_hours("Fri-Sat 22:00-02:00") == "Fr-Sa 22:00-02:00"


def test_get_hours_empty_string_raises() -> None:
    """Test that an empty string raises ValueError."""
    with pytest.raises(ValueError, match="Empty opening hours"):
        get_hours("")


def test_get_hours_invalid_day_raises() -> None:
    """Test that an unrecognized day raises ValueError."""
    with pytest.raises(ValueError, match="Unrecognized day"):
        get_hours("Blursday 9am-5pm")


def test_get_hours_single_day_abbreviation() -> None:
    """Test single two-letter day abbreviations pass through unchanged."""
    assert get_hours("Su 10:00-16:00") == "Su 10:00-16:00"


def test_get_hours_mixed_case_input() -> None:
    """Test that mixed-case day/time text is handled."""
    assert get_hours("mON-fRI 8AM-5PM") == "Mo-Fr 08:00-17:00"


def test_get_hours_mixed_days() -> None:
    """Test that separate day specifications are combined correctly."""
    assert (
        get_hours("M-Thur 9am-5pm; Friday 9am-6pm; Sat closed")
        == "Mo-Th 09:00-17:00; Fr 09:00-18:00; Sa off"
    )


def test_get_hours_exception_days() -> None:
    """Test that explicitly excepted day specifications are combined correctly."""
    assert (
        get_hours("M-Thur 9am-5pm; Wed 9am-6pm; Sat closed")
        == "Mo-Tu,Th 09:00-17:00; We 09:00-18:00; Sa off"
    )


def test_get_hours_real_world() -> None:
    """Test handling of real world raw strings."""
    assert (
        get_hours("""Thursday	5–9:30 PM
    Friday	5–10 PM
    Saturday	11:30 AM–10 PM
    Sunday	11:30 AM–9:30 PM
    Monday	5–9:30 PM
    Tuesday	5–9:30 PM
    Wednesday	5–9:30 PM""")
        == "Mo-Th 17:00-21:30; Fr 17:00-22:00; Sa 11:30-22:00; Su 11:30-21:30"
    )
    assert (
        get_hours("""Thursday10:00 AM - 12:00 AM
    Friday10:00 AM - 1:00 AM
    Saturday10:00 AM - 1:00 AM
    Sunday10:00 AM - 12:00 AM
    Monday10:00 AM - 12:00 AM
    Tuesday10:00 AM - 12:00 AM
    Wednesday10:00 AM - 12:00 AM""")
        == "Mo-Th,Su 10:00-00:00; Fr-Sa 10:00-01:00"
    )
    assert (
        get_hours("""Mon 10am - 2pm
    Tue 10am - 2pm
    Wed 10am - 2pm""")
        == "Mo-We 10:00-14:00"
    )
    assert (
        get_hours("Mon 10am - 2pm, Tue 10am - 2pm, Wed 10am - 2pm")
        == "Mo-We 10:00-14:00"
    )
    assert (
        get_hours("""M-F 11am-10pm
        Saturday 10am-10pm
        Sunday 10am-9pm""")
        == "Mo-Fr 11:00-22:00; Sa 10:00-22:00; Su 10:00-21:00"
    )
    assert (
        get_hours("""
            Tuesday - Saturday
            04:00 PM - 10:00 PM
            Sunday
            04:00 PM - 09:00 PM
""")
        == "Tu-Sa 16:00-22:00; Su 16:00-21:00"
    )
    assert (
        get_hours("""Wed. - Fri.
        11:00 am - 7:45 pm
        Tues., Sat. and Sun.
        11:00 am - 5:45 pm""")
        == "Tu,Sa-Su 11:00-17:45; We-Fr 11:00-19:45"
    )
    assert (
        get_hours(
            "Mon 10am - 2pm, Tue 10am - 2pm, Wed 10am - 2pm, Thu 10am - 2pm, Fri 10am - 2pm, Sat and Sun closed"
        )
        == "Mo-Fr 10:00-14:00; Sa-Su off"
    )
    assert (
        get_hours("""Mon-Tue closed

        Kitchen Hours:
        W-Thur: 4:30–8:30p
        Fri-Sat: 4:30-9:15p
        Sun: 4:30-8:30p""")
        == "Mo-Tu off; We-Th,Su 16:30-20:30; Fr-Sa 16:30-21:15"
    )
    assert (
        get_hours("""Mon-Tue closed
        W-Thur: 4:30–8:30p
        Fri-Sat: 4:30-9:15p
        Sunday: 4:30-8:30p""")
        == "Mo-Tu off; We-Th,Su 16:30-20:30; Fr-Sa 16:30-21:15"
    )
    assert (
        get_hours("""Mon, Wed, Thu: 	 11:00 AM - 09:00 PM
        Fri, Sat: 	 11:00 AM - 09:00 PM
        Sun:
	 11:00 AM - 08:00 PM
        Tue: 	   Closed""")
        == "Mo,We-Sa 11:00-21:00; Tu off; Su 11:00-20:00"
    )
