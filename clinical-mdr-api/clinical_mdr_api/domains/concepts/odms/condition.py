from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api.domains.concepts.concept_base import ConceptVO
from clinical_mdr_api.domains.concepts.odms.description import OdmDescriptionAR
from clinical_mdr_api.domains.concepts.odms.formal_expression import (
    OdmFormalExpressionAR,
)
from clinical_mdr_api.domains.concepts.odms.odm_ar_base import OdmARBase
from clinical_mdr_api.domains.concepts.utils import ENG_LANGUAGE
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from clinical_mdr_api.exceptions import BusinessLogicException


@dataclass(frozen=True)
class OdmConditionVO(ConceptVO):
    oid: str
    formal_expression_uids: list[str]
    description_uids: list[str]
    alias_uids: list[str]

    @classmethod
    def from_repository_values(
        cls,
        oid: str,
        name: str,
        formal_expression_uids: list[str],
        description_uids: list[str],
        alias_uids: list[str],
    ) -> Self:
        return cls(
            oid=oid,
            name=name,
            formal_expression_uids=formal_expression_uids,
            description_uids=description_uids,
            alias_uids=alias_uids,
            name_sentence_case=None,
            definition=None,
            abbreviation=None,
            is_template_parameter=False,
        )

    def validate(
        self,
        concept_exists_by_callback: Callable[[str, str, bool], bool],
        find_odm_formal_expression_callback: Callable[
            [str], OdmFormalExpressionAR | None
        ],
        find_odm_description_callback: Callable[[str], OdmDescriptionAR | None],
        odm_alias_exists_by_callback: Callable[[str, str, bool], bool],
        previous_name: str | None = None,
        previous_oid: str | None = None,
        previous_formal_expression_uids: list[str] | None = None,
    ) -> None:
        self.duplication_check(
            [("name", self.name, previous_name), ("OID", self.oid, previous_oid)],
            concept_exists_by_callback,
            "ODM Condition",
        )
        self.check_concepts_exist(
            [
                (
                    self.alias_uids,
                    "ODM Alias",
                    odm_alias_exists_by_callback,
                )
            ],
            "ODM Condition",
        )

        contexts = set()
        for formal_expression_uid in self.formal_expression_uids:
            formal_expression = find_odm_formal_expression_callback(
                formal_expression_uid
            )
            if not formal_expression:
                raise BusinessLogicException(
                    "ODM Condition tried to connect to non-existent concepts "
                    f"""[('Concept Name: ODM Formal Expression', "uids: {{'{formal_expression_uid}'}}")]."""
                )
            if formal_expression.concept_vo.context in contexts:
                raise BusinessLogicException(
                    f"ODM Condition tried to connect to ODM Formal Expressions with same context ({formal_expression.concept_vo.context})."
                )
            contexts.add(formal_expression.concept_vo.context)

            if previous_formal_expression_uids is None:
                continue
            for previous_formal_expression_uid in previous_formal_expression_uids:
                previous_formal_expression = find_odm_formal_expression_callback(
                    previous_formal_expression_uid
                )
                if (
                    formal_expression
                    and previous_formal_expression
                    and formal_expression.concept_vo.context
                    == previous_formal_expression.concept_vo.context
                    and formal_expression.uid != previous_formal_expression.uid
                ):
                    raise BusinessLogicException(
                        f"ODM Condition tried to connect to ODM Formal Expressions with same context ({formal_expression.concept_vo.context})."
                    )

        descriptions = []
        for description_uid in self.description_uids:
            desc = find_odm_description_callback(description_uid)
            if not desc:
                raise BusinessLogicException(
                    "ODM Condition tried to connect to non-existent concepts "
                    f"""[('Concept Name: ODM Description', "uids: {{'{description_uid}'}}")]."""
                )
            descriptions.append(desc)

        if not any(
            description.concept_vo.language == ENG_LANGUAGE
            for description in descriptions
        ):
            raise BusinessLogicException("An English ODM Description must be provided.")


@dataclass
class OdmConditionAR(OdmARBase):
    _concept_vo: OdmConditionVO

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @property
    def concept_vo(self) -> OdmConditionVO:
        return self._concept_vo

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        concept_vo: OdmConditionVO,
        library: LibraryVO | None,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        return cls(
            _uid=uid,
            _concept_vo=concept_vo,
            _library=library,
            _item_metadata=item_metadata,
        )

    @classmethod
    def from_input_values(
        cls,
        author: str,
        concept_vo: OdmConditionVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], str | None] = (lambda: None),
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        find_odm_formal_expression_callback: Callable[
            [str], OdmFormalExpressionAR | None
        ] = lambda _: None,
        find_odm_description_callback: Callable[
            [str], OdmDescriptionAR | None
        ] = lambda _: None,
        odm_alias_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)

        concept_vo.validate(
            concept_exists_by_callback=concept_exists_by_callback,
            find_odm_formal_expression_callback=find_odm_formal_expression_callback,
            find_odm_description_callback=find_odm_description_callback,
            odm_alias_exists_by_callback=odm_alias_exists_by_callback,
        )

        return cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )

    def edit_draft(
        self,
        author: str,
        change_description: str | None,
        concept_vo: OdmConditionVO,
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        find_odm_formal_expression_callback: Callable[
            [str], OdmFormalExpressionAR | None
        ] = lambda _: None,
        find_odm_description_callback: Callable[
            [str], OdmDescriptionAR | None
        ] = lambda _: None,
        odm_alias_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            concept_exists_by_callback=concept_exists_by_callback,
            find_odm_formal_expression_callback=find_odm_formal_expression_callback,
            find_odm_description_callback=find_odm_description_callback,
            odm_alias_exists_by_callback=odm_alias_exists_by_callback,
            previous_name=self.name,
            previous_oid=self._concept_vo.oid,
            previous_formal_expression_uids=self._concept_vo.formal_expression_uids,
        )

        super()._edit_draft(change_description=change_description, author=author)
        self._concept_vo = concept_vo
