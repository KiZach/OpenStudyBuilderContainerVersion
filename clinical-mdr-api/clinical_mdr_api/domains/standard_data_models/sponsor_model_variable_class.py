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
class SponsorModelVariableClassVO:
    """
    The SponsorModelVariableClassVO acts as the value object for a single SponsorModelVariableClass value object
    """

    dataset_class_uid: str
    variable_class_uid: str
    sponsor_model_name: str
    sponsor_model_version_number: str

    is_basic_std: bool
    label: str
    order: int
    variable_type: str
    length: int
    display_format: str
    xml_datatype: str
    xml_codelist: str
    core: str
    origin: str
    role: str
    term: str
    algorithm: str
    qualifiers: list[str]
    comment: str
    ig_comment: str
    map_var_flag: bool
    fixed_mapping: str
    include_in_raw: bool
    nn_internal: bool
    incl_cre_domain: bool
    xml_codelist_values: bool

    @classmethod
    def from_repository_values(
        cls,
        dataset_class_uid: str,
        variable_class_uid: str,
        sponsor_model_name: str | None,
        sponsor_model_version_number: str | None,
        is_basic_std: bool,
        label: str,
        order: int,
        variable_type: str,
        length: int,
        display_format: str,
        xml_datatype: str,
        xml_codelist: str,
        core: str,
        origin: str,
        role: str,
        term: str,
        algorithm: str,
        qualifiers: list[str],
        comment: str,
        ig_comment: str,
        map_var_flag: bool,
        fixed_mapping: str,
        include_in_raw: bool,
        nn_internal: bool,
        incl_cre_domain: bool,
        xml_codelist_values: bool,
    ) -> Self:
        sponsor_model_variable_class_vo = cls(
            dataset_class_uid=dataset_class_uid,
            variable_class_uid=variable_class_uid,
            sponsor_model_name=sponsor_model_name,
            sponsor_model_version_number=sponsor_model_version_number,
            is_basic_std=is_basic_std,
            label=label,
            order=order,
            variable_type=variable_type,
            length=length,
            display_format=display_format,
            xml_datatype=xml_datatype,
            xml_codelist=xml_codelist,
            core=core,
            origin=origin,
            role=role,
            term=term,
            algorithm=algorithm,
            qualifiers=qualifiers,
            comment=comment,
            ig_comment=ig_comment,
            map_var_flag=map_var_flag,
            fixed_mapping=fixed_mapping,
            include_in_raw=include_in_raw,
            nn_internal=nn_internal,
            incl_cre_domain=incl_cre_domain,
            xml_codelist_values=xml_codelist_values,
        )

        return sponsor_model_variable_class_vo


class SponsorModelVariableClassMetadataVO(LibraryItemMetadataVO):
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
class SponsorModelVariableClassAR(LibraryItemAggregateRootBase):
    """
    An abstract generic sponsor model variable aggregate for versioned sponsor models
    """

    _sponsor_model_variable_class_vo: SponsorModelVariableClassVO

    @property
    def sponsor_model_variable_class_vo(self) -> SponsorModelVariableClassVO:
        return self._sponsor_model_variable_class_vo

    @property
    def name(self) -> str:
        return self._uid

    @sponsor_model_variable_class_vo.setter
    def sponsor_model_variable_class_vo(
        self, sponsor_model_variable_class_vo: SponsorModelVariableClassVO
    ):
        self._sponsor_model_variable_class_vo = sponsor_model_variable_class_vo

    @classmethod
    def from_repository_values(
        cls,
        variable_class_uid: str,
        sponsor_model_variable_class_vo: SponsorModelVariableClassVO,
        library: LibraryVO | None,
        item_metadata: SponsorModelVariableClassMetadataVO,
    ) -> Self:
        sponsor_model_variable_class_ar = cls(
            _uid=variable_class_uid,
            _sponsor_model_variable_class_vo=sponsor_model_variable_class_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return sponsor_model_variable_class_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author: str,
        sponsor_model_variable_class_vo: SponsorModelVariableClassVO,
        library: LibraryVO,
    ) -> Self:
        item_metadata = SponsorModelVariableClassMetadataVO.get_initial_item_metadata(
            author=author,
            version=sponsor_model_variable_class_vo.sponsor_model_version_number,
        )

        sponsor_model_variable_class_ar = cls(
            _uid=sponsor_model_variable_class_vo.variable_class_uid,
            _item_metadata=item_metadata,
            _library=library,
            _sponsor_model_variable_class_vo=sponsor_model_variable_class_vo,
        )
        return sponsor_model_variable_class_ar
