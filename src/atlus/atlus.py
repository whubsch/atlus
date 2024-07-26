"""Functions and tools to process the raw address strings."""

from collections import Counter
from typing import OrderedDict, Union, List, Dict, Tuple
import usaddress
import regex
from .resources import (
    street_expand,
    direction_expand,
    name_expand,
    state_expand,
    saint_comp,
    abbr_join_comp,
    dir_fill_comp,
    sr_comp,
    usa_comp,
    paren_comp,
    grid_comp,
    post_comp,
    street_comp,
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
    >> get_title("PALM BEACH")
    # "Palm Beach"
    >> get_title("BOSTON")
    # "BOSTON"
    >> get_title("BOSTON", single_word=True)
    # "Boston"
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
    >> us_replace("U.S. Route 15")
    # "US Route 15"
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
    >> mc_replace("Fort Mchenry")
    # "Fort McHenry"
    ```

    Args:
        value: String to fix.

    Returns:
        str: Fixed string.
    """
    mc_match = regex.search(r"(.*\bMc)([a-z])(.*)", value)
    if mc_match:
        return mc_match.group(1) + mc_match.group(2).title() + mc_match.group(3)
    return value


def ord_replace(value: str) -> str:
    """Fix string containing improperly capitalized ordinal.

    ```python
    >> ord_replace("3Rd St. NW")
    # "3rd St. NW"
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
        value: String to fix.

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
    >> abbrs("St. Francis")
    # "Saint Francis"
    >> abbrs("E St.")
    # "E Street"
    >> abbrs("E Sewell St")
    # "East Sewell Street"
    ```

    Args:
        value (str): String to expand.

    Returns:
        str: Expanded string.
    """
    value = ord_replace(us_replace(mc_replace(get_title(value))))

    # change likely 'St' to 'Saint'
    value = saint_comp.sub(
        "Saint",
        value,
    )

    # expand common street and word abbreviations
    value = abbr_join_comp.sub(
        name_street_expand,
        value,
    )

    # expand directionals
    value = dir_fill_comp.sub(
        direct_expand,
        value,
    )

    # normalize 'US'
    value = regex.sub(
        r"\bU.[Ss].\B",
        cap_match,
        value,
    )

    # uppercase shortened street descriptors
    value = regex.sub(
        r"\b(C[rh]|S[rh]|[FR]m|Us)\b",
        cap_match,
        value,
    )

    # remove unremoved abbr periods
    value = regex.sub(
        r"([a-zA-Z]{2,})\.",
        r"\1",
        value,
    )

    # expand 'SR' if no other street types
    value = sr_comp.sub("State Route", value)
    return value.strip(" .")


def clean(old: str) -> str:
    """Clean the input string before sending to parser by removing newlines and unicode.

    Args:
        old (str): String to clean.

    Returns:
        str: Cleaned string.
    """
    old = regex.sub(r"<br ?/>", ",", old)
    return regex.sub(r"[^\x00-\x7F\n\r\t]", "", old)  # remove unicode


def help_join(tags, keep: List[str]) -> str:
    """Help to join address fields."""
    tag_join: List[str] = [v for k, v in tags.items() if k in keep]
    return " ".join(tag_join)


def addr_street(tags: Dict[str, str]) -> str:
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


def addr_housenumber(tags: Dict[str, str]) -> str:
    """Build the housenumber field."""
    return help_join(
        tags, ["AddressNumberPrefix", "AddressNumber", "AddressNumberSuffix"]
    )


def _combine_consecutive_tuples(
    tuples_list: List[Tuple[str, str]]
) -> List[Tuple[str, str]]:
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


def _manual_join(parsed: List[tuple]) -> Tuple[Dict[str, str], List[Union[str, None]]]:
    """Remove duplicates and join remaining fields."""
    a = [i for i in parsed if i[1] not in toss_tags]
    counts = Counter([i[1] for i in a])
    ok_tags = [tag for tag, count in counts.items() if count == 1]
    ok_dict: Dict[str, str] = {i[1]: i[0] for i in a if i[1] in ok_tags}
    removed = [osm_mapping.get(field) for field, count in counts.items() if count > 1]

    new_dict: Dict[str, Union[str, None]] = {}
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
    >> collapse_list(["foo", "bar", "foo"])
    # ["foo", "bar"]
    ```

    Args:
        seq (list): The list to collapse.

    Returns:
        list: The collapsed list.
    """
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def get_address(
    address_string: str,
) -> Tuple[OrderedDict[str, Union[str, int]], List[Union[str, None]]]:
    """Process address strings.

    ```python
    >> get_address("345 MAPLE RD, COUNTRYSIDE, PA 24680-0198")
    # {"addr:housenumber": "345", "addr:street": "Maple Road", "addr:city": "Countryside", "addr:state": "PA", "addr:postcode": "24680-0198"}
    >> get_address("777 Strawberry St.")
    # {"addr:housenumber": "777", "addr:street": "Strawberry Street",}
    ```

    Args:
        address_string (str): The address string to process.

    Returns:
        Tuple[OrderedDict[str, Union[str, int]], List[Union[str, None]]]:
        The processed address string and the removed fields.
    """
    address_string = clean(address_string)
    address_string = address_string.replace("  ", " ").strip(" ,.")
    address_string = usa_comp.sub("", address_string)
    address_string = paren_comp.sub("", address_string)
    address_string = grid_comp.sub(grid_match, address_string)
    try:
        cleaned = usaddress.tag(clean(address_string), tag_mapping=osm_mapping)[0]
        removed = []
    except usaddress.RepeatedLabelError as e:
        collapsed = collapse_list([(i[0].strip(" .,#"), i[1]) for i in e.parsed_string])
        cleaned, removed = _manual_join(_combine_consecutive_tuples(collapsed))

    for toss in toss_tags:
        cleaned.pop(toss, None)

    if "addr:housenumber" in cleaned:
        suite = regex.match(r"([0-9]+)[- \/]?([a-zA-Z]+)", cleaned["addr:housenumber"])
        if suite:
            cleaned["addr:housenumber"] = suite.group(1)
            if "addr:unit" not in cleaned:
                cleaned["addr:unit"] = suite.group(2).upper()
            else:
                if cleaned["addr:unit"] != suite.group(2).upper():
                    cleaned.pop("addr:unit")
                    removed += ["addr:unit"]

    if "addr:street" in cleaned:
        street = abbrs(cleaned["addr:street"])
        cleaned["addr:street"] = street_comp.sub(
            "Street",
            street,
        ).strip(".")

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

    return cleaned, removed


def get_phone(phone: str) -> str:
    """Format phone numbers to the US and Canadian standard format of `+1 XXX-XXX-XXXX`.

    ```python
    >> get_phone("2029009019")
    # "+1 202-900-9019"
    >> get_phone("(202) 900-9019")
    # "+1 202-900-9019"
    >> get_phone("202-900-901")
    # ValueError: Invalid phone number: 202-900-901
    ```

    Args:
        phone (str): The phone number to format.

    Returns:
        str: The formatted phone number.

    Raises:
        ValueError: If the phone number is invalid.
    """
    phone_valid = regex.search(
        r"^\(?(?:\+? ?1?[ -.]*)?(?:\(?(\d{3})\)?[ -.]*)(\d{3})[ -.]*(\d{4})$",
        phone,
    )
    if phone_valid:
        return (
            f"+1 {phone_valid.group(1)}-{phone_valid.group(2)}-{phone_valid.group(3)}"
        )
    raise ValueError(f"Invalid phone number: {phone}")
