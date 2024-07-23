from pydantic import Field

from clinical_mdr_api.domains.standard_data_models.sponsor_model_variable_class import (
    SponsorModelVariableClassAR,
)
from clinical_mdr_api.models import Library
from clinical_mdr_api.models.standard_data_models.sponsor_model import SponsorModelBase
from clinical_mdr_api.models.utils import BaseModel


class SponsorModelVariableClass(SponsorModelBase):
    class Config:
        orm_mode = True

    uid: str = Field(
        None,
        title="uid",
        description="",
        source="uid",
    )
    library_name: str | None = Field(
        None,
        title="library_name",
        description="",
        source="has_library.name",
        nullable=True,
    )
    is_basic_std: bool | None = Field(
        None,
        title="is_basic_std",
        source="has_sponsor_model_instance.is_basic_std",
        nullable=True,
    )
    label: str | None = Field(
        None,
        title="label",
        source="has_sponsor_model_instance.label",
        nullable=True,
    )
    order: int | None = Field(
        None,
        title="order",
        source="has_sponsor_model_instance.has_variable_class|ordinal",
        nullable=True,
    )
    variable_type: str | None = Field(
        None,
        title="variable_type",
        source="has_sponsor_model_instance.variable_type",
        nullable=True,
    )
    length: int | None = Field(
        None,
        title="length",
        source="has_sponsor_model_instance.length",
        nullable=True,
    )
    display_format: str | None = Field(
        None,
        title="display_format",
        source="has_sponsor_model_instance.display_format",
        nullable=True,
    )
    xml_datatype: str | None = Field(
        None,
        title="xml_datatype",
        source="has_sponsor_model_instance.xml_datatype",
        nullable=True,
    )
    xml_codelist: str | None = Field(
        None,
        title="xml_codelist",
        source="has_sponsor_model_instance.xml_codelist",
        nullable=True,
    )
    core: str | None = Field(
        None,
        title="core",
        source="has_sponsor_model_instance.core",
        nullable=True,
    )
    origin: str | None = Field(
        None,
        title="origin",
        source="has_sponsor_model_instance.origin",
        nullable=True,
    )
    role: str | None = Field(
        None,
        title="role",
        source="has_sponsor_model_instance.role",
        nullable=True,
    )
    term: str | None = Field(
        None,
        title="term",
        source="has_sponsor_model_instance.term",
        nullable=True,
    )
    algorithm: str | None = Field(
        None,
        title="algorithm",
        source="has_sponsor_model_instance.algorithm",
        nullable=True,
    )
    qualifiers: list[str] | None = Field(
        None,
        title="qualifiers",
        source="has_sponsor_model_instance.qualifiers",
        nullable=True,
    )
    comment: str | None = Field(
        None,
        title="comment",
        source="has_sponsor_model_instance.comment",
        nullable=True,
    )
    ig_comment: str | None = Field(
        None,
        title="ig_comment",
        source="has_sponsor_model_instance.ig_comment",
        nullable=True,
    )
    map_var_flag: bool | None = Field(
        None,
        title="map_var_flag",
        source="has_sponsor_model_instance.map_var_flag",
        nullable=True,
    )
    fixed_mapping: str | None = Field(
        None,
        title="fixed_mapping",
        source="has_sponsor_model_instance.fixed_mapping",
        nullable=True,
    )
    include_in_raw: bool | None = Field(
        None,
        title="include_in_raw",
        source="has_sponsor_model_instance.include_in_raw",
        nullable=True,
    )
    nn_internal: bool | None = Field(
        None,
        title="nn_internal",
        source="has_sponsor_model_instance.nn_internal",
        nullable=True,
    )
    incl_cre_domain: bool | None = Field(
        None,
        title="incl_cre_domain",
        source="has_sponsor_model_instance.incl_cre_domain",
        nullable=True,
    )
    xml_codelist_values: bool | None = Field(
        None,
        title="xml_codelist_values",
        source="has_sponsor_model_instance.xml_codelist_values",
        nullable=True,
    )

    @classmethod
    def from_sponsor_model_variable_class_ar(
        cls,
        sponsor_model_variable_class_ar: SponsorModelVariableClassAR,
    ) -> "SponsorModelVariableClass":
        return cls(
            uid=sponsor_model_variable_class_ar.uid,
            is_basic_std=sponsor_model_variable_class_ar.sponsor_model_variable_class_vo.is_basic_std,
            label=sponsor_model_variable_class_ar.sponsor_model_variable_class_vo.label,
            order=sponsor_model_variable_class_ar.sponsor_model_variable_class_vo.order,
            variable_type=sponsor_model_variable_class_ar.sponsor_model_variable_class_vo.variable_type,
            length=sponsor_model_variable_class_ar.sponsor_model_variable_class_vo.length,
            display_format=sponsor_model_variable_class_ar.sponsor_model_variable_class_vo.display_format,
            xml_datatype=sponsor_model_variable_class_ar.sponsor_model_variable_class_vo.xml_datatype,
            xml_codelist=sponsor_model_variable_class_ar.sponsor_model_variable_class_vo.xml_codelist,
            core=sponsor_model_variable_class_ar.sponsor_model_variable_class_vo.core,
            origin=sponsor_model_variable_class_ar.sponsor_model_variable_class_vo.origin,
            role=sponsor_model_variable_class_ar.sponsor_model_variable_class_vo.role,
            term=sponsor_model_variable_class_ar.sponsor_model_variable_class_vo.term,
            algorithm=sponsor_model_variable_class_ar.sponsor_model_variable_class_vo.algorithm,
            qualifiers=sponsor_model_variable_class_ar.sponsor_model_variable_class_vo.qualifiers,
            comment=sponsor_model_variable_class_ar.sponsor_model_variable_class_vo.comment,
            ig_comment=sponsor_model_variable_class_ar.sponsor_model_variable_class_vo.ig_comment,
            map_var_flag=sponsor_model_variable_class_ar.sponsor_model_variable_class_vo.map_var_flag,
            fixed_mapping=sponsor_model_variable_class_ar.sponsor_model_variable_class_vo.fixed_mapping,
            include_in_raw=sponsor_model_variable_class_ar.sponsor_model_variable_class_vo.include_in_raw,
            nn_internal=sponsor_model_variable_class_ar.sponsor_model_variable_class_vo.nn_internal,
            incl_cre_domain=sponsor_model_variable_class_ar.sponsor_model_variable_class_vo.incl_cre_domain,
            xml_codelist_values=sponsor_model_variable_class_ar.sponsor_model_variable_class_vo.xml_codelist_values,
            library_name=Library.from_library_vo(
                sponsor_model_variable_class_ar.library
            ).name,
        )


class SponsorModelVariableClassInput(BaseModel):
    dataset_class_uid: str = Field(
        ...,
        title="dataset_class_uid",
        description="Uid of the dataset class in which to create the variable. E.g Findings",
    )
    variable_class_uid: str = Field(
        ..., title="uid", description="Unique identifier of the variable class"
    )
    sponsor_model_name: str = Field(
        ...,
        title="sponsor_model_name",
        description="Name of the sponsor model in which to create the variable class. E.g sdtmig_sponsormodel...",
    )
    sponsor_model_version_number: str = Field(
        ...,
        title="sponsor_model_version_number",
        description="Version number of the sponsor model in which to create the variable class",
    )
    is_basic_std: bool = Field(None, title="is_basic_std", description="")
    label: str = Field(None, title="label", description="")
    order: int = Field(None, title="order", description="")
    variable_type: str = Field(None, title="variable_type", description="")
    length: int = Field(None, title="length", description="")
    display_format: str = Field(None, title="display_format", description="")
    xml_datatype: str = Field(None, title="xml_datatype", description="")
    xml_codelist: str = Field(None, title="xml_codelist", description="")
    core: str = Field(None, title="core", description="")
    origin: str = Field(None, title="origin", description="")
    role: str = Field(None, title="role", description="")
    term: str = Field(None, title="term", description="")
    algorithm: str = Field(None, title="algorithm", description="")
    qualifiers: list[str] = Field(None, title="qualifiers", description="")
    comment: str = Field(None, title="comment", description="")
    ig_comment: str = Field(None, title="ig_comment", description="")
    map_var_flag: bool = Field(None, title="map_var_flag", description="")
    fixed_mapping: str = Field(None, title="fixed_mapping", description="")
    include_in_raw: bool = Field(None, title="include_in_raw", description="")
    nn_internal: bool = Field(None, title="nn_internal", description="")
    incl_cre_domain: bool = Field(None, title="incl_cre_domain", description="")
    xml_codelist_values: bool = Field(None, title="xml_codelist_values", description="")
    library_name: str | None = Field(
        "CDISC", title="library_name", description="Defaults to CDISC"
    )
