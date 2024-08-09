"""Convert raw address and phone number strings into the OSM format.

`atlus` is a Python package to convert raw address and phone number strings into
the OSM format. It's designed to be used with US and Canadian phone numbers and
addresses.

```python
>>> import atlus
>>> atlus.abbrs("St. Francis")
"Saint Francis"
>>> atlus.get_address("789 Oak Dr, Smallville California, 98765")[0]
{"addr:housenumber": "789", "addr:street": "Oak Drive", "addr:city": "Smallville",
    "addr:state": "CA", "addr:postcode": "98765"}
>>> atlus.get_phone("(202) 900-9019")
"+1 202-900-9019"
```

"""

# SPDX-FileCopyrightText: 2024-present Will <wahubsch@gmail.com>
#
# SPDX-License-Identifier: MIT

from . import atlus, resources
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

__all__ = [
    "get_address",
    "get_phone",
    "abbrs",
    "get_title",
    "mc_replace",
    "us_replace",
    "ord_replace",
    "remove_br_unicode",
    "atlus",
    "resources",
]
