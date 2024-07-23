from datetime import datetime
from typing import TypeVar

from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesAR,
    CTCodelistAttributesVO,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_name import (
    CTCodelistNameAR,
    CTCodelistNameVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models import (
    CTCodelist,
    CTCodelistCreateInput,
    CTCodelistNameAndAttributes,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.oauth.user import user
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository  # type: ignore
from clinical_mdr_api.services._utils import is_library_editable, normalize_string

_AggregateRootType = TypeVar("_AggregateRootType")


class CTCodelistService:
    _repos: MetaRepository
    user_initials: str | None

    def __init__(self):
        self.user_initials = user().id()
        self._repos = MetaRepository(self.user_initials)

    def __del__(self):
        self._repos.close()

    def non_transactional_create(
        self,
        codelist_input: CTCodelistCreateInput,
        start_date: datetime | None = None,
    ) -> CTCodelist:
        """
        Method creates CTCodelistAttributesAR and saves that object to the database.
        When saving CTCodelistAttributesAR - CTCodelistRoot node is created that will become a root node for
        CTCodelistAttributes and CTCodelistName nodes.
        The uid for the CTCodelistRoot is assigned when the CTCodelistAttributesAR is being created.
        Created CTCodelistRoot uid is then passed to the CTCodelistNameAR.
        The uid of CTCodelistRoot node is used by CTCodelistName repository to create a
        relationship from CTCodelistRoot to CTCodelistName node when saving a CTCodelistNameAR.
        If terms are provided then the codelist will be approved and the terms will be connected to the codelist.
        When no terms are provided the codelist is created in draft state.
        :param codelist_input:
        :return codelist:CTCodelist
        """

        if not self._repos.library_repository.library_exists(
            normalize_string(codelist_input.library_name)
        ):
            raise exceptions.BusinessLogicException(
                f"There is no library identified by provided library name ({codelist_input.library_name})"
            )

        library_vo = LibraryVO.from_input_values_2(
            library_name=codelist_input.library_name,
            is_library_editable_callback=is_library_editable,
        )

        ct_codelist_attributes_ar = CTCodelistAttributesAR.from_input_values(
            author=self.user_initials,
            ct_codelist_attributes_vo=CTCodelistAttributesVO.from_input_values(
                name=codelist_input.name,
                parent_codelist_uid=codelist_input.parent_codelist_uid,
                catalogue_name=codelist_input.catalogue_name,
                submission_value=codelist_input.submission_value,
                preferred_term=codelist_input.nci_preferred_name,
                definition=codelist_input.definition,
                extensible=codelist_input.extensible,
                catalogue_exists_callback=self._repos.ct_catalogue_repository.catalogue_exists,
                codelist_exists_by_uid_callback=self._repos.ct_codelist_attribute_repository.codelist_specific_exists_by_uid,
                codelist_exists_by_name_callback=self._repos.ct_codelist_attribute_repository.codelist_specific_exists_by_name,
                codelist_exists_by_submission_value_callback=(
                    self._repos.ct_codelist_attribute_repository.codelist_attributes_exists_by_submission_value
                ),
            ),
            library=library_vo,
            start_date=start_date,
            generate_uid_callback=self._repos.ct_codelist_attribute_repository.generate_uid,
        )

        if codelist_input.terms:
            ct_codelist_attributes_ar.approve(author=self.user_initials)

        self._repos.ct_codelist_attribute_repository.save(ct_codelist_attributes_ar)

        ct_codelist_name_ar = CTCodelistNameAR.from_input_values(
            author=self.user_initials,
            ct_codelist_name_vo=CTCodelistNameVO.from_input_values(
                name=codelist_input.sponsor_preferred_name,
                catalogue_name=codelist_input.catalogue_name,
                is_template_parameter=codelist_input.template_parameter,
                catalogue_exists_callback=self._repos.ct_catalogue_repository.catalogue_exists,
                codelist_exists_by_name_callback=self._repos.ct_codelist_name_repository.codelist_specific_exists_by_name,
            ),
            library=library_vo,
            start_date=start_date,
            generate_uid_callback=lambda: ct_codelist_attributes_ar.uid,
        )

        self._repos.ct_codelist_name_repository.save(ct_codelist_name_ar)

        if codelist_input.terms:
            parent_codelist_uid = (
                ct_codelist_attributes_ar.ct_codelist_vo.parent_codelist_uid
            )

            term_uids = [term.term_uid for term in codelist_input.terms]

            if parent_codelist_uid:
                sub_codelist_with_given_terms = (
                    self.get_sub_codelists_that_have_given_terms(
                        parent_codelist_uid, term_uids
                    )
                )

                if sub_codelist_with_given_terms.items:
                    raise exceptions.BusinessLogicException(
                        f"""Sub codelists with these terms already exist.
                        Codelist UIDs ({[item.codelist_uid for item in sub_codelist_with_given_terms.items]})"""
                    )

            for term in codelist_input.terms:
                if (
                    parent_codelist_uid
                    and len(
                        self._repos.ct_term_aggregated_repository.find_all_aggregated_result(
                            filter_by={
                                "codelist_uid": {
                                    "v": [parent_codelist_uid],
                                    "op": "eq",
                                },
                                "term_uid": {"v": [term.term_uid], "op": "eq"},
                            }
                        ).items
                    )
                    <= 0
                ):
                    raise exceptions.BusinessLogicException(
                        f"The term identified by ({term.term_uid}) is not in use by parent codelist identified by ({parent_codelist_uid})"
                    )

                ct_codelist_name_ar = (
                    self._repos.ct_codelist_name_repository.find_by_uid(
                        codelist_uid=ct_codelist_attributes_ar.uid
                    )
                )

                self._repos.ct_codelist_attribute_repository.add_term(
                    codelist_uid=ct_codelist_attributes_ar.uid,
                    term_uid=term.term_uid,
                    author=self.user_initials,
                    order=term.order,
                )

        return CTCodelist.from_ct_codelist_ar(
            ct_codelist_name_ar, ct_codelist_attributes_ar
        )

    @db.transaction
    def create(
        self,
        codelist_input: CTCodelistCreateInput,
        start_date: datetime | None = None,
    ) -> CTCodelist:
        return self.non_transactional_create(codelist_input, start_date=start_date)

    def get_all_codelists(
        self,
        catalogue_name: str | None = None,
        library: str | None = None,
        package: str | None = None,
        is_sponsor: bool = False,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        term_filter: dict | None = None,
    ) -> GenericFilteringReturn[CTCodelistNameAndAttributes]:
        self.enforce_catalogue_library_package(catalogue_name, library, package)

        all_aggregated_codelists = (
            self._repos.ct_codelist_aggregated_repository.find_all_aggregated_result(
                catalogue_name=catalogue_name,
                library=library,
                package=package,
                is_sponsor=is_sponsor,
                total_count=total_count,
                sort_by=sort_by,
                filter_by=filter_by,
                filter_operator=filter_operator,
                page_number=page_number,
                page_size=page_size,
                term_filter=term_filter,
            )
        )

        all_aggregated_codelists.items = [
            CTCodelistNameAndAttributes.from_ct_codelist_ar(
                ct_codelist_name_ar, ct_codelist_attributes_ar
            )
            for ct_codelist_name_ar, ct_codelist_attributes_ar in all_aggregated_codelists.items
        ]

        return all_aggregated_codelists

    def get_sub_codelists_that_have_given_terms(
        self,
        codelist_uid: str,
        term_uids: list[str],
        catalogue_name: str | None = None,
        library: str | None = None,
        package: str | None = None,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[CTCodelistNameAndAttributes]:
        self.enforce_catalogue_library_package(catalogue_name, library, package)

        all_aggregated_sub_codelists = (
            self._repos.ct_codelist_aggregated_repository.find_all_aggregated_result(
                library=library,
                total_count=total_count,
                sort_by=sort_by,
                filter_by={"parent_codelist_uid": {"v": [codelist_uid], "op": "eq"}},
                filter_operator=filter_operator,
                page_number=page_number,
                page_size=page_size,
            )
        )

        uid_of_sub_codelist_with_terms = []

        for sub_codelist in all_aggregated_sub_codelists.items:
            all_aggregated_terms = (
                self._repos.ct_term_aggregated_repository.find_all_aggregated_result(
                    codelist_uid=sub_codelist[1].uid,
                    codelist_name=None,
                    library=library,
                    package=package,
                    total_count=total_count,
                    sort_by=sort_by,
                    filter_by=filter_by,
                    filter_operator=filter_operator,
                    page_number=page_number,
                    page_size=page_size,
                )
            ).items

            if set(term_uids) == {term[1].uid for term in all_aggregated_terms}:
                uid_of_sub_codelist_with_terms.append(sub_codelist[1].uid)

        all_aggregated_sub_codelists.items = [
            CTCodelistNameAndAttributes.from_ct_codelist_ar(
                ct_codelist_name_ar, ct_codelist_attributes_ar
            )
            for ct_codelist_name_ar, ct_codelist_attributes_ar in all_aggregated_sub_codelists.items
            if ct_codelist_attributes_ar.uid in uid_of_sub_codelist_with_terms
        ]

        return all_aggregated_sub_codelists

    def get_distinct_values_for_header(
        self,
        catalogue_name: str | None,
        library: str | None,
        package: str | None,
        field_name: str,
        is_sponsor: bool = False,
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        result_count: int = 10,
    ):
        self.enforce_catalogue_library_package(catalogue_name, library, package)

        header_values = (
            self._repos.ct_codelist_aggregated_repository.get_distinct_headers(
                catalogue_name=catalogue_name,
                library=library,
                package=package,
                is_sponsor=is_sponsor,
                field_name=field_name,
                search_string=search_string,
                filter_by=filter_by,
                filter_operator=filter_operator,
                result_count=result_count,
            )
        )

        return header_values

    def non_transactional_add_term(
        self, codelist_uid: str, term_uid: str, order: int
    ) -> CTCodelist:
        ct_codelist_attributes_ar = (
            self._repos.ct_codelist_attribute_repository.find_by_uid(
                codelist_uid=codelist_uid
            )
        )

        if ct_codelist_attributes_ar is not None:
            if (
                not ct_codelist_attributes_ar.library.is_editable
                and not ct_codelist_attributes_ar.ct_codelist_vo.extensible
            ):
                raise exceptions.BusinessLogicException(
                    f"Codelist identified by {codelist_uid} is not extensible"
                )

            parent_codelist_uid = (
                ct_codelist_attributes_ar.ct_codelist_vo.parent_codelist_uid
            )
            if (
                parent_codelist_uid
                and len(
                    self._repos.ct_term_aggregated_repository.find_all_aggregated_result(
                        filter_by={
                            "codelist_uid": {
                                "v": [parent_codelist_uid],
                                "op": "eq",
                            },
                            "term_uid": {"v": [term_uid], "op": "eq"},
                        }
                    ).items
                )
                <= 0
            ):
                raise exceptions.BusinessLogicException(
                    f"The term identified by ({term_uid}) is not in use by parent codelist identified by ({parent_codelist_uid})"
                )

        ct_codelist_name_ar = self._repos.ct_codelist_name_repository.find_by_uid(
            codelist_uid=codelist_uid
        )
        self._repos.ct_codelist_attribute_repository.add_term(
            codelist_uid=codelist_uid,
            term_uid=term_uid,
            author=self.user_initials,
            order=order,
        )

        return CTCodelist.from_ct_codelist_ar(
            ct_codelist_name_ar, ct_codelist_attributes_ar
        )

    @db.transaction
    def add_term(self, codelist_uid: str, term_uid: str, order: int) -> CTCodelist:
        return self.non_transactional_add_term(codelist_uid, term_uid, order)

    @db.transaction
    def remove_term(self, codelist_uid: str, term_uid: str) -> CTCodelist:
        ct_codelist_attributes_ar = (
            self._repos.ct_codelist_attribute_repository.find_by_uid(
                codelist_uid=codelist_uid
            )
        )
        if ct_codelist_attributes_ar is not None:
            if (
                not ct_codelist_attributes_ar.library.is_editable
                and not ct_codelist_attributes_ar.ct_codelist_vo.extensible
            ):
                raise exceptions.BusinessLogicException(
                    f"Codelist identified by {codelist_uid} is not extensible"
                )

            child_codelist_uids = (
                ct_codelist_attributes_ar.ct_codelist_vo.child_codelist_uids
            )
            if child_codelist_uids:
                terms = self._repos.ct_term_aggregated_repository.find_all_aggregated_result(
                    filter_by={
                        "codelist_uid": {
                            "v": child_codelist_uids,
                            "op": "eq",
                        },
                        "term_uid": {"v": [term_uid], "op": "eq"},
                    }
                ).items
                if len(terms) > 0:
                    raise exceptions.BusinessLogicException(
                        f"The term identified by ({term_uid}) is in use by child codelists"
                        f" identified by {[term[1]._ct_term_attributes_vo.codelist_uid for term in terms]}"
                    )
        ct_codelist_name_ar = self._repos.ct_codelist_name_repository.find_by_uid(
            codelist_uid=codelist_uid
        )

        self._repos.ct_codelist_attribute_repository.remove_term(
            codelist_uid=codelist_uid, term_uid=term_uid, author=self.user_initials
        )

        return CTCodelist.from_ct_codelist_ar(
            ct_codelist_name_ar, ct_codelist_attributes_ar
        )

    def enforce_catalogue_library_package(
        self,
        catalogue_name: str | None,
        library: str | None,
        package: str | None,
    ):
        if (
            catalogue_name is not None
            and not self._repos.ct_catalogue_repository.catalogue_exists(
                normalize_string(catalogue_name)
            )
        ):
            raise exceptions.BusinessLogicException(
                f"There is no catalogue identified by provided catalogue name ({catalogue_name})"
            )
        if library is not None and not self._repos.library_repository.library_exists(
            normalize_string(library)
        ):
            raise exceptions.BusinessLogicException(
                f"There is no library identified by provided library name ({library})"
            )
        if (
            package is not None
            and not self._repos.ct_package_repository.package_exists(
                normalize_string(package)
            )
        ):
            raise exceptions.BusinessLogicException(
                f"There is no package identified by provided package name ({package})"
            )
