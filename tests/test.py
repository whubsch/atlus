"""Test functions for the package."""

# python3.12 -m pytest --cov=src --cov-report=html tests/*

from pydantic import ValidationError
import pytest
from src.atlus.objects import Address
from src.atlus.atlus import *


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
        abbr_join_comp.sub(
            name_street_expand,
            "Hollywood Blvd",
        )
        == "Hollywood Boulevard"
    )
    assert (
        abbr_join_comp.sub(
            name_street_expand,
            "Homer Dr.",
        )
        == "Homer Drive"
    )


def test_name_expand() -> None:
    """Test name cases for name_street_expand"""

    assert (
        abbr_join_comp.sub(
            name_street_expand,
            "Intl Dr.",
        )
        == "International Drive"
    )


def test_direct_expand() -> None:
    """Test direct_expand function"""
    assert (
        dir_fill_comp.sub(
            direct_expand,
            "N",
        )
        == "North"
    )
    assert (
        dir_fill_comp.sub(
            direct_expand,
            "N Hyatt Rd.",
        )
        == "North Hyatt Rd."
    )


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
    assert split_unit("123A") == {
        "addr:housenumber": "123",
        "addr:unit": "A",
    }

    assert split_unit("456") == {"addr:housenumber": "456"}

    assert split_unit("  789  ") == {
        "addr:housenumber": "789",
    }

    assert split_unit("123-45") == {
        "addr:housenumber": "123-45",
    }

    assert split_unit("987-B") == {
        "addr:housenumber": "987",
        "addr:unit": "B",
    }

    assert split_unit("987/B") == {
        "addr:housenumber": "987",
        "addr:unit": "B",
    }

    assert split_unit("987 B") == {
        "addr:housenumber": "987",
        "addr:unit": "B",
    }

    assert split_unit("987 B2") == {
        "addr:housenumber": "987",
        "addr:unit": "B2",
    }

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
    assert add == {
        "addr:housenumber": "158",
        "addr:street": "South Thomas Court",
    }
    assert removed == ["addr:postcode"]


def test_valid_phone_number_1() -> None:
    """Test cases for valid phone numbers"""
    assert get_phone("2029009019") == "+1 202-900-9019"
    assert get_phone("(202) 900-9019") == "+1 202-900-9019"
    assert get_phone("202-900-9019") == "+1 202-900-9019"
    assert get_phone("+1 202 900 9019") == "+1 202-900-9019"
    assert get_phone("+1 (202) 900-9019") == "+1 202-900-9019"


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
