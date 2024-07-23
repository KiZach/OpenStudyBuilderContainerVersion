from typing import Self

from pydantic import Field

from clinical_mdr_api.domains.standard_data_models.sponsor_model_dataset_class import (
    SponsorModelDatasetClassAR,
)
from clinical_mdr_api.models import Library
from clinical_mdr_api.models.standard_data_models.sponsor_model import SponsorModelBase
from clinical_mdr_api.models.utils import BaseModel


class SponsorModelDatasetClass(SponsorModelBase):
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
    is_basic_std: bool | None = Field(
        None,
        title="is_basic_std",
        source="has_sponsor_model_instance.is_basic_std",
        nullable=True,
    )
    xml_path: str | None = Field(
        None,
        title="xml_path",
        source="has_sponsor_model_instance.xml_path",
        nullable=True,
    )
    xml_title: str | None = Field(
        None,
        title="xml_title",
        source="has_sponsor_model_instance.xml_title",
        nullable=True,
    )
    structure: str | None = Field(
        None,
        title="structure",
        source="has_sponsor_model_instance.structure",
        nullable=True,
    )
    purpose: str | None = Field(
        None,
        title="purpose",
        source="has_sponsor_model_instance.purpose",
        nullable=True,
    )
    comment: str | None = Field(
        None,
        title="comment",
        source="has_sponsor_model_instance.comment",
        nullable=True,
    )
    label: str | None = Field(
        None,
        title="label",
        source="has_sponsor_model_instance.label",
        nullable=True,
    )

    @classmethod
    def from_sponsor_model_dataset_class_ar(
        cls,
        sponsor_model_dataset_class_ar: SponsorModelDatasetClassAR,
    ) -> Self:
        return cls(
            uid=sponsor_model_dataset_class_ar.uid,
            is_basic_std=sponsor_model_dataset_class_ar.sponsor_model_dataset_class_vo.is_basic_std,
            xml_path=sponsor_model_dataset_class_ar.sponsor_model_dataset_class_vo.xml_path,
            xml_title=sponsor_model_dataset_class_ar.sponsor_model_dataset_class_vo.xml_title,
            structure=sponsor_model_dataset_class_ar.sponsor_model_dataset_class_vo.structure,
            purpose=sponsor_model_dataset_class_ar.sponsor_model_dataset_class_vo.purpose,
            comment=sponsor_model_dataset_class_ar.sponsor_model_dataset_class_vo.comment,
            label=sponsor_model_dataset_class_ar.sponsor_model_dataset_class_vo.label,
            library_name=Library.from_library_vo(
                sponsor_model_dataset_class_ar.library
            ).name,
        )


class SponsorModelDatasetClassInput(BaseModel):
    dataset_class_uid: str = Field(
        ..., title="uid", description="Unique identifier of the dataset class"
    )
    sponsor_model_name: str = Field(
        ...,
        title="sponsor_model_name",
        description="Name of the sponsor model in which to create the dataset class. E.g sdtmig_sponsormodel...",
    )
    sponsor_model_version_number: str = Field(
        ...,
        title="sponsor_model_version_number",
        description="Version number of the sponsor model in which to create the dataset class",
    )
    is_basic_std: bool = Field(None, title="is_basic_std", description="")
    xml_path: str = Field(None, title="xml_path", description="")
    xml_title: str = Field(None, title="xml_title", description="")
    structure: str = Field(None, title="structure", description="")
    purpose: str = Field(None, title="purpose", description="")
    comment: str = Field(None, title="comment", description="")
    label: str = Field(None, title="label", description="")
    library_name: str | None = Field(
        "CDISC", title="library_name", description="Defaults to CDISC"
    )
