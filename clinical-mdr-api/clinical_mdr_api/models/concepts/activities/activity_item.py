from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class CompactActivityItemClass(BaseModel):
    class Config:
        orm_mode = True

    uid: str = Field(
        ...,
        title="activity item class uid",
        description="",
        source="has_activity_item_class.uid",
    )
    name: str | None = Field(
        None,
        title="activity item class name",
        description="",
        source="has_activity_item_class.has_latest_value.name",
    )


class CompactCTTerm(BaseModel):
    class Config:
        orm_mode = True

    uid: str | None = Field(
        None,
        title="ct term uid",
        description="",
        source="has_ct_term.uid",
    )
    name: str | None = Field(
        None,
        title="ct term name",
        description="",
        source="has_ct_term.has_name_root.has_latest_value.name",
    )


class CompactUnitDefinition(BaseModel):
    class Config:
        orm_mode = True

    uid: str | None = Field(
        None,
        title="unit definition uid",
        description="",
        source="has_unit_definition.uid",
    )
    name: str | None = Field(
        None,
        title="unit definition name",
        description="",
        source="has_unit_definition.has_latest_value.name",
    )


class ActivityItem(BaseModel):
    class Config:
        orm_mode = True

    activity_item_class: CompactActivityItemClass = Field(...)
    ct_terms: list[CompactCTTerm] = Field([])
    unit_definitions: list[CompactUnitDefinition] = Field([])


class ActivityItemCreateInput(BaseModel):
    activity_item_class_uid: str
    ct_term_uids: list[str]
    unit_definition_uids: list[str]
