from abc import ABC, abstractmethod
from typing import Any, TypeVar

from neomodel import db
from pydantic import BaseModel

from clinical_mdr_api import exceptions
from clinical_mdr_api.domains.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClassAR,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryVO,
    VersioningException,
)
from clinical_mdr_api.exceptions import ValidationException
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.oauth.user import user
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    calculate_diffs,
    fill_missing_values_in_base_model_from_reference_base_model,
    is_library_editable,
    normalize_string,
)

_AggregateRootType = TypeVar("_AggregateRootType")


class NeomodelExtGenericService(ABC):
    object_name: str
    _repos: MetaRepository
    user_initials: str | None
    repository_interface: type
    api_model_class: BaseModel
    version_class: BaseModel

    def __init__(self):
        self.user_initials = user().id()
        self._repos = MetaRepository(self.user_initials)

    def __del__(self):
        self._repos.close()

    @abstractmethod
    def _create_aggregate_root(
        self, item_input: BaseModel, library: LibraryVO
    ) -> _AggregateRootType:
        raise NotImplementedError()

    @abstractmethod
    def _edit_aggregate(
        self, item: _AggregateRootType, item_edit_input: BaseModel
    ) -> _AggregateRootType:
        raise NotImplementedError

    @abstractmethod
    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: _AggregateRootType
    ) -> BaseModel:
        raise NotImplementedError

    @property
    def repository(self):
        assert self._repos is not None
        return self.repository_interface()

    @db.transaction
    def get_all_items(
        self,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        **kwargs,
    ) -> GenericFilteringReturn[BaseModel]:
        items, total = self.repository.find_all(
            total_count=total_count,
            sort_by=sort_by,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_number=page_number,
            page_size=page_size,
            **kwargs,
        )

        all_items = GenericFilteringReturn.create(items, total)

        return all_items

    def get_distinct_values_for_header(
        self,
        field_name: str,
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        result_count: int = 10,
        **kwargs,
    ) -> list[Any]:
        header_values = self.repository.get_distinct_headers(
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            result_count=result_count,
            **kwargs,
        )

        return header_values

    @db.transaction
    def get_by_uid(
        self,
        uid: str,
    ):
        item = self.repository.find_by_uid(uid=uid)
        if len(item) == 0:
            raise exceptions.NotFoundException(
                f"{self.api_model_class.__class__} with uid {uid} does not exist."
            )
        if len(item) > 1:
            raise ValidationException(
                f"Returned more than one {self.api_model_class.__class__} with uid {uid}"
            )
        return self.api_model_class.from_orm(item[0])

    def _find_by_uid_or_raise_not_found(
        self, uid: str, for_update: bool
    ) -> ActivityInstanceClassAR:
        item = self.repository.find_by_uid_2(uid=uid, for_update=for_update)

        if item is None:
            raise exceptions.NotFoundException(
                f"{self.api_model_class.__name__} with uid {uid} does not exist or there's no version with requested status or version number."
            )
        return item

    @db.transaction
    def get_version_history(self, uid: str) -> list[BaseModel]:
        if self.version_class is not None:
            all_versions = self.repository.get_all_versions_2(uid=uid)
            if all_versions is None:
                raise exceptions.NotFoundException(
                    f"{self.api_model_class.__name__} with uid {uid} does not exist."
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
    def edit_draft(self, uid: str, item_edit_input: BaseModel) -> BaseModel:
        try:
            item = self._find_by_uid_or_raise_not_found(uid=uid, for_update=True)
            fill_missing_values_in_base_model_from_reference_base_model(
                base_model_with_missing_values=item_edit_input,
                reference_base_model=self._transform_aggregate_root_to_pydantic_model(
                    item
                ),
            )
            item = self._edit_aggregate(item=item, item_edit_input=item_edit_input)
            self.repository.save(item)
            return self._transform_aggregate_root_to_pydantic_model(item)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)

    @db.transaction
    def create(self, item_input: BaseModel) -> BaseModel:
        if not self._repos.library_repository.library_exists(
            normalize_string(item_input.library_name)
        ):
            raise exceptions.BusinessLogicException(
                f"There is no library identified by provided library name ({item_input.library_name})"
            )

        library_vo = LibraryVO.from_input_values_2(
            library_name=item_input.library_name,
            is_library_editable_callback=is_library_editable,
        )
        concept_ar = self._create_aggregate_root(
            item_input=item_input, library=library_vo
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
