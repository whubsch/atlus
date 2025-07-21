# Atlus

![GitHub License](https://img.shields.io/github/license/whubsch/atlus)
![GitHub last commit](https://img.shields.io/github/last-commit/whubsch/atlus)
![PyPI - Version](https://img.shields.io/pypi/v/atlus)
![Pepy Total Downlods](https://img.shields.io/pepy/dt/atlus)

This Python project translates raw address strings into the OpenStreetMap (OSM) tagging scheme. The package only supports US (and to some extent Canadian) addresses. You can try out the package without installing it at [the Atlus website](https://atlus.dev).

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
"+1 202-900-9019"
```

## Docs

The documentation for our package is available online at our [documentation page](https://whubsch.github.io/atlus/index.html). We would greatly appreciate your contributions to help improve the auto-generated docs; please submit any updates or corrections via pull requests.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE.txt) file for details.

## See also

- [OpenStreetMap](https://www.openstreetmap.org/)
- [Atlus](https://wiki.openstreetmap.org/wiki/atlus)
- [All the Places](https://wiki.openstreetmap.org/wiki/All_the_Places)
