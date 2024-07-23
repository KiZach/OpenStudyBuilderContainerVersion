from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class SimpleDictionaryItem(BaseModel):
    class Config:
        description = "Simple dictionary item structure"

    code: str = Field(
        ...,
        title="code",
        description="",
    )

    name: str = Field(
        ...,
        title="name",
        description="",
    )

    definition: str = Field(
        ...,
        title="definition",
        description="",
    )
