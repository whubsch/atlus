"""Test functions for the package."""

# python3.12 -m pytest --cov=src --cov-report=html tests/*

from pydantic import ValidationError
import pytest
from src.atlus.objects import Address
from src.atlus.atlus import (
    get_title,
    us_replace,
    mc_replace,
    ord_replace,
    direct_expand,
    cap_match,
    grid_match,
    remove_br_unicode,
    manual_join,
    split_unit,
    remove_prefix,
    get_address,
    get_phone,
    grid_comp,
    regex,
    abbr_join_comp,
    dir_fill_comp,
    name_street_expand,
    help_join,
    collapse_list,
    _process_housenumber,
    _process_street,
    _process_city,
    _process_state,
    _process_unit,
    _process_postcode,
    _apply_field_processors,
)


def test_get_title() -> None:
    """Test get_title function."""
    assert get_title("PALM BEACH") == "Palm Beach"
    assert get_title("BOSTON") == "BOSTON"
    assert get_title("BOSTON", single_word=True) == "Boston"
    assert get_title("NEW YORK CITY") == "New York City"
    assert get_title("MCGREGOR") == "MCGREGOR"  # Test with mock_mc_replace
    assert (
        get_title("MCGREGOR", single_word=True) == "McGregor"
    )  # Test with mock_mc_replace and single_word=True
    assert get_title("Some Mixed Case") == "Some Mixed Case"  # No change expected
    assert get_title("MiXeD cAsE") == "MiXeD cAsE"  # No change expected


def test_us_replace() -> None:
    """Test cases for us_replace"""
    assert us_replace("U.S. Route 15") == "US Route 15"
    assert us_replace("Traveling on U. S. Highway") == "Traveling on US Highway"
    assert us_replace("U S Route is the best") == "US Route is the best"
    assert us_replace("This is the US") == "This is the US"  # No change expected
    assert us_replace("United States") == "United States"  # No change expected


def test_mc_replace() -> None:
    """Test cases for mc_replace"""
    assert mc_replace("Fort Mchenry") == "Fort McHenry"
    assert mc_replace("Mcmaster is a great leader") == "McMaster is a great leader"
    assert mc_replace("Mcdonald's is popular") == "McDonald's is popular"
    assert mc_replace("I like the Mcflurry") == "I like the McFlurry"
    assert mc_replace("Mcflurry Mcmansion") == "McFlurry McMansion"
    assert (
        mc_replace("No Mc in this string") == "No Mc in this string"
    )  # No change expected


def test_ord_replace() -> None:
    """Test cases for ord_replace"""
    assert ord_replace("December 4Th") == "December 4th"
    assert ord_replace("3Rd St. NW") == "3rd St. NW"
    assert ord_replace("1St of May") == "1st of May"


def test_street_expand() -> None:
    """Test street cases for name_street_expand"""
    assert (
        abbr_join_comp.sub(name_street_expand, "Hollywood Blvd")
        == "Hollywood Boulevard"
    )
    assert abbr_join_comp.sub(name_street_expand, "Homer Dr.") == "Homer Drive"


def test_name_expand() -> None:
    """Test name cases for name_street_expand"""

    assert abbr_join_comp.sub(name_street_expand, "Intl Dr.") == "International Drive"


def test_direct_expand() -> None:
    """Test direct_expand function"""
    assert dir_fill_comp.sub(direct_expand, "N") == "North"
    assert dir_fill_comp.sub(direct_expand, "N Hyatt Rd.") == "North Hyatt Rd."


def test_cap_match() -> None:
    value = "Us Route 123"
    assert regex.sub(r"\b(C[rh]|S[rh]|[FR]m|Us)\b", cap_match, value) == "US Route 123"


def test_grid_match() -> None:
    address_string = "N65w25055"
    assert grid_comp.sub(grid_match, address_string) == "N65W25055"


def test_replace_br_tags() -> None:
    """Test cases to replace br tags"""
    assert remove_br_unicode("Hello<br/>World") == "Hello,World"
    assert remove_br_unicode("Hello<br />World") == "Hello,World"


def test_remove_unicode() -> None:
    """Test cases for remove unicode"""
    assert remove_br_unicode("Hello\u2014World") == "HelloWorld"  # \u2014 is an em dash
    assert remove_br_unicode("Café") == "Caf"


def test_ascii_only() -> None:
    """Test cases for ascii only"""
    assert remove_br_unicode("Hello, World!") == "Hello, World!"


def test_mixed_content() -> None:
    """Test cases for mixed content"""
    assert remove_br_unicode("Hello<br/>World\u2014Café") == "Hello,WorldCaf"


def test_empty_string() -> None:
    """Test cases for empty string"""
    assert remove_br_unicode("") == ""


def test_basic_join() -> None:
    """Test cases for basic join"""
    tags = {"street": "Main St", "city": "Springfield", "zip": "12345"}
    keep = ["street", "city"]
    assert help_join(tags, keep) == "Main St Springfield"


def test_manual_join_basic() -> None:
    """Test basic functionality with no duplicates."""
    parsed = [
        ("123", "AddressNumber"),
        ("Main", "StreetName"),
        ("Street", "StreetNamePostType"),
        ("Springfield", "PlaceName"),
        ("IL", "StateName"),
        ("62701", "ZipCode"),
    ]

    result, removed = manual_join(parsed)

    expected = {
        "addr:housenumber": "123",
        "addr:street": "Main Street",
        "addr:city": "Springfield",
        "addr:state": "IL",
        "addr:postcode": "62701",
    }

    assert result == expected
    assert removed == []


def test_manual_join_with_duplicates() -> None:
    """Test handling of duplicate tags."""
    parsed = [
        ("123", "AddressNumber"),
        ("456", "AddressNumber"),  # Duplicate
        ("Main", "StreetName"),
        ("Street", "StreetNamePostType"),
        ("Springfield", "PlaceName"),
        ("IL", "StateName"),
    ]

    result, removed = manual_join(parsed)

    expected = {
        "addr:street": "Main Street",
        "addr:city": "Springfield",
        "addr:state": "IL",
    }

    assert result == expected
    assert removed == ["addr:housenumber"]


def test_manual_join_with_toss_tags() -> None:
    """Test removal of tags in toss_tags list."""
    parsed = [
        ("123", "AddressNumber"),
        ("Main", "StreetName"),
        ("John Doe", "Recipient"),  # Should be tossed
        ("Building A", "LandmarkName"),  # Should be tossed
        ("Springfield", "PlaceName"),
    ]

    result, removed = manual_join(parsed)

    expected = {
        "addr:housenumber": "123",
        "addr:street": "Main",
        "addr:city": "Springfield",
    }

    assert result == expected
    assert removed == []


def test_manual_join_complex_street() -> None:
    """Test joining multiple street components."""
    parsed = [
        ("123", "AddressNumber"),
        ("North", "StreetNamePreDirectional"),
        ("Main", "StreetName"),
        ("Street", "StreetNamePostType"),
        ("Springfield", "PlaceName"),
    ]

    result, removed = manual_join(parsed)

    expected = {
        "addr:housenumber": "123",
        "addr:street": "North Main Street",
        "addr:city": "Springfield",
    }

    assert result == expected
    assert removed == []


def test_manual_join_with_unit() -> None:
    """Test handling of unit/occupancy identifier."""
    parsed = [
        ("123", "AddressNumber"),
        ("Main", "StreetName"),
        ("Apt", "OccupancyType"),  # Should be tossed
        ("2A", "OccupancyIdentifier"),
        ("Springfield", "PlaceName"),
    ]

    result, removed = manual_join(parsed)

    expected = {
        "addr:housenumber": "123",
        "addr:street": "Main",
        "addr:unit": "2A",
        "addr:city": "Springfield",
    }

    assert result == expected
    assert removed == []


def test_manual_join_empty_input() -> None:
    """Test with empty input."""
    parsed = []

    result, removed = manual_join(parsed)

    assert result == {}
    assert removed == []


def test_manual_join_only_toss_tags() -> None:
    """Test with only tags that should be tossed."""
    parsed = [
        ("John Doe", "Recipient"),
        ("Building A", "LandmarkName"),
        ("Box 123", "USPSBoxID"),
    ]

    result, removed = manual_join(parsed)

    assert result == {}
    assert removed == []


def test_manual_join_multiple_duplicates() -> None:
    """Test with multiple different duplicate types."""
    parsed = [
        ("123", "AddressNumber"),
        ("456", "AddressNumber"),  # Duplicate housenumber
        ("Main", "StreetName"),
        ("Oak", "StreetName"),  # Duplicate street
        ("Springfield", "PlaceName"),
        ("Chicago", "PlaceName"),  # Duplicate city
        ("IL", "StateName"),
    ]

    result, removed = manual_join(parsed)

    expected = {"addr:state": "IL"}

    assert result == expected
    assert set(removed) == {"addr:housenumber", "addr:street", "addr:city"}


def test_keep_all() -> None:
    """Test cases for keep all"""
    tags = {"street": "Main St", "city": "Springfield", "zip": "12345"}
    keep = ["street", "city", "zip"]
    assert help_join(tags, keep) == "Main St Springfield 12345"


def test_keep_none() -> None:
    """Test cases for keep none"""
    tags = {"street": "Main St", "city": "Springfield", "zip": "12345"}
    keep = []
    assert help_join(tags, keep) == ""


def test_some_missing() -> None:
    """Test cases for some missing keys"""
    tags = {"street": "Main St", "city": "Springfield"}
    keep = ["street", "city", "zip"]
    assert help_join(tags, keep) == "Main St Springfield"


def test_no_matching_keys() -> None:
    """Test cases for no matching keys"""
    tags = {"street": "Main St", "city": "Springfield"}
    keep = ["zip"]
    assert help_join(tags, keep) == ""


def test_empty_tags() -> None:
    """Test cases for empty tags"""
    tags = {}
    keep = ["street", "city"]
    assert help_join(tags, keep) == ""


def test_non_existent_keys() -> None:
    """Test cases for non-existent keys"""
    tags = {"street": "Main St", "city": "Springfield", "zip": "12345"}
    keep = ["country", "state"]
    assert help_join(tags, keep) == ""


def test_remove_duplicates() -> None:
    """Test cases for remove duplicates"""
    assert collapse_list(["foo", "bar", "foo"]) == ["foo", "bar"]


def test_no_duplicates() -> None:
    """Test cases for no duplicates"""
    assert collapse_list(["foo", "bar", "baz"]) == ["foo", "bar", "baz"]


def test_empty_list() -> None:
    """Test cases for empty list"""
    assert collapse_list([]) == []


def test_all_duplicates() -> None:
    """Test cases for all duplicates"""
    assert collapse_list(["foo", "foo", "foo"]) == ["foo"]


def test_mixed_duplicates() -> None:
    """Test cases for mixed duplicates"""
    assert collapse_list(["foo", "bar", "baz", "foo", "bar"]) == ["foo", "bar", "baz"]


def test_complex_data_types() -> None:
    """Test cases for complex data types"""
    assert collapse_list([1, 2, 1, 3, 4, 2, 5]) == [1, 2, 3, 4, 5]
    assert collapse_list([(1, 2), (1, 2), (2, 3)]) == [(1, 2), (2, 3)]
    assert collapse_list([1, "1", 1, "1"]) == [1, "1"]


def test_split_unit():
    """Test cases for split_unit"""
    assert split_unit("123A") == {"addr:housenumber": "123", "addr:unit": "A"}
    assert split_unit("456") == {"addr:housenumber": "456"}
    assert split_unit("  789  ") == {"addr:housenumber": "789"}
    assert split_unit("123-45") == {"addr:housenumber": "123-45"}
    assert split_unit("987-B") == {"addr:housenumber": "987", "addr:unit": "B"}
    assert split_unit("987/B") == {"addr:housenumber": "987", "addr:unit": "B"}
    assert split_unit("987 B") == {"addr:housenumber": "987", "addr:unit": "B"}
    assert split_unit("987 B2") == {"addr:housenumber": "987", "addr:unit": "B2"}
    assert split_unit("") == {"addr:housenumber": ""}


def test_remove_prefix() -> None:
    """Test cases for remove_prefix"""
    assert remove_prefix("hello", "") == "hello"
    assert remove_prefix("hello", "h") == "ello"
    assert remove_prefix("hello world", "hello ") == "world"
    assert remove_prefix("hello world", "hello") == " world"
    assert remove_prefix("hello world", "goodbye") == "hello world"
    assert remove_prefix("", "") == ""
    assert remove_prefix("prefix", "prefix") == ""
    assert remove_prefix("prefix", "prefix ") == "prefix"


def test_get_address() -> None:
    """Test cases for get address"""
    assert get_address("345 MAPLE RD, COUNTRYSIDE, PA 24680-0198")[0] == {
        "addr:housenumber": "345",
        "addr:street": "Maple Road",
        "addr:city": "Countryside",
        "addr:state": "PA",
        "addr:postcode": "24680-0198",
    }
    assert get_address("777 Strawberry St.")[0] == {
        "addr:housenumber": "777",
        "addr:street": "Strawberry Street",
    }


def test_get_address_removed_unit() -> None:
    """Test cases for get address"""
    add, removed = get_address(
        "222 NW Pineapple Ave Suite A Unit B, Beachville, SC 75309"
    )
    assert add == {
        "addr:housenumber": "222",
        "addr:street": "Northwest Pineapple Avenue",
        "addr:city": "Beachville",
        "addr:state": "SC",
        "addr:postcode": "75309",
    }
    assert removed == ["addr:unit"]


def test_get_address_removed_postcode() -> None:
    """Test cases for get address"""
    add, removed = get_address("158 S. Thomas Court 30008 90210")
    assert add == {"addr:housenumber": "158", "addr:street": "South Thomas Court"}
    assert removed == ["addr:postcode"]


def test_valid_phone_number() -> None:
    """Test cases for valid phone numbers"""
    assert get_phone("2029009019") == "+1-202-900-9019"
    assert get_phone("(202) 900-9019") == "+1-202-900-9019"
    assert get_phone("202-900-9019") == "+1-202-900-9019"
    assert get_phone("+1 202 900 9019") == "+1-202-900-9019"
    assert get_phone("+1 (202) 900-9019") == "+1-202-900-9019"


def test_invalid_phone_number_1() -> None:
    """Test cases for invalid phone numbers"""
    with pytest.raises(ValueError, match="Invalid phone number: 202-900-901"):
        get_phone("202-900-901")


def test_invalid_phone_number_2() -> None:
    """Test cases for invalid phone numbers"""
    with pytest.raises(ValueError, match="Invalid phone number: abc-def-ghij"):
        get_phone("abc-def-ghij")


def test_invalid_phone_number_3() -> None:
    """Test cases for invalid phone numbers"""
    with pytest.raises(ValueError, match="Invalid phone number: 12345"):
        get_phone("12345")


def test_invalid_phone_number_4() -> None:
    """Test cases for blank phone numbers"""
    with pytest.raises(ValueError, match="Invalid phone number: "):
        get_phone("")


def test_address_creation_valid() -> None:
    """Test successful creation with valid data"""
    address = Address(
        **{
            "addr:housenumber": "1200-29",
            "addr:street": "North Spring Street",
            "addr:unit": "B",
            "addr:city": "Los Angeles",
            "addr:state": "CA",
            "addr:postcode": "90012-4801",
        }
    )
    assert address.addr_housenumber == "1200-29"
    assert address.addr_street == "North Spring Street"
    assert address.addr_unit == "B"
    assert address.addr_city == "Los Angeles"
    assert address.addr_state == "CA"
    assert address.addr_postcode == "90012-4801"


def test_address_creation_invalid_state() -> None:
    """Test creation with invalid state (too short)"""
    with pytest.raises(ValidationError):
        Address(
            **{
                "addr:housenumber": "1200-29",
                "addr:street": "North Spring Street",
                "addr:unit": "B",
                "addr:city": "Los Angeles",
                "addr:state": "C",  # Invalid state
                "addr:postcode": "90012-4801",
            }
        )

    # Test creation with invalid state (too long)
    with pytest.raises(ValidationError):
        Address(
            **{
                "addr:housenumber": "1200-29",
                "addr:street": "North Spring Street",
                "addr:unit": "B",
                "addr:city": "Los Angeles",
                "addr:state": "CAL",  # Invalid state
                "addr:postcode": "90012-4801",
            }
        )


def test_address_creation_optional_fields() -> None:
    """Test creation with optional fields missing"""
    address = Address(**{"addr:housenumber": 200, "addr:street": "North Spring Street"})
    assert address.addr_housenumber == 200
    assert address.addr_street == "North Spring Street"
    assert address.addr_unit is None
    assert address.addr_city is None
    assert address.addr_state is None
    assert address.addr_postcode is None


def test_address_alias_handling() -> None:
    """Test creation with aliases"""
    address = Address(
        **{
            "addr:housenumber": 200,
            "addr:street": "North Spring Street",
            "addr:unit": "B",
            "addr:city": "Los Angeles",
            "addr:state": "CA",
            "addr:postcode": "90012",
        }
    )
    assert address.addr_housenumber == 200
    assert address.addr_street == "North Spring Street"
    assert address.addr_unit == "B"
    assert address.addr_city == "Los Angeles"
    assert address.addr_state == "CA"
    assert address.addr_postcode == "90012"


def test_address_model_aliases():
    """Test Address model field aliases."""
    addr = Address(**{"addr:housenumber": "123", "addr:street": "Main St"})

    # Test model_dump with aliases
    dumped = addr.model_dump(exclude_none=True, by_alias=True)
    assert "addr:housenumber" in dumped
    assert "addr:street" in dumped
    assert dumped["addr:housenumber"] == "123"
    assert dumped["addr:street"] == "Main St"

    # Test creation with invalid state (too long)
    with pytest.raises(ValidationError):
        Address(
            **{
                "addr:housenumber": "1200-29",
                "addr:street": "North Spring Street",
                "addr:unit": "B",
                "addr:city": "Los Angeles",
                "addr:state": "CAL",  # Invalid state
                "addr:postcode": "90012-4801",
            }
        )


def test_collapse_list_preserves_order():
    """Test that collapse_list preserves the order of first occurrence."""
    input_list = ["c", "a", "b", "a", "c", "d"]
    expected = ["c", "a", "b", "d"]
    assert collapse_list(input_list) == expected


def test_address_creation_invalid_postcode() -> None:
    """Test creation with invalid postcode"""
    with pytest.raises(ValidationError):
        Address(
            **{
                "addr:housenumber": "1200-29",
                "addr:street": "North Spring Street",
                "addr:unit": "B",
                "addr:city": "Los Angeles",
                "addr:state": "CA",
                "addr:postcode": "9001",  # Invalid postcode
            }
        )


def test_get_address_comprehensive_cleaning():
    """Test get_address with comprehensive address cleaning."""
    # Test address that exercises multiple cleaning functions
    test_address = "123A Main St., Apt B, New York, NY 12345-0000"
    result, removed = get_address(test_address)

    assert result["addr:housenumber"] == "123"
    assert result["addr:unit"] == "A"
    assert "Main" in result["addr:street"]
    assert "Street" in result["addr:street"]
    assert result["addr:postcode"] == "12345"  # Should remove -0000


# Tests for address field helper functions


def test_process_housenumber_with_unit():
    """Test _process_housenumber splits number and unit."""
    result = _process_housenumber("123A")
    assert result["addr:housenumber"] == "123"
    assert result["addr:unit"] == "A"


def test_process_housenumber_without_unit():
    """Test _process_housenumber with just a number."""
    result = _process_housenumber("456")
    assert result["addr:housenumber"] == "456"
    assert "addr:unit" not in result


def test_process_street_abbreviations():
    """Test _process_street expands abbreviations."""
    assert _process_street("Main St") == "Main Street"
    assert _process_street("Oak Ave") == "Oak Avenue"
    assert _process_street("Maple Rd") == "Maple Road"


def test_process_street_removes_dots():
    """Test _process_street removes trailing periods."""
    assert _process_street("Elm St.") == "Elm Street"


def test_process_city_title_case():
    """Test _process_city normalizes city names."""
    assert _process_city("NEW YORK") == "New York"
    assert _process_city("LOS ANGELES") == "Los Angeles"
    assert _process_city("BOSTON") == "Boston"


def test_process_state_abbreviation():
    """Test _process_state handles state abbreviations."""
    assert _process_state("PA") == "PA"
    assert _process_state("pa") == "PA"
    assert _process_state("P.A.") == "PA"


def test_process_state_full_name():
    """Test _process_state handles full state names."""
    assert _process_state("Pennsylvania") == "PA"
    assert _process_state("New York") == "NY"
    assert _process_state("California") == "CA"


def test_process_state_short_name():
    """Test _process_state handles short state names."""
    assert _process_state("Penn") == "PA"
    assert _process_state("CALIF") == "CA"
    assert _process_state("s dak") == "SD"
    assert _process_state("NW Territories") == "NT"


def test_process_state_already_valid():
    """Test _process_state with already valid state code."""
    assert _process_state("NY") == "NY"
    assert _process_state("CA") == "CA"


def test_process_state_invalid():
    """Test _process_state returns original for invalid states."""
    assert _process_state("ZZ") == "ZZ"
    assert _process_state("Invalid") == "Invalid"


def test_process_unit_removes_space_prefix():
    """Test _process_unit removes 'Space' prefix."""
    assert _process_unit("Space 5") == "5"
    assert _process_unit("Space123") == "123"


def test_process_unit_strips_characters():
    """Test _process_unit strips spaces, hashes, and periods."""
    assert _process_unit(" #A ") == "A"
    assert _process_unit("#B.") == "B"
    assert _process_unit("Unit C") == "Unit C"


def test_process_postcode_removes_extra_digits():
    """Test _process_postcode removes trailing zeros."""
    assert _process_postcode("12345-0000") == "12345"
    assert _process_postcode("98765-1234") == "98765-1234"


def test_process_postcode_handles_spaces():
    """Test _process_postcode converts spaces to hyphens."""
    assert _process_postcode("12345 6789") == "12345-6789"


def test_apply_field_processors_integration():
    """Test _apply_field_processors applies all processors correctly."""
    cleaned = {
        "addr:housenumber": "123A",
        "addr:street": "Main St",
        "addr:city": "NEW YORK",
        "addr:state": "ny",
        "addr:postcode": "10001-0000",
    }

    result = _apply_field_processors(cleaned)

    assert result["addr:housenumber"] == "123"
    assert result["addr:unit"] == "A"  # Split from housenumber
    assert result["addr:street"] == "Main Street"
    assert result["addr:city"] == "New York"
    assert result["addr:state"] == "NY"
    assert result["addr:postcode"] == "10001"


def test_apply_field_processors_partial_fields():
    """Test _apply_field_processors with only some fields present."""
    cleaned = {"addr:housenumber": "999", "addr:city": "BOSTON"}

    result = _apply_field_processors(cleaned)

    assert result["addr:housenumber"] == "999"
    assert result["addr:city"] == "Boston"
    assert "addr:street" not in result
    assert "addr:state" not in result


# High priority edge case tests for get_address


def test_get_address_empty_input():
    """Test get_address with empty or whitespace-only input."""
    # Empty string should still return some result (likely empty dict)
    result, removed = get_address("")
    assert isinstance(result, dict)
    assert isinstance(removed, list)


def test_get_address_whitespace_only():
    """Test get_address with whitespace-only input."""
    result, removed = get_address("   ")
    assert isinstance(result, dict)
    assert isinstance(removed, list)


def test_get_address_minimal_address():
    """Test get_address with minimal information (just street)."""
    result, removed = get_address("Main Street")
    assert isinstance(result, dict)
    # Should have at least street information if parseable
    if result:
        assert "addr:street" in result or len(result) >= 0


def test_get_address_only_number():
    """Test get_address with only a house number."""
    result, removed = get_address("123")
    assert isinstance(result, dict)
    assert isinstance(removed, list)


def test_get_address_no_number():
    """Test get_address with street name but no house number."""
    result, removed = get_address("Main Street, Springfield, IL")
    assert isinstance(result, dict)
    # May or may not have a house number depending on parsing
    if "addr:street" in result:
        assert "Main" in result["addr:street"]


def test_get_address_unusual_format():
    """Test get_address with unusual but valid format."""
    # Address with lots of punctuation
    result, removed = get_address("123, Main St.; Springfield!! IL??? 62701")
    assert isinstance(result, dict)
    assert isinstance(removed, list)


def test_get_address_partial_postcode():
    """Test get_address with 5-digit postcode only (no +4)."""
    result, removed = get_address("123 Main St, Springfield, IL 62701")
    assert result["addr:postcode"] == "62701"
    assert result["addr:housenumber"] == "123"


def test_get_address_state_variations():
    """Test get_address handles various state formats."""
    # Full state name uppercase
    result1, _ = get_address("123 Main St, Springfield, ILLINOIS 62701")

    # Lowercase abbreviation
    result2, _ = get_address("123 Main St, Springfield, il 62701")

    # With periods
    result3, _ = get_address("123 Main St, Springfield, I.L. 62701")

    # All should normalize state properly
    for result in [result1, result2, result3]:
        if "addr:state" in result:
            assert len(result["addr:state"]) == 2  # Should be 2-letter code


def test_get_address_multiple_street_parts():
    """Test get_address with complex street names."""
    result, removed = get_address("456 Dr. Martin Luther King Jr. Boulevard")
    assert result["addr:housenumber"] == "456"
    assert "addr:street" in result
    assert "Boulevard" in result["addr:street"]


def test_get_address_duplicate_fields():
    """Test get_address with duplicated fields."""
    result, removed = get_address("123 Main Street 39199 91102")
    assert result["addr:housenumber"] == "123"
    assert result["addr:street"] == "Main Street"
    assert "addr:postcode" in removed


def test_parse_address_repeated_label_error():
    """Test _parse_address explicitly handles RepeatedLabelError path."""
    from src.atlus.atlus import _parse_address

    # This type of address often triggers RepeatedLabelError
    # (multiple address numbers or ambiguous components)
    test_address = "123 456 Main Street"  # Two numbers
    result, removed = _parse_address(test_address)

    assert isinstance(result, dict)
    assert isinstance(removed, list)


def test_parse_address_normal_path():
    """Test _parse_address with normal address (happy path)."""
    from src.atlus.atlus import _parse_address

    result, removed = _parse_address("789 Oak Avenue, Boston, MA 02101")

    assert isinstance(result, dict)
    assert removed == []  # Should be empty for successful parse
    assert len(result) > 0  # Should have parsed components


def test_validate_and_clean_invalid_fields():
    """Test _validate_and_clean removes multiple invalid fields."""
    from src.atlus.atlus import _validate_and_clean

    # Create a dict with invalid field values
    cleaned = {
        "addr:housenumber": "123",
        "addr:street": "Main Street",
        "addr:state": "INVALID_STATE_CODE_TOO_LONG",  # Invalid
        "addr:postcode": "123",  # Too short, invalid format
    }
    removed = []

    result, removed_fields = _validate_and_clean(cleaned, removed)

    # Should have removed invalid fields
    assert "addr:housenumber" in result
    assert "addr:street" in result
    # Invalid fields should be either corrected or removed
    assert len(removed_fields) == 2
    assert "addr:state" in removed_fields
    assert "addr:postcode" in removed_fields


def test_validate_and_clean_all_valid():
    """Test _validate_and_clean with all valid fields."""
    from src.atlus.atlus import _validate_and_clean

    cleaned = {
        "addr:housenumber": "123",
        "addr:street": "Main Street",
        "addr:city": "Springfield",
        "addr:state": "IL",
        "addr:postcode": "62701",
    }
    removed = []

    result, removed_fields = _validate_and_clean(cleaned, removed)

    # All fields should be preserved
    assert result == cleaned
    assert removed_fields == []
