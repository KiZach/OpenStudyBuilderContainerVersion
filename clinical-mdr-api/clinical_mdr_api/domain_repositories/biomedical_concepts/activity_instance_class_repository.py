from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    LATEST_VERSION_ORDER_BY,
    CustomNodeSet,
)
from clinical_mdr_api.domain_repositories.models.biomedical_concepts import (
    ActivityInstanceClassRoot,
    ActivityInstanceClassValue,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.standard_data_model import DatasetClass
from clinical_mdr_api.domain_repositories.neomodel_ext_item_repository import (
    NeomodelExtBaseRepository,
)
from clinical_mdr_api.domains.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClassAR,
    ActivityInstanceClassVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClass,
)


class ActivityInstanceClassRepository(
    NeomodelExtBaseRepository, LibraryItemRepositoryImplBase[_AggregateRootType]
):
    root_class = ActivityInstanceClassRoot
    value_class = ActivityInstanceClassValue
    return_model = ActivityInstanceClass

    def get_neomodel_extension_query(self) -> CustomNodeSet:
        return (
            ActivityInstanceClassRoot.nodes.fetch_relations(
                "has_latest_value", "has_library"
            )
            .fetch_optional_relations("parent_class__has_latest_value")
            .fetch_optional_relations_and_collect("maps_dataset_class")
            .fetch_optional_single_relation_of_type(
                {
                    "has_version": ("latest_version", LATEST_VERSION_ORDER_BY),
                }
            )
        )

    def _has_data_changed(
        self, ar: ActivityInstanceClassAR, value: ActivityInstanceClassValue
    ) -> bool:
        parent = value.has_latest_value.get().parent_class.get_or_none()
        return (
            ar.activity_instance_class_vo.name != value.name
            or ar.activity_instance_class_vo.order != value.order
            or ar.activity_instance_class_vo.definition != value.definition
            or ar.activity_instance_class_vo.is_domain_specific
            != value.is_domain_specific
            or ar.activity_instance_class_vo.parent_uid != parent.uid
            if parent
            else None
        )

    def _get_or_create_value(
        self, root: ActivityInstanceClassRoot, ar: ActivityInstanceClassAR
    ) -> ActivityInstanceClassValue:
        for itm in root.has_version.all():
            if not self._has_data_changed(ar, itm):
                return itm
        latest_draft = root.latest_draft.get_or_none()
        if latest_draft and not self._has_data_changed(ar, latest_draft):
            return latest_draft
        latest_final = root.latest_final.get_or_none()
        if latest_final and not self._has_data_changed(ar, latest_final):
            return latest_final
        latest_retired = root.latest_retired.get_or_none()
        if latest_retired and not self._has_data_changed(ar, latest_retired):
            return latest_retired
        new_value = ActivityInstanceClassValue(
            name=ar.activity_instance_class_vo.name,
            order=ar.activity_instance_class_vo.order,
            definition=ar.activity_instance_class_vo.definition,
            is_domain_specific=ar.activity_instance_class_vo.is_domain_specific,
        )
        self._db_save_node(new_value)
        if ar.activity_instance_class_vo.parent_uid:
            parent = ActivityInstanceClassRoot.nodes.get_or_none(
                uid=ar.activity_instance_class_vo.parent_uid
            )
            root.parent_class.connect(parent)
        return new_value

    def generate_uid(self) -> str:
        return ActivityInstanceClassRoot.get_next_free_uid_and_increment_counter()

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: ActivityInstanceClassRoot,
        library: Library,
        relationship: VersionRelationship,
        value: ActivityInstanceClassValue,
        **_kwargs,
    ) -> ActivityInstanceClassAR:
        parent_class = root.parent_class.get_or_none()
        dataset_class_uids = [node.uid for node in root.maps_dataset_class.all()]
        return ActivityInstanceClassAR.from_repository_values(
            uid=root.uid,
            activity_instance_class_vo=ActivityInstanceClassVO.from_repository_values(
                name=value.name,
                order=value.order,
                definition=value.definition,
                is_domain_specific=value.is_domain_specific,
                parent_uid=parent_class.uid if parent_class else None,
                dataset_class_uids=dataset_class_uids,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def patch_mappings(self, uid: str, dataset_class_uids: list[str]) -> None:
        root = ActivityInstanceClassRoot.nodes.get(uid=uid)
        root.maps_dataset_class.disconnect_all()
        for dataset_class in dataset_class_uids:
            dataset_class = DatasetClass.nodes.get(uid=dataset_class)
            root.maps_dataset_class.connect(dataset_class)

    def _maintain_parameters(
        self,
        versioned_object: _AggregateRootType,
        root: ActivityInstanceClassRoot,
        value: ActivityInstanceClassValue,
    ) -> None:
        # This method from parent repo is not needed for this repo
        # So we use pass to skip implementation
        pass
