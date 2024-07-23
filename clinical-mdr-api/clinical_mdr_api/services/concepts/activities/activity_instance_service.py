import datetime

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain_repositories.concepts.activities.activity_instance_repository import (
    ActivityInstanceRepository,
)
from clinical_mdr_api.domains.concepts.activities.activity_instance import (
    ActivityInstanceAR,
    ActivityInstanceGroupingVO,
    ActivityInstanceVO,
)
from clinical_mdr_api.domains.concepts.activities.activity_item import (
    ActivityItemVO,
    LibraryItem,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryVO,
    VersioningException,
)
from clinical_mdr_api.exceptions import NotFoundException
from clinical_mdr_api.models.concepts.activities.activity_instance import (
    ActivityInstance,
    ActivityInstanceCreateInput,
    ActivityInstanceEditInput,
    ActivityInstanceOverview,
    ActivityInstanceVersion,
)
from clinical_mdr_api.services.concepts import constants
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
    _AggregateRootType,
)


class ActivityInstanceService(ConceptGenericService[ActivityInstanceAR]):
    aggregate_class = ActivityInstanceAR
    repository_interface = ActivityInstanceRepository
    version_class = ActivityInstanceVersion

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ActivityInstanceAR
    ) -> ActivityInstance:
        return ActivityInstance.from_activity_ar(
            activity_ar=item_ar,
            find_activity_hierarchy_by_uid=self._repos.activity_repository.find_by_uid_2,
            find_activity_subgroup_by_uid=self._repos.activity_subgroup_repository.find_by_uid_2,
            find_activity_group_by_uid=self._repos.activity_group_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self, concept_input: ActivityInstanceCreateInput, library: LibraryVO
    ) -> _AggregateRootType:
        activity_items = []
        if concept_input.activity_items is not None:
            for item in concept_input.activity_items:
                unit_definitions = [
                    LibraryItem(uid=unit_uid, name=None)
                    for unit_uid in item.unit_definition_uids
                ]
                ct_terms = [
                    LibraryItem(uid=term_uid, name=None)
                    for term_uid in item.ct_term_uids
                ]
                activity_items.append(
                    ActivityItemVO.from_repository_values(
                        activity_item_class_uid=item.activity_item_class_uid,
                        activity_item_class_name=None,
                        ct_terms=ct_terms,
                        unit_definitions=unit_definitions,
                    )
                )

        return ActivityInstanceAR.from_input_values(
            author=self.user_initials,
            concept_vo=ActivityInstanceVO.from_repository_values(
                nci_concept_id=concept_input.nci_concept_id,
                name=concept_input.name,
                name_sentence_case=concept_input.name_sentence_case,
                definition=concept_input.definition,
                abbreviation=concept_input.abbreviation,
                topic_code=concept_input.topic_code,
                adam_param_code=concept_input.adam_param_code,
                is_required_for_activity=concept_input.is_required_for_activity,
                is_default_selected_for_activity=concept_input.is_default_selected_for_activity,
                is_data_sharing=concept_input.is_data_sharing,
                is_legacy_usage=concept_input.is_legacy_usage,
                is_derived=concept_input.is_derived,
                legacy_description=concept_input.legacy_description,
                activity_groupings=[
                    ActivityInstanceGroupingVO(
                        activity_uid=activity_grouping.activity_uid,
                        activity_group_uid=activity_grouping.activity_group_uid,
                        activity_subgroup_uid=activity_grouping.activity_subgroup_uid,
                    )
                    for activity_grouping in concept_input.activity_groupings
                ]
                if concept_input.activity_groupings
                else [],
                activity_instance_class_uid=concept_input.activity_instance_class_uid,
                activity_instance_class_name=None,
                activity_items=activity_items,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            concept_exists_by_callback=self.repository.exists_by,
            activity_instance_class_exists_by_uid_callback=self._repos.activity_instance_class_repository.check_exists_final_version,
            activity_item_class_exists_by_uid_callback=self._repos.activity_item_class_repository.check_exists_final_version,
            ct_term_exists_by_uid_callback=self._repos.ct_term_name_repository.term_exists,
            unit_definition_exists_by_uid_callback=self._repos.unit_definition_repository.final_concept_exists,
            activity_hierarchy_exists_by_uid_callback=self._repos.activity_repository.final_concept_exists,
            activity_group_exists=self._repos.activity_group_repository.final_concept_exists,
            activity_subgroup_exists=self._repos.activity_subgroup_repository.final_concept_exists,
        )

    def non_transactional_edit(
        self, uid: str, concept_edit_input: ActivityInstanceEditInput
    ) -> ActivityInstance:
        try:
            item = self._find_by_uid_or_raise_not_found(uid=uid, for_update=True)
            edited_item = self._edit_aggregate(
                item=item, concept_edit_input=concept_edit_input
            )
            self.repository.save(edited_item)
            return self._transform_aggregate_root_to_pydantic_model(edited_item)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)

    def _edit_aggregate(
        self, item: ActivityInstanceAR, concept_edit_input: ActivityInstanceEditInput
    ) -> ActivityInstanceAR:
        if concept_edit_input.activity_groupings:
            activity_groupings = [
                ActivityInstanceGroupingVO(
                    activity_uid=activity_grouping.activity_uid,
                    activity_group_uid=activity_grouping.activity_group_uid,
                    activity_subgroup_uid=activity_grouping.activity_subgroup_uid,
                )
                for activity_grouping in concept_edit_input.activity_groupings
            ]
        else:
            activity_groupings = [
                ActivityInstanceGroupingVO(
                    activity_uid=activity_grouping.activity_uid,
                    activity_group_uid=activity_grouping.activity_group_uid,
                    activity_subgroup_uid=activity_grouping.activity_subgroup_uid,
                )
                for activity_grouping in item.concept_vo.activity_groupings
            ]

        if concept_edit_input.activity_items:
            activity_items = []
            for activity_item in concept_edit_input.activity_items:
                unit_definitions = [
                    LibraryItem(uid=unit_uid, name=None)
                    for unit_uid in activity_item.unit_definition_uids
                ]
                ct_terms = [
                    LibraryItem(uid=term_uid, name=None)
                    for term_uid in activity_item.ct_term_uids
                ]
                activity_items.append(
                    ActivityItemVO.from_repository_values(
                        activity_item_class_uid=activity_item.activity_item_class_uid,
                        activity_item_class_name=None,
                        ct_terms=ct_terms,
                        unit_definitions=unit_definitions,
                    )
                )
        else:
            activity_items = item.concept_vo.activity_items

        item.edit_draft(
            author=self.user_initials,
            change_description=concept_edit_input.change_description,
            concept_vo=ActivityInstanceVO.from_repository_values(
                nci_concept_id=concept_edit_input.nci_concept_id,
                name=concept_edit_input.name or item.name,
                name_sentence_case=concept_edit_input.name_sentence_case
                or item.concept_vo.name_sentence_case,
                definition=concept_edit_input.definition or item.concept_vo.definition,
                abbreviation=concept_edit_input.abbreviation
                or item.concept_vo.abbreviation,
                topic_code=concept_edit_input.topic_code or item.concept_vo.topic_code,
                adam_param_code=concept_edit_input.adam_param_code
                or item.concept_vo.adam_param_code,
                is_required_for_activity=concept_edit_input.is_required_for_activity
                if concept_edit_input.is_required_for_activity is not None
                else item.concept_vo.is_required_for_activity,
                is_default_selected_for_activity=concept_edit_input.is_default_selected_for_activity
                if concept_edit_input.is_default_selected_for_activity is not None
                else item.concept_vo.is_default_selected_for_activity,
                is_data_sharing=concept_edit_input.is_data_sharing
                if concept_edit_input.is_data_sharing is not None
                else item.concept_vo.is_data_sharing,
                is_legacy_usage=concept_edit_input.is_legacy_usage
                if concept_edit_input.is_legacy_usage is not None
                else item.concept_vo.is_legacy_usage,
                is_derived=concept_edit_input.is_derived or item.concept_vo.is_derived,
                legacy_description=concept_edit_input.legacy_description
                or item.concept_vo.legacy_description,
                activity_groupings=activity_groupings,
                activity_instance_class_uid=concept_edit_input.activity_instance_class_uid
                or item.concept_vo.activity_instance_class_uid,
                activity_instance_class_name=None,
                activity_items=activity_items,
            ),
            concept_exists_by_callback=self.repository.exists_by,
            activity_instance_class_exists_by_uid_callback=self._repos.activity_instance_class_repository.check_exists_final_version,
            activity_item_class_exists_by_uid_callback=self._repos.activity_item_class_repository.check_exists_final_version,
            ct_term_exists_by_uid_callback=self._repos.ct_term_name_repository.term_exists,
            unit_definition_exists_by_uid_callback=self._repos.unit_definition_repository.final_concept_exists,
            activity_hierarchy_exists_by_uid_callback=self._repos.activity_repository.final_concept_exists,
            activity_group_exists=self._repos.activity_group_repository.final_concept_exists,
            activity_subgroup_exists=self._repos.activity_subgroup_repository.final_concept_exists,
        )
        return item

    def get_activity_instance_overview(
        self, activity_instance_uid: str, version: str | None = None
    ) -> ActivityInstanceOverview:
        if not self.repository.exists_by("uid", activity_instance_uid, True):
            raise NotFoundException(
                f"Cannot find ActivityInstance with the following uid ({activity_instance_uid})"
            )
        overview = (
            self._repos.activity_instance_repository.get_activity_instance_overview(
                uid=activity_instance_uid, version=version
            )
        )
        return ActivityInstanceOverview.from_repository_input(overview=overview)

    def get_cosmos_activity_instance_overview(self, activity_instance_uid: str) -> str:
        if not self.repository.exists_by("uid", activity_instance_uid, True):
            raise NotFoundException(
                f"Cannot find Activity instance with the following uid ({activity_instance_uid})"
            )
        data: dict = self.repository.get_cosmos_activity_instance_overview(
            uid=activity_instance_uid
        )
        result: dict = {
            "packageDate": datetime.date.today().isoformat(),
            "packageType": "bc",
            "conceptId": data["activity_instance_value"]["nci_concept_id"],
            "ncitCode": data["activity_instance_value"]["nci_concept_id"],
            "href": constants.COSM0S_BASE_ITEM_HREF.format(
                data["activity_instance_value"]["nci_concept_id"]
            ),
            "categories": data["activity_subgroups"],
            "shortName": data["activity_instance_value"]["name"],
            "synonyms": data["activity_instance_value"]["abbreviation"],
            "resultScales": [
                constants.COSM0S_RESULT_SCALES_MAP.get(
                    data["activity_instance_class_name"], ""
                )
            ],
            "definition": data["activity_instance_value"]["definition"],
            "dataElementConcepts": [],
        }
        for activity_item in data["activity_items"]:
            result["dataElementConcepts"].append(
                {
                    "conceptId": activity_item["nci_concept_id"],
                    "ncitCode": activity_item["nci_concept_id"],
                    "href": constants.COSM0S_BASE_ITEM_HREF.format(
                        activity_item["nci_concept_id"]
                    ),
                    "shortName": activity_item["name"],
                    "dataType": constants.COSMOS_DEC_TYPES_MAP.get(
                        activity_item["type"], activity_item["type"]
                    ),
                    "exampleSet": activity_item["example_set"],
                }
            )
        return result
