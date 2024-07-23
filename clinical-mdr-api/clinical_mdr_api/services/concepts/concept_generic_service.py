from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Generic, Sequence, TypeVar

from neomodel import db
from pydantic import BaseModel

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
    VersioningException,
)
from clinical_mdr_api.models.concepts.activities.activity import (
    ActivityHierarchySimpleModel,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import SimpleTermModel
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.oauth.user import user
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    calculate_diffs,
    is_library_editable,
    normalize_string,
)

_AggregateRootType = TypeVar("_AggregateRootType")


class ConceptGenericService(Generic[_AggregateRootType], ABC):
    aggregate_class: type
    version_class: type
    repository_interface: type
    _repos: MetaRepository
    user_initials: str | None

    def __init__(self):
        self.user_initials = user().id()
        self._repos = MetaRepository(self.user_initials)

    def __del__(self):
        self._repos.close()

    @staticmethod
    def _fill_missing_values_in_base_model_from_reference_base_model(
        *, base_model_with_missing_values: BaseModel, reference_base_model: BaseModel
    ) -> None:
        """
        Method fills missing values in the PATCH payload when only partial payload is sent by client.
        It takes the values from the object that will be updated in the request.
        There is some difference between GET and PATCH/POST API models in a few fields (in GET requests we return
        unique identifiers of some items and theirs name) and in the PATCH/POST requests we expect only the uid to be
        sent from client.
        Because of that difference, we only want to take unique identifiers from these objects in the PATCH/POST
        request payloads.
        :param base_model_with_missing_values: BaseModel
        :param reference_base_model: BaseModel
        :return None:
        """
        for field_name in base_model_with_missing_values.__fields_set__:
            if isinstance(
                getattr(base_model_with_missing_values, field_name), BaseModel
            ) and isinstance(getattr(reference_base_model, field_name), BaseModel):
                ConceptGenericService._fill_missing_values_in_base_model_from_reference_base_model(
                    base_model_with_missing_values=getattr(
                        base_model_with_missing_values, field_name
                    ),
                    reference_base_model=getattr(reference_base_model, field_name),
                )

        for field_name in (
            reference_base_model.__fields_set__
            - base_model_with_missing_values.__fields_set__
        ).intersection(base_model_with_missing_values.__fields__):
            if isinstance(getattr(reference_base_model, field_name), SimpleTermModel):
                setattr(
                    base_model_with_missing_values,
                    field_name,
                    getattr(reference_base_model, field_name).term_uid,
                )
            elif isinstance(getattr(reference_base_model, field_name), Sequence):
                if reference_base_model.__fields__[field_name].type_ is SimpleTermModel:
                    setattr(
                        base_model_with_missing_values,
                        field_name,
                        [
                            term.term_uid
                            for term in getattr(reference_base_model, field_name)
                        ],
                    )
                elif (
                    reference_base_model.__fields__[field_name].type_
                    is ActivityHierarchySimpleModel
                ):
                    setattr(
                        base_model_with_missing_values,
                        field_name,
                        [
                            term.uid
                            for term in getattr(reference_base_model, field_name)
                        ],
                    )
                else:
                    setattr(
                        base_model_with_missing_values,
                        field_name,
                        getattr(reference_base_model, field_name),
                    )
            else:
                setattr(
                    base_model_with_missing_values,
                    field_name,
                    getattr(reference_base_model, field_name),
                )

    @staticmethod
    def fill_in_additional_fields(
        concept_edit_input: BaseModel, current_ar: _AggregateRootType
    ) -> None:
        """
        Subclasses should override this method to preserve field values which are not explicitly sent in the PATCH payload.
        If a relevant field is not included the PATCH payload,
        this method should populate `concept_edit_input` object with the existing value of that field.

        This method deals only with fields that cannot be preserved
        by the generic `_fill_missing_values_in_base_model_from_reference_base_model` method.
        For example, it should handle all fields that represent links to other entities, e.g `dose_form_uids`.
        """

    @property
    def repository(self) -> ConceptGenericRepository[_AggregateRootType]:
        assert self._repos is not None
        return self.repository_interface()

    @abstractmethod
    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: _AggregateRootType
    ) -> BaseModel:
        raise NotImplementedError

    @abstractmethod
    def _create_aggregate_root(
        self, concept_input: BaseModel, library: LibraryVO
    ) -> _AggregateRootType:
        raise NotImplementedError()

    @abstractmethod
    def _edit_aggregate(
        self, item: _AggregateRootType, concept_edit_input: BaseModel
    ) -> _AggregateRootType:
        raise NotImplementedError

    def get_input_or_previous_property(
        self, input_property: Any, previous_property: Any
    ):
        return input_property if input_property is not None else previous_property

    @db.transaction
    def get_all_concepts(
        self,
        library: str | None = None,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        only_specific_status: str = ObjectStatus.LATEST.name,
        **kwargs,
    ) -> GenericFilteringReturn[BaseModel]:
        return self.non_transactional_get_all_concepts(
            library,
            sort_by,
            page_number,
            page_size,
            filter_by,
            filter_operator,
            total_count,
            only_specific_status,
            **kwargs,
        )

    def non_transactional_get_all_concepts(
        self,
        library: str | None = None,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        only_specific_status: str = ObjectStatus.LATEST.name,
        **kwargs,
    ) -> GenericFilteringReturn[BaseModel]:
        self.enforce_library(library)

        items, total = self.repository.find_all(
            library=library,
            total_count=total_count,
            sort_by=sort_by,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_number=page_number,
            page_size=page_size,
            only_specific_status=only_specific_status,
            **kwargs,
        )

        all_concepts = GenericFilteringReturn.create(items, total)
        all_concepts.items = [
            self._transform_aggregate_root_to_pydantic_model(concept_ar)
            for concept_ar in all_concepts.items
        ]

        return all_concepts

    def get_distinct_values_for_header(
        self,
        library: str | None,
        field_name: str,
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        result_count: int = 10,
        **kwargs,
    ) -> list[Any]:
        self.enforce_library(library)

        header_values = self.repository.get_distinct_headers(
            library=library,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            result_count=result_count,
            **kwargs,
        )

        return header_values

    @db.transaction
    def get_all_concept_versions(
        self,
        library: str | None = None,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        **kwargs,
    ) -> GenericFilteringReturn[BaseModel]:
        self.enforce_library(library)

        items, total = self.repository.find_all(
            library=library,
            total_count=total_count,
            sort_by=sort_by,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_number=page_number,
            page_size=page_size,
            return_all_versions=True,
            only_specific_status=None,
            **kwargs,
        )

        all_concept_versions = GenericFilteringReturn.create(items, total)
        all_concept_versions.items = [
            self._transform_aggregate_root_to_pydantic_model(concept_ar)
            for concept_ar in all_concept_versions.items
        ]

        return all_concept_versions

    @db.transaction
    def get_by_uid(
        self,
        uid: str,
        version: str | None = None,
        at_specific_date: datetime | None = None,
        status: str | None = None,
    ) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(
            uid=uid, version=version, at_specific_date=at_specific_date, status=status
        )
        return self._transform_aggregate_root_to_pydantic_model(item)

    def _find_by_uid_or_raise_not_found(
        self,
        uid: str,
        version: str | None = None,
        at_specific_date: datetime | None = None,
        status: LibraryItemStatus | None = None,
        for_update: bool | None = False,
    ) -> _AggregateRootType:
        item = self.repository.find_by_uid_2(
            uid=uid,
            at_specific_date=at_specific_date,
            version=version,
            status=status,
            for_update=for_update,
        )

        if item is None:
            raise exceptions.NotFoundException(
                f"{self.aggregate_class.__name__} with uid {uid} does not exist or there's no version with requested status or version number."
            )
        return item

    @db.transaction
    def get_version_history(self, uid: str) -> list[BaseModel]:
        if self.version_class is not None:
            all_versions = self.repository.get_all_versions_2(uid=uid)
            if all_versions is None:
                raise exceptions.NotFoundException(
                    f"{self.aggregate_class.__name__} with uid {uid} does not exist."
                )
            versions = [
                self._transform_aggregate_root_to_pydantic_model(codelist_ar).dict()
                for codelist_ar in all_versions
            ]
            return calculate_diffs(versions, self.version_class)
        return []

    @db.transaction
    def create_new_version(self, uid: str) -> BaseModel:
        try:
            item = self._find_by_uid_or_raise_not_found(uid, for_update=True)
            item.create_new_version(author=self.user_initials)
            self.repository.save(item)
            return self._transform_aggregate_root_to_pydantic_model(item)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)

    @db.transaction
    def edit_draft(self, uid: str, concept_edit_input: BaseModel) -> BaseModel:
        return self.non_transactional_edit(uid, concept_edit_input)

    def non_transactional_edit(
        self, uid: str, concept_edit_input: BaseModel
    ) -> BaseModel:
        try:
            item = self._find_by_uid_or_raise_not_found(uid=uid, for_update=True)
            self._fill_missing_values_in_base_model_from_reference_base_model(
                base_model_with_missing_values=concept_edit_input,
                reference_base_model=self._transform_aggregate_root_to_pydantic_model(
                    item
                ),
            )
            self.fill_in_additional_fields(concept_edit_input, item)
            item = self._edit_aggregate(
                item=item, concept_edit_input=concept_edit_input
            )
            self.repository.save(item)
            return self._transform_aggregate_root_to_pydantic_model(item)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)

    @db.transaction
    def create(self, concept_input: BaseModel) -> BaseModel:
        return self.non_transactional_create(concept_input)

    def non_transactional_create(self, concept_input: BaseModel) -> BaseModel:
        if not self._repos.library_repository.library_exists(
            normalize_string(concept_input.library_name)
        ):
            raise exceptions.BusinessLogicException(
                f"There is no library identified by provided library name ({concept_input.library_name})"
            )

        library_vo = LibraryVO.from_input_values_2(
            library_name=concept_input.library_name,
            is_library_editable_callback=is_library_editable,
        )

        concept_ar = self._create_aggregate_root(
            concept_input=concept_input, library=library_vo
        )
        self.repository.save(concept_ar)
        return self._transform_aggregate_root_to_pydantic_model(concept_ar)

    @db.transaction
    def approve(self, uid: str) -> BaseModel:
        try:
            item = self._find_by_uid_or_raise_not_found(uid, for_update=True)
            item.approve(author=self.user_initials)
            self.repository.save(item)
            return self._transform_aggregate_root_to_pydantic_model(item)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)

    @db.transaction
    def inactivate_final(self, uid: str) -> BaseModel:
        try:
            item = self._find_by_uid_or_raise_not_found(uid, for_update=True)
            item.inactivate(author=self.user_initials)
            self.repository.save(item)
            return self._transform_aggregate_root_to_pydantic_model(item)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)

    @db.transaction
    def reactivate_retired(self, uid: str) -> BaseModel:
        try:
            item = self._find_by_uid_or_raise_not_found(uid, for_update=True)
            item.reactivate(author=self.user_initials)
            self.repository.save(item)
            return self._transform_aggregate_root_to_pydantic_model(item)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)

    @db.transaction
    def soft_delete(self, uid: str) -> None:
        try:
            item = self._find_by_uid_or_raise_not_found(uid, for_update=True)
            item.soft_delete()
            self.repository.save(item)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)

    def enforce_library(self, library: str | None):
        if library is not None and not self._repos.library_repository.library_exists(
            normalize_string(library)
        ):
            raise exceptions.BusinessLogicException(
                f"There is no library identified by provided library name ({library})"
            )
