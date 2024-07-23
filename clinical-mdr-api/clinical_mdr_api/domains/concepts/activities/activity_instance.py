from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api import exceptions
from clinical_mdr_api.domains.concepts.activities.activity import ActivityGroupingVO
from clinical_mdr_api.domains.concepts.activities.activity_item import ActivityItemVO
from clinical_mdr_api.domains.concepts.concept_base import (
    ConceptARBase,
    ConceptVO,
    _ConceptVOType,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)


@dataclass(frozen=True)
class ActivityInstanceGroupingVO(ActivityGroupingVO):
    activity_uid: str | None = None


@dataclass(frozen=True)
class ActivityInstanceVO(ConceptVO):
    """
    The ActivityInstanceVO acts as the value object for a single ActivityInstance aggregate
    """

    nci_concept_id: str | None
    topic_code: str
    adam_param_code: str
    is_required_for_activity: bool
    is_default_selected_for_activity: bool
    is_data_sharing: bool
    is_legacy_usage: bool
    is_derived: bool
    legacy_description: str | None
    activity_name: str | None
    activity_groupings: list[ActivityInstanceGroupingVO]
    activity_instance_class_uid: str
    activity_instance_class_name: str | None
    activity_items: list[ActivityItemVO]

    @classmethod
    def from_repository_values(
        cls,
        nci_concept_id: str | None,
        name: str,
        name_sentence_case: str,
        definition: str,
        abbreviation: str | None,
        topic_code: str,
        adam_param_code: str,
        is_required_for_activity: bool,
        is_default_selected_for_activity: bool,
        is_data_sharing: bool,
        is_legacy_usage: bool,
        is_derived: bool,
        legacy_description: str | None,
        activity_groupings: list[ActivityInstanceGroupingVO],
        activity_instance_class_uid: str,
        activity_instance_class_name: str | None,
        activity_items: list[ActivityItemVO],
        activity_name: str | None = None,
    ) -> Self:
        activity_instance_vo = cls(
            nci_concept_id=nci_concept_id,
            name=name,
            name_sentence_case=name_sentence_case,
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=True,
            activity_instance_class_uid=activity_instance_class_uid,
            activity_instance_class_name=activity_instance_class_name,
            topic_code=topic_code,
            adam_param_code=adam_param_code,
            is_required_for_activity=is_required_for_activity,
            is_default_selected_for_activity=is_default_selected_for_activity,
            is_data_sharing=is_data_sharing,
            is_legacy_usage=is_legacy_usage,
            is_derived=is_derived,
            legacy_description=legacy_description,
            activity_groupings=activity_groupings
            if activity_groupings is not None
            else [],
            activity_items=activity_items if activity_items is not None else [],
            activity_name=activity_name,
        )

        return activity_instance_vo

    def validate(
        self,
        activity_hierarchy_exists_by_uid_callback: Callable[[str], bool],
        activity_subgroup_exists: Callable[[str], bool],
        activity_group_exists: Callable[[str], bool],
        activity_instance_class_exists_by_uid_callback: Callable[[str], bool],
        activity_item_class_exists_by_uid_callback: Callable[[str], bool],
        ct_term_exists_by_uid_callback: Callable[[str], bool],
        unit_definition_exists_by_uid_callback: Callable[[str], bool],
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        previous_name: str | None = None,
    ) -> None:
        self.validate_name_sentence_case()
        self.duplication_check(
            [("name", self.name, previous_name)],
            concept_exists_by_callback,
            "Activity Instance",
        )
        for activity_grouping in self.activity_groupings:
            if not activity_hierarchy_exists_by_uid_callback(
                activity_grouping.activity_uid
            ):
                raise exceptions.ValidationException(
                    f"{type(self).__name__} tried to connect to non-existent or non-final Activity identified by uid "
                    f"({activity_grouping.activity_uid})"
                )
            if not activity_subgroup_exists(activity_grouping.activity_subgroup_uid):
                raise exceptions.ValidationException(
                    f"{type(self).__name__} tried to connect to non-existent or non-final Activity Sub Group identified by uid "
                    f"({activity_grouping.activity_subgroup_uid})"
                )
            if not activity_group_exists(activity_grouping.activity_group_uid):
                raise exceptions.ValidationException(
                    f"{type(self).__name__} tried to connect to non-existent or non-final Activity Group identified by uid "
                    f"({activity_grouping.activity_group_uid})"
                )
        for activity_item in self.activity_items:
            if not activity_item_class_exists_by_uid_callback(
                activity_item.activity_item_class_uid
            ):
                raise exceptions.ValidationException(
                    f"{type(self).__name__} tried to connect to non-existent or non-final Activity Item Class "
                    f"identified by uid ({activity_item.activity_item_class_uid})"
                )
            for ct_term in activity_item.ct_terms:
                if not ct_term_exists_by_uid_callback(ct_term.uid):
                    raise exceptions.ValidationException(
                        f"{type(self).__name__} tried to connect to non-existent or non-final CT Term "
                        f"identified by uid ({ct_term.uid})"
                    )
            for unit in activity_item.unit_definitions:
                if not unit_definition_exists_by_uid_callback(unit.uid):
                    raise exceptions.ValidationException(
                        f"{type(self).__name__} tried to connect to non-existent or non-final Unit Definition "
                        f"identified by uid ({unit.uid})"
                    )

        if not activity_instance_class_exists_by_uid_callback(
            self.activity_instance_class_uid
        ):
            raise exceptions.ValidationException(
                f"ActivityInstanceClass with specified uid ({self.activity_instance_class_uid}) doesn't exist"
            )


@dataclass
class ActivityInstanceAR(ConceptARBase):
    _concept_vo: ActivityInstanceVO

    @property
    def concept_vo(self) -> _ConceptVOType:
        return self._concept_vo

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        concept_vo: _ConceptVOType,
        library: LibraryVO | None,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        activity_ar = cls(
            _uid=uid,
            _concept_vo=concept_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return activity_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author: str,
        concept_vo: _ConceptVOType,
        library: LibraryVO,
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        activity_hierarchy_exists_by_uid_callback: Callable[[str], bool],
        activity_subgroup_exists: Callable[[str], bool],
        activity_group_exists: Callable[[str], bool],
        activity_instance_class_exists_by_uid_callback: Callable[[str], bool],
        activity_item_class_exists_by_uid_callback: Callable[[str], bool] | None = None,
        ct_term_exists_by_uid_callback: Callable[[str], bool] | None = None,
        unit_definition_exists_by_uid_callback: Callable[[str], bool] | None = None,
        generate_uid_callback: Callable[[], str | None] = (lambda: None),
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)

        if not library.is_editable:
            raise exceptions.BusinessLogicException(
                f"The library with the name='{library.name}' does not allow to create objects."
            )

        concept_vo.validate(
            concept_exists_by_callback=concept_exists_by_callback,
            activity_hierarchy_exists_by_uid_callback=activity_hierarchy_exists_by_uid_callback,
            activity_subgroup_exists=activity_subgroup_exists,
            activity_group_exists=activity_group_exists,
            activity_instance_class_exists_by_uid_callback=activity_instance_class_exists_by_uid_callback,
            activity_item_class_exists_by_uid_callback=activity_item_class_exists_by_uid_callback,
            ct_term_exists_by_uid_callback=ct_term_exists_by_uid_callback,
            unit_definition_exists_by_uid_callback=unit_definition_exists_by_uid_callback,
        )

        activity_ar = cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )
        return activity_ar

    def edit_draft(
        self,
        author: str,
        change_description: str | None,
        concept_vo: _ConceptVOType,
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        activity_hierarchy_exists_by_uid_callback: Callable[[str], bool] | None = None,
        activity_subgroup_exists: Callable[[str], bool] | None = None,
        activity_group_exists: Callable[[str], bool] | None = None,
        activity_instance_class_exists_by_uid_callback: Callable[[str], bool]
        | None = None,
        activity_item_class_exists_by_uid_callback: Callable[[str], bool] | None = None,
        ct_term_exists_by_uid_callback: Callable[[str], bool] | None = None,
        unit_definition_exists_by_uid_callback: Callable[[str], bool] | None = None,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            concept_exists_by_callback=concept_exists_by_callback,
            activity_hierarchy_exists_by_uid_callback=activity_hierarchy_exists_by_uid_callback,
            activity_subgroup_exists=activity_subgroup_exists,
            activity_group_exists=activity_group_exists,
            activity_instance_class_exists_by_uid_callback=activity_instance_class_exists_by_uid_callback,
            activity_item_class_exists_by_uid_callback=activity_item_class_exists_by_uid_callback,
            ct_term_exists_by_uid_callback=ct_term_exists_by_uid_callback,
            unit_definition_exists_by_uid_callback=unit_definition_exists_by_uid_callback,
            previous_name=self.name,
        )
        if self._concept_vo != concept_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._concept_vo = concept_vo
