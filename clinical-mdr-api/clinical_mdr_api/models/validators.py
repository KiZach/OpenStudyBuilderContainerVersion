"""Reusable pydantic validator functions"""
import re

from clinical_mdr_api.exceptions import ValidationException

FLOAT_REGEX = "^[0-9]+\\.?[0-9]*$"


# pylint: disable=unused-argument
def validate_string_represents_boolean(cls, value, values, field):
    """
    Validates whether a string value represents a boolean value.

    Args:
        cls: The class to which the field belongs.
        value: The value to validate.
        values: The values of all the fields.
        field: The field to validate.

    Returns:
        str: The validated value.

    Raises:
        ValidationException: If the value does not represent a boolean value.
    """
    if not value:
        return "false"

    truthy = ("y", "yes", "t", "true", "on", "1")
    falsy = ("n", "no", "f", "false", "off", "0")

    if value.lower() not in (truthy + falsy):
        raise ValidationException(
            f"Unsupported boolean value '{value}' for field '{field.name}'. Allowed values are: {truthy + falsy}."
        )

    return value


def validate_name_only_contains_letters(cls, value, values, field):
    """
    Validates whether a string value contains only letters.

    Args:
        cls: The class to which the field belongs.
        value: The value to validate.
        values: The values of all the fields.
        field: The field to validate.

    Returns:
        str: The validated value.

    Raises:
        ValueError: If the value contains characters other than letters.
    """
    if re.search("[^a-zA-Z]", value):
        raise ValueError(
            f"Provided value '{value}' for '{field.name}' is invalid. Must only contain letters."
        )
    return value


def validate_regex(cls, value, values, field):
    """
    Validates whether a string value is a valid regular expression.

    Args:
        cls: The class to which the field belongs.
        value: The value to validate.
        values: The values of all the fields.
        field: The field to validate.

    Returns:
        str: The validated regular expression.

    Raises:
        ValueError: If the value is not a valid regular expression.
    """
    if value:
        try:
            re.compile(value)
            return value
        except re.error as exc:
            raise ValueError(
                f"Provided regex value ({value}) for field '{field.name}' is invalid."
            ) from exc
    return value
