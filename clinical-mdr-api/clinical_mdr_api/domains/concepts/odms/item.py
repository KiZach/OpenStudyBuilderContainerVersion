from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api.domains.concepts.concept_base import ConceptVO
from clinical_mdr_api.domains.concepts.odms.odm_ar_base import OdmARBase
from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from clinical_mdr_api.exceptions import BusinessLogicException
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.utils import booltostr


@dataclass(frozen=True)
class OdmItemVO(ConceptVO):
    oid: str | None
    prompt: str | None
    datatype: str | None
    length: int | None
    significant_digits: int | None
    sas_field_name: str | None
    sds_var_name: str | None
    origin: str | None
    comment: str | None
    description_uids: list[str]
    alias_uids: list[str]
    unit_definition_uids: list[str]
    codelist_uid: str | None
    term_uids: list[str]
    activity_uid: str | None
    vendor_attribute_uids: list[str]
    vendor_element_uids: list[str]
    vendor_element_attribute_uids: list[str]

    @classmethod
    def from_repository_values(
        cls,
        oid: str | None,
        name: str,
        prompt: str | None,
        datatype: str | None,
        length: int | None,
        significant_digits: int | None,
        sas_field_name: str | None,
        sds_var_name: str | None,
        origin: str | None,
        comment: str | None,
        description_uids: list[str],
        alias_uids: list[str],
        unit_definition_uids: list[str],
        codelist_uid: str | None,
        term_uids: list[str],
        activity_uid: str | None,
        vendor_element_uids: list[str],
        vendor_attribute_uids: list[str],
        vendor_element_attribute_uids: list[str],
    ) -> Self:
        return cls(
            oid=oid,
            name=name,
            prompt=prompt,
            datatype=datatype,
            length=length,
            significant_digits=significant_digits,
            sas_field_name=sas_field_name,
            sds_var_name=sds_var_name,
            origin=origin,
            comment=comment,
            description_uids=description_uids,
            alias_uids=alias_uids,
            unit_definition_uids=unit_definition_uids,
            codelist_uid=codelist_uid,
            term_uids=term_uids,
            activity_uid=activity_uid,
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
        odm_description_exists_by_callback: Callable[[str, str, bool], bool],
        odm_alias_exists_by_callback: Callable[[str, str, bool], bool],
        unit_definition_exists_by_callback: Callable[[str, str, bool], bool],
        find_codelist_attribute_callback: Callable[[str], CTTermAttributesAR | None],
        find_all_terms_callback: Callable[
            [str], GenericFilteringReturn[CTTermNameAR] | None
        ],
        previous_name: str | None = None,
        previous_oid: str | None = None,
    ) -> None:
        self.duplication_check(
            [("name", self.name, previous_name), ("OID", self.oid, previous_oid)],
            concept_exists_by_callback,
            "ODM Item",
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
                (
                    self.unit_definition_uids,
                    "Unit Definition",
                    unit_definition_exists_by_callback,
                ),
            ],
            "ODM Item",
        )

        if self.codelist_uid is not None and not find_codelist_attribute_callback(
            self.codelist_uid
        ):
            raise BusinessLogicException(
                f"ODM Item tried to connect to non-existent Codelist identified by uid ({self.codelist_uid})."
            )

        if self.term_uids:
            if not self.codelist_uid:
                raise BusinessLogicException(
                    "To add terms you need to specify a codelist."
                )

            codelist_term_uids = [
                term.uid
                for term in find_all_terms_callback(
                    codelist_uid=self.codelist_uid
                ).items
            ]
            for term_uid in self.term_uids:
                if term_uid not in codelist_term_uids:
                    raise BusinessLogicException(
                        f"The term identified by uid ({term_uid}) doesn't belong to the specified codelist identified by uid ({self.codelist_uid})."
                    )


@dataclass
class OdmItemAR(OdmARBase):
    _concept_vo: OdmItemVO

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @property
    def concept_vo(self) -> OdmItemVO:
        return self._concept_vo

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        concept_vo: OdmItemVO,
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
        concept_vo: OdmItemVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], str | None] = (lambda: None),
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        odm_description_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        odm_alias_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        unit_definition_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        find_codelist_attribute_callback: Callable[
            [str], CTTermAttributesAR | None
        ] = lambda _: None,
        find_all_terms_callback: Callable[
            [str], GenericFilteringReturn[CTTermNameAR] | None
        ] = lambda _: None,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)

        concept_vo.validate(
            concept_exists_by_callback=concept_exists_by_callback,
            odm_description_exists_by_callback=odm_description_exists_by_callback,
            odm_alias_exists_by_callback=odm_alias_exists_by_callback,
            unit_definition_exists_by_callback=unit_definition_exists_by_callback,
            find_codelist_attribute_callback=find_codelist_attribute_callback,
            find_all_terms_callback=find_all_terms_callback,
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
        concept_vo: OdmItemVO,
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        odm_description_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        odm_alias_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        unit_definition_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        find_codelist_attribute_callback: Callable[
            [str], CTTermAttributesAR | None
        ] = lambda _: None,
        find_all_terms_callback: Callable[
            [str], GenericFilteringReturn[CTTermNameAR] | None
        ] = lambda _: None,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            concept_exists_by_callback=concept_exists_by_callback,
            odm_description_exists_by_callback=odm_description_exists_by_callback,
            odm_alias_exists_by_callback=odm_alias_exists_by_callback,
            unit_definition_exists_by_callback=unit_definition_exists_by_callback,
            find_codelist_attribute_callback=find_codelist_attribute_callback,
            find_all_terms_callback=find_all_terms_callback,
            previous_name=self.name,
            previous_oid=self._concept_vo.oid,
        )

        if self._concept_vo != concept_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._concept_vo = concept_vo


@dataclass(frozen=True)
class OdmItemRefVO:
    uid: str
    oid: str
    name: str
    item_group_uid: str
    order_number: int
    mandatory: str
    key_sequence: str
    method_oid: str
    imputation_method_oid: str
    role: str
    role_codelist_oid: str
    collection_exception_condition_oid: str | None
    vendor: dict

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        oid: str,
        name: str,
        item_group_uid: str,
        order_number: int,
        mandatory: bool,
        key_sequence: str,
        method_oid: str,
        imputation_method_oid: str,
        role: str,
        role_codelist_oid: str,
        vendor: dict,
        collection_exception_condition_oid: str | None = None,
    ) -> Self:
        return cls(
            uid=uid,
            oid=oid,
            name=name,
            item_group_uid=item_group_uid,
            order_number=order_number,
            mandatory=booltostr(mandatory),
            key_sequence=key_sequence,
            method_oid=method_oid,
            imputation_method_oid=imputation_method_oid,
            role=role,
            role_codelist_oid=role_codelist_oid,
            collection_exception_condition_oid=collection_exception_condition_oid,
            vendor=vendor,
        )


@dataclass(frozen=True)
class OdmItemTermVO:
    uid: str
    name: str
    mandatory: bool
    order: int
    display_text: str
    version: str

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        name: str,
        mandatory: bool,
        order: int,
        display_text: str,
        version: str,
    ) -> Self:
        return cls(
            uid=uid,
            name=name,
            mandatory=mandatory,
            order=order,
            display_text=display_text,
            version=version,
        )


@dataclass(frozen=True)
class OdmItemUnitDefinitionVO:
    uid: str
    name: str
    mandatory: bool
    order: int

    @classmethod
    def from_repository_values(
        cls, uid: str, name: str, mandatory: bool, order: int
    ) -> Self:
        return cls(uid=uid, name=name, mandatory=mandatory, order=order)
