"""Functions and tools to process the raw address strings."""

import regex
from pydantic import ValidationError

from .objects import Address
from .resources import (
    MAX_STATE_WORDS,
    abbr_expansions,
    abbr_join_comp,  # noqa: F401  re-exported to pair with `name_street_expand`
    abbr_word_comp,
    br_comp,
    bracket_comp,
    ca_post_comp,
    cap_comp,
    dir_fill_comp,
    direction_expand,
    direction_tokens,
    grid_comp,
    hash_unit_comp,
    housenumber_comp,
    line_break_comp,
    name_expand,
    occ_comp,
    ord_comp,
    paren_comp,
    period_comp,
    phone_comp,
    po_box_comp,
    post_comp,
    post_sep_comp,
    saint_comp,
    separator_comp,
    sr_comp,
    state_codes,
    state_expand,
    street_comp,
    street_expand,
    street_suffixes,
    unicode_comp,
    us_post_comp,
    usa_comp,
)

ADDRESS_FIELDS = [
    "addr:housenumber",
    "addr:street",
    "addr:unit",
    "addr:city",
    "addr:state",
    "addr:postcode",
]
"""The OSM address tags that `get_address` can return, in output order."""


def get_title(value: str, single_word: bool = False) -> str:
    """Fix ALL-CAPS string.

    ```python
    >>> get_title("PALM BEACH")
    "Palm Beach"
    >>> get_title("BOSTON")
    "BOSTON"
    >>> get_title("BOSTON", single_word=True)
    "Boston"
    >>> get_title("KING'S BEACH")
    "King's Beach"
    ```

    Args:
        value: String to fix.
        single_word: Whether the string should be fixed even if it is a single word.

    Returns:
        str: Fixed string.
    """
    if (value.isupper() and " " in value) or (value.isupper() and single_word):
        return mc_replace(" ".join(x.capitalize() for x in value.split()))
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
    return ord_comp.sub(lower_match, value)


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


def _expand_word(match: regex.Match) -> str:
    """Expand a matched word if it is a known abbreviation, else leave it alone.

    Args:
        match (regex.Match): Matched word.

    Returns:
        str: The expanded abbreviation, or the original text.
    """
    expanded = abbr_expansions.get(match.group(1).upper().rstrip("."))
    return expanded if expanded else match.group(0)


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
    >>> abbrs("E Sewell Rd")
    "East Sewell Road"
    ```

    Note that `St` is left alone here, since it is ambiguous between `Saint`
    and `Street` outside a known saint name. `_process_street` resolves it
    once the token's position in the address is known.

    Args:
        value (str): String to expand.

    Returns:
        str: Expanded string.
    """
    value = ord_replace(us_replace(mc_replace(get_title(value))))

    # change likely 'St' to 'Saint'
    value = saint_comp.sub("Saint", value)

    # expand common street and word abbreviations
    value = abbr_word_comp.sub(_expand_word, value)

    # expand directionals
    value = dir_fill_comp.sub(direct_expand, value)

    # normalize 'US'
    value = us_replace(value)

    # uppercase shortened street descriptors
    value = cap_comp.sub(cap_match, value)

    # remove unremoved abbr periods
    if "." in value:
        value = period_comp.sub(r"\1", value)

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
    if "<br" in old:
        old = br_comp.sub(",", old)
    # the pattern only ever matches code points above 0x7F
    if not old.isascii():
        old = unicode_comp.sub("", old)
    return old


def clean_address(address_string: str) -> str:
    """Clean the input string before sending to parser by removing newlines and unicode.

    Args:
        address_string (str): String to clean.

    Returns:
        str: Cleaned string.
    """
    address_string = remove_br_unicode(address_string)

    # treat line breaks as field separators
    if "\n" in address_string or "\r" in address_string or "\t" in address_string:
        address_string = line_break_comp.sub(", ", address_string)

    # drop parenthetical asides, but keep bracketed content
    if "(" in address_string:
        address_string = paren_comp.sub("", address_string)
    if "[" in address_string or "{" in address_string:
        address_string = bracket_comp.sub(" ", address_string)

    # collapse whitespace before matching country names
    address_string = " ".join(address_string.split()).strip(" ,.")
    if (
        "US" in address_string
        or "United" in address_string
        or "Canada" in address_string
    ):
        address_string = usa_comp.sub("", address_string)

    # normalize the separators left behind by the removals above
    if "," in address_string:
        address_string = separator_comp.sub(", ", address_string)
    address_string = grid_comp.sub(grid_match, address_string)
    return address_string.strip(" ,.;")


def help_join(tags, keep: list[str]) -> str:
    """Help to join address fields."""
    tag_join: list[str] = [v for k, v in tags.items() if k in keep]
    return " ".join(tag_join)


def peel_postcode(address_string: str) -> tuple[list[str], str]:
    """Peel every trailing postal code off the end of the string.

    Repeatedly matches the tail so that a string carrying more than one
    postcode reports all of them; the caller treats that as ambiguous.

    ```python
    >>> peel_postcode("345 Maple Rd, Countryside PA 24680-0198")
    (["24680-0198"], "345 Maple Rd, Countryside PA")
    ```

    Args:
        address_string (str): The string to peel from.

    Returns:
        tuple[list[str], str]: The postcodes found and the remaining string.
    """
    found: list[str] = []
    rest = address_string

    # the two formats are disjoint, so the cheaper and far more common US
    # pattern is tried first
    while rest:
        match = us_post_comp.search(rest)
        if match:
            plus_four = match.group(2)
            found.append(
                f"{match.group(1)}-{plus_four}" if plus_four else match.group(1)
            )
            rest = rest[: match.start(1)].strip(" ,.")
            continue

        match = ca_post_comp.search(rest)
        if match:
            found.append(f"{match.group(1)} {match.group(2)}".upper())
            rest = rest[: match.start(1)].strip(" ,.")
            continue

        break

    return found, rest


def peel_unit(address_string: str) -> tuple[list[str], str]:
    """Remove every secondary-unit designator from the string.

    ```python
    >>> peel_unit("450 Sutter St Unit B, San Francisco")
    (["B"], "450 Sutter St, San Francisco")
    ```

    Args:
        address_string (str): The string to peel from.

    Returns:
        tuple[list[str], str]: The unit identifiers found and the remaining string.
    """
    found: list[str] = []

    def _collect(match: regex.Match) -> str:
        value = match.group(1)
        if value:
            found.append(value)
        return "," if match.group(0).lstrip().startswith(",") else " "

    rest = occ_comp.sub(_collect, address_string)
    if "#" in rest:
        rest = hash_unit_comp.sub(_collect, rest)
    rest = " ".join(rest.split())
    if "," in rest:
        rest = separator_comp.sub(", ", rest)
    return found, rest.strip(" ,.")


def peel_state(address_string: str) -> tuple[str | None, str]:
    """Peel a trailing state or province off the end of the string.

    A spelled-out name is only taken as a state when something else can still
    serve as the city, so that `"200 Park Ave S, New York"` keeps `New York`
    as the city rather than reading it as the state of the same name.

    ```python
    >>> peel_state("456 Elm Avenue, Portland Oregon")
    ("OR", "456 Elm Avenue, Portland")
    ```

    Args:
        address_string (str): The string to peel from.

    Returns:
        tuple[str | None, str]: The state code, if any, and the remaining string.
    """
    tokens = address_string.strip(" ,.").split()

    for size in range(min(MAX_STATE_WORDS, len(tokens) - 1), 0, -1):
        window = tokens[-size:]

        # a comma inside the window means it straddles a field boundary
        if any("," in token for token in window[:-1]):
            continue

        key = " ".join(window).replace(".", "").replace(",", "").upper()
        code = state_expand.get(key) or (key if key in state_codes else None)
        if not code:
            continue

        head = " ".join(tokens[:-size]).strip(" ,.")
        if not head:
            return None, address_string

        # a spelled-out name ending a comma-free tail is more likely the city
        if key not in state_codes and "," not in head:
            return None, address_string

        return code, head

    return None, address_string


def split_street_city(address_string: str) -> tuple[str, str | None]:
    """Split the remaining string into its street and city parts.

    Prefers the comma structure of the input. Without commas, falls back to
    locating the last street suffix and treating whatever follows it (past any
    trailing directional) as the city.

    ```python
    >>> split_street_city("999 River Road, Boulder")
    ("999 River Road", "Boulder")
    >>> split_street_city("555 South Michigan Avenue")
    ("555 South Michigan Avenue", None)
    ```

    Args:
        address_string (str): The string to split.

    Returns:
        tuple[str, str | None]: The street part and the city, if any.
    """
    parts = [part.strip() for part in address_string.split(",") if part.strip()]
    if not parts:
        return "", None
    if len(parts) > 1:
        return " ".join(parts[:-1]), parts[-1]

    tokens = parts[0].split()
    suffixes = [
        index
        for index, token in enumerate(tokens)
        if token.upper().strip(".") in street_suffixes
    ]
    if not suffixes or suffixes[-1] >= len(tokens) - 1:
        return parts[0], None

    cut = suffixes[-1] + 1
    if tokens[cut].upper().strip(".") in direction_tokens:
        cut += 1
    if cut >= len(tokens):
        return parts[0], None

    return " ".join(tokens[:cut]), " ".join(tokens[cut:])


def peel_housenumber(street_string: str) -> tuple[str | None, str]:
    """Peel a leading house number off the street part.

    ```python
    >>> peel_housenumber("1200-29 North Spring Street")
    ("1200-29", "North Spring Street")
    ```

    Args:
        street_string (str): The street part to peel from.

    Returns:
        tuple[str | None, str]: The house number, if any, and the street name.
    """
    match = housenumber_comp.match(street_string.strip())
    if not match:
        return None, street_string.strip()
    return match.group(1), street_string.strip()[match.end() :].strip(" ,.")


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


def _process_housenumber(value: str) -> dict[str, str]:
    """Split house number and unit if needed."""
    return split_unit(value)


def _process_street(value: str) -> str:
    """Normalize street name."""
    street = abbrs(get_title(value, single_word=True))
    return street_comp.sub("Street", street).strip(".")


def _process_city(value: str) -> str:
    """Normalize city name."""
    return abbrs(get_title(value, single_word=True))


def _process_state(value: str) -> str:
    """Normalize state code or name."""
    normalized = value.replace(".", "").upper()

    # Try direct lookup in expansion map (e.g., "PENN" -> "PA")
    if normalized.upper() in state_expand:
        return state_expand[normalized.upper()]

    # Check if already a valid 2-letter state code
    if len(normalized) == 2 and normalized in state_expand.values():
        return normalized

    return value  # Return original if no match


def _process_unit(value: str) -> str:
    """Normalize unit designation."""
    return value.removeprefix("Space").strip(" #.")


def _process_postcode(value: str) -> str:
    """Normalize postal code format."""
    value = value.strip()

    canadian = ca_post_comp.search(value)
    if canadian:
        return f"{canadian.group(1)} {canadian.group(2)}".upper()

    # any separator between the ZIP and the +4 is normalized to a dash
    value = post_sep_comp.sub("-", value)
    return post_comp.sub(r"\1", value)


def _apply_field_processors(cleaned: dict[str, str]) -> dict[str, str]:
    """Apply specialized processors to address fields."""
    processors = {
        "addr:housenumber": _process_housenumber,
        "addr:street": _process_street,
        "addr:city": _process_city,
        "addr:state": _process_state,
        "addr:unit": _process_unit,
        "addr:postcode": _process_postcode,
    }

    result = dict(cleaned)

    for field, processor in processors.items():
        if field in result:
            processed = processor(result[field])
            # Handle housenumber which returns a dict to merge
            if isinstance(processed, dict):
                result.update(processed)
            else:
                result[field] = processed

    return result


def _parse_address(address_string: str) -> tuple[dict[str, str], list[str | None]]:
    """Segment an address string into OSM fields.

    Works right to left, peeling the fields whose position is most reliable
    first, so that each anchor shrinks the string the next one searches. A
    field matched more than once is ambiguous: it is dropped and reported.

    Args:
        address_string (str): The address string to segment.

    Returns:
        tuple[dict[str, str], list[str | None]]:
        The raw segments and the fields removed as ambiguous.
    """
    rest = clean_address(address_string)
    if "box" in rest.lower():
        rest = " ".join(po_box_comp.sub(" ", rest).strip(" ,.").split())

    parsed: dict[str, str] = {}
    removed: list[str | None] = []

    postcodes, rest = peel_postcode(rest)
    if len(postcodes) > 1:
        removed.append("addr:postcode")
    elif postcodes:
        parsed["addr:postcode"] = postcodes[0]

    units, rest = peel_unit(rest)
    if len(units) > 1:
        removed.append("addr:unit")
    elif units:
        parsed["addr:unit"] = units[0]

    state, rest = peel_state(rest)
    if state:
        parsed["addr:state"] = state

    street, city = split_street_city(rest)
    housenumber, street = peel_housenumber(street)

    if housenumber:
        parsed["addr:housenumber"] = housenumber
    if street:
        parsed["addr:street"] = street
    if city:
        parsed["addr:city"] = city

    return {key: parsed[key] for key in ADDRESS_FIELDS if key in parsed}, removed


def _validate_and_clean(
    cleaned: dict[str, str], removed: list[str | None]
) -> tuple[dict[str, str], list[str | None]]:
    """Validate address and remove invalid fields."""
    try:
        validated = Address.model_validate(dict(cleaned))
    except ValidationError as err:
        bad_fields = [str(each.get("loc", [])[0]) for each in err.errors()]
        cleaned_ret = dict(cleaned)
        for field in bad_fields:
            cleaned_ret.pop(field, None)
        removed.extend(bad_fields)
        validated = Address.model_validate(cleaned_ret)

    return validated.model_dump(exclude_none=True, by_alias=True), removed


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
    if not address_string.strip().replace("\n", ""):
        raise ValueError("Address string cannot be empty")

    # Segment the address string into fields
    cleaned, removed = _parse_address(address_string)

    # Apply field-specific processors
    cleaned = _apply_field_processors(cleaned)

    # Drop fields that were parsed but came out empty
    cleaned = {key: value for key, value in cleaned.items() if value}

    # Validate and return
    return _validate_and_clean(cleaned, removed)


def get_phone(phone: str) -> str:
    """Format phone numbers to the US and Canadian standard format of `+1-XXX-XXX-XXXX`.

    ```python
    >>> get_phone("2029009019")
    "+1-202-900-9019"
    >>> get_phone("(202) 900-9019")
    "+1-202-900-9019"
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
    phone_valid = phone_comp.search(phone)
    if phone_valid:
        return (
            f"+1-{phone_valid.group(1)}-{phone_valid.group(2)}-{phone_valid.group(3)}"
        )
    raise ValueError(f"Invalid phone number: {phone}")
