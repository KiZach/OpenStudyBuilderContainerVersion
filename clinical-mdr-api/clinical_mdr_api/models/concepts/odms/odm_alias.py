from typing import Callable, Self

from pydantic import BaseModel, Field

from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domains.concepts.odms.alias import OdmAliasAR
from clinical_mdr_api.models.concepts.concept import (
    ConceptModel,
    ConceptPatchInput,
    ConceptPostInput,
)
from clinical_mdr_api.models.error import BatchErrorResponse


class OdmAlias(ConceptModel):
    context: str
    possible_actions: list[str]

    @classmethod
    def from_odm_alias_ar(cls, odm_alias_ar: OdmAliasAR) -> Self:
        return cls(
            uid=odm_alias_ar._uid,
            name=odm_alias_ar.name,
            context=odm_alias_ar.concept_vo.context,
            library_name=odm_alias_ar.library.name,
            start_date=odm_alias_ar.item_metadata.start_date,
            end_date=odm_alias_ar.item_metadata.end_date,
            status=odm_alias_ar.item_metadata.status.value,
            version=odm_alias_ar.item_metadata.version,
            change_description=odm_alias_ar.item_metadata.change_description,
            user_initials=odm_alias_ar.item_metadata.user_initials,
            possible_actions=sorted(
                [_.value for _ in odm_alias_ar.get_possible_actions()]
            ),
        )


class OdmAliasSimpleModel(BaseModel):
    @classmethod
    def from_odm_alias_uid(
        cls, uid: str, find_odm_alias_by_uid: Callable[[str], ConceptARBase | None]
    ) -> Self | None:
        if uid is not None:
            odm_alias = find_odm_alias_by_uid(uid)

            if odm_alias is not None:
                simple_odm_alias_model = cls(
                    uid=uid,
                    name=odm_alias.concept_vo.name,
                    context=odm_alias.concept_vo.context,
                    version=odm_alias.item_metadata.version,
                )
            else:
                simple_odm_alias_model = cls(
                    uid=uid, name=None, context=None, version=None
                )
        else:
            simple_odm_alias_model = None
        return simple_odm_alias_model

    uid: str = Field(..., title="uid", description="")
    name: str | None = Field(None, title="name", description="")
    context: str | None = Field(None, title="context", description="")
    version: str | None = Field(None, title="version", description="")


class OdmAliasPostInput(ConceptPostInput):
    context: str


class OdmAliasPatchInput(ConceptPatchInput):
    context: str | None


class OdmAliasBatchPatchInput(OdmAliasPatchInput):
    uid: str


class OdmAliasBatchInput(BaseModel):
    method: str = Field(
        ..., title="method", description="HTTP method corresponding to operation type"
    )
    content: OdmAliasBatchPatchInput | OdmAliasPostInput


class OdmAliasBatchOutput(BaseModel):
    response_code: int = Field(
        ...,
        title="response_code",
        description="The HTTP response code related to input operation",
    )
    content: OdmAlias | None | BatchErrorResponse


class OdmAliasVersion(OdmAlias):
    """
    Class for storing OdmAlias and calculation of differences
    """

    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )
