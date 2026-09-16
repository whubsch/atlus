# Atlus

![GitHub License](https://img.shields.io/github/license/whubsch/atlus)
![GitHub last commit](https://img.shields.io/github/last-commit/whubsch/atlus)
![PyPI - Version](https://img.shields.io/pypi/v/atlus)
![Pepy Total Downlods](https://img.shields.io/pepy/dt/atlus)

This Python project translates raw address, phone number, and opening hours strings into the OpenStreetMap (OSM) tagging scheme. The package only supports US (and to some extent Canadian) addresses and phone numbers. The opening hours function only supports strings in English. You can try out the package without installing it at [the Atlus website](https://atlus.dev).

> [!NOTE]
> Use of this package does not absolve you from following OSM's [import guidelines](https://wiki.openstreetmap.org/wiki/Import/Guidelines).

## Table of Contents

- [Features](#features)
- [Usage](#usage)
- [Docs](#docs)
- [License](#license)

## Features

- Expand common street and name abbreviations.
- Parse address parts correctly and reliably.
- Get rid of address junk that is not needed for OpenStreetMap tagging.
- Parse US and Canadian phone numbers into the standard format.
- Parse raw opening hours strings into the OSM `opening_hours` format, including the special `PH` (public holiday) indicator and the `dawn`/`dusk`/`sunrise`/`sunset` solar time keywords.
- Parse raw point-in-time strings (e.g. `collection_times`, `service_times`) into the matching OSM format, dropping any "closed" days rather than erroring (since point-in-time tags have no "closed" concept of their own).
- Raise a clear error instead of guessing when opening hours/point-in-time input references calendar/date-based rules (month names, specific dates, named holidays, or OSM's `Th[4]`-style nth-weekday notation), which aren't supported.
- Optional `no_wrap` mode for `get_hours()` that stops ambiguous times without an am/pm marker -- whether a bare digit (e.g. "9-5") or a bare colon form (e.g. "9:00-5:00") -- from ever being assumed to cross midnight.

## Usage

This package is meant to work with GeoJSON files containing raw address data, including those produced by the [All the Places](https://alltheplaces.xyz) project or [Overture maps](https://wiki.openstreetmap.org/wiki/Overture).

```console
pip install atlus
```

```python
>>> import atlus
>>> atlus.abbrs("St. Francis")
"Saint Francis"
>>> atlus.get_address("789 Oak Dr, Smallville California, 98765")[0]
{"addr:housenumber": "789", "addr:street": "Oak Drive", "addr:city": "Smallville", "addr:state": "CA", "addr:postcode": "98765"}
>>> atlus.get_phone("(202) 900-9019")
"+1-202-900-9019"
>>> atlus.get_hours("Monday to Friday 9am-5pm, Saturday 9am-12pm")
"Mo-Fr 09:00-17:00; Sa 09:00-12:00"
>>> atlus.get_times("Mo-Fr 15:00,18:00,19:00,23:00; Sa 15:00; Su 10:30,23:00")
"Mo-Fr 15:00,18:00,19:00,23:00; Sa 15:00; Su 10:30,23:00"
>>> atlus.get_hours("Mo-Fr sunrise-sunset")
"Mo-Fr sunrise-sunset"
>>> atlus.get_hours("Monday to Friday 9:00-5:00")
"Mo-Fr 09:00-05:00"
>>> atlus.get_hours("Monday to Friday 9:00-5:00", no_wrap=True)
"Mo-Fr 09:00-17:00"
>>> atlus.get_hours("Mo-Fr 13-2", no_wrap=True)
"Mo-Fr 13:00-02:00"
```

A colon on its own doesn't make a time unambiguous -- only an actual am/pm marker does. By default, `get_hours()` assumes a bare colon time with no am/pm marker (e.g. the "5:00" above) is already correct 24-hour time, which is why `"9:00-5:00"` resolves to `"09:00-05:00"` (open until 5 AM) rather than the probably-intended `"09:00-17:00"`. Pass `no_wrap=True` to instead resolve such ambiguous times the same way bare digits like `"9-5"` already are.

`no_wrap` only changes how an _ambiguous_ time is interpreted -- it doesn't disable the pre-existing check that rejects a span which still looks backwards (end before start) once the end hour is too late in the day (6 AM or later) to be a plausible overnight close, so a nonsensical input like `"16-14"` still raises `ValueError` either way.

## Changes

See the [changelog](CHANGELOG.md) for details on recent updates.

## Docs

The documentation for our package is available online at our [documentation page](https://whubsch.github.io/atlus/index.html). We would greatly appreciate your contributions to help improve the auto-generated docs; please submit any updates or corrections via pull requests.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE.txt) file for details.

## See also

- [OpenStreetMap](https://www.openstreetmap.org/)
- [Atlus](https://wiki.openstreetmap.org/wiki/atlus)
- [All the Places](https://wiki.openstreetmap.org/wiki/All_the_Places)
