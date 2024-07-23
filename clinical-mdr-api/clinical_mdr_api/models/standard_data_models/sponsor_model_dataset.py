from typing import Self

from pydantic import Field

from clinical_mdr_api.domains.standard_data_models.sponsor_model_dataset import (
    SponsorModelDatasetAR,
)
from clinical_mdr_api.models import Library
from clinical_mdr_api.models.standard_data_models.sponsor_model import SponsorModelBase
from clinical_mdr_api.models.utils import BaseModel


class SponsorModelDataset(SponsorModelBase):
    class Config:
        orm_mode = True

    uid: str = Field(
        None,
        title="uid",
        description="",
        source="uid",
    )
    library_name: str = Field(
        None,
        title="library_name",
        description="",
        source="has_library.name",
    )
    is_basic_std: bool = Field(
        None, title="is_basic_std", source="has_sponsor_model_instance.is_basic_std"
    )
    xml_path: str = Field(
        None, title="xml_path", source="has_sponsor_model_instance.xml_path"
    )
    xml_title: str = Field(
        None, title="xml_title", source="has_sponsor_model_instance.xml_title"
    )
    structure: str = Field(
        None, title="structure", source="has_sponsor_model_instance.structure"
    )
    purpose: str = Field(
        None, title="purpose", source="has_sponsor_model_instance.purpose"
    )
    keys: list[str] | None = Field(
        None, title="keys", source="has_sponsor_model_instance.has_key.uid"
    )
    sort_keys: list[str] | None = Field(
        None, title="sort_keys", source="has_sponsor_model_instance.has_sort_key.uid"
    )
    source_ig: str | None = Field(
        None, title="Source IG", source="has_sponsor_model_instance.source_ig"
    )
    comment: str = Field(
        None, title="comment", source="has_sponsor_model_instance.comment"
    )
    ig_comment: str = Field(
        None, title="ig_comment", source="has_sponsor_model_instance.ig_comment"
    )
    map_domain_flag: bool = Field(
        None,
        title="map_domain_flag",
        source="has_sponsor_model_instance.map_domain_flag",
    )
    suppl_qual_flag: bool = Field(
        None,
        title="suppl_qual_flag",
        source="has_sponsor_model_instance.suppl_qual_flag",
    )
    include_in_raw: bool = Field(
        None,
        title="include_in_raw",
        source="has_sponsor_model_instance.include_in_raw",
    )
    gen_raw_seqno_flag: bool = Field(
        None,
        title="gen_raw_seqno_flag",
        source="has_sponsor_model_instance.gen_raw_seqno_flag",
    )
    enrich_build_order: int = Field(
        None,
        title="enrich_build_order",
        source="has_sponsor_model_instance.has_dataset|ordinal",
    )
    label: str | None = Field(
        None,
        title="label",
        source="has_sponsor_model_instance.label",
        nullable=True,
    )
    state: str | None = Field(
        None,
        title="state",
        source="has_sponsor_model_instance.state",
        nullable=True,
    )
    extended_domain: str | None = Field(
        None,
        title="extended_domain",
        source="has_sponsor_model_instance.extended_domain",
        nullable=True,
    )

    @classmethod
    def from_sponsor_model_dataset_ar(
        cls,
        sponsor_model_dataset_ar: SponsorModelDatasetAR,
    ) -> Self:
        return cls(
            uid=sponsor_model_dataset_ar.uid,
            is_basic_std=sponsor_model_dataset_ar.sponsor_model_dataset_vo.is_basic_std,
            xml_path=sponsor_model_dataset_ar.sponsor_model_dataset_vo.xml_path,
            xml_title=sponsor_model_dataset_ar.sponsor_model_dataset_vo.xml_title,
            structure=sponsor_model_dataset_ar.sponsor_model_dataset_vo.structure,
            purpose=sponsor_model_dataset_ar.sponsor_model_dataset_vo.purpose,
            keys=sponsor_model_dataset_ar.sponsor_model_dataset_vo.keys,
            sort_keys=sponsor_model_dataset_ar.sponsor_model_dataset_vo.sort_keys,
            source_ig=sponsor_model_dataset_ar.sponsor_model_dataset_vo.source_ig,
            comment=sponsor_model_dataset_ar.sponsor_model_dataset_vo.comment,
            ig_comment=sponsor_model_dataset_ar.sponsor_model_dataset_vo.ig_comment,
            map_domain_flag=sponsor_model_dataset_ar.sponsor_model_dataset_vo.map_domain_flag,
            suppl_qual_flag=sponsor_model_dataset_ar.sponsor_model_dataset_vo.suppl_qual_flag,
            include_in_raw=sponsor_model_dataset_ar.sponsor_model_dataset_vo.include_in_raw,
            gen_raw_seqno_flag=sponsor_model_dataset_ar.sponsor_model_dataset_vo.gen_raw_seqno_flag,
            enrich_build_order=sponsor_model_dataset_ar.sponsor_model_dataset_vo.enrich_build_order,
            label=sponsor_model_dataset_ar.sponsor_model_dataset_vo.label,
            state=sponsor_model_dataset_ar.sponsor_model_dataset_vo.state,
            extended_domain=sponsor_model_dataset_ar.sponsor_model_dataset_vo.extended_domain,
            library_name=Library.from_library_vo(sponsor_model_dataset_ar.library).name,
        )


class SponsorModelDatasetInput(BaseModel):
    dataset_uid: str = Field(
        ..., title="uid", description="Unique identifier of the dataset"
    )
    sponsor_model_name: str = Field(
        ...,
        title="sponsor_model_name",
        description="Name of the sponsor model in which to create the dataset. E.g sdtmig_sponsormodel...",
    )
    sponsor_model_version_number: str = Field(
        ...,
        title="sponsor_model_version_number",
        description="Version number of the sponsor model in which to create the dataset",
    )
    is_basic_std: bool = Field(None, title="is_basic_std", description="")
    xml_path: str = Field(None, title="xml_path", description="")
    xml_title: str = Field(None, title="xml_title", description="")
    structure: str = Field(None, title="structure", description="")
    purpose: str = Field(None, title="purpose", description="")
    keys: list[str] = Field(None, title="keys", description="")
    sort_keys: list[str] = Field(None, title="sort_keys", description="")
    source_ig: str = Field(
        None,
        title="source_ig",
        description="Source Implementation Guide, e.g. SDTMIG 3.3 or TAUG-DIABETES 1.0",
    )
    comment: str = Field(None, title="comment", description="")
    ig_comment: str = Field(None, title="ig_comment", description="")
    map_domain_flag: bool = Field(None, title="map_domain_flag", description="")
    suppl_qual_flag: bool = Field(None, title="suppl_qual_flag", description="")
    include_in_raw: bool = Field(None, title="include_in_raw", description="")
    gen_raw_seqno_flag: bool = Field(None, title="gen_raw_seqno_flag", description="")
    enrich_build_order: int = Field(None, title="enrich_build_order", description="")
    label: str = Field(None, title="label", description="")
    state: str = Field(None, title="state", description="")
    extended_domain: str = Field(None, title="extended_domain", description="")
    library_name: str | None = Field(
        "CDISC", title="library_name", description="Defaults to CDISC"
    )
