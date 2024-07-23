import datetime

from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.config import REQUESTED_LIBRARY_NAME
from clinical_mdr_api.domain_repositories.concepts.activities.activity_repository import (
    ActivityRepository,
)
from clinical_mdr_api.domains.concepts.activities.activity import (
    ActivityAR,
    ActivityGroupingVO,
    ActivityVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.exceptions import NotFoundException
from clinical_mdr_api.models.concepts.activities.activity import (
    Activity,
    ActivityEditInput,
    ActivityFromRequestInput,
    ActivityInput,
    ActivityOverview,
    ActivityRequestRejectInput,
    ActivityVersion,
)
from clinical_mdr_api.services._utils import is_library_editable, normalize_string
from clinical_mdr_api.services.concepts import constants
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
    _AggregateRootType,
)


class ActivityService(ConceptGenericService[ActivityAR]):
    aggregate_class = ActivityAR
    version_class = ActivityVersion
    repository_interface = ActivityRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ActivityAR
    ) -> Activity:
        return Activity.from_activity_ar(
            activity_ar=item_ar,
            find_activity_subgroup_by_uid=self._repos.activity_subgroup_repository.find_by_uid_2,
            find_activity_group_by_uid=self._repos.activity_group_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self, concept_input: ActivityInput, library
    ) -> _AggregateRootType:
        return ActivityAR.from_input_values(
            author=self.user_initials,
            concept_vo=ActivityVO.from_repository_values(
                nci_concept_id=concept_input.nci_concept_id,
                name=concept_input.name,
                name_sentence_case=concept_input.name_sentence_case,
                definition=concept_input.definition,
                abbreviation=concept_input.abbreviation,
                activity_groupings=[
                    ActivityGroupingVO(
                        activity_group_uid=activity_grouping.activity_group_uid,
                        activity_subgroup_uid=activity_grouping.activity_subgroup_uid,
                    )
                    for activity_grouping in concept_input.activity_groupings
                ]
                if concept_input.activity_groupings
                else [],
                request_rationale=concept_input.request_rationale,
                is_request_final=concept_input.is_request_final,
                is_data_collected=concept_input.is_data_collected,
                is_multiple_selection_allowed=concept_input.is_multiple_selection_allowed,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            concept_exists_by_library_and_name_callback=self._repos.activity_repository.latest_concept_in_library_exists_by_name,
            activity_subgroup_exists=self._repos.activity_subgroup_repository.final_concept_exists,
            activity_group_exists=self._repos.activity_group_repository.final_concept_exists,
        )

    def _edit_aggregate(
        self, item: ActivityAR, concept_edit_input: ActivityEditInput
    ) -> ActivityAR:
        item.edit_draft(
            author=self.user_initials,
            change_description=concept_edit_input.change_description,
            concept_vo=ActivityVO.from_repository_values(
                nci_concept_id=concept_edit_input.nci_concept_id,
                name=concept_edit_input.name,
                name_sentence_case=concept_edit_input.name_sentence_case,
                definition=concept_edit_input.definition,
                abbreviation=concept_edit_input.abbreviation,
                activity_groupings=[
                    ActivityGroupingVO(
                        activity_group_uid=activity_grouping.activity_group_uid,
                        activity_subgroup_uid=activity_grouping.activity_subgroup_uid,
                    )
                    for activity_grouping in concept_edit_input.activity_groupings
                ]
                if concept_edit_input.activity_groupings
                else [],
                request_rationale=concept_edit_input.request_rationale,
                is_request_final=concept_edit_input.is_request_final,
                is_data_collected=concept_edit_input.is_data_collected,
                is_multiple_selection_allowed=concept_edit_input.is_multiple_selection_allowed,
            ),
            concept_exists_by_library_and_name_callback=self._repos.activity_repository.latest_concept_in_library_exists_by_name,
            activity_subgroup_exists=self._repos.activity_subgroup_repository.final_concept_exists,
            activity_group_exists=self._repos.activity_group_repository.final_concept_exists,
        )
        return item

    @db.transaction
    def replace_requested_activity_with_sponsor(
        self, sponsor_activity_input: ActivityFromRequestInput
    ) -> Activity:
        if not self._repos.library_repository.library_exists(
            normalize_string(sponsor_activity_input.library_name)
        ):
            raise exceptions.BusinessLogicException(
                f"There is no library identified by provided library name ({sponsor_activity_input.library_name})"
            )

        library_vo = LibraryVO.from_input_values_2(
            library_name=sponsor_activity_input.library_name,
            is_library_editable_callback=is_library_editable,
        )

        # retire Requested Activity first to not conflict the Sponsor Activity name
        activity_request_ar = self.repository.find_by_uid_2(
            uid=sponsor_activity_input.activity_request_uid, for_update=True
        )
        if activity_request_ar.item_metadata.status != LibraryItemStatus.FINAL:
            raise exceptions.BusinessLogicException(
                f"To update the following Activity Request {activity_request_ar.name} to Sponsor Activity it should be in Final state"
            )
        activity_request_ar.inactivate(
            author=self.user_initials,
            change_description="Inactivate Requested Activity as Sponsor Activity was created",
        )
        self.repository.save(activity_request_ar)

        concept_ar = self._create_aggregate_root(
            concept_input=sponsor_activity_input, library=library_vo
        )
        concept_ar.approve(
            author=self.user_initials,
            change_description="Approve Sponsor Activity created from Requested Activity",
        )
        self.repository.save(concept_ar)
        self.repository.replace_request_with_sponsor_activity(
            activity_request_uid=sponsor_activity_input.activity_request_uid,
            sponsor_activity_uid=concept_ar.uid,
        )
        return self._transform_aggregate_root_to_pydantic_model(concept_ar)

    @db.transaction
    def reject_activity_request(
        self,
        activity_request_uid: str,
        activity_request_rejection_input: ActivityRequestRejectInput,
    ) -> Activity:
        # retire Requested Activity first to not conflict the Sponsor Activity name
        activity_request_ar = self.repository.find_by_uid_2(
            uid=activity_request_uid, for_update=True
        )
        if not activity_request_ar:
            raise exceptions.BusinessLogicException(
                f"The activity request ({activity_request_uid}) wasn't found"
            )
        if activity_request_ar.item_metadata.status != LibraryItemStatus.FINAL:
            raise exceptions.BusinessLogicException(
                f"To reject the following Activity Request {activity_request_ar.name} it has to be in Final state"
            )
        if activity_request_ar.library.name != REQUESTED_LIBRARY_NAME:
            raise exceptions.BusinessLogicException(
                "Only Requested Activities can be rejected"
            )
        activity_request_ar.create_new_version(author=self.user_initials)
        activity_request_ar.edit_draft(
            author=self.user_initials,
            change_description=f"Rejecting with the following reason {activity_request_rejection_input.reason_for_rejecting}",
            concept_vo=ActivityVO.from_repository_values(
                nci_concept_id=activity_request_ar.concept_vo.nci_concept_id,
                name=activity_request_ar.concept_vo.name,
                name_sentence_case=activity_request_ar.concept_vo.name_sentence_case,
                definition=activity_request_ar.concept_vo.definition,
                abbreviation=activity_request_ar.concept_vo.abbreviation,
                activity_groupings=activity_request_ar.concept_vo.activity_groupings,
                request_rationale=activity_request_ar.concept_vo.request_rationale,
                is_request_final=activity_request_ar.concept_vo.is_request_final,
                is_request_rejected=True,
                contact_person=activity_request_rejection_input.contact_person,
                reason_for_rejecting=activity_request_rejection_input.reason_for_rejecting,
                is_data_collected=activity_request_ar.concept_vo.is_data_collected,
                is_multiple_selection_allowed=activity_request_ar.concept_vo.is_multiple_selection_allowed,
            ),
            concept_exists_by_library_and_name_callback=self._repos.activity_repository.latest_concept_in_library_exists_by_name,
            activity_subgroup_exists=self._repos.activity_subgroup_repository.final_concept_exists,
            activity_group_exists=self._repos.activity_group_repository.final_concept_exists,
        )
        activity_request_ar.approve(
            author=self.user_initials, change_description="Approving after rejecting"
        )
        activity_request_ar.inactivate(
            author=self.user_initials,
            change_description="Retiring rejected Activity Request",
        )
        self.repository.save(activity_request_ar)
        return self._transform_aggregate_root_to_pydantic_model(activity_request_ar)

    def get_activity_overview(
        self, activity_uid: str, version: str | None
    ) -> ActivityOverview:
        if not self.repository.exists_by("uid", activity_uid, True):
            raise NotFoundException(
                f"Cannot find Activity with the following uid ({activity_uid})"
            )
        overview = self._repos.activity_repository.get_activity_overview(
            uid=activity_uid, version=version
        )
        return ActivityOverview.from_repository_input(overview=overview)

    def get_cosmos_activity_overview(self, activity_uid: str) -> str:
        if not self.repository.exists_by("uid", activity_uid, True):
            raise NotFoundException(
                f"Cannot find Activity with the following uid ({activity_uid})"
            )
        data: dict = self.repository.get_cosmos_activity_overview(uid=activity_uid)
        result: dict = {
            "packageDate": datetime.date.today().isoformat(),
            "packageType": "bc",
            "conceptId": data["activity_value"]["nci_concept_id"],
            "ncitCode": data["activity_value"]["nci_concept_id"],
            "href": constants.COSM0S_BASE_ITEM_HREF.format(
                data["activity_value"]["nci_concept_id"]
            ),
            "categories": data["activity_subgroups"],
            "shortName": data["activity_value"]["name"],
            "synonyms": data["activity_value"]["abbreviation"],
            "resultScales": list(
                set(
                    constants.COSM0S_RESULT_SCALES_MAP.get(
                        instance["activity_instance_class_name"], ""
                    )
                    for instance in data["activity_instances"]
                )
            ),
            "definition": data["activity_value"]["definition"],
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
