from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api.domains.concepts.concept_base import ConceptVO
from clinical_mdr_api.domains.concepts.odms.odm_ar_base import OdmARBase
from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from clinical_mdr_api.exceptions import BusinessLogicException
from clinical_mdr_api.utils import booltostr


@dataclass(frozen=True)
class OdmFormVO(ConceptVO):
    oid: str | None
    repeating: str | None
    sdtm_version: str | None
    scope_uid: str | None
    description_uids: list[str]
    alias_uids: list[str]
    activity_group_uids: list[str]
    item_group_uids: list[str]
    vendor_attribute_uids: list[str]
    vendor_element_uids: list[str]
    vendor_element_attribute_uids: list[str]

    @classmethod
    def from_repository_values(
        cls,
        oid: str | None,
        name: str,
        sdtm_version: str | None,
        repeating: str | None,
        scope_uid: str | None,
        description_uids: list[str],
        alias_uids: list[str],
        activity_group_uids: list[str],
        item_group_uids: list[str],
        vendor_element_uids: list[str],
        vendor_attribute_uids: list[str],
        vendor_element_attribute_uids: list[str],
    ) -> Self:
        return cls(
            oid=oid,
            name=name,
            sdtm_version=sdtm_version,
            repeating=repeating,
            scope_uid=scope_uid,
            description_uids=description_uids,
            alias_uids=alias_uids,
            activity_group_uids=activity_group_uids,
            item_group_uids=item_group_uids,
            vendor_element_uids=vendor_element_uids,
            vendor_attribute_uids=vendor_attribute_uids,
            vendor_element_attribute_uids=vendor_element_attribute_uids,
            name_sentence_case=None,
            definition=None,
            abbreviation=None,
            is_template_parameter=False,
        )

    def validate(
        self,
        concept_exists_by_callback: Callable[[str, str, bool], bool],
        find_term_callback: Callable[[str], CTTermAttributesAR | None],
        odm_description_exists_by_callback: Callable[[str, str, bool], bool],
        odm_alias_exists_by_callback: Callable[[str, str, bool], bool],
        previous_name: str | None = None,
        previous_oid: str | None = None,
    ) -> None:
        self.duplication_check(
            [("name", self.name, previous_name), ("OID", self.oid, previous_oid)],
            concept_exists_by_callback,
            "ODM Form",
        )
        self.check_concepts_exist(
            [
                (
                    self.description_uids,
                    "ODM Description",
                    odm_description_exists_by_callback,
                ),
                (
                    self.alias_uids,
                    "ODM Alias",
                    odm_alias_exists_by_callback,
                ),
            ],
            "ODM Form",
        )

        if self.scope_uid is not None and not find_term_callback(self.scope_uid):
            raise BusinessLogicException(
                f"ODM Form tried to connect to non-existent Scope identified by uid ({self.scope_uid})."
            )


@dataclass
class OdmFormAR(OdmARBase):
    _concept_vo: OdmFormVO

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @property
    def concept_vo(self) -> OdmFormVO:
        return self._concept_vo

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        concept_vo: OdmFormVO,
        library: LibraryVO | None,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        return cls(
            _uid=uid,
            _concept_vo=concept_vo,
            _library=library,
            _item_metadata=item_metadata,
        )

    @classmethod
    def from_input_values(
        cls,
        author: str,
        concept_vo: OdmFormVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], str | None] = (lambda: None),
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        find_term_callback: Callable[[str], CTTermAttributesAR | None] = lambda _: None,
        odm_description_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        odm_alias_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)

        concept_vo.validate(
            concept_exists_by_callback=concept_exists_by_callback,
            find_term_callback=find_term_callback,
            odm_description_exists_by_callback=odm_description_exists_by_callback,
            odm_alias_exists_by_callback=odm_alias_exists_by_callback,
        )

        return cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )

    def edit_draft(
        self,
        author: str,
        change_description: str | None,
        concept_vo: OdmFormVO,
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        find_term_callback: Callable[[str], CTTermAttributesAR | None] = lambda _: None,
        odm_description_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        odm_alias_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            concept_exists_by_callback=concept_exists_by_callback,
            find_term_callback=find_term_callback,
            odm_description_exists_by_callback=odm_description_exists_by_callback,
            odm_alias_exists_by_callback=odm_alias_exists_by_callback,
            previous_name=self.name,
            previous_oid=self._concept_vo.oid,
        )

        if self._concept_vo != concept_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._concept_vo = concept_vo


@dataclass(frozen=True)
class OdmFormRefVO:
    uid: str
    name: str
    study_event_uid: str
    order_number: int
    mandatory: str
    locked: str
    collection_exception_condition_oid: str

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        name: str,
        study_event_uid: str,
        order_number: int,
        mandatory: bool,
        locked: bool,
        collection_exception_condition_oid: str,
    ) -> Self:
        return cls(
            uid=uid,
            name=name,
            study_event_uid=study_event_uid,
            order_number=order_number,
            mandatory=booltostr(mandatory),
            locked=booltostr(locked),
            collection_exception_condition_oid=collection_exception_condition_oid,
        )
