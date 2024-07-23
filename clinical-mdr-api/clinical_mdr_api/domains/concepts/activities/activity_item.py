from dataclasses import dataclass
from typing import Callable, Self

from pydantic import BaseModel

from clinical_mdr_api import exceptions


class LibraryItem(BaseModel):
    uid: str
    name: str | None


@dataclass(frozen=True)
class ActivityItemVO:
    """
    The ActivityItemVO acts as the value object for a single ActivityItem value object
    """

    activity_item_class_uid: str
    activity_item_class_name: str | None
    ct_terms: list[LibraryItem]
    unit_definitions: list[LibraryItem]

    @classmethod
    def from_repository_values(
        cls,
        activity_item_class_uid: str,
        activity_item_class_name: str | None,
        ct_terms: list[dict[str, str]],
        unit_definitions=list[dict[str, str]],
    ) -> Self:
        activity_item_vo = cls(
            activity_item_class_uid=activity_item_class_uid,
            activity_item_class_name=activity_item_class_name,
            ct_terms=ct_terms,
            unit_definitions=unit_definitions,
        )

        return activity_item_vo

    def validate(
        self,
        activity_item_class_exists: Callable[[str], bool],
        ct_term_exists: Callable[[str], bool],
        unit_definition_exists: Callable[[str], bool],
    ) -> None:
        if not activity_item_class_exists(self.activity_item_class_uid):
            raise exceptions.ValidationException(
                f"ActivityItemVO tried to connect to non-existent ActivityItemClass ({self.activity_item_class_uid})."
            )
        for term in self.ct_terms:
            if not ct_term_exists(term.uid):
                raise exceptions.ValidationException(
                    f"ActivityItemVO tried to connect to non-existent or non-final CTTerm ({term.uid})."
                )
        for unit in self.unit_definitions:
            if not unit_definition_exists(unit.uid):
                raise exceptions.ValidationException(
                    f"ActivityItemVO tried to connect to non-existent UnitDefinition ({unit.uid})."
                )
