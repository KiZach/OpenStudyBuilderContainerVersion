from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain_repositories.concepts.odms.study_event_repository import (
    StudyEventRepository,
)
from clinical_mdr_api.domains.concepts.odms.study_event import (
    OdmStudyEventAR,
    OdmStudyEventVO,
)
from clinical_mdr_api.domains.concepts.utils import RelationType
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.concepts.odms.odm_study_event import (
    OdmStudyEvent,
    OdmStudyEventFormPostInput,
    OdmStudyEventPatchInput,
    OdmStudyEventPostInput,
    OdmStudyEventVersion,
)
from clinical_mdr_api.services._utils import get_input_or_new_value, normalize_string
from clinical_mdr_api.services.concepts.odms.odm_generic_service import (
    OdmGenericService,
)
from clinical_mdr_api.utils import strtobool


class OdmStudyEventService(OdmGenericService[OdmStudyEventAR]):
    aggregate_class = OdmStudyEventAR
    version_class = OdmStudyEventVersion
    repository_interface = StudyEventRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: OdmStudyEventAR
    ) -> OdmStudyEvent:
        return OdmStudyEvent.from_odm_study_event_ar(
            odm_study_event_ar=item_ar,
            find_odm_form_by_uid_with_study_event_relation=self._repos.odm_form_repository.find_by_uid_with_study_event_relation,
        )

    def _create_aggregate_root(
        self, concept_input: OdmStudyEventPostInput, library
    ) -> OdmStudyEventAR:
        return OdmStudyEventAR.from_input_values(
            author=self.user_initials,
            concept_vo=OdmStudyEventVO.from_repository_values(
                name=concept_input.name,
                oid=get_input_or_new_value(concept_input.oid, "T.", concept_input.name),
                effective_date=concept_input.effective_date,
                retired_date=concept_input.retired_date,
                description=concept_input.description,
                display_in_tree=concept_input.display_in_tree,
                form_uids=[],
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            concept_exists_by_callback=self._repos.odm_study_event_repository.exists_by,
        )

    def _edit_aggregate(
        self, item: OdmStudyEventAR, concept_edit_input: OdmStudyEventPatchInput
    ) -> OdmStudyEventAR:
        item.edit_draft(
            author=self.user_initials,
            change_description=concept_edit_input.change_description,
            concept_vo=OdmStudyEventVO.from_repository_values(
                name=concept_edit_input.name,
                oid=concept_edit_input.oid,
                effective_date=concept_edit_input.effective_date,
                retired_date=concept_edit_input.retired_date,
                description=concept_edit_input.description,
                display_in_tree=concept_edit_input.display_in_tree,
                form_uids=[],
            ),
            concept_exists_by_callback=self._repos.odm_study_event_repository.exists_by,
        )
        return item

    @db.transaction
    def add_forms(
        self,
        uid: str,
        odm_study_event_form_post_input: list[OdmStudyEventFormPostInput],
        override: bool = False,
    ) -> OdmStudyEvent:
        odm_study_event_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        if odm_study_event_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException(self.OBJECT_IS_INACTIVE)

        if override:
            self._repos.odm_study_event_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.FORM,
                disconnect_all=True,
            )

        for form in odm_study_event_form_post_input:
            self._repos.odm_study_event_repository.add_relation(
                uid=uid,
                relation_uid=form.uid,
                relationship_type=RelationType.FORM,
                parameters={
                    "order_number": form.order_number,
                    "mandatory": strtobool(form.mandatory),
                    "locked": strtobool(form.locked),
                    "collection_exception_condition_oid": form.collection_exception_condition_oid,
                },
            )

        odm_study_event_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_study_event_ar)

    @db.transaction
    def get_active_relationships(self, uid: str):
        if not self._repos.odm_study_event_repository.exists_by("uid", uid, True):
            raise exceptions.NotFoundException(
                f"ODM Study Event identified by uid ({uid}) does not exist."
            )

        return self._repos.odm_study_event_repository.get_active_relationships(uid, [])
