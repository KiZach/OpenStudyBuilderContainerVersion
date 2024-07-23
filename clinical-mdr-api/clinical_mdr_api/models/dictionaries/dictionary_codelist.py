from datetime import datetime
from typing import Self

from pydantic import Field

from clinical_mdr_api.domains.dictionaries.dictionary_codelist import (
    DictionaryCodelistAR,
)
from clinical_mdr_api.models import Library
from clinical_mdr_api.models.utils import BaseModel


class DictionaryCodelist(BaseModel):
    @classmethod
    def from_dictionary_codelist_ar(
        cls, dictionary_codelist_ar: DictionaryCodelistAR
    ) -> Self:
        return cls(
            codelist_uid=dictionary_codelist_ar.uid,
            name=dictionary_codelist_ar.name,
            library_name=Library.from_library_vo(dictionary_codelist_ar.library).name,
            template_parameter=dictionary_codelist_ar.dictionary_codelist_vo.is_template_parameter,
            start_date=dictionary_codelist_ar.item_metadata.start_date,
            end_date=dictionary_codelist_ar.item_metadata.end_date,
            status=dictionary_codelist_ar.item_metadata.status.value,
            version=dictionary_codelist_ar.item_metadata.version,
            change_description=dictionary_codelist_ar.item_metadata.change_description,
            user_initials=dictionary_codelist_ar.item_metadata.user_initials,
            possible_actions=sorted(
                [_.value for _ in dictionary_codelist_ar.get_possible_actions()]
            ),
        )

    codelist_uid: str = Field(
        ...,
        title="codelist_uid",
        description="",
    )

    name: str = Field(
        ...,
        title="name",
        description="",
    )

    template_parameter: bool = Field(
        ...,
        title="template_parameter",
        description="",
    )

    possible_actions: list[str] = Field(
        ...,
        description=(
            "Holds those actions that can be performed on the DictionaryCodelist. "
            "Actions are: 'approve', 'edit', 'new_version'."
        ),
    )

    library_name: str
    start_date: datetime | None = Field(None, nullable=True)
    end_date: datetime | None = Field(None, nullable=True)
    status: str | None = Field(None, nullable=True)
    version: str | None = Field(None, nullable=True)
    change_description: str | None = Field(None, nullable=True)
    user_initials: str | None = Field(None, nullable=True)


class DictionaryCodelistInput(BaseModel):
    name: str | None = Field(
        None,
        title="name",
        description="",
    )

    template_parameter: bool | None = Field(
        None,
        title="template_parameter",
        description="",
    )


class DictionaryCodelistEditInput(DictionaryCodelistInput):
    change_description: str = Field(None, title="change_description", description="")


class DictionaryCodelistCreateInput(DictionaryCodelistInput):
    library_name: str


class DictionaryCodelistTermInput(BaseModel):
    term_uid: str = Field(
        ...,
        title="term_uid",
        description="",
    )


class DictionaryCodelistVersion(DictionaryCodelist):
    """
    Class for storing DictionaryCodelist and calculation of differences
    """

    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )
