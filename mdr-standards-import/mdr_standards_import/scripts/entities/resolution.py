from typing import Sequence, TypeVar

from mdr_standards_import.scripts.entities.inconsistency import Inconsistency


T = TypeVar("T", bound="Resolution")


class Resolution:
    default_resolutions = [
        # dict(order=1, action='catalogue-priority', valid_for_taglines=[
        #     Inconsistency.inconsistent_codelist_attributes_tagline,
        #     Inconsistency.inconsistent_term_attributes_tagline,
        #     Inconsistency.inconsistent_term_submission_value_tagline
        # ]),
        # dict(order=2, action='merge-terms',
        #      valid_for_taglines=['inconsistent terms']),
        # False positive: these codelists are not part of a code/name codelist pair.
        dict(
            action="ignore",
            valid_for_taglines=[Inconsistency.unexpected_codelist_name_tagline],
            valid_for_concept_ids=["C66788", "C170452"],
        ),
        # T(action='ignore', valid_for_taglines=[
        #     Inconsistency.no_codelists_in_package_tagline,
        #     Inconsistency.inconsistent_codelist_attributes_tagline,
        #     Inconsistency.inconsistent_term_attributes_tagline,
        #     Inconsistency.inconsistent_terms_tagline,
        #     Inconsistency.unexpected_codelist_name_tagline,
        #     Inconsistency.inconsistent_term_submission_value_tagline
        # ], valid_for_concept_ids=[]),
        # TODO add a comment property to the Resolution node
    ]

    def __init__(
        self,
        action: str,
        valid_for_taglines: Sequence[str],
        valid_for_concept_ids: Sequence[str] = [],
        invalid_for_concept_ids: Sequence[str] = [],
    ):
        self.order: int = None
        self.action: str = None
        self.valid_for_taglines: Sequence[str] = []
        self.valid_for_concept_ids: Sequence[str] = []
        self.invalid_for_concept_ids: Sequence[str] = []

    # def __init__(self, order: int, action: str, valid_for_taglines: List[str], valid_for_concept_ids: List[str], invalid_for_concept_ids: List[str]):
    #     self.order = order
    #     self.action = action
    #     self.valid_for_taglines = valid_for_taglines
    #     self.valid_for_concept_ids = valid_for_concept_ids
    #     self.invalid_for_concept_ids = invalid_for_concept_ids

    @staticmethod
    def from_node_records(node_records):
        if node_records is None:
            return []
        resolutions = []
        for node_record in node_records:
            resolutions.append(Resolution.from_node_record(node_record))
        return resolutions

    @staticmethod
    def from_node_record(node_record):
        resolution_data = (
            node_record.get("resolution", None) if node_record is not None else None
        )
        resolution = Resolution()
        if resolution_data:
            resolution.order = resolution_data.get("order", None)
            resolution.action = resolution_data.get("action", None)
            resolution.valid_for_taglines = resolution_data.get(
                "valid_for_taglines", []
            )
            resolution.valid_for_concept_ids = resolution_data.get(
                "valid_for_concept_ids", []
            )
            resolution.invalid_for_concept_ids = resolution_data.get(
                "invalid_for_concept_ids", []
            )

        return resolution
