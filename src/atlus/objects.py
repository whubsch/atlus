"""Define objects for parsing fields."""

from pydantic import BaseModel, Field


class Address(BaseModel):
    """Define address parsing fields."""

    addr_housenumber: int | str | None = Field(
        alias="addr:housenumber",
        description="The house number that is included in the address.",
        examples=[200, "1200-29"],
        default=None,
    )
    addr_street: str | None = Field(
        alias="addr:street",
        description="The street that the address is located on.",
        examples=["North Spring Street"],
        default=None,
    )
    addr_unit: str | None = Field(
        alias="addr:unit",
        description="The unit number or letter that is included in the address.",
        examples=["B"],
        default=None,
    )
    addr_city: str | None = Field(
        alias="addr:city",
        description="The city that the address is located in.",
        examples=["Los Angeles"],
        default=None,
    )
    addr_state: str | None = Field(
        alias="addr:state",
        pattern=r"^[A-Z]{2}$",
        description="The state or territory of the address.",
        examples=["CA"],
        default=None,
    )
    addr_postcode: str | None = Field(
        alias="addr:postcode",
        pattern=r"^\d{5}(?:\-\d{4})?$",
        description="The postal code of the address.",
        examples=["90012", "90012-4801"],
        default=None,
    )
