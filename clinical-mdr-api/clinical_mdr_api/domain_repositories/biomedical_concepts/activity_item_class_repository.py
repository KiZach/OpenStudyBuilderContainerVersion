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
    ActivityItemClassRoot,
    ActivityItemClassValue,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.standard_data_model import (
    VariableClass,
)
from clinical_mdr_api.domain_repositories.neomodel_ext_item_repository import (
    NeomodelExtBaseRepository,
)
from clinical_mdr_api.domains.biomedical_concepts.activity_item_class import (
    ActivityItemClassAR,
    ActivityItemClassVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.biomedical_concepts.activity_item_class import (
    ActivityItemClass,
)


class ActivityItemClassRepository(
    NeomodelExtBaseRepository, LibraryItemRepositoryImplBase[_AggregateRootType]
):
    root_class = ActivityItemClassRoot
    value_class = ActivityItemClassValue
    return_model = ActivityItemClass

    def get_neomodel_extension_query(self) -> CustomNodeSet:
        return (
            ActivityItemClassRoot.nodes.fetch_relations(
                "has_latest_value",
                "has_library",
                "has_latest_value__has_role__has_name_root__has_latest_value",
                "has_latest_value__has_data_type__has_name_root__has_latest_value",
            )
            .fetch_optional_relations_and_collect(
                "has_activity_instance_class__has_latest_value",
                "maps_variable_class",
            )
            .fetch_optional_single_relation_of_type(
                {
                    "has_version": ("latest_version", LATEST_VERSION_ORDER_BY),
                }
            )
        )

    def _has_data_changed(
        self, ar: ActivityItemClassAR, value: ActivityItemClassValue
    ) -> bool:
        existing_activity_instance_class_uids = set(
            node.uid
            for node in value.has_version.single().has_activity_instance_class.all()
        )
        new_activity_instance_class_uids = set(
            ar.activity_item_class_vo.activity_instance_class_uids
        )
        return (
            ar.activity_item_class_vo.name != value.name
            or ar.activity_item_class_vo.definition != value.definition
            or ar.activity_item_class_vo.nci_concept_id != value.nci_concept_id
            or ar.activity_item_class_vo.order != value.order
            or ar.activity_item_class_vo.mandatory != value.mandatory
            or len(
                new_activity_instance_class_uids - existing_activity_instance_class_uids
            )
            > 0
            or ar.activity_item_class_vo.role_uid != value.has_role.get().uid
            or ar.activity_item_class_vo.data_type_uid != value.has_data_type.get().uid
        )

    def _get_or_create_value(
        self, root: ActivityItemClassRoot, ar: ActivityItemClassAR
    ) -> ActivityItemClassValue:
        for itm in root.has_version.all():
            if not self._has_data_changed(ar, itm):
                return itm
        new_value = ActivityItemClassValue(
            name=ar.activity_item_class_vo.name,
            order=ar.activity_item_class_vo.order,
            mandatory=ar.activity_item_class_vo.mandatory,
            definition=ar.activity_item_class_vo.definition,
            nci_concept_id=ar.activity_item_class_vo.nci_concept_id,
        )
        self._db_save_node(new_value)
        for (
            activity_instance_class_uid
        ) in ar.activity_item_class_vo.activity_instance_class_uids:
            activity_instance_class = ActivityInstanceClassRoot.nodes.get_or_none(
                uid=activity_instance_class_uid
            )
            root.has_activity_instance_class.connect(activity_instance_class)
        new_value.has_data_type.connect(
            CTTermRoot.nodes.get(uid=ar.activity_item_class_vo.data_type_uid)
        )
        new_value.has_role.connect(
            CTTermRoot.nodes.get(uid=ar.activity_item_class_vo.role_uid)
        )
        return new_value

    def generate_uid(self) -> str:
        return ActivityItemClassRoot.get_next_free_uid_and_increment_counter()

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: ActivityItemClassRoot,
        library: Library,
        relationship: VersionRelationship,
        value: ActivityItemClassValue,
        **_kwargs,
    ) -> ActivityItemClassAR:
        activity_instance_class_uids = [
            node.uid for node in root.has_activity_instance_class.all()
        ]
        role_term = value.has_role.get()
        data_type_term = value.has_data_type.get()
        variable_class_uids = [node.uid for node in root.maps_variable_class.all()]
        return ActivityItemClassAR.from_repository_values(
            uid=root.uid,
            activity_item_class_vo=ActivityItemClassVO.from_repository_values(
                name=value.name,
                definition=value.definition,
                nci_concept_id=value.nci_concept_id,
                order=value.order,
                mandatory=value.mandatory,
                activity_instance_class_uids=activity_instance_class_uids,
                role_uid=role_term.uid,
                role_name=role_term.has_name_root.get().has_latest_value.get().name,
                data_type_uid=data_type_term.uid,
                data_type_name=data_type_term.has_name_root.get()
                .has_latest_value.get()
                .name,
                variable_class_uids=variable_class_uids,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def patch_mappings(self, uid: str, variable_class_uids: list[str]) -> None:
        root = ActivityItemClassRoot.nodes.get(uid=uid)
        root.maps_variable_class.disconnect_all()
        for variable_class in variable_class_uids:
            variable_class = VariableClass.nodes.get(uid=variable_class)
            root.maps_variable_class.connect(variable_class)

    def _maintain_parameters(
        self,
        versioned_object: _AggregateRootType,
        root: ActivityItemClassRoot,
        value: ActivityItemClassValue,
    ) -> None:
        # This method from parent repo is not needed for this repo
        # So we use pass to skip implementation
        pass
