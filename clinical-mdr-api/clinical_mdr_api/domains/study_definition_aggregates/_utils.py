from dataclasses import dataclass
from typing import Callable

from clinical_mdr_api import exceptions


def default_failure_callback_for_variable(variable_name: str) -> Callable[[str], bool]:
    """
    function used to generate produce a default value for some methods arguments in StudyDefinitionAR class
    :param variable_name: A name of the variable which shows up in a message inside a value error exception.
    :return: A Callable[[str],bool] which raises ValeError once called. A Value error says there was no proper
    callback function provided.
    """

    def raise_value_error(msg: str) -> bool:
        raise exceptions.ValidationException(msg)

    return lambda _: raise_value_error(
        f"A proper existence check callback not provided for {variable_name}"
    )


def dataclass_with_default_init(*args, _cls=None, **kwargs):
    def wrap(cls):
        # Save the current __init__ and remove it so dataclass will
        # create the default __init__.
        user_init = getattr(cls, "__init__")
        delattr(cls, "__init__")

        # let dataclass process our class.
        result = dataclass(cls, *args, **kwargs)

        # Restore the user's __init__ save the default init to __default_init__.
        setattr(result, "__default_init__", result.__init__)
        setattr(result, "__init__", user_init)

        # Just in case that dataclass will return a new instance,
        # (currently, does not happen), restore class's __init__.
        if result is not cls:
            setattr(cls, "__init__", user_init)

        return result

    # Support both dataclass_with_default_init() and dataclass_with_default_init
    if _cls is None:
        return wrap
    return wrap(_cls)


def call_default_init(obj, *args, **kwargs) -> None:
    """
    Convenience function to call __default_init__ avoiding static type checking issues.
    """
    getattr(obj, "__default_init__")(*args, **kwargs)
