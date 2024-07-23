from datetime import date
from typing import Callable, Self

from pydantic import BaseModel, Field

from clinical_mdr_api.domains.concepts.odms.form import OdmFormRefVO
from clinical_mdr_api.domains.concepts.odms.study_event import OdmStudyEventAR
from clinical_mdr_api.models.concepts.concept import (
    ConceptModel,
    ConceptPatchInput,
    ConceptPostInput,
)
from clinical_mdr_api.models.concepts.odms.odm_form import OdmFormRefModel


class OdmStudyEvent(ConceptModel):
    oid: str | None = Field(None, nullable=True)
    effective_date: date | None = Field(None, nullable=True)
    retired_date: date | None = Field(None, nullable=True)
    description: str | None = Field(None, nullable=True)
    display_in_tree: bool = True
    forms: list[OdmFormRefModel]
    possible_actions: list[str]

    @classmethod
    def from_odm_study_event_ar(
        cls,
        odm_study_event_ar: OdmStudyEventAR,
        find_odm_form_by_uid_with_study_event_relation: Callable[
            [str, str], OdmFormRefVO | None
        ],
    ) -> Self:
        return cls(
            uid=odm_study_event_ar._uid,
            name=odm_study_event_ar.concept_vo.name,
            oid=odm_study_event_ar.concept_vo.oid,
            effective_date=odm_study_event_ar.concept_vo.effective_date,
            retired_date=odm_study_event_ar.concept_vo.retired_date,
            description=odm_study_event_ar.concept_vo.description,
            display_in_tree=odm_study_event_ar.concept_vo.display_in_tree,
            library_name=odm_study_event_ar.library.name,
            start_date=odm_study_event_ar.item_metadata.start_date,
            end_date=odm_study_event_ar.item_metadata.end_date,
            status=odm_study_event_ar.item_metadata.status.value,
            version=odm_study_event_ar.item_metadata.version,
            change_description=odm_study_event_ar.item_metadata.change_description,
            user_initials=odm_study_event_ar.item_metadata.user_initials,
            forms=sorted(
                [
                    OdmFormRefModel.from_odm_form_uid(
                        uid=form_uid,
                        study_event_uid=odm_study_event_ar._uid,
                        find_odm_form_by_uid_with_study_event_relation=find_odm_form_by_uid_with_study_event_relation,
                    )
                    for form_uid in odm_study_event_ar.concept_vo.form_uids
                ],
                key=lambda item: (item.order_number, item.name),
            ),
            possible_actions=sorted(
                [_.value for _ in odm_study_event_ar.get_possible_actions()]
            ),
        )


class OdmStudyEventPostInput(ConceptPostInput):
    oid: str | None
    effective_date: date | None = None
    retired_date: date | None = None
    description: str | None = None
    display_in_tree: bool = True


class OdmStudyEventPatchInput(ConceptPatchInput):
    oid: str | None
    effective_date: date | None
    retired_date: date | None
    description: str | None
    display_in_tree: bool = True


class OdmStudyEventFormPostInput(BaseModel):
    uid: str
    order_number: int
    mandatory: str
    locked: str = "No"
    collection_exception_condition_oid: str | None = None


class OdmStudyEventVersion(OdmStudyEvent):
    """
    Class for storing OdmStudyEvents and calculation of differences
    """

    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the timeframe (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )
