def strtobool(value: str) -> int:
    """Convert a string representation of truth to integer 1 (true) or 0 (false).

    Returns 1 for True values: 'y', 'yes', 't', 'true', 'on', '1'.
    Returns 0 for False values: 'n', 'no', 'f', 'false', 'off', '0'.
    Otherwise raises ValueError.

    Reimplemented because of deprecation https://peps.python.org/pep-0632/#migration-advice

    Returns int to remain compatible with Python 3.7 distutils.util.strtobool().
    """

    val = value.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return 1
    if val in ("n", "no", "f", "false", "off", "0"):
        return 0
    raise ValueError(f"invalid truth value: {value:s}")


def booltostr(value: bool | str, true_format: str = "Yes") -> str:
    """
    Converts a boolean value to a string representation.
    True values are 'y', 'Yes', 'yes', 't', 'true', 'on', and '1';
    False values are 'n', 'No', 'no', 'f', 'false', 'off', and '0'.

    Args:
        value (bool | str): The boolean value to convert. If a string is passed, it will be converted to a boolean.
        true_format (str, optional): The string representation of the True value. Defaults to "Yes".

    Returns:
        str: The string representation of the boolean value.

    Raises:
        ValueError: If the true_format argument is invalid.
    """
    if isinstance(value, str):
        value = bool(strtobool(value))

    mapping = {
        "y": "n",
        "Yes": "No",
        "yes": "no",
        "t": "f",
        "true": "false",
        "on": "off",
        "1": "0",
    }

    if true_format in mapping:
        if value:
            return true_format
        return mapping[true_format]
    raise ValueError(f"Invalid true format {true_format}")
