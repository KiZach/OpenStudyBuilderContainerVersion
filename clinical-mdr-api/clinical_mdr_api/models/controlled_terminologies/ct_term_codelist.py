from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class CTTermCodelist(BaseModel):
    codelist_uid: str = Field(
        ...,
        title="codelist_uid",
        description="",
    )
    order: int | None = Field(
        None,
        title="order",
        description="",
        nullable=True,
    )
