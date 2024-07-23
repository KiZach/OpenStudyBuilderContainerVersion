from pydantic import Field

from clinical_mdr_api.models.syntax_templates.template_parameter_multi_select_input import (
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.models.utils import BaseModel


class PreInstanceInput(BaseModel):
    parameter_terms: list[TemplateParameterMultiSelectInput] = Field(
        None,
        title="parameter_terms",
        description="An ordered list of selected parameter terms that are used to replace the parameters of the objective template.",
    )
    library_name: str = Field(
        None,
        title="library_name",
        description="If specified: The name of the library to which the objective will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
        "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true. \n\n"
        "If not specified: The library of the objective template will be used.",
    )
