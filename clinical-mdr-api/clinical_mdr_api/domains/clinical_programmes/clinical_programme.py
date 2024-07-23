from dataclasses import dataclass, field
from typing import Any, Callable

from clinical_mdr_api.domains._utils import normalize_string


@dataclass
class ClinicalProgrammeAR:
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    _uid: str
    _name: str

    @property
    def uid(self) -> str:
        return self._uid

    @property
    def name(self) -> str:
        return self._name

    @staticmethod
    def from_input_values(name: str, generate_uid_callback: Callable[[], str]):
        uid = generate_uid_callback()

        return ClinicalProgrammeAR(_uid=uid, _name=normalize_string(name))
