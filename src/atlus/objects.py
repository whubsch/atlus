"""Define objects for parsing fields."""

from enum import Enum

import regex
from pydantic import BaseModel, Field, field_validator, model_validator


class Address(BaseModel):
    """Define address parsing fields."""

    addr_housenumber: int | str | None = Field(
        alias="addr:housenumber",
        description="The house number that is included in the address.",
        examples=[200, "1200-29"],
        default=None,
    )
    addr_street: str | None = Field(
        alias="addr:street",
        description="The street that the address is located on.",
        examples=["North Spring Street"],
        default=None,
    )
    addr_unit: str | None = Field(
        alias="addr:unit",
        description="The unit number or letter that is included in the address.",
        examples=["B"],
        default=None,
    )
    addr_city: str | None = Field(
        alias="addr:city",
        description="The city that the address is located in.",
        examples=["Los Angeles"],
        default=None,
    )
    addr_state: str | None = Field(
        alias="addr:state",
        pattern=r"^[A-Z]{2}$",
        description="The state or territory of the address.",
        examples=["CA"],
        default=None,
    )
    addr_postcode: str | None = Field(
        alias="addr:postcode",
        pattern=r"^\d{5}(?:\-\d{4})?$",
        description="The postal code of the address.",
        examples=["90012", "90012-4801"],
        default=None,
    )


class Day(str, Enum):
    """Two-letter OSM day abbreviations, in canonical week order, plus the
    special `PH` (public holiday) indicator.

    `PH` isn't a real weekday -- it's never part of a day range, always
    stands alone, and always sorts after every other day.
    """

    MO = "Mo"
    TU = "Tu"
    WE = "We"
    TH = "Th"
    FR = "Fr"
    SA = "Sa"
    SU = "Su"
    PH = "PH"

    @property
    def weekday_index(self) -> int:
        """Return the day's position in the week, starting with Monday at 0."""
        return list(Day).index(self)


class DayRange(BaseModel):
    """A single day, or an inclusive range of days (e.g. `Mo` or `Mo-Fr`)."""

    start: Day = Field(description="The first (or only) day in the range.")
    end: Day | None = Field(
        default=None, description="The last day in the range, if a range."
    )

    @model_validator(mode="after")
    def _check_ph_standalone(self) -> "DayRange":
        """Ensure `PH` (public holiday) is never part of an actual range."""
        if (
            self.end is not None
            and self.start != self.end
            and Day.PH in (self.start, self.end)
        ):
            raise ValueError("'PH' cannot be part of a day range.")
        return self

    def to_osm(self) -> str:
        """Render the day range in OSM `opening_hours` syntax.

        ```python
        >>> DayRange(start=Day.MO).to_osm()
        "Mo"
        >>> DayRange(start=Day.MO, end=Day.FR).to_osm()
        "Mo-Fr"
        ```
        """
        if self.end is None or self.end == self.start:
            return self.start.value
        return f"{self.start.value}-{self.end.value}"


class TimeSpan(BaseModel):
    """A single opening time interval, e.g. `08:00-12:00` or `sunrise-sunset`."""

    start: str = Field(
        pattern=r"^(?:([01]\d|2[0-4]):[0-5]\d|dawn|dusk|sunrise|sunset)$",
        description="The start time, in 24-hour `HH:MM` format, or one of"
        " the solar keywords `dawn`, `dusk`, `sunrise`, `sunset`.",
        examples=["08:00", "sunrise"],
    )
    end: str = Field(
        pattern=r"^(?:([01]\d|2[0-4]):[0-5]\d|dawn|dusk|sunrise|sunset)$",
        description="The end time, in 24-hour `HH:MM` format, or one of the"
        " solar keywords `dawn`, `dusk`, `sunrise`, `sunset`. May be earlier"
        " than `start` to represent a span that crosses midnight.",
        examples=["17:30", "sunset"],
    )

    def to_osm(self) -> str:
        """Render the time span in OSM `opening_hours` syntax.

        ```python
        >>> TimeSpan(start="08:00", end="17:30").to_osm()
        "08:00-17:30"
        ```
        """
        return f"{self.start}-{self.end}"


class RuleSet(BaseModel):
    """A single opening_hours rule: a set of days and their time span(s)."""

    days: list[DayRange] = Field(
        default_factory=list,
        description="The day or days that this rule applies to. An empty"
        " list means the rule applies every day of the week.",
    )
    times: list[TimeSpan] = Field(
        default_factory=list,
        description="The time span(s) that the location is open, if any.",
    )
    closed: bool = Field(
        default=False, description="Whether this rule marks the day(s) as closed."
    )
    is_24h: bool = Field(
        default=False,
        description="Whether this rule marks the day(s) as open 24 hours.",
    )

    @model_validator(mode="after")
    def _check_exclusive(self) -> "RuleSet":
        """Ensure closed/24h/times are mutually exclusive."""
        modes = [self.closed, self.is_24h, bool(self.times)]
        if sum(modes) > 1:
            raise ValueError(
                "A RuleSet must be exactly one of: closed, 24 hours, or timed."
            )
        return self

    def to_osm(self) -> str:
        """Render the rule in OSM `opening_hours` syntax.

        ```python
        >>> RuleSet(
        ...     days=[DayRange(start=Day.MO, end=Day.FR)],
        ...     times=[TimeSpan(start="08:00", end="12:00")],
        ... ).to_osm()
        "Mo-Fr 08:00-12:00"
        ```
        """
        days_str = ",".join(d.to_osm() for d in self.days)
        if self.closed:
            body = "off"
        elif self.is_24h:
            body = "24/7"
        else:
            body = ",".join(t.to_osm() for t in self.times)
        return f"{days_str} {body}".strip() if days_str else body


class PointRuleSet(BaseModel):
    """A single point-in-time rule: a set of days and specific clock times.

    Used for tags like `collection_times`/`service_times` that record
    single points in time rather than open/close ranges.
    """

    days: list[DayRange] = Field(
        default_factory=list,
        description="The day or days that this rule applies to. An empty"
        " list means the rule applies every day of the week.",
    )
    times: list[str] = Field(
        default_factory=list,
        description="The point-in-time value(s), in 24-hour `HH:MM` format.",
        examples=["15:00"],
    )

    @field_validator("times")
    @classmethod
    def _check_time_format(cls, value: list[str]) -> list[str]:
        """Ensure every time value is a valid 24-hour `HH:MM` string, or one
        of the solar keywords `dawn`, `dusk`, `sunrise`, `sunset`.
        """
        pattern = regex.compile(
            r"^(?:([01]\d|2[0-4]):[0-5]\d|dawn|dusk|sunrise|sunset)$"
        )
        for time in value:
            if not pattern.match(time):
                raise ValueError(f"Invalid time format: {time!r}")
        return value

    def to_osm(self) -> str:
        """Render the rule in OSM point-in-time syntax.

        ```python
        >>> PointRuleSet(
        ...     days=[DayRange(start=Day.MO, end=Day.FR)],
        ...     times=["15:00", "18:00"],
        ... ).to_osm()
        "Mo-Fr 15:00,18:00"
        ```
        """
        days_str = ",".join(d.to_osm() for d in self.days)
        body = ",".join(self.times)
        return f"{days_str} {body}".strip() if days_str else body


class PointTimes(BaseModel):
    """A full point-in-time value (e.g. `collection_times`) made of one or
    more rules.
    """

    rules: list[PointRuleSet] = Field(
        default_factory=list,
        description="The ordered list of rules that make up the full value.",
    )

    @field_validator("rules")
    @classmethod
    def _check_not_empty(cls, value: list[PointRuleSet]) -> list[PointRuleSet]:
        """Ensure at least one rule is present."""
        if not value:
            raise ValueError("PointTimes must contain at least one rule.")
        return value

    def to_osm(self) -> str:
        """Render the full value in OSM point-in-time syntax.

        ```python
        >>> PointTimes(rules=[
        ...     RuleSet := PointRuleSet(
        ...         days=[DayRange(start=Day.MO, end=Day.FR)],
        ...         times=["15:00", "18:00"],
        ...     ),
        ...     PointRuleSet(
        ...         days=[DayRange(start=Day.SA)],
        ...         times=["15:00"],
        ...     ),
        ... ]).to_osm()
        "Mo-Fr 15:00,18:00; Sa 15:00"
        ```
        """
        return "; ".join(r.to_osm() for r in self.rules)


class OpeningHours(BaseModel):
    """A full `opening_hours` value made of one or more rules."""

    rules: list[RuleSet] = Field(
        default_factory=list,
        description="The ordered list of rules that make"
        " up the full opening_hours string.",
    )

    @field_validator("rules")
    @classmethod
    def _check_not_empty(cls, value: list[RuleSet]) -> list[RuleSet]:
        """Ensure at least one rule is present."""
        if not value:
            raise ValueError("OpeningHours must contain at least one rule.")
        return value

    def to_osm(self) -> str:
        """Render the full value in OSM `opening_hours` syntax.

        ```python
        >>> OpeningHours(rules=[
        ...     RuleSet(
        ...         days=[DayRange(start=Day.MO, end=Day.FR)],
        ...         times=[TimeSpan(start="08:00", end="12:00")],
        ...     ),
        ...     RuleSet(
        ...         days=[DayRange(start=Day.SA)],
        ...         times=[TimeSpan(start="08:00", end="12:00")],
        ...     ),
        ... ]).to_osm()
        "Mo-Fr 08:00-12:00; Sa 08:00-12:00"
        ```
        """
        return "; ".join(r.to_osm() for r in self.rules)
