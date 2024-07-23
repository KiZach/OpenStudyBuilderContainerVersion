import unittest
from typing import Callable

from clinical_mdr_api.domains.concepts.compound import CompoundAR, CompoundVO
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.utils import random_str


def create_random_compound_vo() -> CompoundVO:
    random_compound_vo = CompoundVO.from_repository_values(
        name=random_str(),
        name_sentence_case=random_str(),
        definition=random_str(),
        abbreviation=random_str(),
        dose_values_uids=[random_str()],
        strength_values_uids=[random_str()],
        lag_time_uids=[random_str()],
        delivery_devices_uids=[random_str()],
        dispensers_uids=[random_str()],
        projects_uids=[random_str()],
        brands_uids=[random_str()],
        dose_frequency_uids=[random_str()],
        dosage_form_uids=[random_str()],
        route_of_administration_uids=[random_str()],
        half_life_uid=random_str(),
        analyte_number=random_str(),
        nnc_short_number=random_str(),
        nnc_long_number=random_str(),
        is_sponsor_compound=True,
        is_name_inn=True,
        substance_terms_uids=[random_str(), random_str()],
    )
    return random_compound_vo


def create_random_compound_ar(
    # pylint: disable=unnecessary-lambda
    generate_uid_callback: Callable[[], str] = lambda: random_str(),
    library: str = "Library",
    is_editable: bool = True,
) -> CompoundAR:
    random_compound_ar = CompoundAR.from_input_values(
        generate_uid_callback=generate_uid_callback,
        concept_vo=create_random_compound_vo(),
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=is_editable
        ),
        author="TODO Initials",
        compound_uid_by_property_value_callback=lambda _, __: False,
        ct_term_exists_callback=lambda _: True,
        numeric_value_exists_callback=lambda _: True,
        lag_time_exists_callback=lambda _: True,
        dictionary_term_exists_callback=lambda _: True,
        project_exists_callback=lambda _: True,
        brand_exists_callback=lambda _: True,
    )

    return random_compound_ar


class TestCompound(unittest.TestCase):
    def test__init__ar_created(self):
        # given

        # when
        compound_ar = create_random_compound_ar()

        # then
        self.assertIsNone(compound_ar.item_metadata._end_date)
        self.assertIsNotNone(compound_ar.item_metadata._start_date)
        self.assertEqual(compound_ar.item_metadata.version, "0.1")
        self.assertEqual(compound_ar.item_metadata.status, LibraryItemStatus.DRAFT)

    def test__approve__version_created(self):
        # given
        compound_ar = create_random_compound_ar()

        # when
        compound_ar.approve(author="TODO")

        # then
        self.assertIsNone(compound_ar.item_metadata._end_date)
        self.assertIsNotNone(compound_ar.item_metadata._start_date)
        self.assertEqual(compound_ar.item_metadata.version, "1.0")
        self.assertEqual(compound_ar.item_metadata.status, LibraryItemStatus.FINAL)

    def test__create_new_version__version_created(self):
        # given
        compound_ar = create_random_compound_ar()
        compound_ar.approve(author="TODO")

        # when
        compound_ar.create_new_version(author="TODO")

        # then
        self.assertIsNone(compound_ar.item_metadata._end_date)
        self.assertIsNotNone(compound_ar.item_metadata._start_date)
        self.assertEqual(compound_ar.item_metadata.version, "1.1")
        self.assertEqual(compound_ar.item_metadata.status, LibraryItemStatus.DRAFT)

    def test__inactivate_final__version_created(self):
        # given
        compound_ar = create_random_compound_ar()
        compound_ar.approve(author="TODO")

        # when
        compound_ar.inactivate(author="TODO")

        # then
        self.assertIsNone(compound_ar.item_metadata._end_date)
        self.assertIsNotNone(compound_ar.item_metadata._start_date)
        self.assertEqual(compound_ar.item_metadata.version, "1.0")
        self.assertEqual(compound_ar.item_metadata.status, LibraryItemStatus.RETIRED)

    def test__reactivate_retired__version_created(self):
        # given
        compound_ar = create_random_compound_ar()
        compound_ar.approve(author="TODO")
        compound_ar.inactivate(author="TODO")

        # when
        compound_ar.reactivate(author="TODO")

        # then
        self.assertIsNone(compound_ar.item_metadata._end_date)
        self.assertIsNotNone(compound_ar.item_metadata._start_date)
        self.assertEqual(compound_ar.item_metadata.version, "1.0")
        self.assertEqual(compound_ar.item_metadata.status, LibraryItemStatus.FINAL)

    def test__delete_draft__object_deleted(self):
        # given
        compound_ar = create_random_compound_ar()

        # when
        compound_ar.soft_delete()

        # then
        self.assertTrue(compound_ar.is_deleted)

    def test__edit_draft_version__version_created(self):
        # given
        compound_ar = create_random_compound_ar()

        compound_ar.approve(author="Test")
        compound_ar.create_new_version(author="TODO")

        # when
        compound_vo = create_random_compound_vo()

        compound_ar.edit_draft(
            author="TODO",
            change_description="Test",
            concept_vo=compound_vo,
            compound_uid_by_property_value_callback=lambda _, __: False,
            ct_term_exists_callback=lambda _: True,
            numeric_value_exists_callback=lambda _: True,
            lag_time_exists_callback=lambda _: True,
            dictionary_term_exists_callback=lambda _: True,
            project_exists_callback=lambda _: True,
            brand_exists_callback=lambda _: True,
        )
        # then
        self.assertIsNone(compound_ar.item_metadata.end_date)
        self.assertIsNotNone(compound_ar.item_metadata.start_date)
        self.assertEqual(compound_ar.item_metadata.version, "1.2")
        self.assertEqual(compound_ar.item_metadata.status, LibraryItemStatus.DRAFT)
        self.assertEqual(compound_ar.item_metadata.user_initials, "TODO")
        self.assertEqual(compound_ar.item_metadata.change_description, "Test")
        self.assertEqual(compound_ar.name, compound_vo.name)
        self.assertEqual(
            compound_ar.concept_vo.name_sentence_case,
            compound_vo.name_sentence_case,
        )
        self.assertEqual(compound_ar.concept_vo.definition, compound_vo.definition)
        self.assertEqual(
            compound_ar.concept_vo.dose_values_uids, compound_vo.dose_values_uids
        )
        self.assertEqual(
            compound_ar.concept_vo.delivery_devices_uids,
            compound_vo.delivery_devices_uids,
        )
        self.assertEqual(
            compound_ar.concept_vo.dispensers_uids, compound_vo.dispensers_uids
        )
        self.assertEqual(
            compound_ar.concept_vo.projects_uids, compound_vo.projects_uids
        )
        self.assertEqual(compound_ar.concept_vo.brands_uids, compound_vo.brands_uids)
        self.assertEqual(
            compound_ar.concept_vo.strength_values_uids,
            compound_vo.strength_values_uids,
        )
        self.assertEqual(
            compound_ar.concept_vo.lag_time_uids, compound_vo.lag_time_uids
        )
        self.assertEqual(
            compound_ar.concept_vo.dose_frequency_uids,
            compound_vo.dose_frequency_uids,
        )
        self.assertEqual(
            compound_ar.concept_vo.dosage_form_uids, compound_vo.dosage_form_uids
        )
        self.assertEqual(
            compound_ar.concept_vo.half_life_uid, compound_vo.half_life_uid
        )
        self.assertEqual(
            compound_ar.concept_vo.route_of_administration_uids,
            compound_vo.route_of_administration_uids,
        )
        self.assertEqual(
            compound_ar.concept_vo.analyte_number, compound_vo.analyte_number
        )
        self.assertEqual(
            compound_ar.concept_vo.nnc_short_number, compound_vo.nnc_short_number
        )
        self.assertEqual(
            compound_ar.concept_vo.nnc_long_number, compound_vo.nnc_long_number
        )
        self.assertEqual(
            compound_ar.concept_vo.is_sponsor_compound, compound_vo.is_sponsor_compound
        )
        self.assertEqual(compound_ar.concept_vo.is_name_inn, compound_vo.is_name_inn)
        self.assertEqual(
            compound_ar.concept_vo.substance_terms_uids,
            compound_vo.substance_terms_uids,
        )
