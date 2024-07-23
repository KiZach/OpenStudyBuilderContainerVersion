import unittest
from typing import Callable

from clinical_mdr_api import exceptions
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
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.utils import random_str


def create_random_activity_instance_grouping_vo() -> ActivityInstanceGroupingVO:
    random_activity_instance_grouping_vo = ActivityInstanceGroupingVO(
        activity_group_uid=random_str(),
        activity_subgroup_uid=random_str(),
        activity_uid=random_str(),
    )
    return random_activity_instance_grouping_vo


def create_random_activity_instance_vo() -> ActivityInstanceVO:
    name = random_str()
    random_activity_instance_vo = ActivityInstanceVO.from_repository_values(
        nci_concept_id=random_str(),
        name=name,
        name_sentence_case=name,
        definition=random_str(),
        abbreviation=random_str(),
        activity_instance_class_uid=random_str(),
        activity_instance_class_name=random_str(),
        topic_code=random_str(),
        adam_param_code=random_str(),
        is_required_for_activity=True,
        is_default_selected_for_activity=True,
        is_data_sharing=True,
        is_legacy_usage=True,
        is_derived=False,
        legacy_description=random_str(),
        activity_groupings=[
            create_random_activity_instance_grouping_vo(),
            create_random_activity_instance_grouping_vo(),
        ],
        activity_items=[
            ActivityItemVO.from_repository_values(
                activity_item_class_uid=random_str(),
                activity_item_class_name=random_str(),
                ct_terms=[LibraryItem(uid=random_str(), name=random_str())],
                unit_definitions=[LibraryItem(uid=random_str(), name=random_str())],
            ),
            ActivityItemVO.from_repository_values(
                activity_item_class_uid=random_str(),
                activity_item_class_name=random_str(),
                ct_terms=[LibraryItem(uid=random_str(), name=random_str())],
                unit_definitions=[LibraryItem(uid=random_str(), name=random_str())],
            ),
        ],
    )
    return random_activity_instance_vo


def create_random_activity_instance_ar(
    # pylint: disable=unnecessary-lambda
    generate_uid_callback: Callable[[], str] = lambda: random_str(),
    library: str = "Library",
    is_editable: bool = True,
) -> ActivityInstanceAR:
    random_activity_instance_ar = ActivityInstanceAR.from_input_values(
        generate_uid_callback=generate_uid_callback,
        concept_vo=create_random_activity_instance_vo(),
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=is_editable
        ),
        author="TODO Initials",
        concept_exists_by_callback=lambda x, y, z: False,
        activity_hierarchy_exists_by_uid_callback=lambda _: True,
        activity_subgroup_exists=lambda _: True,
        activity_group_exists=lambda _: True,
        activity_instance_class_exists_by_uid_callback=lambda _: True,
        activity_item_class_exists_by_uid_callback=lambda _: True,
        ct_term_exists_by_uid_callback=lambda _: True,
        unit_definition_exists_by_uid_callback=lambda _: True,
    )

    return random_activity_instance_ar


class TestActivityInstance(unittest.TestCase):
    def test__init__ar_created(self):
        # given

        # when
        activity_instance_ar = create_random_activity_instance_ar()

        # then
        self.assertIsNone(activity_instance_ar.item_metadata._end_date)
        self.assertIsNotNone(activity_instance_ar.item_metadata._start_date)
        self.assertEqual(activity_instance_ar.item_metadata.version, "0.1")
        self.assertEqual(
            activity_instance_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )

    def test__approve__version_created(self):
        # given
        activity_instance_ar = create_random_activity_instance_ar()

        # when
        activity_instance_ar.approve(author="TODO")

        # then
        self.assertIsNone(activity_instance_ar.item_metadata._end_date)
        self.assertIsNotNone(activity_instance_ar.item_metadata._start_date)
        self.assertEqual(activity_instance_ar.item_metadata.version, "1.0")
        self.assertEqual(
            activity_instance_ar.item_metadata.status, LibraryItemStatus.FINAL
        )

    def test__create_new_version__version_created(self):
        # given
        activity_instance_ar = create_random_activity_instance_ar()
        activity_instance_ar.approve(author="TODO")

        # when
        activity_instance_ar.create_new_version(author="TODO")

        # then
        self.assertIsNone(activity_instance_ar.item_metadata._end_date)
        self.assertIsNotNone(activity_instance_ar.item_metadata._start_date)
        self.assertEqual(activity_instance_ar.item_metadata.version, "1.1")
        self.assertEqual(
            activity_instance_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )

    def test__inactivate_final__version_created(self):
        # given
        activity_instance_ar = create_random_activity_instance_ar()
        activity_instance_ar.approve(author="TODO")

        # when
        activity_instance_ar.inactivate(author="TODO")

        # then
        self.assertIsNone(activity_instance_ar.item_metadata._end_date)
        self.assertIsNotNone(activity_instance_ar.item_metadata._start_date)
        self.assertEqual(activity_instance_ar.item_metadata.version, "1.0")
        self.assertEqual(
            activity_instance_ar.item_metadata.status, LibraryItemStatus.RETIRED
        )

    def test__reactivate_retired__version_created(self):
        # given
        activity_instance_ar = create_random_activity_instance_ar()
        activity_instance_ar.approve(author="TODO")
        activity_instance_ar.inactivate(author="TODO")

        # when
        activity_instance_ar.reactivate(author="TODO")

        # then
        self.assertIsNone(activity_instance_ar.item_metadata._end_date)
        self.assertIsNotNone(activity_instance_ar.item_metadata._start_date)
        self.assertEqual(activity_instance_ar.item_metadata.version, "1.0")
        self.assertEqual(
            activity_instance_ar.item_metadata.status, LibraryItemStatus.FINAL
        )

    def test__delete_draft__object_deleted(self):
        # given
        activity_instance_ar = create_random_activity_instance_ar()

        # when
        activity_instance_ar.soft_delete()

        # then
        self.assertTrue(activity_instance_ar.is_deleted)


class TestActivityInstanceNegative(unittest.TestCase):
    def test__init__ar_validation_failure(self):
        name = random_str()
        with self.assertRaises(exceptions.ValidationException) as context:
            ActivityInstanceAR.from_input_values(
                generate_uid_callback=random_str,
                concept_vo=ActivityInstanceVO.from_repository_values(
                    nci_concept_id="C123",
                    name=name,
                    name_sentence_case="Different from name",
                    definition=random_str(),
                    abbreviation=random_str(),
                    activity_instance_class_uid=random_str(),
                    activity_instance_class_name=random_str(),
                    topic_code=random_str(),
                    adam_param_code=random_str(),
                    is_required_for_activity=True,
                    is_default_selected_for_activity=True,
                    is_data_sharing=True,
                    is_legacy_usage=True,
                    is_derived=False,
                    legacy_description=random_str(),
                    activity_groupings=[
                        create_random_activity_instance_grouping_vo(),
                        create_random_activity_instance_grouping_vo(),
                    ],
                    activity_items=[
                        ActivityItemVO.from_repository_values(
                            activity_item_class_uid=random_str(),
                            activity_item_class_name=random_str(),
                            ct_terms={"name": random_str(), "uid": random_str()},
                            unit_definitions={
                                "name": random_str(),
                                "uid": random_str(),
                            },
                        ),
                        ActivityItemVO.from_repository_values(
                            activity_item_class_uid=random_str(),
                            activity_item_class_name=random_str(),
                            ct_terms={"name": random_str(), "uid": random_str()},
                            unit_definitions={
                                "name": random_str(),
                                "uid": random_str(),
                            },
                        ),
                    ],
                ),
                library=LibraryVO.from_repository_values(
                    library_name="library", is_editable=True
                ),
                author="TODO Initials",
                concept_exists_by_callback=lambda x, y, z: False,
                activity_hierarchy_exists_by_uid_callback=lambda _: True,
                activity_subgroup_exists=lambda _: True,
                activity_group_exists=lambda _: True,
                activity_instance_class_exists_by_uid_callback=lambda _: True,
                activity_item_class_exists_by_uid_callback=lambda _: True,
                ct_term_exists_by_uid_callback=lambda _: True,
                unit_definition_exists_by_uid_callback=lambda _: True,
            )

        assert (
            context.exception.msg
            == f"Lowercase versions of '{name}' and 'Different from name' must be equal"
        )
