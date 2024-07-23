from enum import Enum

from pydantic import Field

from clinical_mdr_api.models.controlled_terminologies.ct_codelist import (
    CTCodelistNameAndAttributes,
)
from clinical_mdr_api.models.utils import BaseModel


class CodelistCount(BaseModel):
    library_name: str
    count: int


class TermCount(BaseModel):
    library_name: str
    count: int


class CountTypeEnum(str, Enum):
    ADDED = "added"
    DELETED = "deleted"
    UPDATED = "updated"


class CountByType(BaseModel):
    type: CountTypeEnum
    count: int


class CountByTypeByYear(BaseModel):
    year: int
    counts: list[CountByType]


class CTStats(BaseModel):
    catalogues: int = Field(
        ..., title="catalogues", description="Number of catalogues in the database"
    )
    packages: int = Field(
        ..., title="packages", description="Number of packages in the database"
    )
    codelist_counts: list[CodelistCount] = Field(
        ...,
        title="codelist_counts",
        description="Count of codelists grouped by Library",
    )
    term_counts: list[TermCount] = Field(
        ..., title="term_counts", description="Count of terms grouped by Library"
    )
    codelist_change_percentage: float = Field(
        ...,
        title="codelist_change_percentage",
        description="Mean percentage of evolution for codelists",
    )
    term_change_percentage: float = Field(
        ...,
        title="term_change_percentage",
        description="Mean percentage of evolution for terms",
    )
    codelist_change_details: list[CountByTypeByYear] = Field(
        ...,
        title="codelist_change_details",
        description="Codelist changes, grouped by type and year",
    )
    term_change_details: list[CountByTypeByYear] = Field(
        ...,
        title="term_change_details",
        description="Term changes, grouped by type and year",
    )
    latest_added_codelists: list[CTCodelistNameAndAttributes] = Field(
        ...,
        title="latest_added_codelists",
        description="List of latest added codelists",
    )
