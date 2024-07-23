from datetime import date, datetime
from typing import Any, Self

from pydantic import Field

from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.domains.controlled_terminologies.ct_package import CTPackageAR
from clinical_mdr_api.models.utils import BaseModel, snake_case_data


class CTPackage(BaseModel):
    @classmethod
    def from_ct_package_ar(cls, ct_package_ar: CTPackageAR) -> Self:
        return cls(
            uid=ct_package_ar.uid,
            catalogue_name=ct_package_ar.catalogue_name,
            name=ct_package_ar.name,
            label=ct_package_ar.label,
            description=ct_package_ar.description,
            href=ct_package_ar.href,
            registration_status=ct_package_ar.registration_status,
            source=ct_package_ar.source,
            extends_package=ct_package_ar.extends_package,
            import_date=ct_package_ar.import_date,
            effective_date=ct_package_ar.effective_date,
            user_initials=ct_package_ar.user_initials,
        )

    uid: str = Field(
        ...,
        title="uid",
        description="",
    )

    catalogue_name: str = Field(
        ...,
        title="catalogue_name",
        description="",
    )
    name: str = Field(
        ...,
        title="name",
        description="",
    )
    label: str | None = Field(None, title="label", description="", nullable=True)
    description: str | None = Field(
        None, title="description", description="", nullable=True
    )
    href: str | None = Field(None, title="href", description="", nullable=True)
    registration_status: str | None = Field(
        None, title="registration_status", description="", nullable=True
    )
    source: str | None = Field(None, title="source", description="", nullable=True)
    extends_package: str | None = Field(
        None,
        title="extends_package",
        description="CDISC CT Package extended by this sponsor package",
        nullable=True,
    )
    import_date: datetime = Field(
        ...,
        title="import_date",
        description="",
    )
    effective_date: date = Field(
        ...,
        title="effective_date",
        description="",
    )
    user_initials: str = Field(
        ...,
        title="user_initials",
        description="",
    )


class CodelistChangeItem(BaseModel):
    uid: str
    value_node: dict
    change_date: datetime
    is_change_of_codelist: bool

    @classmethod
    def from_repository_output(cls, query_output) -> Self:
        return cls(
            uid=query_output["uid"],
            value_node=snake_case_data(query_output["value_node"]),
            change_date=convert_to_datetime(value=query_output["change_date"]),
            is_change_of_codelist=query_output.get("is_change_of_codelist", True),
        )


class TermChangeItem(BaseModel):
    uid: str
    value_node: dict
    change_date: datetime
    codelists: list[Any]

    @classmethod
    def from_repository_output(cls, query_output) -> Self:
        return cls(
            uid=query_output["uid"],
            value_node=snake_case_data(query_output["value_node"]),
            change_date=convert_to_datetime(value=query_output["change_date"]),
            codelists=query_output["codelists"],
        )


class CTPackageChanges(BaseModel):
    from_package: str
    to_package: str
    new_codelists: list[CodelistChangeItem]
    deleted_codelists: list[CodelistChangeItem]
    updated_codelists: list[CodelistChangeItem]

    new_terms: list[TermChangeItem]
    deleted_terms: list[TermChangeItem]
    updated_terms: list[TermChangeItem]

    @classmethod
    def from_repository_output(
        cls, old_package_name: str, new_package_name: str, query_output
    ) -> Self:
        return cls(
            from_package=old_package_name,
            to_package=new_package_name,
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


class CTPackageChangesSpecificCodelist(CTPackageChanges):
    not_modified_terms: list[TermChangeItem]

    @classmethod
    def from_repository_output(
        cls, old_package_name: str, new_package_name: str, query_output
    ) -> Self:
        return cls(
            from_package=old_package_name,
            to_package=new_package_name,
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
            not_modified_terms=[
                TermChangeItem.from_repository_output(item)
                for item in query_output["not_modified_terms"]
            ],
        )


class CTPackageDates(BaseModel):
    @classmethod
    def from_repository_output(
        cls, catalogue_name: str, effective_dates: list[date]
    ) -> Self:
        return cls(catalogue_name=catalogue_name, effective_dates=effective_dates)

    catalogue_name: str = Field(
        ...,
        title="catalogue_name",
        description="",
    )
    effective_dates: list[date] = Field(..., title="effective_dates", description="")
