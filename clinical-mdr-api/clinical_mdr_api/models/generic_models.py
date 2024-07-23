from pydantic import BaseModel, Field


class SimpleNameModel(BaseModel):
    uid: str = Field(..., title="uid", description="")
    name: str | None = Field(None, title="name", description="")
    name_sentence_case: str | None = Field(
        None, title="name_sentence_case", description=""
    )
