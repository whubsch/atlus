# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-09-16

### Added

- **`no_wrap` parameter for `get_hours()`**: When `True`, ambiguous times --
  a bare digit (e.g. "9-5") or a bare colon form with no am/pm marker (e.g.
  "9:00-5:00") -- never assume an overnight wrap:
  - A colon alone does _not_ make a time unambiguous. Without `no_wrap`,
    "Mo-Fr 9:00-5:00" silently resolves to "Mo-Fr 09:00-05:00" (open until
    5 AM), since a bare colon time is otherwise assumed to already be
    correct 24-hour time. `no_wrap` fixes this specific case by resolving
    it as "09:00-17:00" instead, the same as "9-5" already was.
  - If the start hour is already > 12 (e.g. the "13" in "13-2"), there's no
    12-hour reading of it, so both hours are taken at face value
    ("13:00-02:00").
  - Otherwise the start hour is assumed to be AM, and the end hour is only
    shifted to PM when it's numerically <= the start hour -- just enough to
    keep the span from running backwards on the same day ("9-5"/"9:00-5:00"
    become "09:00-17:00", but "9-14" stays "09:00-14:00").
  - Times with a real am/pm marker (e.g. "9am-5pm" or "10pm-2am") are
    unaffected.
  - Does not disable the pre-existing check that rejects a span which still
    looks backwards once the end hour is too late in the day (6 AM or
    later) to be a plausible overnight close, so a nonsensical bare
    "16-14" still raises `ValueError` with or without `no_wrap`.
  - Defaults to `False`, preserving existing behavior.

## [1.2.0] - 2026-08-11

### Changed

- **Address parsing no longer depends on `usaddress`**: `get_address()` now uses
  a built-in parser that works right to left, peeling off the fields whose
  position is most reliable (postcode, then unit, then state) before splitting
  the remainder into street and city
  - Removes the `usaddress` dependency and its `python-crfsuite` C extension,
    making the package pure Python
  - `pydantic` is now a real runtime dependency instead of a test-only extra,
    which it always was in practice
  - Roughly 3.2x faster end to end and 3.9x faster in the parsing stage; run
    `scripts/bench_address.py` to reproduce

- **Address processing is substantially faster, with byte-identical output**
  - Every pattern is now compiled once at import instead of being rebuilt from
    a source string on each call, which alone accounted for most of the cost of
    `abbrs()`, `clean_address()`, and `remove_br_unicode()`
  - `abbrs()` no longer matches a 215-way alternation of every known
    abbreviation; it scans for one generic word shape and resolves matches with
    a dict lookup, covering the same spans far more cheaply (~3.6x)
  - Passes that cannot apply are skipped with a cheap containment check: the
    non-ASCII strip is skipped when `str.isascii()` is true, and the HTML
    break, PO box, bracket, country, and separator passes are skipped when
    their trigger characters are absent (`clean_address` ~4.1x)

- **Opening hours parsing is faster too**, with byte-identical output. The same
  patterns-per-call issue applied to `hours.py`: `_normalize()` is ~16x faster,
  `_parse_days()` ~2.5x, and `get_hours()`/`get_times()` ~1.5x overall. Run
  `scripts/bench_hours.py` to reproduce.

### Added

- `scripts/bench_address.py` and `scripts/bench_hours.py`, with saved baselines,
  so performance changes can be measured rather than estimated

- **Canadian postal codes are now accepted** in `addr:postcode` and normalized
  to the standard `A1A 1A1` form

- **Malformed ZIP+4 separators are normalized to a dash**, so `62701+0299` and
  `10001.0192` become `62701-0299` and `10001-0192` instead of being discarded

### Fixed

- Bracketed unit designators such as `[Suite 5]` no longer leak the closing
  bracket into `addr:unit`
- Addresses split across newlines no longer lose their postcode
- Street names containing `&` are no longer truncated at the ampersand
- `addr:housenumber` is never returned as an empty string

### Removed

- `manual_join()`, `osm_mapping`, `toss_tags`, `addr_street()`, and
  `addr_housenumber()`, which existed only to reshape `usaddress` output. None
  were part of the public API exported from `atlus`.

## [1.1.0] - 2026-08-10

### Added

- **Opening Hours Support**: New `get_hours()` function to parse raw opening hours strings into OSM `opening_hours` format
  - Support for multiple time formats and day abbreviations
  - Handles special OSM indicators like `PH` (public holiday)
  - Support for solar time keywords: `dawn`, `dusk`, `sunrise`, `sunset`
  - Comprehensive real-world test coverage

- **Point-in-Time Support**: New `get_times()` function to parse collection times, service times, and other point-in-time strings into OSM format
  - Gracefully handles closed days without erroring
  - Compatible with various time string formats

- **Output Validation**: New output validator to ensure parsed data conforms to OSM tagging standards

- **Expanded Language Support**: Expanded Spanish language coverage in abbreviation expansions

- **Enhanced Testing**:
  - Real-world test cases from actual websites
  - Comprehensive test suite for opening hours and point-in-time parsing
  - Improved address tests

- **Build Tool Upgrade**: Migrated to `uv` package manager for faster dependency resolution and testing
  - Added `uv.lock` for reproducible builds
  - Updated tox configuration to use `uv`

- **Documentation**:
  - Added opening_hours documentation
  - Updated README with new `get_hours()` and `get_times()` examples

### Changed

- Refactored core atlus module for better organization
- Improved error handling with clearer messages for unsupported calendar/date-based rules
- Enhanced address object structure for better data handling
- Updated GitHub Actions workflows for improved CI/CD

### Fixed

- Fixed merge conflicts from feature branch
- Corrected `Day.weekday_index` attribute naming in test suite
- Resolved issues with uv and tox integration

### Dependencies

- Updated GitHub Action versions for security and stability

[1.3.0]: https://github.com/whubsch/atlus/compare/1.2.0...1.3.0
[1.2.0]: https://github.com/whubsch/atlus/compare/1.1.0...1.2.0
[1.1.0]: https://github.com/whubsch/atlus/compare/1.0.1...1.1.0
