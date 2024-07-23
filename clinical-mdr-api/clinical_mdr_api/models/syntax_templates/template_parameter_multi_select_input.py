from pydantic import Field

from clinical_mdr_api.models.syntax_templates.template_parameter_term import (
    IndexedTemplateParameterTerm,
)
from clinical_mdr_api.models.utils import BaseModel


class TemplateParameterMultiSelectInput(BaseModel):
    terms: list[IndexedTemplateParameterTerm] | None = Field(
        ...,
        title="terms",
        description="A list of indexed template parameter terms that are used at this position in the template.",
    )
    value: float | None = Field(
        None,
        title="value",
        description="A numeric value used at this position in the template.",
    )
    conjunction: str | None = Field(
        None,
        title="conjunction",
        description="If the selected template parameter term has multiple values, "
        "the conjunction string to connect them. Available values are ['and', 'or', ','].",
    )
