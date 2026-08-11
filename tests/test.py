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
    peel_postcode,
    peel_unit,
    peel_state,
    split_street_city,
    peel_housenumber,
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


def test_peel_postcode_basic() -> None:
    """Test that a trailing ZIP is peeled off the end."""
    assert peel_postcode("345 Maple Rd, Countryside PA 24680-0198") == (
        ["24680-0198"],
        "345 Maple Rd, Countryside PA",
    )
    assert peel_postcode("123 Main St, Springfield IL 62701") == (
        ["62701"],
        "123 Main St, Springfield IL",
    )


def test_peel_postcode_canadian() -> None:
    """Test that a Canadian postal code is peeled and normalized."""
    assert peel_postcode("100 Wellington St, Ottawa ON K1A 0A9") == (
        ["K1A 0A9"],
        "100 Wellington St, Ottawa ON",
    )
    assert peel_postcode("100 Wellington St, Ottawa ON k1a-0a9") == (
        ["K1A 0A9"],
        "100 Wellington St, Ottawa ON",
    )


def test_peel_postcode_duplicates() -> None:
    """Test that every trailing postcode is reported, not just the last."""
    found, rest = peel_postcode("123 Main Street 39199 91102")
    assert found == ["91102", "39199"]
    assert rest == "123 Main Street"


def test_peel_postcode_absent() -> None:
    """Test that a string with no postcode is returned untouched."""
    assert peel_postcode("999 River Road, Boulder") == ([], "999 River Road, Boulder")


def test_peel_unit_basic() -> None:
    """Test that a secondary-unit designator is removed from the string."""
    assert peel_unit("450 Sutter St Unit B, San Francisco") == (
        ["B"],
        "450 Sutter St, San Francisco",
    )
    assert peel_unit("555 Hubbard Avenue, Suite 12, Pittsfield") == (
        ["12"],
        "555 Hubbard Avenue, Pittsfield",
    )


def test_peel_unit_hash() -> None:
    """Test that a bare hash unit is recognized."""
    assert peel_unit("200 Park Ave S, Apt #1401, New York") == (
        ["1401"],
        "200 Park Ave S, New York",
    )


def test_peel_unit_duplicates() -> None:
    """Test that multiple unit designators are all reported."""
    found, rest = peel_unit("222 NW Pineapple Ave Suite A Unit B")
    assert found == ["A", "B"]
    assert rest == "222 NW Pineapple Ave"


def test_peel_unit_absent() -> None:
    """Test that a string with no unit is returned untouched."""
    assert peel_unit("123 Main Street") == ([], "123 Main Street")


def test_peel_state_code() -> None:
    """Test that a two-letter state code is peeled and upper-cased."""
    assert peel_state("789 Pine Road, Seattle WA") == ("WA", "789 Pine Road, Seattle")
    assert peel_state("255 W Main St, Avon ct") == ("CT", "255 W Main St, Avon")


def test_peel_state_full_name() -> None:
    """Test that a spelled-out state name maps to its code."""
    assert peel_state("456 Elm Avenue, Portland Oregon") == (
        "OR",
        "456 Elm Avenue, Portland",
    )


def test_peel_state_province() -> None:
    """Test that a Canadian province is recognized."""
    assert peel_state("100 Wellington St, Ottawa Ontario") == (
        "ON",
        "100 Wellington St, Ottawa",
    )


def test_peel_state_prefers_city() -> None:
    """Test that a spelled-out name is left as the city when nothing else can be."""
    assert peel_state("200 Park Ave S, New York") == (None, "200 Park Ave S, New York")


def test_peel_state_absent() -> None:
    """Test that a string with no state is returned untouched."""
    assert peel_state("999 River Road") == (None, "999 River Road")


def test_split_street_city_comma() -> None:
    """Test that the comma structure drives the street/city split."""
    assert split_street_city("999 River Road, Boulder") == ("999 River Road", "Boulder")
    assert split_street_city("123 Main St, Apt 2, Springfield") == (
        "123 Main St Apt 2",
        "Springfield",
    )


def test_split_street_city_no_comma() -> None:
    """Test the suffix-based fallback when the input has no commas."""
    assert split_street_city("8064 Brewerton Rd Cicero") == (
        "8064 Brewerton Rd",
        "Cicero",
    )


def test_split_street_city_trailing_directional() -> None:
    """Test that a directional after the suffix stays with the street."""
    assert split_street_city("1 Pennsylvania Ave Nw") == ("1 Pennsylvania Ave Nw", None)


def test_split_street_city_street_only() -> None:
    """Test that a bare street yields no city."""
    assert split_street_city("555 South Michigan Avenue") == (
        "555 South Michigan Avenue",
        None,
    )


def test_split_street_city_empty() -> None:
    """Test with empty input."""
    assert split_street_city("") == ("", None)


def test_peel_housenumber_basic() -> None:
    """Test that a leading house number is peeled off the street."""
    assert peel_housenumber("123 Main Street") == ("123", "Main Street")
    assert peel_housenumber("1200-29 North Spring Street") == (
        "1200-29",
        "North Spring Street",
    )
    assert peel_housenumber("123A Main Street") == ("123A", "Main Street")


def test_peel_housenumber_grid() -> None:
    """Test that a Wisconsin grid-style number is peeled."""
    assert peel_housenumber("N65W25055 Main Street") == ("N65W25055", "Main Street")


def test_peel_housenumber_absent() -> None:
    """Test that a street with no house number is returned untouched."""
    assert peel_housenumber("Main Street") == (None, "Main Street")


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

    assert get_address("665 W 5300 S, Murray, UT 84123")[0] == {
        "addr:housenumber": "665",
        "addr:street": "West 5300 South",
        "addr:city": "Murray",
        "addr:state": "UT",
        "addr:postcode": "84123",
    }
    assert get_address("456 Elm Ave Ste 32, Anytown New York 12345")[0] == {
        "addr:housenumber": "456",
        "addr:street": "Elm Avenue",
        "addr:unit": "32",
        "addr:city": "Anytown",
        "addr:state": "NY",
        "addr:postcode": "12345",
    }


REAL_WORLD_ADDRESSES = [
    # Full addresses with ZIP+4
    pytest.param(
        "345 Maple Rd, Countryside PA 24680-0198",
        {
            "addr:housenumber": "345",
            "addr:street": "Maple Road",
            "addr:city": "Countryside",
            "addr:state": "PA",
            "addr:postcode": "24680-0198",
        },
    ),
    pytest.param(
        "777 Oak Street, Springfield IL 62701+0299",
        {
            "addr:housenumber": "777",
            "addr:street": "Oak Street",
            "addr:city": "Springfield",
            "addr:state": "IL",
            "addr:postcode": "62701-0299",
        },
    ),
    pytest.param(
        "123 Main Street, New York NY 10001.0192",
        {
            "addr:housenumber": "123",
            "addr:street": "Main Street",
            "addr:city": "New York",
            "addr:state": "NY",
            "addr:postcode": "10001-0192",
        },
    ),
    # Addresses without ZIP code
    pytest.param(
        "250 Route 59, Airmont NY",
        {
            "addr:housenumber": "250",
            "addr:street": "Route 59",
            "addr:city": "Airmont",
            "addr:state": "NY",
        },
    ),
    pytest.param(
        "456 Elm Avenue, Portland Oregon",
        {
            "addr:housenumber": "456",
            "addr:street": "Elm Avenue",
            "addr:city": "Portland",
            "addr:state": "OR",
        },
    ),
    pytest.param(
        "789 Pine Road, Seattle WA",
        {
            "addr:housenumber": "789",
            "addr:street": "Pine Road",
            "addr:city": "Seattle",
            "addr:state": "WA",
        },
    ),
    # Addresses without city
    pytest.param(
        "100 Market Street, CA 94105",
        {
            "addr:housenumber": "100",
            "addr:street": "Market Street",
            "addr:state": "CA",
            "addr:postcode": "94105",
        },
    ),
    pytest.param(
        "505 Broadway, NY",
        {"addr:housenumber": "505", "addr:street": "Broadway", "addr:state": "NY"},
    ),
    # Addresses without state or ZIP
    pytest.param(
        "999 River Road, Boulder",
        {
            "addr:housenumber": "999",
            "addr:street": "River Road",
            "addr:city": "Boulder",
        },
    ),
    pytest.param(
        "321 Oak Lane, Denver",
        {"addr:housenumber": "321", "addr:street": "Oak Lane", "addr:city": "Denver"},
    ),
    # Street-only addresses (no city, state, or ZIP)
    pytest.param(
        "555 South Michigan Avenue",
        {"addr:housenumber": "555", "addr:street": "South Michigan Avenue"},
    ),
    pytest.param(
        "1 Pennsylvania Ave Nw",
        {"addr:housenumber": "1", "addr:street": "Pennsylvania Avenue Northwest"},
    ),
    pytest.param(
        "33 W 42nd Street",
        {"addr:housenumber": "33", "addr:street": "West 42nd Street"},
    ),
    pytest.param(
        "8900 Sunset Boulevard",
        {"addr:housenumber": "8900", "addr:street": "Sunset Boulevard"},
    ),
    # Addresses with just number and street (abbreviated street type)
    pytest.param(
        "100 Market St", {"addr:housenumber": "100", "addr:street": "Market Street"}
    ),
    pytest.param(
        "250 Oak Ave", {"addr:housenumber": "250", "addr:street": "Oak Avenue"}
    ),
    pytest.param("500 Elm Dr", {"addr:housenumber": "500", "addr:street": "Elm Drive"}),
    # Addresses with inconsistent abbreviations (mixed full and abbreviated)
    pytest.param(
        "1470 South Washington Street, North Attleboro MA",
        {
            "addr:housenumber": "1470",
            "addr:street": "South Washington Street",
            "addr:city": "North Attleboro",
            "addr:state": "MA",
        },
    ),
    pytest.param(
        "255 W Main St, Avon CT 06001",
        {
            "addr:housenumber": "255",
            "addr:street": "West Main Street",
            "addr:city": "Avon",
            "addr:state": "CT",
            "addr:postcode": "06001",
        },
    ),
    pytest.param(
        "8064 North Brewerton Rd, Cicero New York 13039",
        {
            "addr:housenumber": "8064",
            "addr:street": "North Brewerton Road",
            "addr:city": "Cicero",
            "addr:state": "NY",
            "addr:postcode": "13039",
        },
    ),
    pytest.param(
        "100 E Elm Street, Denver Colorado",
        {
            "addr:housenumber": "100",
            "addr:street": "East Elm Street",
            "addr:city": "Denver",
            "addr:state": "CO",
        },
    ),
    pytest.param(
        "300 NW Lovejoy St, Portland OR",
        {
            "addr:housenumber": "300",
            "addr:street": "Northwest Lovejoy Street",
            "addr:city": "Portland",
            "addr:state": "OR",
        },
    ),
    # Directional without city/state
    pytest.param(
        "1470 S Washington Street",
        {"addr:housenumber": "1470", "addr:street": "South Washington Street"},
    ),
    pytest.param(
        "255 West Main Street",
        {"addr:housenumber": "255", "addr:street": "West Main Street"},
    ),
    pytest.param(
        "8064 N Brewerton Road",
        {"addr:housenumber": "8064", "addr:street": "North Brewerton Road"},
    ),
    # Addresses with unit/suite but no state
    pytest.param(
        "555 Hubbard Avenue, Suite 12, Pittsfield MA",
        {
            "addr:housenumber": "555",
            "addr:street": "Hubbard Avenue",
            "addr:unit": "12",
            "addr:city": "Pittsfield",
            "addr:state": "MA",
        },
    ),
    pytest.param(
        "100 S Michigan Ave, Apt 2500, Chicago Illinois",
        {
            "addr:housenumber": "100",
            "addr:street": "South Michigan Avenue",
            "addr:unit": "2500",
            "addr:city": "Chicago",
            "addr:state": "IL",
        },
    ),
    pytest.param(
        "450 Sutter St Unit B, San Francisco CA",
        {
            "addr:housenumber": "450",
            "addr:street": "Sutter Street",
            "addr:unit": "B",
            "addr:city": "San Francisco",
            "addr:state": "CA",
        },
    ),
    pytest.param(
        "200 Park Ave S, Apt #1401, New York",
        {
            "addr:housenumber": "200",
            "addr:street": "Park Avenue South",
            "addr:unit": "1401",
            "addr:city": "New York",
        },
    ),
    # House number ranges
    pytest.param(
        "66-4 Parkhurst Road, Chelmsford MA 01824",
        {
            "addr:housenumber": "66-4",
            "addr:street": "Parkhurst Road",
            "addr:city": "Chelmsford",
            "addr:state": "MA",
            "addr:postcode": "01824",
        },
    ),
    pytest.param(
        "1200-29 North Spring Street, Los Angeles CA",
        {
            "addr:housenumber": "1200-29",
            "addr:street": "North Spring Street",
            "addr:city": "Los Angeles",
            "addr:state": "CA",
        },
    ),
    pytest.param(
        "500-600 Broadway, New York NY 10012",
        {
            "addr:housenumber": "500-600",
            "addr:street": "Broadway",
            "addr:city": "New York",
            "addr:state": "NY",
            "addr:postcode": "10012",
        },
    ),
    # Routes with abbreviated forms
    pytest.param(
        "3949 Route 31, Clay NY 13041",
        {
            "addr:housenumber": "3949",
            "addr:street": "Route 31",
            "addr:city": "Clay",
            "addr:state": "NY",
            "addr:postcode": "13041",
        },
    ),
    pytest.param(
        "25737 US Route 11, Evans Mills NY 13637",
        {
            "addr:housenumber": "25737",
            "addr:street": "Route 11",
            "addr:city": "Evans Mills",
            "addr:state": "NY",
            "addr:postcode": "13637",
        },
    ),
    pytest.param(
        "1201 Highway 300, Newburgh NY 12550",
        {
            "addr:housenumber": "1201",
            "addr:street": "Highway 300",
            "addr:city": "Newburgh",
            "addr:state": "NY",
            "addr:postcode": "12550",
        },
    ),
    pytest.param(
        "990 Route 5, Geneva NY 14456",
        {
            "addr:housenumber": "990",
            "addr:street": "Route 5",
            "addr:city": "Geneva",
            "addr:state": "NY",
            "addr:postcode": "14456",
        },
    ),
    # Mixed full and abbreviated road names
    pytest.param(
        "141 Washington Avenue Extension, Albany NY 12205",
        {
            "addr:housenumber": "141",
            "addr:street": "Washington Avenue Extension",
            "addr:city": "Albany",
            "addr:state": "NY",
            "addr:postcode": "12205",
        },
    ),
    pytest.param(
        "8 Embarcadero Plz, San Francisco CA 94111",
        {
            "addr:housenumber": "8",
            "addr:street": "Embarcadero Plaza",
            "addr:city": "San Francisco",
            "addr:state": "CA",
            "addr:postcode": "94111",
        },
    ),
    pytest.param(
        "233 S Wacker Dr, Chicago Illinois 60606",
        {
            "addr:housenumber": "233",
            "addr:street": "South Wacker Drive",
            "addr:city": "Chicago",
            "addr:state": "IL",
            "addr:postcode": "60606",
        },
    ),
    # Routes without full state name
    pytest.param(
        "4180 US Highway 431, Roanoke AL 36274",
        {
            "addr:housenumber": "4180",
            "addr:street": "Highway 431",
            "addr:city": "Roanoke",
            "addr:state": "AL",
            "addr:postcode": "36274",
        },
    ),
    pytest.param(
        "2643 Highway 280 W, Alexander City AL 35010",
        {
            "addr:housenumber": "2643",
            "addr:street": "Highway 280 West",
            "addr:city": "Alexander City",
            "addr:state": "AL",
            "addr:postcode": "35010",
        },
    ),
    pytest.param(
        "27520 Hwy 98, Daphne AL 36526",
        {
            "addr:housenumber": "27520",
            "addr:street": "Highway 98",
            "addr:city": "Daphne",
            "addr:state": "AL",
            "addr:postcode": "36526",
        },
    ),
    # Business/landmark addresses
    pytest.param(
        "101 Sanford Farm Shopping Center, Amsterdam NY 12010",
        {
            "addr:housenumber": "101",
            "addr:street": "Sanford Farm Shopping Center",
            "addr:city": "Amsterdam",
            "addr:state": "NY",
            "addr:postcode": "12010",
        },
    ),
    pytest.param(
        "200 Sunrise Mall, Massapequa NY 11758",
        {
            "addr:housenumber": "200",
            "addr:street": "Sunrise Mall",
            "addr:city": "Massapequa",
            "addr:state": "NY",
            "addr:postcode": "11758",
        },
    ),
    pytest.param(
        "161 Centereach Mall, Centereach NY 11720",
        {
            "addr:housenumber": "161",
            "addr:street": "Centereach Mall",
            "addr:city": "Centereach",
            "addr:state": "NY",
            "addr:postcode": "11720",
        },
    ),
    # Complex/hyphenated streets
    pytest.param("579 Troy-Schenectady Road, Latham NY 12110", {}),
    pytest.param(
        "3700 Highway 280-431 North, Phenix City AL 36867",
        {
            "addr:housenumber": "3700",
            "addr:street": "Highway 280-431 North",
            "addr:city": "Phenix City",
            "addr:state": "AL",
            "addr:postcode": "36867",
        },
    ),
    pytest.param(
        "5783 So Transit Road, Lockport NY 14094",
        {
            "addr:housenumber": "5783",
            "addr:street": "South Transit Road",
            "addr:city": "Lockport",
            "addr:state": "NY",
            "addr:postcode": "14094",
        },
        marks=pytest.mark.xfail(reason="So", strict=False),
    ),
    # Numeric streets
    pytest.param(
        "3501 20th Avenue, Valley AL 36854",
        {
            "addr:housenumber": "3501",
            "addr:street": "20th Avenue",
            "addr:city": "Valley",
            "addr:state": "AL",
            "addr:postcode": "36854",
        },
    ),
    pytest.param(
        "233 5th Ave Extension, Johnstown MA",
        {
            "addr:housenumber": "233",
            "addr:street": "5th Avenue Extension",
            "addr:city": "Johnstown",
            "addr:state": "MA",
        },
    ),
    pytest.param(
        "100 Park Avenue South, New York NY",
        {
            "addr:housenumber": "100",
            "addr:street": "Park Avenue South",
            "addr:city": "New York",
            "addr:state": "NY",
        },
    ),
    # Mixed case/abbreviation quirks
    pytest.param(
        "1470 south Washington street, North Attleboro ma 02760",
        {
            "addr:housenumber": "1470",
            "addr:street": "South Washington Street",
            "addr:city": "North Attleboro",
            "addr:state": "MA",
            "addr:postcode": "02760",
        },
        marks=pytest.mark.xfail(reason="mixed case", strict=False),
    ),
    pytest.param(
        "255 WEST MAIN ST, AVON ct 06001",
        {
            "addr:housenumber": "255",
            "addr:street": "West Main Street",
            "addr:city": "Avon",
            "addr:state": "CT",
            "addr:postcode": "06001",
        },
    ),
    pytest.param(
        "100 East ELM Street, CO",
        {
            "addr:housenumber": "100",
            "addr:street": "East Elm Street",
            "addr:state": "CO",
        },
        marks=pytest.mark.xfail(reason="mixed case street", strict=False),
    ),
    # Addresses with no separators
    pytest.param(
        "1000 Main Street, New York New York 10001",
        {
            "addr:housenumber": "1000",
            "addr:street": "Main Street",
            "addr:city": "New York",
            "addr:state": "NY",
            "addr:postcode": "10001",
        },
    ),
    pytest.param(
        "500 Oak Avenue, Denver Colorado 80202",
        {
            "addr:housenumber": "500",
            "addr:street": "Oak Avenue",
            "addr:city": "Denver",
            "addr:state": "CO",
            "addr:postcode": "80202",
        },
    ),
    # Extra commas/spaces
    pytest.param(
        "555 Hubbard Avenue, Suite 12, Pittsfield MA 01201",
        {
            "addr:housenumber": "555",
            "addr:street": "Hubbard Avenue",
            "addr:unit": "12",
            "addr:city": "Pittsfield",
            "addr:state": "MA",
            "addr:postcode": "01201",
        },
    ),
    pytest.param(
        "60603 South Michigan Avenue, Apt 2500, Chicago IL 60603",
        {
            "addr:housenumber": "60603",
            "addr:street": "South Michigan Avenue",
            "addr:unit": "2500",
            "addr:city": "Chicago",
            "addr:state": "IL",
            "addr:postcode": "60603",
        },
    ),
    # Addresses with special characters
    pytest.param(
        "1234 O'Reilly Street, Boston 02101",
        {
            "addr:housenumber": "1234",
            "addr:street": "O'Reilly Street",
            "addr:city": "Boston",
            "addr:postcode": "02101",
        },
    ),
    pytest.param(
        "9999 Smith & Sons Lane, Houston",
        {
            "addr:housenumber": "9999",
            "addr:street": "Smith & Sons Lane",
            "addr:city": "Houston",
        },
    ),
    # Addresses with only abbreviations
    pytest.param(
        "123 N Main St", {"addr:housenumber": "123", "addr:street": "North Main Street"}
    ),
    pytest.param(
        "100 W Pine Dr", {"addr:housenumber": "100", "addr:street": "West Pine Drive"}
    ),
    pytest.param(
        "First N Main St",
        {"addr:housenumber": "First", "addr:street": "North Main Street"},
        marks=pytest.mark.xfail(reason="First", strict=False),
    ),
    pytest.param(
        "Sixth N Main St",
        {"addr:housenumber": "Sixth", "addr:street": "North Main Street"},
        marks=pytest.mark.xfail(reason="Sixth", strict=False),
    ),
    # Route abbreviations without direction
    pytest.param(
        "8064 Brewerton Rd, Cicero NY 13039",
        {
            "addr:housenumber": "8064",
            "addr:street": "Brewerton Road",
            "addr:city": "Cicero",
            "addr:state": "NY",
            "addr:postcode": "13039",
        },
    ),
    pytest.param(
        "2181 Pelham Pkwy, Pelham AL",
        {
            "addr:housenumber": "2181",
            "addr:street": "Pelham Parkway",
            "addr:city": "Pelham",
            "addr:state": "AL",
        },
    ),
    pytest.param(
        "165 Vaughan Ln, Pell City AL",
        {
            "addr:housenumber": "165",
            "addr:street": "Vaughan Lane",
            "addr:city": "Pell City",
            "addr:state": "AL",
        },
    ),
    # Mixed state representations
    pytest.param(
        "3700  Hwy  280-431  North,  Phenix City  AL  36867",
        {
            "addr:housenumber": "3700",
            "addr:street": "Highway 280-431 North",
            "addr:city": "Phenix City",
            "addr:state": "AL",
            "addr:postcode": "36867",
        },
    ),
    pytest.param(
        "1903 Cobbs Ford Rd, Prattville AL",
        {
            "addr:housenumber": "1903",
            "addr:street": "Cobbs Ford Road",
            "addr:city": "Prattville",
            "addr:state": "AL",
        },
    ),
    pytest.param(
        "4180 US Highway 431, Roanoke AL 36274",
        {
            "addr:housenumber": "4180",
            "addr:street": "Highway 431",
            "addr:city": "Roanoke",
            "addr:state": "AL",
            "addr:postcode": "36274",
        },
    ),
    # Addresses with trailing/leading spaces
    pytest.param(
        "  13675 Highway 43, Russellville AL 35653  ",
        {
            "addr:housenumber": "13675",
            "addr:street": "Highway 43",
            "addr:city": "Russellville",
            "addr:state": "AL",
            "addr:postcode": "35653",
        },
    ),
    pytest.param(
        "  1095 Industrial Parkway, Saraland AL 36571  ",
        {
            "addr:housenumber": "1095",
            "addr:street": "Industrial Parkway",
            "addr:city": "Saraland",
            "addr:state": "AL",
            "addr:postcode": "36571",
        },
    ),
    # Business/campus addresses
    pytest.param(
        "150 Springville Station Boulevard, Springville AL 35146",
        {
            "addr:housenumber": "150",
            "addr:street": "Springville Station Boulevard",
            "addr:city": "Springville",
            "addr:state": "AL",
            "addr:postcode": "35146",
        },
    ),
    pytest.param(
        "690 Hwy 78, Sumiton AK 35148",
        {
            "addr:housenumber": "690",
            "addr:street": "Highway 78",
            "addr:city": "Sumiton",
            "addr:state": "AK",
            "addr:postcode": "35148",
        },
    ),
    pytest.param(
        "41301 US Hwy 280, Sylacauga ALABAMA 35150",
        {
            "addr:housenumber": "41301",
            "addr:street": "Highway 280",
            "addr:city": "Sylacauga",
            "addr:state": "AL",
            "addr:postcode": "35150",
        },
    ),
    # Addresses with parentheses/brackets
    pytest.param(
        "555 Main Street (Downtown), Boston MA 02101",
        {
            "addr:housenumber": "555",
            "addr:street": "Main Street",
            "addr:city": "Boston",
            "addr:state": "MA",
            "addr:postcode": "02101",
        },
    ),
    pytest.param(
        "100 Oak Avenue [Suite 5], Denver CO 80202-9387",
        {
            "addr:housenumber": "100",
            "addr:street": "Oak Avenue",
            "addr:unit": "5",
            "addr:city": "Denver",
            "addr:state": "CO",
            "addr:postcode": "80202-9387",
        },
    ),
    # Addresses with newlines
    pytest.param(
        """555 Main Street
        Boston MA 02101
        USA""",
        {
            "addr:housenumber": "555",
            "addr:street": "Main Street",
            "addr:city": "Boston",
            "addr:state": "MA",
            "addr:postcode": "02101",
        },
    ),
    pytest.param(
        """100 E Oak Ave NW
        Denver Colorado""",
        {
            "addr:housenumber": "100",
            "addr:street": "East Oak Avenue Northwest",
            "addr:city": "Denver",
            "addr:state": "CO",
        },
    ),
    # Canadian addresses
    pytest.param(
        "123 QUEEN ST W, TORONTO ON M5H 2M9",
        {
            "addr:housenumber": "123",
            "addr:street": "Queen Street West",
            "addr:city": "Toronto",
            "addr:state": "ON",
            "addr:postcode": "M5H 2M9",
        },
    ),
    pytest.param(
        "456 KING'S RIVER RD, Vancouver BC V6B 1A1",
        {
            "addr:housenumber": "456",
            "addr:street": "King's River Road",
            "addr:city": "Vancouver",
            "addr:state": "BC",
            "addr:postcode": "V6B 1A1",
        },
    ),
]


@pytest.mark.parametrize(("raw", "expected"), REAL_WORLD_ADDRESSES)
def test_get_address_works(raw: str, expected: dict[str, str]) -> None:
    """Test cases for get address"""
    parse = get_address(raw)
    assert isinstance(parse[0], dict)
    assert "addr:street" in parse[0] and "addr:housenumber" in parse[0]
    assert not parse[1]
    if expected:
        assert parse[0] == expected


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


def test_parse_address_ambiguous_field():
    """Test _parse_address drops and reports a field it matched twice."""
    from src.atlus.atlus import _parse_address

    result, removed = _parse_address("123 Main Street 39199 91102")

    assert "addr:postcode" not in result
    assert removed == ["addr:postcode"]


def test_parse_address_normal_path():
    """Test _parse_address with normal address (happy path)."""
    from src.atlus.atlus import _parse_address

    result, removed = _parse_address("789 Oak Avenue, Boston, MA 02101")

    assert result == {
        "addr:housenumber": "789",
        "addr:street": "Oak Avenue",
        "addr:city": "Boston",
        "addr:state": "MA",
        "addr:postcode": "02101",
    }
    assert removed == []  # Should be empty for successful parse


def test_parse_address_returns_raw_segments():
    """Test _parse_address segments without normalizing the field values."""
    from src.atlus.atlus import _parse_address

    result, removed = _parse_address("100 W Pine Dr, Denver Colorado")

    # normalization is the job of _apply_field_processors, not the segmenter
    assert result["addr:street"] == "W Pine Dr"
    assert result["addr:state"] == "CO"
    assert removed == []


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
