"""Test functions for opening hours parsing."""

# python3.12 -m pytest --cov=src --cov-report=html tests/*

import pytest
from pydantic import ValidationError

from src.atlus.hours import (
    _normalize,
    _parse_days,
    _parse_point_segment,
    _parse_point_time,
    _parse_point_times,
    _parse_segment,
    _parse_single_time,
    _parse_time_span,
    _parse_times,
    _resolve_pair,
    _split_day_time,
    get_hours,
    get_times,
)
from src.atlus.objects import (
    Day,
    DayRange,
    OpeningHours,
    PointRuleSet,
    PointTimes,
    RuleSet,
    TimeSpan,
)

# ---------------------------------------------------------------------------
# Object model tests
# ---------------------------------------------------------------------------


def test_day_values() -> None:
    """Test Day enum values are the two-letter OSM codes."""
    assert Day.MO.value == "Mo"
    assert Day.SU.value == "Su"


def test_day_index() -> None:
    """Test Day.weekday_index returns week position."""
    assert Day.MO.weekday_index == 0
    assert Day.SU.weekday_index == 6


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
        ("22:00-2:00", TimeSpan(start="22:00", end="02:00")),
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


# ---------------------------------------------------------------------------
# Solar time keyword tests (dawn/dusk/sunrise/sunset)
# ---------------------------------------------------------------------------


def test_time_span_solar_keywords() -> None:
    """Test TimeSpan accepts solar keywords in place of clock times."""
    span = TimeSpan(start="sunrise", end="sunset")
    assert span.to_osm() == "sunrise-sunset"


def test_get_hours_sunrise_sunset() -> None:
    """Test a day range with a sunrise-sunset span."""
    assert get_hours("Mo-Fr sunrise-sunset") == "Mo-Fr sunrise-sunset"


def test_get_hours_dawn_dusk() -> None:
    """Test dawn/dusk as an alternate pair of solar keywords."""
    assert get_hours("Mo-Fr dawn-dusk") == "Mo-Fr dawn-dusk"


def test_get_hours_solar_no_days() -> None:
    """Test a bare solar time span with no day prefix."""
    assert get_hours("sunrise-sunset") == "sunrise-sunset"


def test_get_hours_solar_mixed_with_clock_time() -> None:
    """Test a solar keyword paired with an explicit clock time."""
    assert get_hours("Mo-Fr sunrise-17:00") == "Mo-Fr sunrise-17:00"
    assert get_hours("Mo-Fr 08:00-sunset") == "Mo-Fr 08:00-sunset"


def test_get_hours_solar_case_insensitive() -> None:
    """Test that solar keywords are normalized to lowercase."""
    assert get_hours("Mo-Fr Sunrise-Sunset") == "Mo-Fr sunrise-sunset"


def test_get_times_solar_keywords() -> None:
    """Test that get_times also accepts solar keywords as point times."""
    assert get_times("Mo-Fr sunrise,sunset") == "Mo-Fr sunrise,sunset"


def test_point_rule_set_solar_keyword() -> None:
    """Test PointRuleSet accepts a solar keyword as a point time."""
    assert PointRuleSet(times=["sunrise"]).to_osm() == "sunrise"


def test_get_hours_empty_string_raises() -> None:
    """Test that an empty string raises ValueError."""
    with pytest.raises(ValueError, match="Empty opening hours"):
        get_hours("")


# ---------------------------------------------------------------------------
# Unsupported calendar/date-based rule rejection tests
# ---------------------------------------------------------------------------


def test_get_hours_month_name_raises() -> None:
    """Test that a month name/specific date raises ValueError."""
    with pytest.raises(ValueError, match="Calendar/date-based rules"):
        get_hours("Mo-Su 10:00-17:00; Jan 1 off; Dec 25 off; Thanksgiving off")


def test_get_hours_nth_weekday_notation_raises() -> None:
    """Test that OSM's 'nth weekday of month' notation raises ValueError."""
    with pytest.raises(ValueError, match="Calendar/date-based rules"):
        get_hours(
            "We-Su 11:00-17:00; Jan 01 off, easter, Jul 04, "
            "Nov Th[4]-Fr[4], Dec 24-25 off"
        )


def test_get_hours_holiday_name_raises() -> None:
    """Test that a bare named holiday raises ValueError."""
    with pytest.raises(ValueError, match="Calendar/date-based rules"):
        get_hours("Mo-Fr 09:00-17:00; Easter off")


def test_get_times_month_name_raises() -> None:
    """Test that get_times also rejects calendar/date-based references."""
    with pytest.raises(ValueError, match="Calendar/date-based rules"):
        get_times("Dec 25 15:00")


def test_get_hours_invalid_day_raises() -> None:
    """Test that an unrecognized day raises ValueError."""
    with pytest.raises(ValueError, match="Unrecognized day"):
        get_hours("Blursday 9am-5pm")


def test_get_hours_single_day_abbreviation() -> None:
    """Test single two-letter day abbreviations pass through unchanged."""
    assert get_hours("Su 10:00-16:00") == "Su 10:00-16:00"


# ---------------------------------------------------------------------------
# PH (public holiday) tests
# ---------------------------------------------------------------------------


def test_day_range_ph_standalone() -> None:
    """Test DayRange.to_osm renders a standalone PH day."""
    assert DayRange(start=Day.PH).to_osm() == "PH"


def test_day_range_ph_in_range_raises() -> None:
    """Test that PH can never be part of an actual day range."""
    with pytest.raises(ValidationError):
        DayRange(start=Day.PH, end=Day.MO)
    with pytest.raises(ValidationError):
        DayRange(start=Day.MO, end=Day.PH)


def test_get_hours_ph_off() -> None:
    """Test a trailing PH clause with a closed status."""
    assert get_hours("Mo-Fr 09:00-17:00; PH off") == "Mo-Fr 09:00-17:00; PH off"


def test_get_hours_ph_with_times() -> None:
    """Test a trailing PH clause with its own timed rule."""
    result = get_hours("Mo-Fr 09:00-17:00; PH 10:00-14:00")
    assert result == "Mo-Fr 09:00-17:00; PH 10:00-14:00"


def test_get_hours_ph_sorts_last_regardless_of_input_order() -> None:
    """Test that PH always sorts after every other day, even if it's
    written first in the input.
    """
    assert get_hours("PH off; Mo-Fr 09:00-17:00") == "Mo-Fr 09:00-17:00; PH off"


def test_get_hours_ph_in_day_range_raises() -> None:
    """Test that using PH as part of a day range raises an error."""
    with pytest.raises(ValidationError):
        get_hours("PH-Mo 09:00-17:00")


# ---------------------------------------------------------------------------
# Point-in-time (collection_times/service_times) object model tests
# ---------------------------------------------------------------------------


def test_point_rule_set_to_osm() -> None:
    """Test PointRuleSet.to_osm formatting."""
    rule = PointRuleSet(
        days=[DayRange(start=Day.MO, end=Day.FR)], times=["15:00", "18:00"]
    )
    assert rule.to_osm() == "Mo-Fr 15:00,18:00"


def test_point_rule_set_no_days() -> None:
    """Test PointRuleSet.to_osm with no days specified."""
    assert PointRuleSet(times=["15:00"]).to_osm() == "15:00"


def test_point_rule_set_invalid_time_raises() -> None:
    """Test PointRuleSet rejects malformed time strings."""
    with pytest.raises(ValidationError):
        PointRuleSet(times=["3:00 pm"])


def test_point_times_to_osm() -> None:
    """Test PointTimes.to_osm joins multiple rules with '; '."""
    result = PointTimes(
        rules=[
            PointRuleSet(
                days=[DayRange(start=Day.MO, end=Day.FR)], times=["15:00", "18:00"]
            ),
            PointRuleSet(days=[DayRange(start=Day.SA)], times=["15:00"]),
        ]
    ).to_osm()
    assert result == "Mo-Fr 15:00,18:00; Sa 15:00"


def test_point_times_empty_rules_raises() -> None:
    """Test PointTimes rejects an empty rule list."""
    with pytest.raises(ValidationError):
        PointTimes(rules=[])


# ---------------------------------------------------------------------------
# Point-in-time parsing tests
# ---------------------------------------------------------------------------


def test_parse_point_time_24h() -> None:
    """Test parsing an already-24-hour point time."""
    assert _parse_point_time("15:00") == "15:00"


def test_parse_point_time_am_pm() -> None:
    """Test parsing 12-hour am/pm point times."""
    assert _parse_point_time("3pm") == "15:00"
    assert _parse_point_time("10:30am") == "10:30"


def test_parse_point_time_bare_digit() -> None:
    """Test a bare digit with no colon/meridiem is taken at face value."""
    assert _parse_point_time("15") == "15:00"


def test_parse_point_times_sorted_and_deduped() -> None:
    """Test that point times are sorted and de-duplicated."""
    assert _parse_point_times("18:00, 15:00, 15:00") == ["15:00", "18:00"]


def test_parse_point_segment() -> None:
    """Test parsing a full day+time point segment."""
    rule = _parse_point_segment("Mo-Fr 15:00,18:00")
    assert rule.days == [DayRange(start=Day.MO, end=Day.FR)]
    assert rule.times == ["15:00", "18:00"]


# ---------------------------------------------------------------------------
# get_times tests
# ---------------------------------------------------------------------------


def test_get_times_doc_example() -> None:
    """Test the collection_times-style example with multiple rules."""
    result = get_times("Mo-Fr 15:00,18:00,19:00,23:00; Sa 15:00; Su 10:30,23:00")
    assert result == "Mo-Fr 15:00,18:00,19:00,23:00; Sa 15:00; Su 10:30,23:00"


def test_get_times_am_pm() -> None:
    """Test 12-hour am/pm point times are converted to 24-hour."""
    assert get_times("Monday to Friday 3pm and 6pm") == "Mo-Fr 15:00,18:00"


def test_get_times_no_days() -> None:
    """Test a bare list of times with no day prefix."""
    assert get_times("15:00,18:00") == "15:00,18:00"


def test_get_times_coalesces_identical_days() -> None:
    """Test that identical per-day rules coalesce into a day range."""
    assert get_times("Mo-Su 15:00") == "Mo-Su 15:00"


def test_get_times_empty_string_raises() -> None:
    """Test that an empty string raises ValueError."""
    with pytest.raises(ValueError, match="Empty collection/service times"):
        get_times("")


def test_get_times_ignores_closed_day() -> None:
    """Test that a 'closed' rule is dropped rather than erroring."""
    result = get_times("Monday-Friday: 4:15pm Saturday: 1:00pm Sunday: Closed")
    assert result == "Mo-Fr 16:15; Sa 13:00"


def test_get_times_ignores_leading_closed_day() -> None:
    """Test that a 'closed' rule is dropped regardless of its position."""
    assert get_times("Su closed; Mo-Fr 15:00") == "Mo-Fr 15:00"


def test_get_times_all_closed_raises() -> None:
    """Test that a string with no actual times left raises ValueError."""
    with pytest.raises(ValueError):
        get_times("Mo-Su closed")


def test_get_times_backwards_window() -> None:
    """Test that backward time windows raise ValueError."""
    with pytest.raises(ValueError, match="isn't a plausible overnight closing"):
        get_hours("Su 16:00-14:00")


def test_get_times_backwards_window_late_night() -> None:
    """Test that late-night backward windows does not raise ValueError."""
    assert get_hours("Monday thru Friday 6pm-2am") == "Mo-Fr 18:00-02:00"


def test_get_hours_mixed_case_input() -> None:
    """Test that mixed-case day/time text is handled."""
    assert get_hours("mON-fRI 8AM-5PM") == "Mo-Fr 08:00-17:00"


def test_get_hours_fi() -> None:
    """Test that Fi is handled like Fr."""
    assert get_hours("Mo-Fi 8AM-5PM") == get_hours("Mo-Fr 8AM-5PM")


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


REAL_WORLD_HOURS_CASES = [
    pytest.param(
        """Thursday	5–9:30 PM
    Friday	5–10 PM
    Saturday	11:30 AM–10 PM
    Sunday	11:30 AM–9:30 PM
    Monday	5–9:30 PM
    Tuesday	5–9:30 PM
    Wednesday	5–9:30 PM""",
        "Mo-Th 17:00-21:30; Fr 17:00-22:00; Sa 11:30-22:00; Su 11:30-21:30",
        id="tab_separated_days",
    ),
    pytest.param(
        """Thursday10:00 AM - 12:00 AM
    Friday10:00 AM - 1:00 AM
    Saturday10:00 AM - 1:00 AM
    Sunday10:00 AM - 12:00 AM
    Monday10:00 AM - 12:00 AM
    Tuesday10:00 AM - 12:00 AM
    Wednesday10:00 AM - 12:00 AM""",
        "Mo-Th,Su 10:00-00:00; Fr-Sa 10:00-01:00",
        id="no_separator_between_day_and_time",
    ),
    pytest.param(
        """Mon 10am - 2pm
    Tue 10am - 2pm
    Wed 10am - 2pm""",
        "Mo-We 10:00-14:00",
        id="newline_separated_days",
    ),
    pytest.param(
        "Mon 10am - 2pm, Tue 10am - 2pm, Wed 10am - 2pm",
        "Mo-We 10:00-14:00",
        id="comma_separated_days",
    ),
    pytest.param(
        """M-F 11am-10pm
        Saturday 10am-10pm
        Sunday 10am-9pm""",
        "Mo-Fr 11:00-22:00; Sa 10:00-22:00; Su 10:00-21:00",
        id="mixed_day_abbreviations",
    ),
    pytest.param(
        """
            Tuesday - Saturday
            04:00 PM - 10:00 PM
            Sunday
            04:00 PM - 09:00 PM
""",
        "Tu-Sa 16:00-22:00; Su 16:00-21:00",
        id="days_and_times_on_separate_lines",
    ),
    pytest.param(
        """Wed. - Fri.
        11:00 am - 7:45 pm
        Tues., Sat. and Sun.
        11:00 am - 5:45 pm""",
        "Tu,Sa-Su 11:00-17:45; We-Fr 11:00-19:45",
        id="days_and_times_on_separate_lines_with_and",
    ),
    pytest.param(
        "Mon 10am - 2pm, Tue 10am - 2pm, Wed 10am - 2pm, Thu 10am - 2pm, Fri 10am - 2pm, Sat and Sun closed",
        "Mo-Fr 10:00-14:00; Sa-Su off",
        id="comma_separated_days_with_closed_tail",
    ),
    pytest.param(
        """Mon-Tue closed

        Kitchen Hours:
        W-Thur: 4:30–8:30p
        Fri-Sat: 4:30-9:15p
        Sun: 4:30-8:30p""",
        "Mo-Tu off; We-Th,Su 16:30-20:30; Fr-Sa 16:30-21:15",
        id="header_line_and_shared_meridiem",
    ),
    pytest.param(
        """Mon-Tue closed
        W-Thur: 4:30–8:30p
        Fri-Sat: 4:30-9:15p
        Sunday: 4:30-8:30p""",
        "Mo-Tu off; We-Th,Su 16:30-20:30; Fr-Sa 16:30-21:15",
        id="colon_separated_days_and_shared_meridiem",
    ),
    pytest.param(
        """Mon, Wed, Thu: 	 11:00 AM - 09:00 PM
        Fri, Sat: 	 11:00 AM - 09:00 PM
        Sun:
	 11:00 AM - 08:00 PM
        Tue: 	   Closed""",
        "Mo,We-Sa 11:00-21:00; Tu off; Su 11:00-20:00",
        id="comma_separated_days_with_colon_and_out_of_order_closed",
    ),
    pytest.param(
        """Monday

            11 AM–2:30 PM
            5–10 PM

        Tuesday

            11 AM–2:30 PM
            5–10 PM

        Wednesday

            11 AM–2:30 PM
            5–10 PM

        Thursday

            11 AM–2:30 PM
            5–10 PM

        Friday

            11 AM–2:30 PM
            5–10 PM

        Saturday

            10 AM–2:30 PM
            5–10 PM

        Sunday

            10 AM–2:30 PM
            5–10 PM""",
        "Mo-Fr 11:00-14:30,17:00-22:00; Sa-Su 10:00-14:30,17:00-22:00",
        id="day_then_multiple_time_spans_on_following_lines",
    ),
    pytest.param(
        """Mon–Thu 5:30 PM–9:30 PM · Fri 5 PM–10 PM · Sat 11 AM–2:30 PM, 5 PM–10 PM · Sun 11 AM–2:30 PM, 5 PM–9 PM""",
        "Mo-Th 17:30-21:30; Fr 17:00-22:00; Sa 11:00-14:30,17:00-22:00; Su 11:00-14:30,17:00-21:00",
        id="middle_dot_separated_rules",
    ),
    pytest.param(
        """Mon–Thu 5:30 PM–9:30 PM • Fri 5 PM–10 PM • Sat 11 AM–2:30 PM, 5 PM–10 PM • Sun 11 AM–2:30 PM, 5 PM–9 PM""",
        "Mo-Th 17:30-21:30; Fr 17:00-22:00; Sa 11:00-14:30,17:00-22:00; Su 11:00-14:30,17:00-21:00",
        id="bullet_separated_rules",
    ),
    pytest.param(
        """Thursday: 5:00pm – 12:00am
        Friday: 5:00pm – 3:00am
        Saturday: 11:00am – 3:00am
        Sunday: 11:00am – 12:00am
        Closed Monday – Wednesday """,
        "Mo-We off; Th 17:00-00:00; Fr 17:00-03:00; Sa 11:00-03:00; Su 11:00-00:00",
        id="closed_day_range_stated_after_open_days",
    ),
    pytest.param(
        """Monday - Friday
       11 am - 2.30 pm
       5 pm - 10 pm

       Saturday and Sunday
       11 am - 10 pm """,
        "Mo-Fr 11:00-14:30,17:00-22:00; Sa-Su 11:00-22:00",
        id="period_as_minute_separator",
    ),
    pytest.param(
        """Monday - Friday
       11 am - 2h30 pm
       5 pm - 10 pm

       Saturday and Sunday
       11 am - 10 pm """,
        "Mo-Fr 11:00-14:30,17:00-22:00; Sa-Su 11:00-22:00",
        id="h_as_minute_separator",
    ),
    pytest.param(
        """Monday - Friday
       1100 - 1430
       1700 - 2200

       Saturday and Sunday
       1100 - 2200 """,
        "Mo-Fr 11:00-14:30,17:00-22:00; Sa-Su 11:00-22:00",
        id="no_minute_separator",
    ),
    pytest.param(
        """
            Tuesday - Thursday
            11:00 AM - 03:00 PM
            05:00 PM - 09:00 PM
            Friday
            12:00 PM - 10:00 PM
            Saturday - Sunday
            12:00 PM - 09:00 PM
""",
        "Tu-Th 11:00-15:00,17:00-21:00; Fr 12:00-22:00; Sa-Su 12:00-21:00",
        id="day_range_then_multiple_time_spans_then_more_day_ranges",
    ),
    pytest.param(
        "Mo-Th 1030-0100, Fr-Sa 1030-0200",
        "Mo-Th 10:30-01:00; Fr-Sa 10:30-02:00",
        id="military_time",
    ),
    pytest.param(
        "Mo-Fr 08:00-21:00 Sa-Su 08:00-18:00",
        "Mo-Fr 08:00-21:00; Sa-Su 08:00-18:00",
        id="no_separator",
    ),
    pytest.param(
        "08:00AM-06:00PM Monday-Friday; 08:00AM-01:00PM Saturday",
        "Mo-Fr 08:00-18:00; Sa 08:00-13:00",
        id="times_first",
    ),
    pytest.param(
        "Fri - Sat 5:00pm - 10:00pm Last Seating / Sun - Thurs 5:00pm - 9:00pm Last Seating",
        "Mo-Th,Su 17:00-21:00; Fr-Sa 17:00-22:00",
        id="last_seating",
    ),
    pytest.param(
        """Monday Through Thursday
        5pm–9pm

        Friday & Saturday
        5pm–9:30pm""",
        "Mo-Th 17:00-21:00; Fr-Sa 17:00-21:30",
        id="through",
    ),
    pytest.param(
        """Monday-Thursday
        11:30am-3pm, 3pm-5pm, 5pm-9:30pm""",
        "Mo-Th 11:30-21:30",
        id="merge_windows",
    ),
    pytest.param(
        "Mon - Fri: 8:00am - 5:00pm Sat & Sun: Closed",
        "Mo-Fr 08:00-17:00; Sa-Su off",
        id="no_separator",
    ),
    pytest.param(
        "Mon - Thur 12pm-9pm Fri & Sat 12pm-10pm Sun CLOSED",
        "Mo-Th 12:00-21:00; Fr-Sa 12:00-22:00; Su off",
        id="no_separator_2",
    ),
    pytest.param(
        "Mon - Thur 12pm-9pm | Fri & Sat 12pm-10pm | Sun CLOSED",
        "Mo-Th 12:00-21:00; Fr-Sa 12:00-22:00; Su off",
        id="pipe_separator",
    ),
    pytest.param(
        "Mo-Su 09:00-13:00 Mo-Su 16:30-20:30",
        "Mo-Su 09:00-13:00,16:30-20:30",
        id="multi_window",
    ),
    pytest.param(
        "Mo-Fr 08:00-20:00; Sa 09:00--18:00; Su 11:00-16:00",
        "Mo-Fr 08:00-20:00; Sa 09:00-18:00; Su 11:00-16:00",
        id="double_dash",
    ),
    pytest.param("We/Sa 12:00-17:00", "We,Sa 12:00-17:00", id="slash_separator"),
    pytest.param("8am a 7pm", "08:00-19:00", id="a_separator"),
    pytest.param(
        "Domingo a domingo 6:00 am -6:00 pm", "06:00-18:00", id="domingo_a_domingo"
    ),
    pytest.param("Tuesday: 10 a.m. - 6 P.M.", "Tu 10:00-18:00", id="a.m._p.m."),
    pytest.param(
        "Monday to Friday – 8:30AM to 5:00PM, Saturday & Sunday – Closed",
        "Mo-Fr 08:30-17:00; Sa-Su off",
        id="a.m._p.m.",
    ),
    pytest.param(
        "Mo-Wed 08:00-18:00 Thur 09-17",
        "Mo-We 08:00-18:00; Th 09:00-17:00",
        id="mixed_names_no_sep",
    ),
    pytest.param(
        "Monday through Thursday 8:30 AM - 5 PM, Friday 8:30 AM - 1:30 PM, Closed Saturday and Sunday",
        "Mo-Th 08:30-17:00; Fr 08:30-13:30; Sa-Su off",
        id="closed_before_days",
        marks=pytest.mark.xfail(
            reason="Reversed 'Closed X and Y' phrasing after a comma-joined"
            " list of normal day+time rules isn't reliably split from the"
            " preceding rule; fixing this would require reworking the"
            " shared comma/space day-splitting regexes used by every case.",
            strict=True,
        ),
    ),
    pytest.param("10:30 - 1:00; PH off", "10:30-01:00; PH off", id="ph_off"),
    pytest.param("Friday 10:30 - dusk", "Fr 10:30-dusk", id="dusk"),
    pytest.param(
        "todos los dias 10:30 a.m. - 6:30 p.m.", "10:30-18:30", id="todos_los_dias"
    ),
    pytest.param(
        "Lunes, Martes, Jueves, Viernes 8:00 am a 12:00 pm y de 1:00 pm a 5:00 pm Miércoles y Sábado 8:00 am a 2:00 p.m.",
        "Mo-Tu,Th-Fr 08:00-12:00,13:00-17:00; We,Sa 08:00-14:00",
        id="de_check",
    ),
]


@pytest.mark.parametrize(("raw", "expected"), REAL_WORLD_HOURS_CASES)
def test_get_hours_real_world(raw: str, expected: str) -> None:
    """Test handling of real world raw strings."""
    assert get_hours(raw) == expected


REAL_WORLD_TIMES_CASES = [
    pytest.param("11am", "11:00", id="basic"),
    pytest.param("9:00 AM & 11:00 AM", "09:00,11:00", id="double"),
    pytest.param("Monday - Saturday, 10:00 AM", "Mo-Sa 10:00", id="all_week"),
    pytest.param(
        "Saturday 10:00 AM, Sunday 9:00 AM & 11:00 AM",
        "Sa 10:00; Su 09:00,11:00",
        id="days",
    ),
    pytest.param(
        "Sat. 4:30 pm; Sundays at 7:45 am; 9:30 am; 11 am; 12:30 pm; 5:30 pm",
        "Sa 16:30; Su 07:45,09:30,11:00,12:30,17:30",
        id="days2",
    ),
    pytest.param(
        "Monday-Friday: 4:15pm Saturday: 1:00pm Sunday: Closed",
        "Mo-Fr 16:15; Sa 13:00",
        id="closed",
    ),
    pytest.param(
        "Martes 6:30 pm, Jueves 6:30 pm, Sábado 6:30 pm, Domingo 9:00 am y 11:00 am.",
        "Tu,Th,Sa 18:30; Su 09:00,11:00",
        id="spanish_days",
    ),
    pytest.param(
        "Martes, Jueves y Sábado 6:00 pm, Domingo 8:00 am",
        "Tu,Th,Sa 18:00; Su 08:00",
        id="spanish_days",
    ),
]


@pytest.mark.parametrize(("raw", "expected"), REAL_WORLD_TIMES_CASES)
def test_get_times_real_world(raw: str, expected: str) -> None:
    """Test handling of real world raw strings."""
    assert get_times(raw) == expected
