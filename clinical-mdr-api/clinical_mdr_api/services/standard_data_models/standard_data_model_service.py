from neomodel import db

from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.utils import BaseModel
from clinical_mdr_api.services.neomodel_ext_generic import (
    NeomodelExtGenericService,
    _AggregateRootType,
)


class StandardDataModelService(NeomodelExtGenericService):
    def _create_aggregate_root(
        self, item_input: BaseModel, library: LibraryVO
    ) -> _AggregateRootType:
        pass

    def _edit_aggregate(
        self, item: _AggregateRootType, item_edit_input: BaseModel
    ) -> _AggregateRootType:
        pass

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: _AggregateRootType
    ) -> BaseModel:
        pass

    @db.transaction
    def get_by_uid(
        self,
        uid: str,
        **kwargs,
    ):
        item = self.repository.find_by_uid(uid=uid, **kwargs)
        return item
