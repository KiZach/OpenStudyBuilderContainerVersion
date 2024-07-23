from typing import Self

from pydantic import Field

from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.utils import BaseModel


class Library(BaseModel):
    name: str = Field(
        ...,
        description="The name of the library and at the same time the unique identifier for a library entity.",
    )
    is_editable: bool = Field(
        False,
        description="Denotes whether or not the library allows to \n\n"
        "* create new entities (e.g. objective templates, objectives, ...) and \n"
        "* change existing entities.",
    )

    @classmethod
    def from_library_vo(cls, library_vo: LibraryVO) -> Self:
        return cls(name=library_vo.name, is_editable=library_vo.is_editable)


class ItemCounts(BaseModel):
    """
    Model used for expressing counts of instantiations of objective, endpoint etc.
    templates.
    """

    total: int = Field(0, description="Total count of instantiations")
    draft: int = Field(0, description="Count of instantiations in draft status")
    retired: int = Field(0, description="Count of instantiations in retired status")
    final: int = Field(0, description="Count of instantiations in final status")
