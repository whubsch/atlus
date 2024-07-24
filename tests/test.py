from src.atlus.atlus import *


def test_us_replace():
    # Test cases for us_replace
    assert us_replace("U.S. Route 15") == "US Route 15"
    assert us_replace("Traveling on U. S. Highway") == "Traveling on US Highway"
    assert us_replace("U S Route is the best") == "US Route is the best"
    assert us_replace("This is the US") == "This is the US"  # No change expected
    assert us_replace("United States") == "United States"  # No change expected


def test_mc_replace():
    # Test cases for mc_replace
    assert mc_replace("Fort Mchenry") == "Fort McHenry"
    assert mc_replace("Mcmaster is a great leader") == "McMaster is a great leader"
    assert mc_replace("Mcdonald's is popular") == "McDonald's is popular"
    assert mc_replace("I like the Mcflurry") == "I like the McFlurry"
    assert (
        mc_replace("No Mc in this string") == "No Mc in this string"
    )  # No change expected


def test_ord_replace():
    assert ord_replace("December 4Th") == "December 4th"
    assert ord_replace("3Rd St. NW") == "3rd St. NW"


def test_street_expand():
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

    assert (
        abbr_join_comp.sub(
            name_street_expand,
            "Intl Dr.",
        )
        == "International Drive"
    )


# def test_direct_expand():
#     with pytest.raises(ValueError):
#         direct_expand(None)

#     assert direct_expand(regex.match("([NSWE])", "N")) == "North"


# def test_cap_match():
#     assert cap_match(regex.match("(\w+)", "test")) == "TEST"


# Add more tests for other functions in the file
