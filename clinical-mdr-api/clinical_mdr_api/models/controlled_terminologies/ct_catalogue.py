from datetime import datetime
from typing import Self

from pydantic import Field

from clinical_mdr_api.models.controlled_terminologies.ct_package import (
    CodelistChangeItem,
    TermChangeItem,
)
from clinical_mdr_api.models.utils import BaseModel


class CTCatalogue(BaseModel):
    name: str = Field(
        ...,
        title="name",
        description="",
    )

    library_name: str | None = Field(
        None, title="library_name", description="", nullable=True
    )


class CTCatalogueChanges(BaseModel):
    start_datetime: datetime
    end_datetime: datetime
    new_codelists: list[CodelistChangeItem]
    deleted_codelists: list[CodelistChangeItem]
    updated_codelists: list[CodelistChangeItem]
    new_terms: list[TermChangeItem]
    deleted_terms: list[TermChangeItem]
    updated_terms: list[TermChangeItem]

    @classmethod
    def from_repository_output(
        cls, start_datetime: datetime, end_datetime: datetime, query_output
    ) -> Self:
        return cls(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            new_codelists=[
                CodelistChangeItem.from_repository_output(item)
                for item in query_output["new_codelists"]
            ],
            updated_codelists=[
                CodelistChangeItem.from_repository_output(item)
                for item in query_output["updated_codelists"]
            ],
            deleted_codelists=[
                CodelistChangeItem.from_repository_output(item)
                for item in query_output["deleted_codelists"]
            ],
            new_terms=[
                TermChangeItem.from_repository_output(item)
                for item in query_output["new_terms"]
            ],
            updated_terms=[
                TermChangeItem.from_repository_output(item)
                for item in query_output["updated_terms"]
            ],
            deleted_terms=[
                TermChangeItem.from_repository_output(item)
                for item in query_output["deleted_terms"]
            ],
        )
