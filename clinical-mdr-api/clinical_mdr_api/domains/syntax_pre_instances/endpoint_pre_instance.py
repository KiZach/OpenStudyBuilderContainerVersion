from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api.domains.libraries.object import ParametrizedTemplateVO
from clinical_mdr_api.domains.syntax_pre_instances.pre_instance_ar import PreInstanceAR
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameAndAttributes,
    SimpleTermModel,
)


@dataclass
class EndpointPreInstanceAR(PreInstanceAR):
    """
    Implementation of EndpointPreInstanceAR. Solely based on Parametrized Template.
    """

    _indications: SimpleTermModel | None = None

    _categories: list[SimpleCTTermNameAndAttributes] | None = None

    _subcategories: list[SimpleCTTermNameAndAttributes] | None = None

    @property
    def indications(self) -> SimpleTermModel:
        return self._indications

    @property
    def categories(self) -> list[SimpleCTTermNameAndAttributes]:
        return self._categories

    @property
    def sub_categories(self) -> list[SimpleCTTermNameAndAttributes]:
        return self._subcategories

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        template: ParametrizedTemplateVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
        sequence_id: str,
        study_count: int = 0,
        indications: SimpleTermModel | None = None,
        categories: list[SimpleCTTermNameAndAttributes] | None = None,
        sub_categories: list[SimpleCTTermNameAndAttributes] | None = None,
    ) -> Self:
        return cls(
            _uid=uid,
            _sequence_id=sequence_id,
            _item_metadata=item_metadata,
            _library=library,
            _template=template,
            _indications=indications,
            _categories=categories,
            _subcategories=sub_categories,
            _study_count=study_count,
        )

    @classmethod
    def from_input_values(
        cls,
        author: str,
        library: LibraryVO,
        template: ParametrizedTemplateVO,
        generate_uid_callback: Callable[[], str | None] = (lambda: None),
        next_available_sequence_id_callback: Callable[[str], str | None] = (
            lambda _: None
        ),
        indications: SimpleTermModel | None = None,
        categories: list[SimpleCTTermNameAndAttributes] | None = None,
        sub_categories: list[SimpleCTTermNameAndAttributes] | None = None,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)

        generated_uid = generate_uid_callback()

        ar = cls(
            _uid=generated_uid,
            _sequence_id=next_available_sequence_id_callback(template.template_uid),
            _library=library,
            _template=template,
            _item_metadata=item_metadata,
        )
        ar._indications = indications
        ar._categories = categories
        ar._subcategories = sub_categories

        return ar
