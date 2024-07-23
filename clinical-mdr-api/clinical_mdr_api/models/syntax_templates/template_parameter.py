from pydantic import Field

from clinical_mdr_api.models.syntax_templates.template_parameter_term import (
    TemplateParameterTerm,
)
from clinical_mdr_api.models.utils import BaseModel


class TemplateParameter(BaseModel):
    name: str | None = Field(
        ...,
        title="name",
        description="The name of the template parameter. E.g. 'Intervention', 'Indication', 'Activity', ...",
    )

    terms: list[TemplateParameterTerm] = Field(
        [],
        title="terms",
        description="The possible terms of the template parameter.",
    )


class ComplexTemplateParameter(BaseModel):
    name: str | None
    format: str | None
    parameters: list[TemplateParameter] = Field([])
    terms: list[TemplateParameterTerm] = Field(
        [],
        title="terms",
        description="The possible terms of the template parameter.",
    )
