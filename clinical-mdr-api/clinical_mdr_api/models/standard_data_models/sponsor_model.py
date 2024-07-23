from typing import Self

from pydantic import Field

from clinical_mdr_api.domains.standard_data_models.sponsor_model import SponsorModelAR
from clinical_mdr_api.models import Library
from clinical_mdr_api.models.concepts.concept import VersionProperties
from clinical_mdr_api.models.utils import BaseModel


class SponsorModelBase(BaseModel):
    pass


class SponsorModel(SponsorModelBase, VersionProperties):
    class Config:
        orm_mode = True

    uid: str = Field(
        None,
        title="uid",
        description="",
        source="uid",
    )
    name: str = Field(
        ...,
        title="name",
        description="The name or the sponsor model. E.g. sdtm_sponsormodel_3.2-NN15",
        source="has_latest_sponsor_model_value.name",
    )
    extended_implementation_guide: str | None = Field(
        None,
        title="extended_implementation_guide",
        description="",
        source="has_latest_sponsor_model_value__extends_version.name",
    )
    library_name: str = Field(
        None,
        title="library_name",
        description="",
        source="has_library.name",
    )

    @classmethod
    def from_sponsor_model_ar(
        cls,
        sponsor_model_ar: SponsorModelAR,
    ) -> Self:
        return cls(
            uid=sponsor_model_ar.uid,
            name=sponsor_model_ar.name,
            library_name=Library.from_library_vo(sponsor_model_ar.library).name,
            start_date=sponsor_model_ar.item_metadata.start_date,
            end_date=sponsor_model_ar.item_metadata.end_date,
            status=sponsor_model_ar.item_metadata.status.value,
            version=sponsor_model_ar.item_metadata.version,
            change_description=sponsor_model_ar.item_metadata.change_description,
            user_initials=sponsor_model_ar.item_metadata.user_initials,
            possible_actions=sorted(
                [_.value for _ in sponsor_model_ar.get_possible_actions()]
            ),
        )


class SponsorModelInput(BaseModel):
    ig_uid: str = Field(
        "SDTMIG",
        title="ig_uid",
        description="Unique identifier of the implementation guide to create the sponsor model from. E.g. SDTMIG",
    )
    ig_version_number: str = Field(
        ...,
        title="ig_version_number",
        description="the version number of the Implementation Guide which the sponsor model is based on",
    )
    version_number: str = Field(
        ...,
        title="version_number",
        description="Version number of the sponsor model to use - will be concatenated at the end of the full name",
    )
    change_description: str | None = Field(
        "Imported new version",
        title="change_description",
        description="Optionally, provide a change description.",
    )
    library_name: str | None = Field(
        "CDISC", title="library_name", description="Defaults to CDISC"
    )
