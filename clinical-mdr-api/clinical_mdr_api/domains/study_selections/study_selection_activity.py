import datetime
from dataclasses import dataclass
from typing import Callable

from clinical_mdr_api import exceptions
from clinical_mdr_api.domains._utils import normalize_string
from clinical_mdr_api.domains.study_selections import study_selection_base


@dataclass(frozen=True)
class StudySelectionActivityVO(study_selection_base.StudySelectionBaseVO):
    """
    The StudySelectionActivityVO acts as the value object for a
    single selection between a study and an activity
    """

    study_selection_uid: str
    study_activity_subgroup_uid: str | None
    activity_subgroup_uid: str | None
    activity_subgroup_name: str | None
    study_activity_group_uid: str | None
    activity_group_uid: str | None
    activity_group_name: str | None
    study_uid: str
    activity_uid: str
    activity_version: str | None
    activity_library_name: str | None
    study_soa_group_uid: str
    soa_group_term_uid: str
    activity_order: int | None
    show_activity_in_protocol_flowchart: bool
    show_activity_group_in_protocol_flowchart: bool
    show_activity_subgroup_in_protocol_flowchart: bool
    show_soa_group_in_protocol_flowchart: bool
    # Study selection Versioning
    start_date: datetime.datetime
    user_initials: str | None
    accepted_version: bool = False
    activity_name: str | None = None

    @classmethod
    def from_input_values(
        cls,
        study_uid: str,
        activity_uid: str,
        activity_version: str,
        study_soa_group_uid: str,
        soa_group_term_uid: str,
        user_initials: str,
        activity_library_name: str | None = None,
        study_activity_subgroup_uid: str | None = None,
        activity_subgroup_uid: str | None = None,
        activity_subgroup_name: str | None = None,
        study_activity_group_uid: str | None = None,
        activity_group_uid: str | None = None,
        activity_group_name: str | None = None,
        show_activity_in_protocol_flowchart: bool | None = False,
        show_activity_group_in_protocol_flowchart: bool | None = True,
        show_activity_subgroup_in_protocol_flowchart: bool | None = True,
        show_soa_group_in_protocol_flowchart: bool | None = False,
        activity_order: int | None = 0,
        study_selection_uid: str | None = None,
        start_date: datetime.datetime | None = None,
        accepted_version: bool = False,
        activity_name: str | None = None,
        generate_uid_callback: Callable[[], str] | None = None,
    ):
        if study_selection_uid is None:
            study_selection_uid = generate_uid_callback()

        if start_date is None:
            start_date = datetime.datetime.now(datetime.timezone.utc)

        return cls(
            study_uid=normalize_string(study_uid),
            activity_uid=normalize_string(activity_uid),
            activity_name=normalize_string(activity_name),
            activity_library_name=normalize_string(activity_library_name),
            activity_version=activity_version,
            study_soa_group_uid=normalize_string(study_soa_group_uid),
            soa_group_term_uid=normalize_string(soa_group_term_uid),
            show_activity_in_protocol_flowchart=show_activity_in_protocol_flowchart,
            show_activity_group_in_protocol_flowchart=show_activity_group_in_protocol_flowchart,
            show_activity_subgroup_in_protocol_flowchart=show_activity_subgroup_in_protocol_flowchart,
            show_soa_group_in_protocol_flowchart=show_soa_group_in_protocol_flowchart,
            start_date=start_date,
            study_selection_uid=normalize_string(study_selection_uid),
            study_activity_subgroup_uid=normalize_string(study_activity_subgroup_uid),
            activity_subgroup_uid=normalize_string(activity_subgroup_uid),
            activity_subgroup_name=normalize_string(activity_subgroup_name),
            study_activity_group_uid=normalize_string(study_activity_group_uid),
            activity_group_uid=normalize_string(activity_group_uid),
            activity_group_name=normalize_string(activity_group_name),
            activity_order=activity_order,
            user_initials=normalize_string(user_initials),
            accepted_version=accepted_version,
        )

    def validate(
        self,
        object_exist_callback: Callable[[str], bool] = (lambda _: True),
        ct_term_level_exist_callback: Callable[[str], bool] = (lambda _: True),
    ) -> None:
        # Checks if there exists an activity which is approved with activity_uid
        if not object_exist_callback(normalize_string(self.activity_uid)):
            raise exceptions.ValidationException(
                f"There is no approved activity identified by provided uid ({self.activity_uid})"
            )
        if not ct_term_level_exist_callback(self.soa_group_term_uid):
            raise exceptions.ValidationException(
                f"There is no approved flowchart group identified by provided term uid ({self.soa_group_term_uid})"
            )


@dataclass
class StudySelectionActivityAR(study_selection_base.StudySelectionBaseAR):
    """
    The StudySelectionActivityAR holds all the study activity
    selections for a given study, the aggregate root also, takes care
    of all operations changing the study selections for a study.

    * add more selections
    * remove selections
    * patch selection
    * delete selection

    """

    _object_type = "activity"
    _object_uid_field = "activity_uid"
    _object_name_field = "activity_name"
    _order_field_name = "activity_order"

    def validate(self):
        objects = []
        for selection in self.study_objects_selection:
            object_name = getattr(selection, self._object_name_field)
            activity_subgroup_uid = selection.activity_subgroup_uid
            activity_group_uid = selection.activity_group_uid
            if (object_name, activity_subgroup_uid, activity_group_uid) in objects:
                raise exceptions.ValidationException(
                    f"There is already a study selection to that {self._object_type} ({object_name}) with the same groupings"
                )
            objects.append((object_name, activity_subgroup_uid, activity_group_uid))
