import unittest
from typing import Callable

from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import (
    CTTermCodelistVO,
    CTTermNameAR,
    CTTermNameVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.utils import random_str


def create_random_ct_term_name_vo(codelist_uid: str = random_str()) -> CTTermNameVO:
    random_ct_term_name_vo = CTTermNameVO.from_repository_values(
        codelists=[CTTermCodelistVO(codelist_uid=codelist_uid, order=1)],
        catalogue_name=random_str(),
        name=random_str(),
        name_sentence_case=random_str(),
    )
    return random_ct_term_name_vo


def create_random_ct_term_name_ar(
    # pylint: disable=unnecessary-lambda
    generate_uid_callback: Callable[[], str] = lambda: random_str(),
    codelist_uid: str = random_str(),
    library: str = "Library",
    is_editable: bool = True,
) -> CTTermNameAR:
    random_ct_term_name_ar = CTTermNameAR.from_input_values(
        generate_uid_callback=generate_uid_callback,
        ct_term_name_vo=create_random_ct_term_name_vo(codelist_uid=codelist_uid),
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=is_editable
        ),
        author="TODO Initials",
    )
    return random_ct_term_name_ar


class TestCTTermNameAR(unittest.TestCase):
    def test__init__ar_created(self):
        # given

        # when
        ct_term_name_ar = create_random_ct_term_name_ar()

        # then
        self.assertIsNone(ct_term_name_ar.item_metadata._end_date)
        self.assertIsNotNone(ct_term_name_ar.item_metadata._start_date)
        self.assertEqual(ct_term_name_ar.item_metadata.version, "0.1")
        self.assertEqual(ct_term_name_ar.item_metadata.status, LibraryItemStatus.DRAFT)

    def test__approve__version_created(self):
        # given
        ct_term_name_ar = create_random_ct_term_name_ar()

        # when
        ct_term_name_ar.approve(author="TODO")

        # then
        self.assertIsNone(ct_term_name_ar.item_metadata._end_date)
        self.assertIsNotNone(ct_term_name_ar.item_metadata._start_date)
        self.assertEqual(ct_term_name_ar.item_metadata.version, "1.0")
        self.assertEqual(ct_term_name_ar.item_metadata.status, LibraryItemStatus.FINAL)

    def test__create_new_version__version_created(self):
        # given
        ct_term_name_ar = create_random_ct_term_name_ar()
        ct_term_name_ar.approve(author="TODO")

        # when
        ct_term_name_ar.create_new_version(author="TODO")

        # then
        self.assertIsNone(ct_term_name_ar.item_metadata._end_date)
        self.assertIsNotNone(ct_term_name_ar.item_metadata._start_date)
        self.assertEqual(ct_term_name_ar.item_metadata.version, "1.1")
        self.assertEqual(ct_term_name_ar.item_metadata.status, LibraryItemStatus.DRAFT)

    def test__edit_draft_version__version_created(self):
        # given
        ct_term_name_ar = create_random_ct_term_name_ar()

        ct_term_name_ar.approve(author="Test")
        ct_term_name_ar.create_new_version(author="TODO")

        # when
        ct_term_vo = create_random_ct_term_name_vo()
        ct_term_name_ar.edit_draft(
            author="TODO",
            change_description="Test",
            ct_term_vo=ct_term_vo,
            term_exists_by_name_in_codelists_callback=lambda x, y: False,
        )

        # then
        self.assertIsNone(ct_term_name_ar.item_metadata.end_date)
        self.assertIsNotNone(ct_term_name_ar.item_metadata.start_date)
        self.assertEqual(ct_term_name_ar.item_metadata.version, "1.2")
        self.assertEqual(ct_term_name_ar.item_metadata.status, LibraryItemStatus.DRAFT)
        self.assertEqual(ct_term_name_ar.item_metadata.user_initials, "TODO")
        self.assertEqual(ct_term_name_ar.item_metadata.change_description, "Test")
        self.assertEqual(
            ct_term_name_ar.ct_term_vo.codelists[0].codelist_uid,
            ct_term_vo.codelists[0].codelist_uid,
        )
        self.assertEqual(
            ct_term_name_ar.ct_term_vo.codelists[0].order,
            ct_term_vo.codelists[0].order,
        )
        self.assertEqual(ct_term_name_ar.name, ct_term_vo.name)
        self.assertEqual(
            ct_term_name_ar.ct_term_vo.name_sentence_case, ct_term_vo.name_sentence_case
        )
        self.assertEqual(
            ct_term_name_ar.ct_term_vo.catalogue_name, ct_term_vo.catalogue_name
        )
