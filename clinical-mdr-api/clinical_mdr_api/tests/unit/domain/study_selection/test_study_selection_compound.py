import datetime
import random
import unittest
from copy import copy

from clinical_mdr_api import exceptions
from clinical_mdr_api.domains.concepts.compound import CompoundAR, CompoundVO
from clinical_mdr_api.domains.study_selections.study_selection_compound import (
    StudySelectionCompoundsAR,
    StudySelectionCompoundVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.tests.unit.domain.utils import random_str

uid_list = ["uid_compound", "null_value"]


# Simple callback to see if string exist in list(mock DB)
def _check_uid_exists_callback(uid: str) -> bool:
    if uid in uid_list:
        return True
    return False


def _compound_callback(uid: str) -> bool:
    return CompoundAR.from_repository_values(
        uid=uid,
        library=LibraryVO.from_repository_values(
            library_name="Sponsor", is_editable=True
        ),
        item_metadata=None,
        concept_vo=CompoundVO.from_repository_values(
            name="a",
            name_sentence_case="a",
            definition="a",
            abbreviation="a",
            is_name_inn=False,
            is_sponsor_compound=False,
            analyte_number="a",
            nnc_long_number="a",
            nnc_short_number="a",
            substance_terms_uids=[],
            projects_uids=[],
            brands_uids=[],
            lag_time_uids=[],
            half_life_uid="half_life_ui1",
            dosage_form_uids=["dosage_form_uid1"],
            dispensers_uids=["dispensers_uid1"],
            strength_values_uids=["strength_values_uid1"],
            route_of_administration_uids=["route_of_administration_uid1"],
            delivery_devices_uids=["delivery_devices_uid1"],
            dose_frequency_uids=["dose_frequency_uid1"],
            dose_values_uids=["dose_values_uid1"],
        ),
    )


def _return_false_callback(_val) -> bool:
    return False


def create_random_valid_vo(
    selection_uid: str | None = None,
) -> StudySelectionCompoundVO:
    if selection_uid is None:
        selection_uid = random_str()
    uid_compound = random_str()
    uid_list.append(uid_compound)
    start_datetime = datetime.datetime.now(datetime.timezone.utc)
    study_selection_compound_vo = StudySelectionCompoundVO.from_input_values(
        compound_uid=uid_compound,
        compound_alias_uid=uid_compound,
        type_of_treatment_uid=random_str(),
        reason_for_missing_value_uid=None,
        route_of_administration_uid="route_of_administration_uid1",
        strength_value_uid="strength_values_uid1",
        dosage_form_uid="dosage_form_uid1",
        dispensed_in_uid="dispensers_uid1",
        device_uid="delivery_devices_uid1",
        formulation_uid=random_str(),
        other_info=random_str(),
        start_date=start_datetime,
        user_initials="TODO USER",
        study_selection_uid=selection_uid,
    )
    study_selection_compound_vo.validate(
        selection_uid_by_details_callback=_return_false_callback,
        reason_for_missing_callback=_check_uid_exists_callback,
        compound_exist_callback=_check_uid_exists_callback,
        compound_alias_exist_callback=_check_uid_exists_callback,
        compound_callback=_compound_callback,
    )
    return study_selection_compound_vo


# test StudySelectionCompoundVO
class TestStudySelectionCompoundVO(unittest.TestCase):
    def test__validate__success(self):
        start_datetime = datetime.datetime.now(datetime.timezone.utc)
        test_tuples = [
            [
                "uid_compound",
                random_str(),
                random_str(),
                None,
                "route_of_administration_uid1",
                "strength_values_uid1",
                "dosage_form_uid1",
                random_str(),
                "dispensers_uid1",
                random_str(),
                "delivery_devices_uid1",
                random_str(),
                random_str(),
                random_str(),
                random_str(),
            ],
            [
                " uid_compound",
                random_str(),
                random_str(),
                None,
                "route_of_administration_uid1",
                "strength_values_uid1",
                "dosage_form_uid1",
                random_str(),
                "dispensers_uid1",
                random_str(),
                "delivery_devices_uid1",
                random_str(),
                random_str(),
                random_str(),
                random_str(),
            ],
            [
                "uid_compound ",
                random_str(),
                random_str(),
                None,
                "route_of_administration_uid1",
                "strength_values_uid1",
                "dosage_form_uid1",
                random_str(),
                "dispensers_uid1",
                random_str(),
                "delivery_devices_uid1",
                random_str(),
                random_str(),
                random_str(),
                random_str(),
            ],
            [
                " uid_compound ",
                random_str(),
                random_str(),
                None,
                "route_of_administration_uid1",
                "strength_values_uid1",
                "dosage_form_uid1",
                random_str(),
                "dispensers_uid1",
                random_str(),
                "delivery_devices_uid1",
                random_str(),
                random_str(),
                random_str(),
                random_str(),
            ],
            [
                None,
                random_str(),
                random_str(),
                "null_value",
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            ],
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_compound = StudySelectionCompoundVO.from_input_values(
                    compound_uid=test_tuple[0],
                    compound_alias_uid=test_tuple[0],
                    type_of_treatment_uid=test_tuple[1],
                    reason_for_missing_value_uid=test_tuple[3],
                    route_of_administration_uid=test_tuple[4],
                    strength_value_uid=test_tuple[5],
                    dosage_form_uid=test_tuple[6],
                    dispensed_in_uid=test_tuple[8],
                    device_uid=test_tuple[10],
                    formulation_uid=test_tuple[12],
                    other_info=test_tuple[14],
                    start_date=start_datetime,
                    user_initials="TODO USER",
                    study_selection_uid="dummy",
                )
                study_selection_compound.validate(
                    selection_uid_by_details_callback=_return_false_callback,
                    reason_for_missing_callback=_check_uid_exists_callback,
                    compound_exist_callback=_check_uid_exists_callback,
                    compound_alias_exist_callback=_check_uid_exists_callback,
                    compound_callback=_compound_callback,
                )

    def test__validate__failure(self):
        start_datetime = datetime.datetime.now(datetime.timezone.utc)
        test_tuples = [
            [
                "uid_compound",
                random_str(),
                random_str(),
                "null_value",
                random_str(),
                random_str(),
                random_str(),
                random_str(),
                random_str(),
                random_str(),
                random_str(),
                random_str(),
                random_str(),
                random_str(),
                random_str(),
            ],
            [
                " uid_compound_WRONG_VALUE",
                random_str(),
                random_str(),
                None,
                random_str(),
                random_str(),
                random_str(),
                random_str(),
                random_str(),
                random_str(),
                random_str(),
                random_str(),
                random_str(),
                random_str(),
                random_str(),
            ],
            [
                None,
                random_str(),
                random_str(),
                "null_value_WRONG VALUE",
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            ],
            [
                random_str(),
                random_str(),
                random_str(),
                "null_value",
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            ],
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_compound = StudySelectionCompoundVO.from_input_values(
                    compound_uid=test_tuple[0],
                    compound_alias_uid=test_tuple[0],
                    type_of_treatment_uid=test_tuple[1],
                    reason_for_missing_value_uid=test_tuple[3],
                    route_of_administration_uid=test_tuple[4],
                    strength_value_uid=test_tuple[5],
                    dosage_form_uid=test_tuple[6],
                    dispensed_in_uid=test_tuple[8],
                    device_uid=test_tuple[10],
                    formulation_uid=test_tuple[12],
                    other_info=test_tuple[14],
                    start_date=start_datetime,
                    user_initials="TODO USER",
                    study_selection_uid="dummy",
                )
                with self.assertRaises(exceptions.ValidationException):
                    study_selection_compound.validate(
                        selection_uid_by_details_callback=_return_false_callback,
                        reason_for_missing_callback=_check_uid_exists_callback,
                        compound_exist_callback=_check_uid_exists_callback,
                        compound_alias_exist_callback=_check_uid_exists_callback,
                        compound_callback=_compound_callback,
                    )


class TestStudySelectionCompoundAR(unittest.TestCase):
    def test__add_new_vo(self):
        test_tuples = [
            (random_str(), []),
            (random_str(), [create_random_valid_vo()]),
            (random_str(), [create_random_valid_vo(), create_random_valid_vo()]),
            (
                random_str(),
                [
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                ],
            ),
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_compound_ar = (
                    StudySelectionCompoundsAR.from_repository_values(
                        study_uid=test_tuple[0],
                        study_compounds_selection=copy(test_tuple[1]),
                    )
                )
                study_selection_compound_ar.repository_closure_data = copy(
                    test_tuple[1]
                )
                self.assertEqual(
                    len(test_tuple[1]),
                    len(study_selection_compound_ar.study_compounds_selection),
                )

                study_selection_compound_ar.add_compound_selection(
                    create_random_valid_vo(),
                    _check_uid_exists_callback,
                    _check_uid_exists_callback,
                    _check_uid_exists_callback,
                    _compound_callback,
                )

                self.assertEqual(
                    len(test_tuple[1]) + 1,
                    len(study_selection_compound_ar.study_compounds_selection),
                )

    def test__get_specific_vo(self):
        test_tuples = [
            (random_str(), []),
            (random_str(), [create_random_valid_vo()]),
            (random_str(), [create_random_valid_vo(), create_random_valid_vo()]),
            (
                random_str(),
                [
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                ],
            ),
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_compound_ar = (
                    StudySelectionCompoundsAR.from_repository_values(
                        study_uid=test_tuple[0],
                        study_compounds_selection=copy(test_tuple[1]),
                    )
                )
                new_vo = create_random_valid_vo()
                study_selection_compound_ar.add_compound_selection(
                    new_vo,
                    _check_uid_exists_callback,
                    _check_uid_exists_callback,
                    _check_uid_exists_callback,
                )

                (
                    selection,
                    order,
                ) = study_selection_compound_ar.get_specific_compound_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(new_vo, selection)
                self.assertEqual(len(test_tuple[1]) + 1, order)
                with self.assertRaises(exceptions.NotFoundException):
                    study_selection_compound_ar.get_specific_compound_selection(
                        "wrong uid"
                    )

    def test__remove_vo(self):
        test_tuples = [
            (random_str(), []),
            (random_str(), [create_random_valid_vo()]),
            (random_str(), [create_random_valid_vo(), create_random_valid_vo()]),
            (
                random_str(),
                [
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                ],
            ),
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_compound_ar = (
                    StudySelectionCompoundsAR.from_repository_values(
                        study_uid=test_tuple[0],
                        study_compounds_selection=copy(test_tuple[1]),
                    )
                )
                new_vo = create_random_valid_vo()
                study_selection_compound_ar.add_compound_selection(
                    new_vo,
                    selection_uid_by_details_callback=_return_false_callback,
                )

                # ensure it is still there
                (
                    selection,
                    _order,
                ) = study_selection_compound_ar.get_specific_compound_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(new_vo, selection)

                # remove the vo
                study_selection_compound_ar.remove_compound_selection(
                    new_vo.study_selection_uid
                )

                # assert that it is no longer in the AR
                with self.assertRaises(exceptions.NotFoundException):
                    study_selection_compound_ar.get_specific_compound_selection(
                        new_vo.study_selection_uid
                    )

    def test__update_vo(self):
        test_tuples = [
            (random_str(), []),
            (random_str(), [create_random_valid_vo()]),
            (random_str(), [create_random_valid_vo(), create_random_valid_vo()]),
            (
                random_str(),
                [
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                ],
            ),
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_compound_ar = (
                    StudySelectionCompoundsAR.from_repository_values(
                        study_uid=test_tuple[0],
                        study_compounds_selection=copy(test_tuple[1]),
                    )
                )
                new_vo = create_random_valid_vo()
                study_selection_compound_ar.add_compound_selection(
                    new_vo,
                    selection_uid_by_details_callback=_return_false_callback,
                )

                # ensure it is still there
                (
                    selection,
                    _order,
                ) = study_selection_compound_ar.get_specific_compound_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(new_vo, selection)

                # create a updated vo
                updated_vo = create_random_valid_vo(
                    selection_uid=new_vo.study_selection_uid
                )

                # update the selection
                study_selection_compound_ar.update_selection(
                    updated_study_compound_selection=updated_vo,
                    selection_uid_by_details_callback=_return_false_callback,
                    reason_for_missing_callback=_check_uid_exists_callback,
                    compound_exist_callback=_check_uid_exists_callback,
                    compound_alias_exist_callback=_check_uid_exists_callback,
                )

                # assert that the two vo are not the same
                self.assertFalse(new_vo is updated_vo)

                # assert updated has updated to the new vo but kept the uid
                (
                    selection
                ) = study_selection_compound_ar.get_specific_compound_selection(
                    new_vo.study_selection_uid
                )

                self.assertEqual(selection[0], updated_vo)

    def test__reorder_vo(self):
        test_tuples = [
            (random_str(), []),
            (random_str(), [create_random_valid_vo()]),
            (random_str(), [create_random_valid_vo(), create_random_valid_vo()]),
            (
                random_str(),
                [
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                    create_random_valid_vo(),
                ],
            ),
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                study_selection_compound_ar = (
                    StudySelectionCompoundsAR.from_repository_values(
                        study_uid=test_tuple[0],
                        study_compounds_selection=copy(test_tuple[1]),
                    )
                )
                new_vo = create_random_valid_vo()
                study_selection_compound_ar.add_compound_selection(
                    new_vo,
                    selection_uid_by_details_callback=_return_false_callback,
                )

                # ensure it is still there
                (
                    selection,
                    order,
                ) = study_selection_compound_ar.get_specific_compound_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(new_vo, selection)

                new_order = random.randrange(1, len(test_tuple[1]) + 2, 1)
                study_selection_compound_ar.set_new_order_for_selection(
                    study_selection_uid=new_vo.study_selection_uid, new_order=new_order
                )

                (
                    selection,
                    order,
                ) = study_selection_compound_ar.get_specific_compound_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(new_order, order)

                # assert that the selection is put on the end when the order is higher than the amount of selections in total
                study_selection_compound_ar.set_new_order_for_selection(
                    study_selection_uid=new_vo.study_selection_uid, new_order=999
                )
                (
                    selection,
                    order,
                ) = study_selection_compound_ar.get_specific_compound_selection(
                    new_vo.study_selection_uid
                )

                self.assertEqual(
                    len(study_selection_compound_ar.study_compounds_selection), order
                )

                # assert that the selection is put in front when the order is lower than 1
                study_selection_compound_ar.set_new_order_for_selection(
                    study_selection_uid=new_vo.study_selection_uid, new_order=-99
                )
                (
                    selection,
                    order,
                ) = study_selection_compound_ar.get_specific_compound_selection(
                    new_vo.study_selection_uid
                )
                self.assertEqual(1, order)
