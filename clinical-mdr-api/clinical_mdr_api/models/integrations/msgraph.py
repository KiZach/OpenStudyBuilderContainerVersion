from pydantic import BaseModel, Field


class GraphGroup(BaseModel):
    id: str = Field(..., title="Unique identifier for the group")
    display_name: str = Field(
        ..., alias="displayName", title="Display name for the group"
    )
    description: str | None = Field(..., title="An optional description for the group")


class GraphUser(BaseModel):
    id: str = Field(..., title="Unique identifier for the user")
    display_name: str | None = Field(
        None,
        alias="displayName",
        title="Name displayed in the address book for the user",
    )
    given_name: str | None = Field(
        None, alias="givenName", title="First name of the user"
    )
    email: str | None = Field(None, alias="mail", title="User's email address")
    surname: str | None = Field(None, title="Last name of the user")
