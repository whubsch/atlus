"""Convert raw address and phone number strings into the OSM format.

`atlus` is a Python package to convert raw address, phone number, and opening
hours strings into the OSM format. It's designed to be used with US and Canadian
phone numbers and addresses.

```python
>>> import atlus
>>> atlus.abbrs("St. Francis")
"Saint Francis"
>>> atlus.get_address("789 Oak Dr, Smallville California, 98765")[0]
{"addr:housenumber": "789", "addr:street": "Oak Drive", "addr:city": "Smallville",
    "addr:state": "CA", "addr:postcode": "98765"}
>>> atlus.get_phone("(202) 900-9019")
"+1-202-900-9019"
>>> atlus.get_hours("Monday to Friday 9am-5pm, Saturday 9am-12pm")
"Mo-Fr 09:00-17:00; Sa 09:00-12:00"
>>> atlus.get_times("Mo-Fr 15:00,18:00,19:00,23:00; Sa 15:00; Su 10:30,23:00")
"Mo-Fr 15:00,18:00,19:00,23:00; Sa 15:00; Su 10:30,23:00"
```

"""

# SPDX-FileCopyrightText: 2024-present Will <wahubsch@gmail.com>
#
# SPDX-License-Identifier: MIT

from . import atlus, hours, resources
from .atlus import (
    abbrs,
    get_address,
    get_phone,
    get_title,
    mc_replace,
    ord_replace,
    remove_br_unicode,
    us_replace,
)
from .hours import get_hours, get_times

__all__ = [
    "get_address",
    "get_phone",
    "get_hours",
    "get_times",
    "abbrs",
    "get_title",
    "mc_replace",
    "us_replace",
    "ord_replace",
    "remove_br_unicode",
    "atlus",
    "hours",
    "resources",
]
