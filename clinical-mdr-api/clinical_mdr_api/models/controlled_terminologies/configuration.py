from typing import Self

from pydantic import Field, validator

from clinical_mdr_api.domains.controlled_terminologies.configurations import CTConfigAR
from clinical_mdr_api.models.concepts.concept import (
    NoLibraryConceptModelNoName,
    VersionProperties,
)
from clinical_mdr_api.models.utils import BaseModel


class CTConfigBaseModel(BaseModel):
    study_field_name: str
    study_field_data_type: str
    study_field_null_value_code: str | None = Field(
        None,
        nullable=True,
    )

    configured_codelist_uid: str | None = Field(
        None,
        nullable=True,
    )
    configured_term_uid: str | None = Field(
        None,
        nullable=True,
    )

    study_field_grouping: str | None = Field(
        None,
        nullable=True,
    )
    study_field_name_api: str
    is_dictionary_term: bool


class CTConfigOGM(VersionProperties):
    class Config:
        orm_mode = True

    uid: str = Field(..., source="uid")
    study_field_name: str = Field(..., source="has_latest_value.study_field_name")
    study_field_data_type: str | None = Field(
        None, source="has_latest_value.study_field_data_type", nullable=True
    )
    study_field_null_value_code: str | None = Field(
        None,
        source="has_latest_value.study_field_null_value_code",
        nullable=True,
    )

    configured_codelist_uid: str | None = Field(
        None,
        source="has_latest_value.has_configured_codelist.uid",
        nullable=True,
    )
    configured_term_uid: str | None = Field(
        None,
        source="has_latest_value.has_configured_term.uid",
        nullable=True,
    )

    study_field_grouping: str | None = Field(
        None,
        source="has_latest_value.study_field_grouping",
        nullable=True,
    )
    study_field_name_api: str | None = Field(
        None, source="has_latest_value.study_field_name_api", nullable=True
    )
    is_dictionary_term: bool = Field(..., source="has_latest_value.is_dictionary_term")


class CTConfigModel(CTConfigBaseModel, NoLibraryConceptModelNoName):
    @classmethod
    def from_ct_config_ar(cls, ct_config_definition_ar: CTConfigAR) -> Self:
        return CTConfigModel(
            uid=ct_config_definition_ar.uid,
            study_field_name=ct_config_definition_ar.value.study_field_name,
            study_field_data_type=ct_config_definition_ar.value.study_field_data_type,
            study_field_null_value_code=ct_config_definition_ar.value.study_field_null_value_code,
            configured_codelist_uid=ct_config_definition_ar.value.configured_codelist_uid,
            configured_term_uid=ct_config_definition_ar.value.configured_term_uid,
            study_field_grouping=ct_config_definition_ar.value.study_field_grouping,
            study_field_name_api=ct_config_definition_ar.value.study_field_name_api,
            is_dictionary_term=ct_config_definition_ar.value.is_dictionary_term,
            start_date=ct_config_definition_ar.item_metadata.start_date,
            status=ct_config_definition_ar.item_metadata.status.value,
            version=ct_config_definition_ar.item_metadata.version,
            user_initials=ct_config_definition_ar.item_metadata.user_initials,
            change_description=ct_config_definition_ar.item_metadata.change_description,
        )


class CTConfigPostInput(CTConfigBaseModel):
    # field used to create a configuration based on codelist name
    configured_codelist_name: str | None

    @validator("*")
    # pylint: disable=no-self-argument
    def replace_empty_string_with_none(cls, field):
        if field == "":
            return None
        return field


class CTConfigPatchInput(CTConfigBaseModel):
    change_description: str
