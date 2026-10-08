import pytest

from app.core.address import validate_ethereum_address
from app.core.exceptions import InvalidAddressError

VALID_CHECKSUM = "0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe"
VALID_LOWERCASE = VALID_CHECKSUM.lower()


def test_valid_checksum_address_returned_as_is():
    assert validate_ethereum_address(VALID_CHECKSUM) == VALID_CHECKSUM


def test_valid_lowercase_address_is_checksummed():
    result = validate_ethereum_address(VALID_LOWERCASE)
    assert result == VALID_CHECKSUM


@pytest.mark.parametrize(
    "bad_address",
    [
        "",
        "not-an-address",
        "0x123",  # too short
        "0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAeFF",  # too long
        "de0B295669a9FD93d5F28D9Ec85E40f4cb697BAe",  # missing 0x
    ],
)
def test_invalid_addresses_raise(bad_address):
    with pytest.raises(InvalidAddressError):
        validate_ethereum_address(bad_address)
