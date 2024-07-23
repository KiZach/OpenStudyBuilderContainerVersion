from clinical_mdr_api.domain_repositories.biomedical_concepts.activity_instance_class_repository import (
    ActivityInstanceClassRepository,
)
from clinical_mdr_api.domains.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClassAR,
    ActivityInstanceClassVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClass,
    ActivityInstanceClassInput,
    ActivityInstanceClassMappingInput,
    ActivityInstanceClassVersion,
)
from clinical_mdr_api.services._utils import raise_404_if_none
from clinical_mdr_api.services.neomodel_ext_generic import (
    NeomodelExtGenericService,
    _AggregateRootType,
)


class ActivityInstanceClassService(NeomodelExtGenericService):
    repository_interface = ActivityInstanceClassRepository
    api_model_class = ActivityInstanceClass
    version_class = ActivityInstanceClassVersion

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ActivityInstanceClassAR
    ) -> ActivityInstanceClass:
        return ActivityInstanceClass.from_activity_instance_class_ar(
            activity_instance_class_ar=item_ar,
            find_activity_instance_class_by_uid=self._repos.activity_instance_class_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self, item_input: ActivityInstanceClassInput, library: LibraryVO
    ) -> _AggregateRootType:
        return ActivityInstanceClassAR.from_input_values(
            author=self.user_initials,
            activity_instance_class_vo=ActivityInstanceClassVO.from_repository_values(
                name=item_input.name,
                order=item_input.order,
                definition=item_input.definition,
                is_domain_specific=item_input.is_domain_specific,
                parent_uid=item_input.parent_uid,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            activity_instance_class_parent_exists=self._repos.activity_instance_class_repository.check_exists_final_version,
            activity_instance_class_exists_by_name_callback=self._repos.activity_instance_class_repository.check_exists_by_name,
        )

    def _edit_aggregate(
        self, item: ActivityInstanceClassAR, item_edit_input: ActivityInstanceClassInput
    ) -> ActivityInstanceClassAR:
        item.edit_draft(
            author=self.user_initials,
            change_description=item_edit_input.change_description,
            activity_instance_class_vo=ActivityInstanceClassVO.from_repository_values(
                name=item_edit_input.name,
                order=item_edit_input.order,
                definition=item_edit_input.definition,
                is_domain_specific=item_edit_input.is_domain_specific,
                parent_uid=item_edit_input.parent_uid,
            ),
            activity_instance_class_parent_exists=self._repos.activity_instance_class_repository.check_exists_final_version,
            activity_instance_class_exists_by_name_callback=self._repos.activity_instance_class_repository.check_exists_by_name,
        )
        return item

    def patch_mappings(
        self, uid: str, mapping_input: ActivityInstanceClassMappingInput
    ) -> ActivityInstanceClass:
        activity_instance_class = (
            self._repos.activity_instance_class_repository.find_by_uid(uid)
        )
        raise_404_if_none(
            activity_instance_class,
            f"Activity instance class with uid '{uid}' does not exist.",
        )

        try:
            self._repos.activity_instance_class_repository.patch_mappings(
                uid, mapping_input.dataset_class_uids
            )
        finally:
            self._repos.activity_instance_class_repository.close()

        return self.get_by_uid(uid)
