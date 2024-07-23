from typing import Callable, Self

from pydantic import Field

from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domains.concepts.odms.formal_expression import (
    OdmFormalExpressionAR,
)
from clinical_mdr_api.models.concepts.concept import NoLibraryConceptModelNoName
from clinical_mdr_api.models.utils import BaseModel


class OdmFormalExpression(NoLibraryConceptModelNoName):
    library_name: str
    context: str | None
    expression: str | None
    possible_actions: list[str]

    @classmethod
    def from_odm_formal_expression_ar(
        cls,
        odm_formal_expression_ar: OdmFormalExpressionAR,
    ) -> Self:
        return cls(
            uid=odm_formal_expression_ar._uid,
            context=odm_formal_expression_ar.concept_vo.context,
            expression=odm_formal_expression_ar.concept_vo.expression,
            library_name=odm_formal_expression_ar.library.name,
            start_date=odm_formal_expression_ar.item_metadata.start_date,
            end_date=odm_formal_expression_ar.item_metadata.end_date,
            status=odm_formal_expression_ar.item_metadata.status.value,
            version=odm_formal_expression_ar.item_metadata.version,
            change_description=odm_formal_expression_ar.item_metadata.change_description,
            user_initials=odm_formal_expression_ar.item_metadata.user_initials,
            possible_actions=sorted(
                [_.value for _ in odm_formal_expression_ar.get_possible_actions()]
            ),
        )


class OdmFormalExpressionSimpleModel(BaseModel):
    @classmethod
    def from_odm_formal_expression_uid(
        cls,
        uid: str,
        find_odm_formal_expression_by_uid: Callable[[str], ConceptARBase | None],
    ) -> Self | None:
        if uid is not None:
            odm_formal_expression = find_odm_formal_expression_by_uid(uid)

            if odm_formal_expression is not None:
                simple_odm_formal_expression_model = cls(
                    uid=uid,
                    context=odm_formal_expression.concept_vo.context,
                    expression=odm_formal_expression.concept_vo.expression,
                    version=odm_formal_expression.item_metadata.version,
                )
            else:
                simple_odm_formal_expression_model = cls(
                    uid=uid,
                    context=None,
                    expression=None,
                    version=None,
                )
        else:
            simple_odm_formal_expression_model = None
        return simple_odm_formal_expression_model

    uid: str = Field(..., title="uid", description="")
    context: str | None = Field(None, title="context", description="")
    expression: str | None = Field(None, title="expression", description="")
    version: str | None = Field(None, title="version", description="")


class OdmFormalExpressionPostInput(BaseModel):
    library_name: str = "Sponsor"
    context: str
    expression: str


class OdmFormalExpressionPatchInput(BaseModel):
    change_description: str
    context: str | None
    expression: str | None


class OdmFormalExpressionBatchPatchInput(OdmFormalExpressionPatchInput):
    uid: str


class OdmFormalExpressionVersion(OdmFormalExpression):
    """
    Class for storing OdmFormalExpression and calculation of differences
    """

    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )
