"""
Address validation.

Every provider call must be given a validated, checksummed address. This is
the one place that logic lives, so it can't drift between routers.
"""
import re

from eth_utils import is_address, to_checksum_address

from app.core.exceptions import InvalidAddressError

_HEX_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")


def validate_ethereum_address(address: str) -> str:
    """Validate and normalize an Ethereum-style address.

    Returns the EIP-55 checksummed address.
    Raises InvalidAddressError if the address is malformed.
    """
    if not address or not _HEX_ADDRESS_RE.match(address):
        raise InvalidAddressError(
            f"'{address}' is not a valid Ethereum address. "
            "Expected a 42-character 0x-prefixed hex string."
        )

    if not is_address(address):
        raise InvalidAddressError(f"'{address}' failed address validation.")

    return to_checksum_address(address)
