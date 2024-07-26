# python3.12 -m pytest tests/*

import pytest
from src.atlus.atlus import *


def test_get_title():
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


def test_us_replace():
    """Test cases for us_replace"""
    assert us_replace("U.S. Route 15") == "US Route 15"
    assert us_replace("Traveling on U. S. Highway") == "Traveling on US Highway"
    assert us_replace("U S Route is the best") == "US Route is the best"
    assert us_replace("This is the US") == "This is the US"  # No change expected
    assert us_replace("United States") == "United States"  # No change expected


def test_mc_replace():
    """Test cases for mc_replace"""
    assert mc_replace("Fort Mchenry") == "Fort McHenry"
    assert mc_replace("Mcmaster is a great leader") == "McMaster is a great leader"
    assert mc_replace("Mcdonald's is popular") == "McDonald's is popular"
    assert mc_replace("I like the Mcflurry") == "I like the McFlurry"
    assert (
        mc_replace("No Mc in this string") == "No Mc in this string"
    )  # No change expected


def test_ord_replace():
    """Test cases for ord_replace"""
    assert ord_replace("December 4Th") == "December 4th"
    assert ord_replace("3Rd St. NW") == "3rd St. NW"
    assert ord_replace("1St of May") == "1st of May"


def test_street_expand():
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


def test_name_expand():
    """Test name cases for name_street_expand"""

    assert (
        abbr_join_comp.sub(
            name_street_expand,
            "Intl Dr.",
        )
        == "International Drive"
    )


def test_direct_expand():
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


def test_replace_br_tags():
    """Test cases to replace br tags"""
    assert clean("Hello<br/>World") == "Hello,World"
    assert clean("Hello<br />World") == "Hello,World"


def test_remove_unicode():
    """Test cases for remove unicode"""
    assert clean("Hello\u2014World") == "HelloWorld"  # \u2014 is an em dash
    assert clean("Café") == "Caf"


def test_ascii_only():
    """Test cases for ascii only"""
    assert clean("Hello, World!") == "Hello, World!"


def test_mixed_content():
    """Test cases for mixed content"""
    assert clean("Hello<br/>World\u2014Café") == "Hello,WorldCaf"


def test_empty_string():
    """Test cases for empty string"""
    assert clean("") == ""


def test_basic_join():
    """Test cases for basic join"""
    tags = {"street": "Main St", "city": "Springfield", "zip": "12345"}
    keep = ["street", "city"]
    assert help_join(tags, keep) == "Main St Springfield"


def test_keep_all():
    """Test cases for keep all"""
    tags = {"street": "Main St", "city": "Springfield", "zip": "12345"}
    keep = ["street", "city", "zip"]
    assert help_join(tags, keep) == "Main St Springfield 12345"


def test_keep_none():
    """Test cases for keep none"""
    tags = {"street": "Main St", "city": "Springfield", "zip": "12345"}
    keep = []
    assert help_join(tags, keep) == ""


def test_some_missing():
    """Test cases for some missing keys"""
    tags = {"street": "Main St", "city": "Springfield"}
    keep = ["street", "city", "zip"]
    assert help_join(tags, keep) == "Main St Springfield"


def test_no_matching_keys():
    """Test cases for no matching keys"""
    tags = {"street": "Main St", "city": "Springfield"}
    keep = ["zip"]
    assert help_join(tags, keep) == ""


def test_empty_tags():
    """Test cases for empty tags"""
    tags = {}
    keep = ["street", "city"]
    assert help_join(tags, keep) == ""


def test_non_existent_keys():
    """Test cases for non-existent keys"""
    tags = {"street": "Main St", "city": "Springfield", "zip": "12345"}
    keep = ["country", "state"]
    assert help_join(tags, keep) == ""


def test_remove_duplicates():
    """Test cases for remove duplicates"""
    assert collapse_list(["foo", "bar", "foo"]) == ["foo", "bar"]


def test_no_duplicates():
    """Test cases for no duplicates"""
    assert collapse_list(["foo", "bar", "baz"]) == ["foo", "bar", "baz"]


def test_empty_list():
    """Test cases for empty list"""
    assert collapse_list([]) == []


def test_all_duplicates():
    """Test cases for all duplicates"""
    assert collapse_list(["foo", "foo", "foo"]) == ["foo"]


def test_mixed_duplicates():
    """Test cases for mixed duplicates"""
    assert collapse_list(["foo", "bar", "baz", "foo", "bar"]) == ["foo", "bar", "baz"]


def test_complex_data_types():
    """Test cases for complex data types"""
    assert collapse_list([1, 2, 1, 3, 4, 2, 5]) == [1, 2, 3, 4, 5]
    assert collapse_list([(1, 2), (1, 2), (2, 3)]) == [(1, 2), (2, 3)]
    assert collapse_list([1, "1", 1, "1"]) == [1, "1"]


def test_get_address():
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


def test_get_address_removed():
    """Test cases for get address"""
    add = get_address("222 NW Pineapple Ave Suite A Unit B, Beachville, SC 75309")
    assert add[0] == {
        "addr:housenumber": "222",
        "addr:street": "Northwest Pineapple Avenue",
        "addr:city": "Beachville",
        "addr:state": "SC",
        "addr:postcode": "75309",
    }
    assert add[1] == ["addr:unit"]
    # add = get_address("158 S. Thomas Court 30008 90210")
    # assert add[0] == {
    #     "addr:housenumber": "158",
    #     "addr:street": "South Thomas Court",
    # }
    # assert add[1] == ["addr:postcode"]


def test_valid_phone_number_1():
    """Test cases for valid phone numbers"""
    assert get_phone("2029009019") == "+1 202-900-9019"
    assert get_phone("(202) 900-9019") == "+1 202-900-9019"
    assert get_phone("202-900-9019") == "+1 202-900-9019"
    assert get_phone("+1 202 900 9019") == "+1 202-900-9019"
    assert get_phone("+1 (202) 900-9019") == "+1 202-900-9019"


def test_invalid_phone_number_1():
    """Test cases for invalid phone numbers"""
    with pytest.raises(ValueError, match="Invalid phone number: 202-900-901"):
        get_phone("202-900-901")


def test_invalid_phone_number_2():
    """Test cases for invalid phone numbers"""
    with pytest.raises(ValueError, match="Invalid phone number: abc-def-ghij"):
        get_phone("abc-def-ghij")


def test_invalid_phone_number_3():
    """Test cases for invalid phone numbers"""
    with pytest.raises(ValueError, match="Invalid phone number: 12345"):
        get_phone("12345")


def test_invalid_phone_number_4():
    """Test cases for blank phone numbers"""
    with pytest.raises(ValueError, match="Invalid phone number: "):
        get_phone("")
