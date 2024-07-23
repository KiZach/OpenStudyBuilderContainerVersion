import re
from enum import Enum
from typing import Any

from bs4 import BeautifulSoup

from clinical_mdr_api import exceptions
from clinical_mdr_api.domains.iso_languages import LANGUAGES_INDEXED_BY


class ObjectStatus(Enum):
    """
    Enum for object status.

    Possible values:
    - LATEST_FINAL: The latest final version of the object.
    - LATEST_RETIRED: The latest retired version of the object.
    - LATEST_DRAFT: The latest draft version of the object.
    - LATEST: The latest version of the object, regardless of the status.
    """

    LATEST_FINAL = "final"
    LATEST_RETIRED = "retired"
    LATEST_DRAFT = "draft"
    LATEST = "latest"


def get_iso_lang_data(
    query: str,
    key: str = "639-3",
    return_key: str | None = None,
    ignore_case: bool = True,
) -> str | dict[Any] | list[Any]:
    """
    Returns ISO language data based on the provided query string and key.

    Args:
        query (str): Query string to search for in the language index.
        key (str, optional): Key to use for indexing the language data. Defaults to "639-3".
        return_key (str | None, optional): Key to return from the found language data. Defaults to None.
        ignore_case (bool, optional): Whether to ignore case when searching for the query string. Defaults to True.

    Returns:
        str | dict[Any] | list[Any]: The value of the found language data, or the entire language data if return_key is None.

    Raises:
        TypeError: If the query string is not a string.
        ValueError: If the provided key is not a valid index for the language data.
        KeyError: If the query string is not found in the language index, or if it is found but does not match the query when ignore_case is False.

    Example:
        >>> get_iso_lang_data("spa", "639-2/T", "names")
        ["Spanish", "Castilian"]
    """
    if not isinstance(query, str):
        raise TypeError(f"Expected type str but found {type(query)}")

    try:
        index = LANGUAGES_INDEXED_BY[key]
    except KeyError as exc:
        raise exceptions.ValidationException(
            f"Languages not indexed by key: {key}"
        ) from exc

    casefolded_query = query.casefold()

    try:
        lang = index[casefolded_query]
    except KeyError as exc:
        raise KeyError(query) from exc

    if not ignore_case and lang[key] != query:
        raise KeyError(query)

    return lang[return_key] if return_key else lang


def normalize_string(string: str | None) -> str | None:
    """
    Normalizes a string by stripping whitespace and returning None if the resulting string is empty.

    Args:
        string (str | None): The string to normalize.

    Returns:
        str | None: The normalized string, or None if the resulting string is empty.

    Example:
        >>> normalize_string("   hello world   ")
        "hello world"
    """
    if string:
        string = string.strip()
    return string or None


def strip_html(html: str) -> str:
    """
    Removes HTML tags from a string.

    Args:
        html (str): The string containing HTML tags.

    Returns:
        str: The string with HTML tags removed.

    Example:
        >>> strip_html("<p>Some <b>bold</b> text.</p>")
        "Some bold text."
    """
    return BeautifulSoup(html, "lxml").text


def convert_to_plain(text: str) -> str:
    """
    Converts a text with HTML tags and square brackets to plain text.

    Args:
        text (str): The text to convert.

    Returns:
        str: The plain text.

    Example:
        >>> convert_to_plain("<p>Some [text] with <b>HTML</b> tags.</p>")
        "Some text with HTML tags."
    """
    return strip_html(text).replace("[", "").replace("]", "")


def extract_parameters(name: str) -> list[str]:
    """
    Extracts parameters from a string. A parameter is a string that is between two square brackets.

    Args:
        name (str): The string to extract parameters from.

    Returns:
        list[str]: A sequence of parameter names.

    Example:
        >>> extract_parameters("Some [parameter1] and [parameter2]")
        ["parameter1", "parameter2"]
    """
    return re.findall(r"\[([\w\s\-]+)]", name)


def is_syntax_of_template_name_correct(name: str) -> bool:
    """
    Checks the syntax of the name.
    The syntax is considered to be valid if all of the following conditions are true:
    - The name consists of at least one printable character.
    - The name contains no brackets or a matching number of opening and closing brackets [].
    - The name does not contain nested brackets like this: [a[b]c].
    - The parameters within the brackets need to consist of at least one character.

    Args:
        name (str): The name of the template.

    Returns:
        bool: True if the syntax of the name is valid.
    """
    if not isinstance(name, str):
        raise TypeError(f"Expected type str but found {type(name)}")

    if len(name.strip()) == 0:
        return False

    brackets_counter = 0
    char_counter = 0
    for char in name:
        if char == "[":
            brackets_counter += 1
            char_counter = 0
        elif char == "]":
            if char_counter == 0:
                return False
            brackets_counter -= 1
            char_counter = 0
        else:
            char_counter += 1

        if brackets_counter < 0 or brackets_counter > 1:
            return False

    return brackets_counter == 0


def factorize_dict(data: dict) -> dict:
    """
    Factorizes a dictionary by adding underscores to keys that do not start with an underscore.

    Args:
        data (dict): The dictionary to factorize.

    Returns:
        dict: The factorized dictionary.

    Example:
        >>> factorize_dict({"key1": 1, "_key2": 2, "key3": 3})
        {"_key1": 1, "_key2": 2, "_key3": 3}
    """
    return_dict = {}
    for key, value in data.items():
        new_key = key if key.startswith("_") else "_" + key
        return_dict[new_key] = value
    return return_dict


def defactorize_dict(data: dict) -> dict:
    """
    Defactorizes a dictionary by removing underscores from keys that start with an underscore.

    Args:
        data (dict): The dictionary to defactorize.

    Returns:
        dict: The defactorized dictionary.

    Example:
        >>> defactorize_dict({"_key1": 1, "key2": 2, "_key3": 3})
        {"key1": 1, "key2": 2, "key3": 3}
    """
    return_dict = {}
    for key, value in data.items():
        new_key = key[1:] if key.startswith("_") else key
        return_dict[new_key] = value
    return return_dict


def are_floats_equal(float_1: float, float_2: float) -> bool:
    """
    Asserts that two floating point numbers are equal, using the default tolerance.

    Args:
        float_1 (float): The first floating point number.
        float_2 (float): The second floating point number.

    Returns:
        bool: True if the two floating point numbers are equal.
    """
    epsilon = 1e-6
    return abs(float_1 - float_2) < epsilon
