from typing import Any, TypeVar

from neomodel import db
from pydantic import BaseModel

from clinical_mdr_api import exceptions, models
from clinical_mdr_api.domain_repositories.dictionaries.dictionary_codelist_repository import (
    DictionaryCodelistGenericRepository,
)
from clinical_mdr_api.domains.dictionaries.dictionary_codelist import (
    DictionaryCodelistAR,
    DictionaryCodelistVO,
    DictionaryType,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryVO,
    VersioningException,
)
from clinical_mdr_api.models import (
    DictionaryCodelist,
    DictionaryCodelistCreateInput,
    DictionaryCodelistEditInput,
    DictionaryCodelistVersion,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.oauth.user import user
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository  # type: ignore
from clinical_mdr_api.services._utils import (
    calculate_diffs,
    is_library_editable,
    normalize_string,
)

_AggregateRootType = TypeVar("_AggregateRootType")


class DictionaryCodelistGenericService:
    @classmethod
    def get_input_or_previous_property(
        cls, input_property: Any, previous_property: Any
    ):
        return input_property if input_property is not None else previous_property

    aggregate_class = DictionaryCodelistAR
    version_class = DictionaryCodelistVersion
    repository_interface = DictionaryCodelistGenericRepository
    _repos: MetaRepository
    user_initials: str | None

    def __init__(self):
        self.user_initials = user().id()

        self._repos = MetaRepository(self.user_initials)

    def __del__(self):
        self._repos.close()

    @property
    def repository(self) -> DictionaryCodelistGenericRepository:
        assert self._repos is not None
        return self.repository_interface()

    @classmethod
    def get_dictionary_type(cls, library: str):
        library = library.lower()
        if library == "snomed":
            dictionary_type = DictionaryType.SNOMED
        elif library == "med-rt":
            dictionary_type = DictionaryType.MED_RT
        elif library == "unii":
            dictionary_type = DictionaryType.UNII
        elif library == "ucum":
            dictionary_type = DictionaryType.UCUM
        else:
            raise exceptions.BusinessLogicException(
                f"The following dictionary type ({library}) is not supported."
            )
        return dictionary_type

    @db.transaction
    def get_all_dictionary_codelists(
        self,
        library: str,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[BaseModel]:
        self.enforce_library(library)

        dictionary_type = self.get_dictionary_type(library=library)

        items, total = self.repository.find_all(
            library_name=dictionary_type,
            sort_by=sort_by,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_number=page_number,
            page_size=page_size,
            total_count=total_count,
        )

        all_dictionary_codelists = GenericFilteringReturn.create(items, total)
        all_dictionary_codelists.items = [
            DictionaryCodelist.from_dictionary_codelist_ar(dictionary_codelist_ar)
            for dictionary_codelist_ar in all_dictionary_codelists.items
        ]

        return all_dictionary_codelists

    def get_distinct_values_for_header(
        self,
        library: str,
        field_name: str,
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        result_count: int = 10,
    ) -> list[str]:
        self.enforce_library(library)

        # First, check that attributes provided for filtering exist in the return class
        # Properties can be nested => check if root property exists in class
        if not models.utils.is_attribute_in_model(
            field_name.split(".")[0], DictionaryCodelist
        ):
            raise exceptions.NotFoundException(
                f"Invalid field name specified in the filter dictionary : {field_name}"
            )

        dictionary_type = self.get_dictionary_type(library=library)

        header_values = self.repository.get_distinct_headers(
            library=dictionary_type,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            result_count=result_count,
        )
        return header_values

    @db.transaction
    def get_by_uid(self, codelist_uid: str, version: str | None = None) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(
            codelist_uid=codelist_uid, version=version
        )
        return DictionaryCodelist.from_dictionary_codelist_ar(item)

    def _find_by_uid_or_raise_not_found(
        self,
        codelist_uid: str,
        version: str | None = None,
        for_update: bool | None = False,
    ) -> _AggregateRootType:
        item = self.repository.find_by_uid_2(
            uid=codelist_uid, version=version, for_update=for_update
        )
        if item is None:
            raise exceptions.NotFoundException(
                f"""{self.aggregate_class.__name__} with uid {codelist_uid} does not exist
                or there's no version with requested status or version number."""
            )
        return item

    @db.transaction
    def get_version_history(self, codelist_uid) -> list[BaseModel]:
        if self.version_class is not None:
            all_versions = self.repository.get_all_versions_2(codelist_uid)
            if all_versions is None:
                raise exceptions.NotFoundException(
                    f"{self.aggregate_class.__name__} with uid {codelist_uid} does not exist."
                )
            versions = [
                DictionaryCodelist.from_dictionary_codelist_ar(
                    dictionary_codelist_ar
                ).dict()
                for dictionary_codelist_ar in all_versions
            ]
            return calculate_diffs(versions, self.version_class)
        return []

    @db.transaction
    def create(
        self, codelist_input: DictionaryCodelistCreateInput
    ) -> DictionaryCodelist:
        if not self._repos.library_repository.library_exists(
            normalize_string(codelist_input.library_name)
        ):
            raise exceptions.BusinessLogicException(
                f"There is no library identified by provided library name ({codelist_input.library_name})"
            )

        library_vo = LibraryVO.from_input_values_2(
            library_name=codelist_input.library_name,
            is_library_editable_callback=is_library_editable,
        )
        dictionary_codelist_ar = DictionaryCodelistAR.from_input_values(
            author=self.user_initials,
            dictionary_codelist_vo=DictionaryCodelistVO.from_input_values(
                name=codelist_input.name,
                is_template_parameter=codelist_input.template_parameter,
                current_terms=[],
                previous_terms=[],
                codelist_exists_by_name_callback=self.repository.codelist_exists_by_name,
            ),
            library=library_vo,
            generate_uid_callback=self.repository.generate_uid,
        )

        self.repository.save(dictionary_codelist_ar)

        return DictionaryCodelist.from_dictionary_codelist_ar(dictionary_codelist_ar)

    @db.transaction
    def create_new_version(self, codelist_uid: str) -> BaseModel:
        try:
            item = self._find_by_uid_or_raise_not_found(codelist_uid, for_update=True)
            item.create_new_version(author=self.user_initials)
            self.repository.save(item)
            return DictionaryCodelist.from_dictionary_codelist_ar(item)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)

    @db.transaction
    def edit_draft(
        self, codelist_uid: str, codelist_input: DictionaryCodelistEditInput
    ) -> BaseModel:
        try:
            item = self._find_by_uid_or_raise_not_found(codelist_uid, for_update=True)
            item.edit_draft(
                author=self.user_initials,
                change_description=codelist_input.change_description,
                dictionary_codelist_vo=DictionaryCodelistVO.from_input_values(
                    name=self.get_input_or_previous_property(
                        codelist_input.name, item.name
                    ),
                    is_template_parameter=self.get_input_or_previous_property(
                        codelist_input.template_parameter,
                        item.dictionary_codelist_vo.is_template_parameter,
                    ),
                    current_terms=item.dictionary_codelist_vo.current_terms,
                    previous_terms=item.dictionary_codelist_vo.previous_terms,
                ),
                codelist_exists_by_name_callback=self.repository.codelist_exists_by_name,
            )
            self.repository.save(item)
            return DictionaryCodelist.from_dictionary_codelist_ar(item)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)

    @db.transaction
    def approve(self, codelist_uid: str) -> BaseModel:
        try:
            item = self._find_by_uid_or_raise_not_found(
                codelist_uid=codelist_uid, for_update=True
            )
            item.approve(author=self.user_initials)
            self.repository.save(item)
            return DictionaryCodelist.from_dictionary_codelist_ar(item)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)

    def enforce_library(self, library: str | None):
        if library is not None and not self._repos.library_repository.library_exists(
            normalize_string(library)
        ):
            raise exceptions.BusinessLogicException(
                f"There is no library identified by provided library name ({library})"
            )

    @db.transaction
    def add_term(self, codelist_uid: str, term_uid: str) -> DictionaryCodelist:
        if not self.repository.codelist_exists(normalize_string(codelist_uid)):
            raise exceptions.BusinessLogicException(
                f"There is no DictionaryCodelistRoot identified by provided codelist_uid ({codelist_uid})"
            )
        if not self._repos.dictionary_term_generic_repository.term_exists(
            normalize_string(term_uid)
        ):
            raise exceptions.BusinessLogicException(
                f"There is no DictionaryTermRoot identified by provided term_uid ({term_uid})"
            )

        dictionary_codelist_ar = self._find_by_uid_or_raise_not_found(
            codelist_uid=codelist_uid, for_update=True
        )

        dictionary_codelist_ar.add_term(
            codelist_uid=codelist_uid, term_uid=term_uid, author=self.user_initials
        )

        self.repository.save(dictionary_codelist_ar)
        return DictionaryCodelist.from_dictionary_codelist_ar(
            dictionary_codelist_ar=dictionary_codelist_ar
        )

    @db.transaction
    def remove_term(self, codelist_uid: str, term_uid: str) -> DictionaryCodelist:
        if not self.repository.codelist_exists(normalize_string(codelist_uid)):
            raise exceptions.BusinessLogicException(
                f"There is no DictionaryCodelistRoot identified by provided codelist_uid ({codelist_uid})"
            )
        if not self._repos.dictionary_term_generic_repository.term_exists(
            normalize_string(term_uid)
        ):
            raise exceptions.BusinessLogicException(
                f"There is no DictionaryTermRoot identified by provided term_uid ({term_uid})"
            )

        dictionary_codelist_ar = self._find_by_uid_or_raise_not_found(
            codelist_uid=codelist_uid, for_update=True
        )

        dictionary_codelist_ar.remove_term(
            codelist_uid=codelist_uid, term_uid=term_uid, author=self.user_initials
        )

        self.repository.save(dictionary_codelist_ar)
        return DictionaryCodelist.from_dictionary_codelist_ar(
            dictionary_codelist_ar=dictionary_codelist_ar
        )
