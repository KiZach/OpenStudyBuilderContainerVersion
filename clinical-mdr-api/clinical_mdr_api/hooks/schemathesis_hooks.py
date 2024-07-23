import os

import schemathesis

STUDY_UID = os.getenv("SCHEMATHESIS_STUDY_UID", "0")


def is_in_range(val):
    """Temporarily filter out all characters outside of 0x20...0xFFFF range"""
    val = str(val)
    return all(0x20 <= ord(char) <= 0xFFFF for char in val)


def is_desired_header(headers: dict) -> bool:
    """
    Returns True if all headers are within range.

    Args:
        headers (dict): The headers to check.

    Returns:
        bool: True if all headers are within range, False otherwise.
    """
    if headers:
        for name, value in headers.items():
            if not is_in_range(name) or not is_in_range(value):
                return False
    return True


@schemathesis.hooks.register
def before_generate_headers(
    _context: schemathesis.hooks.HookContext,
    strategy: schemathesis.hooks.st.SearchStrategy,
):
    return strategy.filter(is_desired_header)


@schemathesis.hooks.register
def before_generate_case(
    context: schemathesis.hooks.HookContext,
    strategy: schemathesis.hooks.st.SearchStrategy,
):
    op = context.operation

    def tune_case(case: schemathesis.models.Case):
        # Replace study uid path param with value supplied inside STUDY_UID env variable
        if (
            str(op.method).upper() == "GET"
            and str(op.path).startswith("/studies/{uid}/")
            and case.path_parameters["uid"] == "0"
        ):
            case.path_parameters["uid"] = STUDY_UID

        # If any character inside a query parameter needs more than 2 bytes to be UTF-8 encoded,
        # replace it with dummy string
        if case.query:
            for key, value in case.query.items():
                if not is_in_range(value):
                    print(f"\nQuery param: {key}: {value} is not a 2-byte utf-8!")
                    case.query[key] = "blabla"

        return case

    return strategy.map(tune_case)
