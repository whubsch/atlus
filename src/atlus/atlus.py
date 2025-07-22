"""Functions and tools to process the raw address strings."""

from collections import Counter

import regex
import usaddress
from pydantic import ValidationError

from .objects import Address
from .resources import (
    abbr_join_comp,
    dir_fill_comp,
    direction_expand,
    grid_comp,
    name_expand,
    paren_comp,
    post_comp,
    saint_comp,
    sr_comp,
    state_expand,
    street_comp,
    street_expand,
    usa_comp,
)

toss_tags = [
    "Recipient",
    "IntersectionSeparator",
    "LandmarkName",
    "USPSBoxGroupID",
    "USPSBoxGroupType",
    "USPSBoxID",
    "USPSBoxType",
    "OccupancyType",
]
"""Tags from the `usaddress` package to remove."""

osm_mapping = {
    "AddressNumber": "addr:housenumber",
    "AddressNumberPrefix": "addr:housenumber",
    "AddressNumberSuffix": "addr:housenumber",
    "StreetName": "addr:street",
    "StreetNamePreDirectional": "addr:street",
    "StreetNamePreModifier": "addr:street",
    "StreetNamePreType": "addr:street",
    "StreetNamePostDirectional": "addr:street",
    "StreetNamePostModifier": "addr:street",
    "StreetNamePostType": "addr:street",
    "OccupancyIdentifier": "addr:unit",
    "PlaceName": "addr:city",
    "StateName": "addr:state",
    "ZipCode": "addr:postcode",
}
"""Mapping from `usaddress` fields to OSM tags."""


def get_title(value: str, single_word: bool = False) -> str:
    """Fix ALL-CAPS string.

    ```python
    >>> get_title("PALM BEACH")
    "Palm Beach"
    >>> get_title("BOSTON")
    "BOSTON"
    >>> get_title("BOSTON", single_word=True)
    "Boston"
    ```

    Args:
        value: String to fix.
        single_word: Whether the string should be fixed even if it is a single word.

    Returns:
        str: Fixed string.
    """
    if (value.isupper() and " " in value) or (value.isupper() and single_word):
        return mc_replace(value.title())
    return value


def us_replace(value: str) -> str:
    """Fix string containing improperly formatted US.

    ```python
    >>> us_replace("U.S. Route 15")
    "US Route 15"
    ```

    Args:
        value: String to fix.

    Returns:
        str: Fixed string.
    """
    return value.replace("U.S.", "US").replace("U. S.", "US").replace("U S ", "US ")


def mc_replace(value: str) -> str:
    """Fix string containing improperly formatted Mc- prefix.

    ```python
    >>> mc_replace("Fort Mchenry")
    "Fort McHenry"
    ```

    Args:
        value: String to fix.

    Returns:
        str: Fixed string.
    """
    words = []
    for word in value.split():
        mc_match = word.partition("Mc")
        words.append(mc_match[0] + mc_match[1] + mc_match[2].capitalize())
    return " ".join(words)


def ord_replace(value: str) -> str:
    """Fix string containing improperly capitalized ordinal.

    ```python
    >>> ord_replace("3Rd St. NW")
    "3rd St. NW"
    ```

    Args:
        value: String to fix.

    Returns:
        str: Fixed string.
    """
    return regex.sub(r"(\b\d+[SNRT][tTdDhH]\b)", lower_match, value)


def name_street_expand(match: regex.Match) -> str:
    """Expand matched street type abbreviations.

    Args:
        match (regex.Match): Matched string.

    Returns:
        str: Expanded string.
    """
    mat = match.group(1).upper().rstrip(".")
    if mat:
        return ({**name_expand, **street_expand})[mat].title()
    raise ValueError


def direct_expand(match: regex.Match) -> str:
    """Expand matched directional abbreviations.

    Args:
        match (regex.Match): Matched string.

    Returns:
        str: Expanded string.
    """
    mat = match.group(1).upper().replace(".", "")
    if mat:
        return direction_expand[mat].title()
    raise ValueError


def cap_match(match: regex.Match) -> str:
    """Make matches uppercase.

    Args:
        match (regex.Match): Matched string.

    Returns:
        str: Capitalized string.
    """
    return "".join(match.groups()).upper().replace(".", "")


def lower_match(match: regex.Match) -> str:
    """Lower-case improperly cased ordinal values.

    Args:
        match: String to fix.

    Returns:
        str: Fixed string.
    """
    return match.group(1).lower()


def grid_match(match_str: regex.Match) -> str:
    """Clean grid addresses."""
    return match_str.group(0).replace(" ", "").upper()


def abbrs(value: str) -> str:
    """Bundle most common abbreviation expansion functions.

    ```python
    >>> abbrs("St. Francis")
    "Saint Francis"
    >>> abbrs("E St.")
    "E Street"
    >>> abbrs("E Sewell St")
    "East Sewell Street"
    ```

    Args:
        value (str): String to expand.

    Returns:
        str: Expanded string.
    """
    value = ord_replace(us_replace(mc_replace(get_title(value))))

    # change likely 'St' to 'Saint'
    value = saint_comp.sub("Saint", value)

    # expand common street and word abbreviations
    value = abbr_join_comp.sub(name_street_expand, value)

    # expand directionals
    value = dir_fill_comp.sub(direct_expand, value)

    # normalize 'US'
    value = us_replace(value)

    # uppercase shortened street descriptors
    value = regex.sub(r"\b(C[rh]|S[rh]|[FR]m|Us)\b", cap_match, value)

    # remove unremoved abbr periods
    value = regex.sub(r"([a-zA-Z]{2,})\.", r"\1", value)

    # expand 'SR' if no other street types
    value = sr_comp.sub("State Route", value)
    return value.strip(" .")


def remove_br_unicode(old: str) -> str:
    """Clean the input string before sending to parser by removing newlines and unicode.

    Args:
        old (str): String to clean.

    Returns:
        str: Cleaned string.
    """
    old = regex.sub(r"<br ?/>", ",", old)
    return regex.sub(r"[^\x00-\x7F\n\r\t]", "", old)  # remove unicode


def clean_address(address_string: str) -> str:
    """Clean the input string before sending to parser by removing newlines and unicode.

    Args:
        address_string (str): String to clean.

    Returns:
        str: Cleaned string.
    """
    address_string = usa_comp.sub(
        "", remove_br_unicode(address_string).replace("  ", " ").strip(" ,.")
    )
    address_string = paren_comp.sub("", address_string)
    return grid_comp.sub(grid_match, address_string).strip(" ,.")


def help_join(tags, keep: list[str]) -> str:
    """Help to join address fields."""
    tag_join: list[str] = [v for k, v in tags.items() if k in keep]
    return " ".join(tag_join)


def addr_street(tags: dict[str, str]) -> str:
    """Build the street field."""
    return help_join(
        tags,
        [
            "StreetName",
            "StreetNamePreDirectional",
            "StreetNamePreModifier",
            "StreetNamePreType",
            "StreetNamePostDirectional",
            "StreetNamePostModifier",
            "StreetNamePostType",
        ],
    )


def addr_housenumber(tags: dict[str, str]) -> str:
    """Build the housenumber field."""
    return help_join(
        tags, ["AddressNumberPrefix", "AddressNumber", "AddressNumberSuffix"]
    )


def _combine_consecutive_tuples(
    tuples_list: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    """Join adjacent `usaddress` fields."""
    combined_list = []
    current_tag = None
    current_value = None

    for value, tag in tuples_list:
        if tag != current_tag:
            if current_tag:
                combined_list.append((current_value, current_tag))
            current_value, current_tag = value, tag
        else:
            current_value = " ".join(i for i in [current_value, value] if i)

    if current_tag:
        combined_list.append((current_value, current_tag))

    return combined_list


def manual_join(parsed: list[tuple]) -> tuple[dict[str, str], list[str | None]]:
    """Remove duplicates and join remaining fields."""
    parsed_clean = [i for i in parsed if i[1] not in toss_tags]
    counts = Counter([i[1] for i in parsed_clean])
    ok_tags = [tag for tag, count in counts.items() if count == 1]
    ok_dict: dict[str, str] = {i[1]: i[0] for i in parsed_clean if i[1] in ok_tags}
    removed = [osm_mapping.get(field) for field, count in counts.items() if count > 1]

    new_dict: dict[str, str | None] = {}
    if "addr:street" not in removed:
        new_dict["addr:street"] = addr_street(ok_dict)
    if "addr:housenumber" not in removed:
        new_dict["addr:housenumber"] = addr_housenumber(ok_dict)
    if "addr:unit" not in removed:
        new_dict["addr:unit"] = ok_dict.get("OccupancyIdentifier")
    if "addr:city" not in removed:
        new_dict["addr:city"] = ok_dict.get("PlaceName")
    if "addr:state" not in removed:
        new_dict["addr:state"] = ok_dict.get("StateName")
    if "addr:postcode" not in removed:
        new_dict["addr:postcode"] = ok_dict.get("ZipCode")

    return {k: v for k, v in new_dict.items() if v}, removed


def collapse_list(seq: list) -> list:
    """Remove duplicates in list while keeping order.

    ```python
    >>> collapse_list(["foo", "bar", "foo"])
    ["foo", "bar"]
    ```

    Args:
        seq (list): The list to collapse.

    Returns:
        list: The collapsed list.
    """
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def split_unit(address_string: str) -> dict[str, str]:
    """Split unit from address string, if present."""
    address_string = address_string.strip(" ")
    if not any(char.isalpha() for char in address_string):
        return {"addr:housenumber": address_string}

    add_dict = {}
    number = ""
    for char in address_string:
        if char.isdigit():
            number += char
        else:
            break

    unit = remove_prefix(address_string, number).lstrip(" -,/")
    if unit:
        add_dict["addr:unit"] = unit
    add_dict["addr:housenumber"] = number

    return add_dict


def remove_prefix(text: str, prefix: str) -> str:
    """Remove prefix from string for Python 3.8."""
    if text.startswith(prefix):
        return text[len(prefix) :]
    return text


def get_address(address_string: str) -> tuple[dict[str, str], list[str | None]]:
    """Process address strings.

    ```python
    >>> get_address("345 MAPLE RD, COUNTRYSIDE, PA 24680-0198")[0]
    {"addr:housenumber": "345", "addr:street": "Maple Road",
    "addr:city": "Countryside", "addr:state": "PA", "addr:postcode": "24680-0198"}
    >>> get_address("777 Strawberry St.")[0]
    {"addr:housenumber": "777", "addr:street": "Strawberry Street"}
    >>> address = get_address("222 NW Pineapple Ave Suite A Unit B")
    >>> address[0]
    {"addr:housenumber": "222", "addr:street": "Northwest Pineapple Avenue"}
    >>> address[1]
    ["addr:unit"]
    ```

    Args:
        address_string (str): The address string to process.

    Returns:
        tuple[dict[str, str], list[str | None]]:
        The processed address string and the removed fields.
    """
    try:
        cleaned = usaddress.tag(clean_address(address_string), tag_mapping=osm_mapping)[
            0
        ]
        removed = []
    except usaddress.RepeatedLabelError as err:
        collapsed = collapse_list(
            [(i[0].strip(" .,#"), i[1]) for i in err.parsed_string]
        )
        cleaned, removed = manual_join(_combine_consecutive_tuples(collapsed))

    for toss in toss_tags:
        cleaned.pop(toss, None)

    if "addr:housenumber" in cleaned:
        cleaned = {**cleaned, **split_unit(cleaned["addr:housenumber"])}

    if "addr:street" in cleaned:
        street = abbrs(cleaned["addr:street"])
        cleaned["addr:street"] = street_comp.sub("Street", street).strip(".")

    if "addr:city" in cleaned:
        cleaned["addr:city"] = abbrs(get_title(cleaned["addr:city"], single_word=True))

    if "addr:state" in cleaned:
        old = cleaned["addr:state"].replace(".", "")
        if old.upper() in state_expand:
            cleaned["addr:state"] = state_expand[old.upper()]
        elif len(old) == 2 and old.upper() in list(state_expand.values()):
            cleaned["addr:state"] = old.upper()

    if "addr:unit" in cleaned:
        cleaned["addr:unit"] = cleaned["addr:unit"].removeprefix("Space").strip(" #.")

    if "addr:postcode" in cleaned:
        # remove extraneous postcode digits
        cleaned["addr:postcode"] = post_comp.sub(
            r"\1", cleaned["addr:postcode"]
        ).replace(" ", "-")

    try:
        validated: Address = Address.model_validate(dict(cleaned))
    except ValidationError as err:
        bad_fields: list = [each.get("loc", [])[0] for each in err.errors()]
        cleaned_ret = dict(cleaned)
        for each in bad_fields:
            cleaned_ret.pop(each, None)

        removed.extend(bad_fields)
        validated: Address = Address.model_validate(cleaned_ret)

    return validated.model_dump(exclude_none=True, by_alias=True), removed


def get_phone(phone: str) -> str:
    """Format phone numbers to the US and Canadian standard format of `+1 XXX-XXX-XXXX`.

    ```python
    >>> get_phone("2029009019")
    "+1 202-900-9019"
    >>> get_phone("(202) 900-9019")
    "+1 202-900-9019"
    >>> get_phone("202-900-901")
    ValueError: Invalid phone number: 202-900-901
    ```

    Args:
        phone (str): The phone number to format.

    Returns:
        str: The formatted phone number.

    Raises:
        ValueError: If the phone number is invalid.
    """
    phone_valid = regex.search(
        r"^\(?(?:\+? ?1?[ -.]*)?(?:\(?(\d{3})\)?[ -.]*)(\d{3})[ -.]*(\d{4})$", phone
    )
    if phone_valid:
        return (
            f"+1 {phone_valid.group(1)}-{phone_valid.group(2)}-{phone_valid.group(3)}"
        )
    raise ValueError(f"Invalid phone number: {phone}")
