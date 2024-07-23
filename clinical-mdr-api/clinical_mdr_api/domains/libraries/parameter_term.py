from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api import exceptions
from clinical_mdr_api.domains._utils import extract_parameters


@dataclass(frozen=True)
class ParameterTermVO:
    uid: str


@dataclass(frozen=True)
class SimpleParameterTermVO(ParameterTermVO):
    """
    Value object representing single parameter term - a pair of (name, uid)
    """

    value: str

    @classmethod
    def from_repository_values(cls, *, uid: str, value: str) -> Self:
        return cls(uid=uid, value=value)

    @classmethod
    def from_input_values(
        cls,
        *,
        uid: str,
        parameter_term_by_uid_lookup_callback: Callable[[str], str | None]
        | None = None,
        value: str | None = None,
    ) -> Self:
        if value is None:
            if parameter_term_by_uid_lookup_callback is None:
                raise exceptions.ValidationException(
                    "parameter_term_by_uid_lookup_callback is required when value is None"
                )
            value = parameter_term_by_uid_lookup_callback(uid)
            if value is None:
                raise exceptions.ValidationException(
                    # f"Unknown template parameter uid ({uid})."
                    "One or more of the specified template parameters can not be found."
                )
        return cls(uid=uid, value=value)


@dataclass(frozen=True)
class NumericParameterTermVO(SimpleParameterTermVO):
    value: float

    @classmethod
    def from_input_values(cls, *, uid: str, value: float) -> Self:
        return cls(uid=uid, value=value)


@dataclass(frozen=True)
class ComplexParameterTerm(ParameterTermVO):
    parameters: list[SimpleParameterTermVO]
    parameter_template: str
    conjunction: str = ""

    @property
    def value(self):
        val = self.parameter_template
        for i, param in enumerate(extract_parameters(self.parameter_template)):
            val = val.replace(f"[{param}]", str(self.parameters[i].value))
        return val


@dataclass(frozen=True)
class ParameterTermEntryVO:
    """
    Value Object representing a set of single parameter terms entered into template
    placeholder. Contains parameter name, a conjunction  and list of parameter
    values to be combined into resulting name.
    """

    parameters: list[ParameterTermVO]
    conjunction: str
    parameter_name: str

    @classmethod
    def from_repository_values(
        cls,
        *,
        parameter_name: str,
        parameters: list[ParameterTermVO],
        conjunction: str,
    ) -> Self:
        return cls(
            parameter_name=parameter_name,
            parameters=tuple(parameters),
            conjunction=conjunction,
        )

    @classmethod
    def from_input_values(
        cls,
        *,
        parameter_name: str,
        parameters: list[ParameterTermVO],
        conjunction: str,
        parameter_exists_callback: Callable[[str], bool],
        parameter_term_uid_exists_for_parameter_callback: Callable[[str, str], bool],
        conjunction_exists_callback: Callable[[str], bool],
    ) -> Self:
        if not parameter_exists_callback(parameter_name):
            raise exceptions.ValidationException(
                f"Unknown parameter name: {parameter_name}"
            )

        for parameter_term in parameters:
            if not parameter_term_uid_exists_for_parameter_callback(
                parameter_name, parameter_term.uid, parameter_term.value
            ):
                raise exceptions.ValidationException(
                    f"Parameter term {parameter_term.uid} ('{parameter_term.value}') not valid for"
                    f" parameter '{parameter_name}'"
                )

        if not conjunction_exists_callback(conjunction):
            raise exceptions.ValidationException(f"Unknown conjunction: {conjunction}")

        return cls(
            parameter_name=parameter_name,
            conjunction=conjunction,
            parameters=tuple(parameters),
        )
