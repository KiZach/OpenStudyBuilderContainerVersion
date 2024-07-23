import datetime
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Self

from clinical_mdr_api import exceptions
from clinical_mdr_api.domains._utils import normalize_string


@dataclass(frozen=True)
class StudySelectionBranchArmVO:
    """
    The StudySelectionBranchArmVO acts as the value object for a single selection between a study and an branch arm
    """

    study_selection_uid: str
    study_uid: str | None
    name: str | None
    short_name: str | None
    code: str | None
    description: str | None
    colour_code: str | None
    randomization_group: str | None
    number_of_subjects: int | None
    arm_root_uid: str | None
    start_date: datetime.datetime
    user_initials: str
    end_date: datetime.datetime | None
    status: str | None
    change_type: str | None
    accepted_version: bool = False

    @classmethod
    def from_input_values(
        cls,
        user_initials: str,
        study_selection_uid: str | None = None,
        study_uid: str | None = None,
        name: str | None = None,
        short_name: str | None = None,
        code: str | None = None,
        description: str | None = None,
        colour_code: str | None = None,
        randomization_group: str | None = None,
        number_of_subjects: int | None = 0,
        arm_root_uid: str | None = None,
        start_date: datetime.datetime | None = None,
        end_date: datetime.datetime | None = None,
        status: str | None = None,
        change_type: str | None = None,
        accepted_version: bool | None = False,
        generate_uid_callback: Callable[[], str] | None = None,
    ):
        """
        Factory method
        :param study_uid
        :param study_selection_uid
        :param name
        :param short_name
        :param code
        :param description
        :param colour_code
        :param randomization_group
        :param number_of_subjects
        :param start_date
        :param user_initials
        :param end_date
        :param status
        :param change_type
        :param accepted_version
        :return:
        """
        if study_selection_uid is None:
            study_selection_uid = generate_uid_callback()

        if start_date is None:
            start_date = datetime.datetime.now(datetime.timezone.utc)

        # returns a new instance of the VO

        return StudySelectionBranchArmVO(
            study_uid=study_uid,
            study_selection_uid=normalize_string(study_selection_uid),
            name=name,
            short_name=short_name,
            code=code,
            description=description,
            colour_code=colour_code,
            randomization_group=randomization_group,
            number_of_subjects=number_of_subjects,
            arm_root_uid=arm_root_uid,
            start_date=start_date,
            user_initials=user_initials,
            end_date=end_date,
            status=status,
            change_type=change_type,
            accepted_version=accepted_version,
        )

    def validate(
        self,
        study_branch_arm_study_arm_update_conflict_callback: Callable[[str], bool] = (
            lambda _: True
        ),
        study_arm_exists_callback: Callable[[str], bool] = (lambda _: True),
        branch_arm_exists_callback_by: Callable[[str], bool] = (lambda _: True),
    ) -> None:
        """
        Validating business logic for a VO
        :param study_arm_exists_callback:
        :param branch_arm_exists_callback_by:
        :return:
        """
        # Checks whether a BranchArm that has connected StudyDesignCells is not trying to change StudyArm
        if self.arm_root_uid and study_branch_arm_study_arm_update_conflict_callback(
            branch_arm_vo=self
        ):
            raise exceptions.ValidationException(
                f"Cannot change StudyArm when the specific BranchArm ({self.study_selection_uid}) has connected StudyDesignCells"
            )
        # Check if there exist a StudyArm with the selected uid
        if not study_arm_exists_callback(self.arm_root_uid):
            raise exceptions.ValidationException(
                f"There is no approved arm level identified by provided arm uid ({self.arm_root_uid})"
            )

        # check if the specified name is already used with the callback
        if self.name and branch_arm_exists_callback_by(
            "name", "name", branch_arm_vo=self
        ):
            raise exceptions.ValidationException(
                f'Value "{self.name}" in field Branch Arm Name is not unique for the study'
            )

        # check if the specified Short name is already used with the callback
        if self.short_name and branch_arm_exists_callback_by(
            "short_name", "short_name", branch_arm_vo=self
        ):
            raise exceptions.ValidationException(
                f'Value "{self.short_name}" in field Branch Arm Short Name is not unique for the study'
            )

        # check if the specified code is already used with the callback
        if self.code and branch_arm_exists_callback_by(
            "branch_arm_code", "code", branch_arm_vo=self
        ):
            raise exceptions.ValidationException(
                f'Value "{self.code}" in field Branch Arm Code is not unique for the study'
            )

        # check if the specified randomization group is already used with the callback
        if self.randomization_group and branch_arm_exists_callback_by(
            "randomization_group", "randomization_group", branch_arm_vo=self
        ):
            raise exceptions.ValidationException(
                f'Value "{self.randomization_group}" in field Branch Arm Randomization code is not unique for the study'
            )


@dataclass
class StudySelectionBranchArmAR:
    _study_uid: str
    _study_branch_arms_selection: tuple[StudySelectionBranchArmVO]
    # a dataclass feature that has Any value with a type field NOT included on the
    # generated init method, NOT included con copare generated methods, included on
    # the string returned by the generated method, and its default is None
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    def get_specific_object_selection(
        self, study_selection_uid: str
    ) -> tuple[StudySelectionBranchArmVO, int]:
        for order, selection in enumerate(self.study_branch_arms_selection, start=1):
            if selection.study_selection_uid == study_selection_uid:
                return selection, order
        raise exceptions.NotFoundException(
            f"The study selection {study_selection_uid} does not exist for study {self._study_uid}"
        )

    @property
    def study_uid(self) -> str:
        return self._study_uid

    @property
    def study_branch_arms_selection(self) -> tuple[StudySelectionBranchArmVO]:
        return self._study_branch_arms_selection

    def get_specific_branch_arm_selection(
        self, study_branch_arm_uid: str, arm_root_uid: str | None = None
    ) -> tuple[StudySelectionBranchArmVO, int] | None:
        # the study branch arm must be in any parent arm
        if study_branch_arm_uid not in [
            x.study_selection_uid for x in self.study_branch_arms_selection
        ]:
            raise exceptions.NotFoundException(
                f"There is no selection '{study_branch_arm_uid}'"
            )

        # First, filter on branch_arm selection with the same parent arm
        # to get the order in the context of the parent arm
        # The parent arm might not be known by some caller methods
        # So first step is to get it
        if arm_root_uid is None:
            _arm_root_uid = [
                x.arm_root_uid
                for x in self.study_branch_arms_selection
                if x.study_selection_uid == study_branch_arm_uid
            ]
            if len(_arm_root_uid) == 1:
                arm_root_uid = _arm_root_uid[0]
            else:
                return None, 0

        # Then, filter the list on parent arm, and return the order of the branch_arm selection in the parent arm group
        study_branch_arms_selection_with_root = [
            x
            for x in self.study_branch_arms_selection
            if x.arm_root_uid == arm_root_uid
        ]
        for order, selection in enumerate(
            study_branch_arms_selection_with_root, start=1
        ):
            if selection.study_selection_uid == study_branch_arm_uid:
                return selection, order
        raise exceptions.ValidationException(
            f"The study branch arm with provided uid does not exist ({study_branch_arm_uid})"
        )

    def _add_selection(self, study_branch_arm_selection) -> None:
        new_selections = self._study_branch_arms_selection + (
            study_branch_arm_selection,
        )
        self._study_branch_arms_selection = new_selections

    def add_branch_arm_selection(
        self,
        study_branch_arm_selection: StudySelectionBranchArmVO,
        study_branch_arm_study_arm_update_conflict_callback: Callable[[str], bool] = (
            lambda _: True
        ),
        study_arm_exists_callback: Callable[[str], bool] = (lambda _: True),
        branch_arm_exists_callback_by: Callable[[str], bool] = (lambda _: True),
    ) -> None:
        """
        Adding a new study branch arm to the _study_branch_arm_selection
        :param study_branch_arm_selection:
        :param study_arm_exists_callback:
        :param branch_arm_exists_callback_by:
        :return:
        """
        study_branch_arm_selection.validate(
            study_branch_arm_study_arm_update_conflict_callback=study_branch_arm_study_arm_update_conflict_callback,
            study_arm_exists_callback=study_arm_exists_callback,
            branch_arm_exists_callback_by=branch_arm_exists_callback_by,
        )
        self._add_selection(study_branch_arm_selection)

    @classmethod
    def from_repository_values(
        cls,
        study_uid: str,
        study_branch_arms_selection: Iterable[StudySelectionBranchArmVO],
    ) -> Self:
        """
        Factory method to create a AR
        :param study_uid:
        :param study_endpoints_selection:
        :return:
        """
        return cls(
            _study_uid=normalize_string(study_uid),
            _study_branch_arms_selection=tuple(study_branch_arms_selection),
        )

    def remove_branch_arm_selection(self, study_selection_uid: str):
        """
        removing a study branch arm
        :param study_selection_uid:
        :return:
        """
        updated_selection = []
        for selection in self.study_branch_arms_selection:
            if selection.study_selection_uid != study_selection_uid:
                updated_selection.append(selection)
        self._study_branch_arms_selection = tuple(updated_selection)

    def set_new_order_for_selection(self, study_selection_uid: str, new_order: int):
        """
        Used to reorder a study compound
        :param study_selection_uid:
        :param new_order:
        :return:
        """
        # check if the new order is valid using the robustness principle
        if new_order > len(self.study_branch_arms_selection):
            # If order is higher than maximum allowed then set to max
            new_order = len(self.study_branch_arms_selection)
        elif new_order < 1:
            # If order is lower than 1 set to 1
            new_order = 1
        # find the selection
        selected_value, old_order = self.get_specific_branch_arm_selection(
            study_selection_uid
        )
        # change the order
        updated_selections = []
        for order, selection in enumerate(self.study_branch_arms_selection, start=1):
            # if the order is the where the new item is meant to be put
            if order == new_order:
                # we check if the order is being changed to lower or higher and add it to the list appropriately
                if old_order >= new_order:
                    updated_selections.append(selected_value)
                    if (
                        selection.study_selection_uid
                        != selected_value.study_selection_uid
                    ):
                        updated_selections.append(selection)
                else:
                    if (
                        selection.study_selection_uid
                        != selected_value.study_selection_uid
                    ):
                        updated_selections.append(selection)
                    updated_selections.append(selected_value)
            # We add all other vo to in the same order as before, except for the vo we are moving
            elif selection.study_selection_uid != selected_value.study_selection_uid:
                updated_selections.append(selection)
        self._study_branch_arms_selection = tuple(updated_selections)

    def update_selection(
        self,
        updated_study_branch_arm_selection: StudySelectionBranchArmVO,
        study_branch_arm_study_arm_update_conflict_callback: Callable[[str], bool] = (
            lambda _: True
        ),
        study_arm_exists_callback: Callable[[str], bool] = (lambda _: True),
        branch_arm_exists_callback_by: Callable[[str], bool] = (lambda _: True),
    ) -> None:
        """
        Used when a study branch arm is patched
        :param study_arm_exists_callback:
        :param branch_arm_exists_callback_by:
        :return:
        """
        updated_study_branch_arm_selection.validate(
            study_branch_arm_study_arm_update_conflict_callback=study_branch_arm_study_arm_update_conflict_callback,
            study_arm_exists_callback=study_arm_exists_callback,
            branch_arm_exists_callback_by=branch_arm_exists_callback_by,
        )
        # Check if study objective or level have changed
        updated_selection = []
        for selection in self.study_branch_arms_selection:
            if (
                selection.study_selection_uid
                != updated_study_branch_arm_selection.study_selection_uid
            ):
                updated_selection.append(selection)
            else:
                updated_selection.append(updated_study_branch_arm_selection)
        self._study_branch_arms_selection = tuple(updated_selection)
