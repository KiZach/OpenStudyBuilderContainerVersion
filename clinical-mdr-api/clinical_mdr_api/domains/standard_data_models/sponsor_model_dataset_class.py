import datetime
from dataclasses import dataclass
from typing import Self

from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)


@dataclass(frozen=True)
class SponsorModelDatasetClassVO:
    """
    The SponsorModelDatasetClassVO acts as the value object for a single SponsorModelDatasetClass value object
    """

    sponsor_model_name: str
    sponsor_model_version_number: str
    dataset_class_uid: str

    is_basic_std: bool
    xml_path: str
    xml_title: str
    structure: str
    purpose: str
    comment: str
    label: str

    @classmethod
    def from_repository_values(
        cls,
        sponsor_model_name: str,
        sponsor_model_version_number: int,
        dataset_class_uid: str,
        is_basic_std: bool,
        xml_path: str,
        xml_title: str,
        structure: str,
        purpose: str,
        comment: str,
        label: str,
    ) -> Self:
        sponsor_model_dataset_class_vo = cls(
            sponsor_model_name=sponsor_model_name,
            sponsor_model_version_number=sponsor_model_version_number,
            dataset_class_uid=dataset_class_uid,
            is_basic_std=is_basic_std,
            xml_path=xml_path,
            xml_title=xml_title,
            structure=structure,
            purpose=purpose,
            comment=comment,
            label=label,
        )

        return sponsor_model_dataset_class_vo


class SponsorModelDatasetMetadataVO(LibraryItemMetadataVO):
    @property
    def version(self) -> str:
        return self._major_version

    # pylint: disable=arguments-renamed
    @classmethod
    def get_initial_item_metadata(cls, author: str, version: str) -> Self:
        return cls(
            _change_description="Approved version",
            _status=LibraryItemStatus.FINAL,
            _author=author,
            _start_date=datetime.datetime.now(datetime.timezone.utc),
            _end_date=None,
            _major_version=version,
            _minor_version=0,
        )


@dataclass
class SponsorModelDatasetClassAR(LibraryItemAggregateRootBase):
    """
    An abstract generic sponsor model dataset class aggregate for versioned sponsor models
    """

    _sponsor_model_dataset_class_vo: SponsorModelDatasetClassVO

    @property
    def sponsor_model_dataset_class_vo(self) -> SponsorModelDatasetClassVO:
        return self._sponsor_model_dataset_class_vo

    @property
    def name(self) -> str:
        return self._uid

    @sponsor_model_dataset_class_vo.setter
    def sponsor_model_dataset_class_vo(
        self, sponsor_model_dataset_class_vo: SponsorModelDatasetClassVO
    ):
        self._sponsor_model_dataset_class_vo = sponsor_model_dataset_class_vo

    @classmethod
    def from_repository_values(
        cls,
        dataset_class_uid: str,
        sponsor_model_dataset_class_vo: SponsorModelDatasetClassVO,
        library: LibraryVO | None,
        item_metadata: SponsorModelDatasetMetadataVO,
    ) -> Self:
        sponsor_model_dataset_class_ar = cls(
            _uid=dataset_class_uid,
            _sponsor_model_dataset_class_vo=sponsor_model_dataset_class_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return sponsor_model_dataset_class_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author: str,
        sponsor_model_dataset_class_vo: SponsorModelDatasetClassVO,
        library: LibraryVO,
    ) -> Self:
        item_metadata = SponsorModelDatasetMetadataVO.get_initial_item_metadata(
            author=author,
            version=sponsor_model_dataset_class_vo.sponsor_model_version_number,
        )

        sponsor_model_dataset_class_ar = cls(
            _uid=sponsor_model_dataset_class_vo.dataset_class_uid,
            _item_metadata=item_metadata,
            _library=library,
            _sponsor_model_dataset_class_vo=sponsor_model_dataset_class_vo,
        )
        return sponsor_model_dataset_class_ar
