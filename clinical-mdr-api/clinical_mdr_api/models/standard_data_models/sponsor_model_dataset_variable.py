from pydantic import Field

from clinical_mdr_api.domains.standard_data_models.sponsor_model_dataset_variable import (
    SponsorModelDatasetVariableAR,
)
from clinical_mdr_api.models import Library
from clinical_mdr_api.models.standard_data_models.sponsor_model import SponsorModelBase
from clinical_mdr_api.models.utils import BaseModel


class SponsorModelDatasetVariable(SponsorModelBase):
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
        source="has_sponsor_model_instance.has_variable|ordinal",
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
    xml_codelist_multi: list[str] | None = Field(
        None,
        title="xml_codelist_multi",
        source="has_sponsor_model_instance.xml_codelist_multi",
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
    class_table: str | None = Field(
        None,
        title="class_table",
        source="has_sponsor_model_instance.class_table",
        nullable=True,
    )
    class_column: str | None = Field(
        None,
        title="class_column",
        source="has_sponsor_model_instance.class_column",
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
    value_lvl_where_cols: str | None = Field(
        None,
        title="value_lvl_where_cols",
        source="has_sponsor_model_instance.value_lvl_where_cols",
        nullable=True,
    )
    value_lvl_label_col: str | None = Field(
        None,
        title="value_lvl_label_col",
        source="has_sponsor_model_instance.value_lvl_label_col",
        nullable=True,
    )
    value_lvl_collect_ct_val: str | None = Field(
        None,
        title="value_lvl_collect_ct_val",
        source="has_sponsor_model_instance.value_lvl_collect_ct_val",
        nullable=True,
    )
    value_lvl_ct_codelist_id_col: str | None = Field(
        None,
        title="value_lvl_ct_codelist_id_col",
        source="has_sponsor_model_instance.value_lvl_ct_codelist_id_col",
        nullable=True,
    )
    enrich_build_order: int | None = Field(
        None,
        title="enrich_build_order",
        source="has_sponsor_model_instance.enrich_build_order",
        nullable=True,
    )
    enrich_rule: str | None = Field(
        None,
        title="enrich_rule",
        source="has_sponsor_model_instance.enrich_rule",
        nullable=True,
    )
    xml_codelist_values: bool | None = Field(
        None,
        title="xml_codelist_values",
        source="has_sponsor_model_instance.xml_codelist_values",
        nullable=True,
    )

    @classmethod
    def from_sponsor_model_dataset_variable_ar(
        cls,
        sponsor_model_dataset_variable_ar: SponsorModelDatasetVariableAR,
    ) -> "SponsorModelDatasetVariable":
        return cls(
            uid=sponsor_model_dataset_variable_ar.uid,
            is_basic_std=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.is_basic_std,
            label=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.label,
            order=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.order,
            variable_type=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.variable_type,
            length=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.length,
            display_format=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.display_format,
            xml_datatype=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.xml_datatype,
            xml_codelist=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.xml_codelist,
            xml_codelist_multi=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.xml_codelist_multi,
            core=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.core,
            origin=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.origin,
            role=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.role,
            term=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.term,
            algorithm=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.algorithm,
            qualifiers=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.qualifiers,
            comment=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.comment,
            ig_comment=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.ig_comment,
            class_table=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.class_table,
            class_column=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.class_column,
            map_var_flag=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.map_var_flag,
            fixed_mapping=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.fixed_mapping,
            include_in_raw=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.include_in_raw,
            nn_internal=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.nn_internal,
            value_lvl_where_cols=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.value_lvl_where_cols,
            value_lvl_label_col=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.value_lvl_label_col,
            value_lvl_collect_ct_val=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.value_lvl_collect_ct_val,
            value_lvl_ct_codelist_id_col=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.value_lvl_ct_codelist_id_col,
            enrich_build_order=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.enrich_build_order,
            enrich_rule=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.enrich_rule,
            xml_codelist_values=sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo.xml_codelist_values,
            library_name=Library.from_library_vo(
                sponsor_model_dataset_variable_ar.library
            ).name,
        )


class SponsorModelDatasetVariableInput(BaseModel):
    dataset_uid: str = Field(
        ...,
        title="dataset_uid",
        description="Uid of the dataset in which to create the variable. E.g AE",
    )
    dataset_variable_uid: str = Field(
        ..., title="uid", description="Unique identifier of the variable"
    )
    sponsor_model_name: str = Field(
        ...,
        title="sponsor_model_name",
        description="Name of the sponsor model in which to create the variable. E.g sdtmig_sponsormodel...",
    )
    sponsor_model_version_number: str = Field(
        ...,
        title="sponsor_model_version_number",
        description="Version number of the sponsor model in which to create the variable",
    )
    is_basic_std: bool = Field(None, title="is_basic_std", description="")
    label: str = Field(None, title="label", description="")
    order: int = Field(None, title="order", description="")
    variable_type: str = Field(None, title="variable_type", description="")
    length: int = Field(None, title="length", description="")
    display_format: str = Field(None, title="display_format", description="")
    xml_datatype: str = Field(None, title="xml_datatype", description="")
    xml_codelist: str = Field(None, title="xml_codelist", description="")
    xml_codelist_multi: list[str] = Field(
        None, title="xml_codelist_multi", description=""
    )
    core: str = Field(None, title="core", description="")
    origin: str = Field(None, title="origin", description="")
    role: str = Field(None, title="role", description="")
    term: str = Field(None, title="term", description="")
    algorithm: str = Field(None, title="algorithm", description="")
    qualifiers: list[str] = Field(None, title="qualifiers", description="")
    comment: str = Field(None, title="comment", description="")
    ig_comment: str = Field(None, title="ig_comment", description="")
    class_table: str = Field(None, title="class_table", description="")
    class_column: str = Field(None, title="class_column", description="")
    map_var_flag: bool = Field(None, title="map_var_flag", description="")
    fixed_mapping: str = Field(None, title="fixed_mapping", description="")
    include_in_raw: bool = Field(None, title="include_in_raw", description="")
    nn_internal: bool = Field(None, title="nn_internal", description="")
    value_lvl_where_cols: str = Field(
        None, title="value_lvl_where_cols", description=""
    )
    value_lvl_label_col: str = Field(None, title="value_lvl_label_col", description="")
    value_lvl_collect_ct_val: str = Field(
        None, title="value_lvl_collect_ct_val", description=""
    )
    value_lvl_ct_codelist_id_col: str = Field(
        None, title="value_lvl_ct_codelist_id_col", description=""
    )
    enrich_build_order: int = Field(None, title="enrich_build_order", description="")
    enrich_rule: str = Field(None, title="enrich_rule", description="")
    xml_codelist_values: bool = Field(None, title="xml_codelist_values", description="")
    library_name: str | None = Field(
        "CDISC", title="library_name", description="Defaults to CDISC"
    )
