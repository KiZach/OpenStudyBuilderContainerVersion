import datetime
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Self

from clinical_mdr_api import exceptions
from clinical_mdr_api.domains._utils import normalize_string
from clinical_mdr_api.domains.concepts.compound import CompoundAR
from clinical_mdr_api.exceptions import BusinessLogicException


def _raise(exc: Exception) -> Any:
    raise exc


@dataclass(frozen=True)
class StudySelectionCompoundVO:
    """
    The StudySelectionCompoundVO acts as the value object for a single selection between a study and a compound
    """

    study_selection_uid: str
    study_uid: str | None
    compound_uid: str | None
    compound_alias_uid: str | None
    type_of_treatment_uid: str | None
    reason_for_missing_value_uid: str | None
    dispensed_in_uid: str | None
    route_of_administration_uid: str | None
    strength_value_uid: str | None
    dosage_form_uid: str | None
    device_uid: str | None
    formulation_uid: str | None
    other_info: str | None
    study_compound_dosing_count: int | None
    # Study selection Versioning
    start_date: datetime.datetime
    user_initials: str | None

    @classmethod
    def from_input_values(
        cls,
        compound_uid: str | None,
        compound_alias_uid: str | None,
        type_of_treatment_uid: str | None,
        reason_for_missing_value_uid: str | None,
        route_of_administration_uid: str | None,
        strength_value_uid: str | None,
        dosage_form_uid: str | None,
        dispensed_in_uid: str | None,
        device_uid: str | None,
        formulation_uid: str | None,
        other_info: str | None,
        user_initials: str,
        study_uid: str | None = None,
        study_selection_uid: str | None = None,
        study_compound_dosing_count: int | None = None,
        start_date: datetime.datetime | None = None,
        generate_uid_callback: Callable[[], str] = (
            lambda: _raise(
                ValueError("generate_uid_callback necessary when uid not provided")
            )
        ),
    ) -> Self:
        """
        Factory method
        :param dispensed_in_uid:
        :param other_info:
        :param formulation_uid:
        :param device_uid:
        :param compound_uid:
        :param compound_alias_uid:
        :param type_of_treatment_uid:
        :param reason_for_missing_value_uid:
        :param route_of_administration_uid:
        :param strength_value_uid:
        :param dosage_form_uid:
        :param study_selection_uid:
        :param generate_uid_callback:
        :return:
        """
        if study_selection_uid is None:
            study_selection_uid = generate_uid_callback()

        if start_date is None:
            start_date = datetime.datetime.now(datetime.timezone.utc)

        # returns a new instance of the VO
        return StudySelectionCompoundVO(
            study_uid=study_uid,
            study_selection_uid=normalize_string(study_selection_uid),
            compound_uid=normalize_string(compound_uid),
            compound_alias_uid=normalize_string(compound_alias_uid),
            type_of_treatment_uid=normalize_string(type_of_treatment_uid),
            reason_for_missing_value_uid=normalize_string(reason_for_missing_value_uid),
            route_of_administration_uid=normalize_string(route_of_administration_uid),
            strength_value_uid=normalize_string(strength_value_uid),
            dosage_form_uid=normalize_string(dosage_form_uid),
            dispensed_in_uid=normalize_string(dispensed_in_uid),
            device_uid=normalize_string(device_uid),
            formulation_uid=normalize_string(formulation_uid),
            other_info=normalize_string(other_info),
            study_compound_dosing_count=study_compound_dosing_count,
            user_initials=normalize_string(user_initials),
            start_date=start_date,
        )

    def validate(
        self,
        selection_uid_by_details_callback: Callable[
            ["StudySelectionCompoundVO"], str
        ] = (lambda _: False),
        reason_for_missing_callback: Callable[[str], bool] = (lambda _: True),
        compound_exist_callback: Callable[[str], bool] = (lambda _: True),
        compound_alias_exist_callback: Callable[[str], bool] = (lambda _: True),
        compound_callback: Callable[[str], CompoundAR] = (lambda _: None),
    ) -> None:
        """
        Raises ValueError or BusinessLogicException if values do not comply with relevant business rules.

        """
        if (
            self.reason_for_missing_value_uid is not None
            and not reason_for_missing_callback(self.reason_for_missing_value_uid)
        ):
            raise exceptions.ValidationException(
                "Unknown reason for missing value code provided for Reason For Missing"
            )

        if self.reason_for_missing_value_uid is not None:
            for value in (
                self.compound_uid,
                self.compound_alias_uid,
                self.route_of_administration_uid,
                self.strength_value_uid,
                self.dosage_form_uid,
                self.dispensed_in_uid,
                self.device_uid,
                self.formulation_uid,
                self.other_info,
            ):
                if value is not None:
                    raise exceptions.ValidationException(
                        "If reason_for_missing_null_value_uid has a value, "
                        + "all fields except type of treatment have to be empty"
                    )

        if self.compound_uid is not None and not compound_exist_callback(
            normalize_string(self.compound_uid)
        ):
            raise exceptions.ValidationException(
                f"There is no approved compound identified by provided uid ({self.compound_uid})"
            )

        if self.compound_alias_uid is not None and not compound_alias_exist_callback(
            normalize_string(self.compound_alias_uid)
        ):
            raise exceptions.ValidationException(
                f"There is no approved compound alias identified by provided uid ({self.compound_alias_uid})"
            )

        # Find an existing study compound selection with the same details:
        #   - Compound alias
        #   - Pharmaceutical dosage form
        #   - Compound strength value
        #   - Route of administration
        #   - Dispenser
        #   - Delivery device
        exisiting_uid = selection_uid_by_details_callback(self)
        if exisiting_uid and self.study_selection_uid != exisiting_uid:
            raise BusinessLogicException(
                "Compound selection with the specified combination of compound, "
                "pharmaceutical dosage form, strength, route of administration, dispenser and delivery device already exists."
            )

        # Validate that each of these selections is actually defined on the selected library compound:
        #   - Pharmaceutical dosage form
        #   - Compound strength value
        #   - Route of administration
        #   - Dispenser
        #   - Delivery device
        compound: CompoundAR = compound_callback(self.compound_uid)
        if compound:
            if (
                self.dosage_form_uid is not None
                and self.dosage_form_uid not in compound.concept_vo.dosage_form_uids
            ):
                raise BusinessLogicException(
                    f"Selected pharmaceutical dosage form is not valid for compound '{compound.concept_vo.name}'."
                )
            if (
                self.strength_value_uid is not None
                and self.strength_value_uid
                not in compound.concept_vo.strength_values_uids
            ):
                raise BusinessLogicException(
                    f"Selected strength value is not valid for compound '{compound.concept_vo.name}'."
                )
            if (
                self.route_of_administration_uid is not None
                and self.route_of_administration_uid
                not in compound.concept_vo.route_of_administration_uids
            ):
                raise BusinessLogicException(
                    f"Selected route of administration is not valid for compound '{compound.concept_vo.name}'."
                )
            if (
                self.dispensed_in_uid is not None
                and self.dispensed_in_uid not in compound.concept_vo.dispensers_uids
            ):
                raise BusinessLogicException(
                    f"Selected dispenser is not valid for compound '{compound.concept_vo.name}'."
                )
            if (
                self.device_uid is not None
                and self.device_uid not in compound.concept_vo.delivery_devices_uids
            ):
                raise BusinessLogicException(
                    f"Selected delivery device is not valid for compound '{compound.concept_vo.name}'."
                )


@dataclass
class StudySelectionCompoundsAR:
    _study_uid: str
    _study_compounds_selection: list[StudySelectionCompoundVO]
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    @property
    def study_uid(self) -> str:
        return self._study_uid

    @property
    def study_compounds_selection(self) -> list[StudySelectionCompoundVO]:
        return self._study_compounds_selection

    def get_specific_compound_selection(
        self, study_selection_uid: str
    ) -> tuple[StudySelectionCompoundVO, int]:
        """
        Used to receive a specific VO from the AR
        :param study_selection_uid:
        :return:
        """
        for order, selection in enumerate(self.study_compounds_selection, start=1):
            if selection.study_selection_uid == study_selection_uid:
                return selection, order
        raise exceptions.NotFoundException(
            f"There is no selection between the study compound '{study_selection_uid}' and the study"
        )

    def add_compound_selection(
        self,
        study_compound_selection: StudySelectionCompoundVO,
        selection_uid_by_details_callback: Callable[["StudySelectionCompoundVO"], str],
        reason_for_missing_callback: Callable[[str], bool] = (lambda _: True),
        compound_exist_callback: Callable[[str], bool] = (lambda _: True),
        compound_alias_exist_callback: Callable[[str], bool] = (lambda _: True),
        compound_callback: Callable[[str], CompoundAR] = (lambda _: None),
    ) -> None:
        """
        Adding a new study compound to the _study_compound_selection
        :param study_compound_selection:
        :param reason_for_missing_callback:
        :param compound_exist_callback:
        :param compound_alias_exist_callback:
        :return:
        """
        # validate VO before adding
        study_compound_selection.validate(
            selection_uid_by_details_callback=selection_uid_by_details_callback,
            reason_for_missing_callback=reason_for_missing_callback,
            compound_exist_callback=compound_exist_callback,
            compound_alias_exist_callback=compound_alias_exist_callback,
            compound_callback=compound_callback,
        )
        self._study_compounds_selection = self._study_compounds_selection + [
            study_compound_selection
        ]

    @classmethod
    def from_repository_values(
        cls,
        study_uid: str,
        study_compounds_selection: Iterable[StudySelectionCompoundVO],
    ) -> Self:
        """
        Factory method to create a AR
        :param study_uid:
        :param study_compounds_selection:
        :return:
        """
        return cls(
            _study_uid=normalize_string(study_uid),
            _study_compounds_selection=list(study_compounds_selection),
        )

    def remove_compound_selection(self, study_selection_uid: str):
        """
        removing a study compound
        :param study_selection_uid:
        :return:
        """
        updated_selection = []
        for selection in self.study_compounds_selection:
            if selection.study_selection_uid != study_selection_uid:
                updated_selection.append(selection)
        self._study_compounds_selection = tuple(updated_selection)

    def set_new_order_for_selection(self, study_selection_uid: str, new_order: int):
        """
        Used to reorder a study compound
        :param study_selection_uid:
        :param new_order:
        :return:
        """
        # check if the new order is valid using the robustness principle
        if new_order > len(self.study_compounds_selection):
            # If order is higher than maximum allowed then set to max
            new_order = len(self.study_compounds_selection)
        elif new_order < 1:
            # If order is lower than 1 set to 1
            new_order = 1
        # find the selection
        selected_value, old_order = self.get_specific_compound_selection(
            study_selection_uid
        )
        # change the order
        updated_selections = []
        for order, selection in enumerate(self.study_compounds_selection, start=1):
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
        self._study_compounds_selection = tuple(updated_selections)

    def update_selection(
        self,
        updated_study_compound_selection: StudySelectionCompoundVO,
        selection_uid_by_details_callback: Callable[["StudySelectionCompoundVO"], str],
        reason_for_missing_callback: Callable[[str], bool] = (lambda _: True),
        compound_exist_callback: Callable[[str], bool] = (lambda _: True),
        compound_alias_exist_callback: Callable[[str], bool] = (lambda _: True),
    ) -> None:
        """
        Used when a study compound is updated
        :param compound_exist_callback:
        :param reason_for_missing_callback:
        :param updated_study_compound_selection:
        :return:
        """
        updated_study_compound_selection.validate(
            selection_uid_by_details_callback=selection_uid_by_details_callback,
            reason_for_missing_callback=reason_for_missing_callback,
            compound_exist_callback=compound_exist_callback,
            compound_alias_exist_callback=compound_alias_exist_callback,
        )
        updated_selection = []
        for selection in self.study_compounds_selection:
            if (
                selection.study_selection_uid
                == updated_study_compound_selection.study_selection_uid
            ):
                updated_selection.append(updated_study_compound_selection)
            else:
                updated_selection.append(selection)
        self._study_compounds_selection = tuple(updated_selection)
