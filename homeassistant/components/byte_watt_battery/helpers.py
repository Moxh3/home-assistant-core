"""Utility functions."""

import hashlib
import time


def generate_auth_timestamp() -> int:
    """Calculate the timestamp."""
    return int(time.time())


def generate_auth_signature(timestamp) -> str:
    """Calculate the authentication signature."""
    # Constants from the original code
    r = "LS885ZYDA95JV"
    a = "FQKUIUUUV7PQNODZ"
    A = "RDZIS4ERRED"
    i = "S0EED8BCWSS"

    # Construct the string to hash
    auth_string = r + a + A + i + str(timestamp)

    # Calculate SHA512 hash
    hash_object = hashlib.sha512(auth_string.encode())
    hash_hex = hash_object.hexdigest()

    # Construct the final authsignature
    return "al8e4s" + hash_hex + "ui893ed"
