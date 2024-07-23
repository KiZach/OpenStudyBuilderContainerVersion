from neomodel import db

from clinical_mdr_api import exceptions, models
from clinical_mdr_api.domain_repositories.models.study_selections import StudyObjective
from clinical_mdr_api.domain_repositories.models.syntax import (
    ObjectiveRoot,
    ObjectiveTemplateRoot,
)
from clinical_mdr_api.domain_repositories.study_selections.study_objective_repository import (
    SelectionHistory,
)
from clinical_mdr_api.domains.study_selections.study_selection_objective import (
    StudySelectionObjectivesAR,
    StudySelectionObjectiveVO,
)
from clinical_mdr_api.domains.syntax_instances.objective import ObjectiveAR
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.exceptions import NotFoundException
from clinical_mdr_api.models.study_selections.study_selection import (
    StudySelectionObjective,
    StudySelectionObjectiveCreateInput,
    StudySelectionObjectiveInput,
    StudySelectionObjectiveTemplateSelectInput,
)
from clinical_mdr_api.models.syntax_instances.objective import ObjectiveCreateInput
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.oauth.user import user
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    build_simple_filters,
    extract_filtering_values,
    fill_missing_values_in_base_model_from_reference_base_model,
    generic_item_filtering,
    generic_pagination,
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)
from clinical_mdr_api.services.studies.study_selection_base import StudySelectionMixin
from clinical_mdr_api.services.syntax_instances.objectives import ObjectiveService


class StudyObjectiveSelectionService(StudySelectionMixin):
    _repos: MetaRepository

    _vo_to_ar_filter_map = {
        "order": "objective_level_order",
        "start_date": "start_date",
        "user_initials": "user_initials",
    }

    def __init__(self):
        self._repos = MetaRepository()
        self.author = user().id()

    #     # def _get_endpoint_count_for_objective(self, study_uid: str, study_objective_uid: str) -> int:
    #     study_endpoints = self._repos.study_endpoint_repository.find_by_study(study_uid)
    #     assert study_endpoints is not None
    #     selection = study_endpoints.study_endpoints_selection
    #     return sum(map((lambda _: 1 if _.study_objective_uid == study_objective_uid else 0), selection))

    def _check_for_study_endpoints_and_update(
        self, study_uid: str, study_objective_uid: str
    ) -> None:
        """
        Function to check if there are any study endpoints using the study objective when the study objective is deleted
        if any study endpoint is using the study objective, then these study endpoints are set to have None as study
        objective

        :param study_uid:
        :param study_objective_uid:
        :return:
        """
        # load study endpoint aggregate
        endpoint_selection_aggregate = (
            self._repos.study_endpoint_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )
        )

        # set any study endpoint using the study objective to have No study objective if they are using it
        assert endpoint_selection_aggregate is not None
        endpoint_selection_aggregate.deleting_study_objective(study_objective_uid)

        # save study endpoints
        self._repos.study_endpoint_repository.save(
            study_selection=endpoint_selection_aggregate, author=self.author
        )

    def _transform_all_to_response_model(
        self,
        study_selection: StudySelectionObjectivesAR,
        no_brackets: bool,
        study_value_version: str | None = None,
    ) -> list[models.StudySelectionObjective]:
        result = []
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_selection.study_uid,
            study_value_version=study_value_version,
        )
        for order, selection in enumerate(
            study_selection.study_objectives_selection, start=1
        ):
            if selection.is_instance:
                result.append(
                    models.StudySelectionObjective.from_study_selection_objectives_ar_and_order(
                        study_selection_objectives_ar=study_selection,
                        order=order,
                        accepted_version=selection.accepted_version,
                        get_objective_by_uid_callback=self._transform_latest_objective_model,
                        get_objective_by_uid_version_callback=self._transform_objective_model,
                        get_ct_term_by_uid=self._find_by_uid_or_raise_not_found,
                        get_study_endpoint_count_callback=self._repos.study_endpoint_repository.quantity_of_study_endpoints_in_study_objective_uid,
                        no_brackets=no_brackets,
                        find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                        study_value_version=study_value_version,
                        terms_at_specific_datetime=terms_at_specific_datetime,
                    )
                )
            else:
                result.append(
                    models.StudySelectionObjective.from_study_selection_objective_template_ar_and_order(
                        study_selection_objective_ar=study_selection,
                        order=order,
                        accepted_version=selection.accepted_version,
                        get_objective_template_by_uid_callback=self._transform_latest_objective_template_model,
                        get_objective_template_by_uid_version_callback=self._transform_objective_template_model,
                        find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                        study_value_version=study_value_version,
                    )
                )
        return result

    @db.transaction
    def update_selection_to_latest_version(
        self, study_uid: str, study_selection_uid: str
    ):
        selection_ar, selection, order = self._get_specific_objective_selection_by_uids(
            study_uid, study_selection_uid, for_update=True
        )
        objective_uid = selection.objective_uid
        objective_ar = self._repos.objective_repository.find_by_uid(objective_uid)
        if objective_ar.item_metadata.status == LibraryItemStatus.DRAFT:
            objective_ar.approve(self.author)
            self._repos.objective_repository.save(objective_ar)
        elif objective_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException(
                "Cannot add retired objective as selection. Please reactivate."
            )
        new_selection = selection.update_version(objective_ar.item_metadata.version)
        selection_ar.update_selection(
            new_selection, objective_exist_callback=lambda x: True
        )
        self._repos.study_objective_repository.save(selection_ar, self.author)
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_uid
        )
        return models.StudySelectionObjective.from_study_selection_objectives_ar_and_order(
            study_selection_objectives_ar=selection_ar,
            order=order,
            get_objective_by_uid_callback=self._transform_latest_objective_model,
            get_objective_by_uid_version_callback=self._transform_objective_model,
            get_ct_term_by_uid=self._find_by_uid_or_raise_not_found,
            get_study_endpoint_count_callback=self._repos.study_endpoint_repository.quantity_of_study_endpoints_in_study_objective_uid,
            find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    @db.transaction
    def update_selection_accept_version(self, study_uid: str, study_selection_uid: str):
        selection: StudySelectionObjectiveVO
        selection_ar, selection, order = self._get_specific_objective_selection_by_uids(
            study_uid, study_selection_uid, for_update=True
        )
        objective_uid = selection.objective_uid
        objective_ar = self._repos.objective_repository.find_by_uid(objective_uid)
        if objective_ar.item_metadata.status == LibraryItemStatus.DRAFT:
            objective_ar.approve(self.author)
            self._repos.objective_repository.save(objective_ar)
        elif objective_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException(
                "Cannot add retired objective as selection. Please reactivate."
            )
        new_selection = selection.accept_versions()
        selection_ar.update_selection(
            new_selection, objective_exist_callback=lambda x: True
        )
        self._repos.study_objective_repository.save(selection_ar, self.author)
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_uid
        )
        return models.StudySelectionObjective.from_study_selection_objectives_ar_and_order(
            study_selection_objectives_ar=selection_ar,
            order=order,
            accepted_version=new_selection.accepted_version,
            get_objective_by_uid_callback=self._transform_latest_objective_model,
            get_objective_by_uid_version_callback=self._transform_objective_model,
            get_ct_term_by_uid=self._find_by_uid_or_raise_not_found,
            get_study_endpoint_count_callback=self._repos.study_endpoint_repository.quantity_of_study_endpoints_in_study_objective_uid,
            find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    @db.transaction
    def make_selection(
        self, study_uid: str, selection_create_input: StudySelectionObjectiveInput
    ) -> models.StudySelectionObjective:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = repos.study_objective_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )
            objective_repo = repos.objective_repository
            selected_objective: ObjectiveAR = objective_repo.find_by_uid(
                selection_create_input.objective_uid, status=LibraryItemStatus.FINAL
            )
            if selected_objective is None:
                raise exceptions.BusinessLogicException(
                    f"There is no approved objective identified by provided uid ({selection_create_input.objective_uid})"
                )

            # load the order of the Objective level CT term
            if selection_create_input.objective_level_uid is not None:
                objective_level_order = (
                    self._repos.ct_term_name_repository.term_specific_order_by_uid(
                        uid=selection_create_input.objective_level_uid
                    )
                )
            else:
                objective_level_order = None
            # create new VO to add
            new_selection = StudySelectionObjectiveVO.from_input_values(
                objective_uid=selection_create_input.objective_uid,
                objective_version=selected_objective.item_metadata.version,
                objective_level_uid=selection_create_input.objective_level_uid,
                objective_level_order=objective_level_order,
                generate_uid_callback=repos.study_objective_repository.generate_uid,
                user_initials=self.author,
            )

            # Check the state of the objective, if latest version is in draft then we approve it, if retired then we throw a error
            objective_repo = self._repos.objective_repository
            if new_selection.objective_uid is not None:
                objective_ar = objective_repo.find_by_uid(
                    new_selection.objective_uid, for_update=True
                )
                if objective_ar is None:
                    raise exceptions.BusinessLogicException(
                        f"There is no approved objective identified by provided uid ({new_selection.objective_uid})"
                    )
                # if in draft status - approve
                if objective_ar.item_metadata.status == LibraryItemStatus.DRAFT:
                    objective_ar.approve(self.author)
                    objective_repo.save(objective_ar)
                # if in retired then we return a error
                elif objective_ar.item_metadata.status == LibraryItemStatus.RETIRED:
                    raise exceptions.BusinessLogicException(
                        f"There is no approved objective identified by provided uid ({new_selection.objective_uid})"
                    )

            # add VO to aggregate
            objective_repo = repos.objective_repository
            assert selection_aggregate is not None
            selection_aggregate.add_objective_selection(
                new_selection,
                objective_repo.check_exists_final_version,
                self._repos.ct_term_name_repository.term_specific_exists_by_uid,
            )
            selection_aggregate.validate()

            # sync with DB and save the update
            repos.study_objective_repository.save(selection_aggregate, self.author)

            # Fetch the new selection which was just added
            new_selection, order = selection_aggregate.get_specific_objective_selection(
                new_selection.study_selection_uid
            )
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )
            # add the objective and return
            return models.StudySelectionObjective.from_study_selection_objectives_ar_and_order(
                study_selection_objectives_ar=selection_aggregate,
                order=order,
                get_objective_by_uid_callback=self._transform_latest_objective_model,
                get_objective_by_uid_version_callback=self._transform_objective_model,
                get_ct_term_by_uid=self._find_by_uid_or_raise_not_found,
                get_study_endpoint_count_callback=self._repos.study_endpoint_repository.quantity_of_study_endpoints_in_study_objective_uid,
                find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()

    def non_transactional_make_selection_create_objective(
        self, study_uid: str, selection_create_input: StudySelectionObjectiveCreateInput
    ) -> models.StudySelectionObjective:
        repos = self._repos
        try:
            # Load aggregate
            # check if name exists
            objective_service = ObjectiveService()
            objective_ar = objective_service.create_ar_from_input_values(
                selection_create_input.objective_data,
                study_uid=study_uid,
                include_study_endpoints=True,
            )

            objective_uid = objective_ar.uid
            if not objective_service.repository.check_exists_by_name(objective_ar.name):
                objective_service.repository.save(objective_ar)
            else:
                objective_uid = objective_service.repository.find_uid_by_name(
                    name=objective_ar.name
                )
                if objective_uid is None:
                    raise NotFoundException(
                        f"Could not find node with label ObjectiveRoot and name {objective_ar.name}"
                    )
            objective_ar = objective_service.repository.find_by_uid(
                objective_uid, for_update=True
            )
            # getting selection aggregate
            selection_aggregate = repos.study_objective_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # if in draft status - approve
            if objective_ar.item_metadata.status == LibraryItemStatus.DRAFT:
                objective_ar.approve(self.author)
                objective_service.repository.save(objective_ar)
            elif objective_ar.item_metadata.status == LibraryItemStatus.RETIRED:
                raise exceptions.BusinessLogicException(
                    f"There is no approved objective identified by provided uid ({objective_uid})"
                )

            # get order from the Objective level CT term
            if selection_create_input.objective_level_uid is not None:
                objective_level_order = (
                    self._repos.ct_term_name_repository.term_specific_order_by_uid(
                        uid=selection_create_input.objective_level_uid
                    )
                )
            else:
                objective_level_order = None

            # create new VO to add
            new_selection = StudySelectionObjectiveVO.from_input_values(
                user_initials=self.author,
                objective_uid=objective_uid,
                objective_version=objective_ar.item_metadata.version,
                objective_level_uid=selection_create_input.objective_level_uid,
                objective_level_order=objective_level_order,
                generate_uid_callback=repos.study_objective_repository.generate_uid,
            )

            # add VO to aggregate
            objective_repo = repos.objective_repository
            assert selection_aggregate is not None
            selection_aggregate.add_objective_selection(
                new_selection,
                objective_repo.check_exists_final_version,
                self._repos.ct_term_name_repository.term_specific_exists_by_uid,
            )

            # sync with DB and save the update
            repos.study_objective_repository.save(selection_aggregate, self.author)

            # Fetch the new selection which was just added
            (
                new_selection,
                order,
            ) = selection_aggregate.get_specific_objective_selection(
                new_selection.study_selection_uid
            )
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )
            # add the objective and return
            return models.StudySelectionObjective.from_study_selection_objectives_ar_and_order(
                study_selection_objectives_ar=selection_aggregate,
                order=order,
                get_objective_by_uid_callback=self._transform_latest_objective_model,
                get_objective_by_uid_version_callback=self._transform_objective_model,
                get_ct_term_by_uid=self._find_by_uid_or_raise_not_found,
                get_study_endpoint_count_callback=self._repos.study_endpoint_repository.quantity_of_study_endpoints_in_study_objective_uid,
                find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()

    @db.transaction
    def make_selection_create_objective(
        self, study_uid: str, selection_create_input: StudySelectionObjectiveCreateInput
    ) -> models.StudySelectionObjective:
        return self.non_transactional_make_selection_create_objective(
            study_uid, selection_create_input
        )

    def batch_select_objective_template(
        self,
        study_uid: str,
        selection_create_input: list[StudySelectionObjectiveTemplateSelectInput],
    ) -> list[StudySelectionObjective]:
        """
        Select multiple objective templates as a batch.

        This will only select the templates and not create instances,
        except for templates that have no parameters and objective input
        containing parameter values (coming from pre-instances).

        Args:
            study_uid (str)
            selection_create_input (StudySelectionObjectiveBatchSelectInput): [description]

        Returns:
            list[StudySelectionObjective]
        """
        repos = self._repos
        try:
            with db.transaction:
                objective_template_repo = repos.objective_template_repository
                selections = []
                for template_input in selection_create_input:
                    # Get objective template
                    objective_template = objective_template_repo.find_by_uid(
                        uid=template_input.objective_template_uid
                    )
                    if objective_template is None:
                        raise exceptions.NotFoundException(
                            f"Objective template with uid {template_input.objective_template_uid} does not exist"
                        )

                    if (
                        objective_template.template_value.parameter_names is not None
                        and len(objective_template.template_value.parameter_names) > 0
                        and (
                            template_input.parameter_terms is None
                            or len(template_input.parameter_terms) == 0
                        )
                    ):
                        # Get selection aggregate
                        selection_aggregate = (
                            repos.study_objective_repository.find_by_study(
                                study_uid=study_uid, for_update=True
                            )
                        )
                        # Create new VO to add
                        new_selection = StudySelectionObjectiveVO.from_input_values(
                            user_initials=self.author,
                            is_instance=False,
                            objective_uid=objective_template.uid,
                            objective_version=objective_template.item_metadata.version,
                            objective_level_uid=None,
                            objective_level_order=None,
                            generate_uid_callback=repos.study_objective_repository.generate_uid,
                        )

                        # Add template to selection
                        try:
                            assert selection_aggregate is not None
                            selection_aggregate.add_objective_selection(
                                new_selection,
                                objective_exist_callback=objective_template_repo.check_exists_final_version,
                                ct_term_level_exist_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                            )
                        except ValueError as value_error:
                            raise exceptions.ValidationException(value_error.args[0])

                        # Sync with DB and save the update
                        repos.study_objective_repository.save(
                            selection_aggregate, self.author
                        )

                        # Fetch the new selection which was just added
                        (
                            new_selection,
                            order,
                        ) = selection_aggregate.get_specific_objective_selection(
                            study_selection_uid=new_selection.study_selection_uid
                        )

                        # add the objective and return
                        selections.append(
                            models.StudySelectionObjective.from_study_selection_objective_template_ar_and_order(
                                study_selection_objective_ar=selection_aggregate,
                                order=order,
                                get_objective_template_by_uid_callback=self._transform_latest_objective_template_model,
                                get_objective_template_by_uid_version_callback=self._transform_objective_template_model,
                                find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                            )
                        )
                    else:
                        parameter_terms = (
                            template_input.parameter_terms
                            if template_input.parameter_terms is not None
                            else []
                        )
                        new_selection = self.non_transactional_make_selection_create_objective(
                            study_uid=study_uid,
                            selection_create_input=StudySelectionObjectiveCreateInput(
                                objective_data=ObjectiveCreateInput(
                                    objective_template_uid=template_input.objective_template_uid,
                                    parameter_terms=parameter_terms,
                                    library_name=template_input.library_name,
                                )
                            ),
                        )
                        selections.append(new_selection)
                return selections
        finally:
            repos.close()

    def make_selection_preview_objective(
        self, study_uid: str, selection_create_input: StudySelectionObjectiveCreateInput
    ) -> models.StudySelectionObjective:
        repos = self._repos
        try:
            # Load aggregate
            with db.transaction:
                # check if name exists
                objective_service = ObjectiveService()
                objective_ar = objective_service.create_ar_from_input_values(
                    selection_create_input.objective_data,
                    generate_uid_callback=(lambda: "preview"),
                    study_uid=study_uid,
                    include_study_endpoints=True,
                )
                objective_uid = objective_ar.uid
                objective_ar.approve(self.author)
                selection_aggregate = repos.study_objective_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )

                # create new VO to add
                new_selection = StudySelectionObjectiveVO.from_input_values(
                    user_initials=self.author,
                    objective_uid=objective_uid,
                    objective_version=objective_ar.item_metadata.version,
                    objective_level_uid=selection_create_input.objective_level_uid,
                    objective_level_order=None,
                    generate_uid_callback=(lambda: "preview"),
                )

                selection_aggregate.add_objective_selection(
                    new_selection,
                    (lambda _: True),
                    self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                )

                # Fetch the new selection which was just added
                (
                    new_selection,
                    order,
                ) = selection_aggregate.get_specific_objective_selection(
                    new_selection.study_selection_uid
                )
                terms_at_specific_datetime = (
                    self._extract_study_standards_effective_date(study_uid=study_uid)
                )
                # add the objective and return
                return models.StudySelectionObjective.from_study_selection_objectives_ar_and_order(
                    study_selection_objectives_ar=selection_aggregate,
                    order=order,
                    get_objective_by_uid_callback=(
                        lambda _: models.Objective.from_objective_ar(objective_ar)
                    ),
                    get_objective_by_uid_version_callback=(
                        lambda _: models.Objective.from_objective_ar(objective_ar)
                    ),
                    get_ct_term_by_uid=self._find_by_uid_or_raise_not_found,
                    get_study_endpoint_count_callback=self._repos.study_endpoint_repository.quantity_of_study_endpoints_in_study_objective_uid,
                    find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                    terms_at_specific_datetime=terms_at_specific_datetime,
                )
        finally:
            repos.close()

    @db.transaction
    def get_all_selections_for_all_studies(
        self,
        no_brackets: bool,
        project_name: str | None = None,
        project_number: str | None = None,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[models.StudySelectionObjective]:
        # Extract the study uids to use database level filtering for these
        # instead of service level filtering
        if filter_operator is None or filter_operator == FilterOperator.AND:
            study_uids = extract_filtering_values(filter_by, "study_uid")
        else:
            study_uids = None

        repos = self._repos
        objective_selection_ars = repos.study_objective_repository.find_all(
            project_name=project_name,
            project_number=project_number,
            study_uids=study_uids,
        )

        # In order for filtering to work, we need to unwind the aggregated AR object first
        # Unwind ARs
        selections = []
        for ar in objective_selection_ars:
            parsed_selections = self._transform_all_to_response_model(
                ar, no_brackets=no_brackets
            )
            for selection in parsed_selections:
                selections.append(selection)

        # Do filtering, sorting, pagination and count
        filtered_items = service_level_generic_filtering(
            items=selections,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )
        return filtered_items

    @db.transaction
    def get_distinct_values_for_header(
        self,
        field_name: str,
        study_uid: str | None = None,
        project_name: str | None = None,
        project_number: str | None = None,
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        result_count: int = 10,
        study_value_version: str | None = None,
    ):
        repos = self._repos

        if study_uid:
            objective_selection_ars = repos.study_objective_repository.find_by_study(
                study_uid, study_value_version=study_value_version
            )

            header_values = service_level_generic_header_filtering(
                items=self._transform_all_to_response_model(
                    objective_selection_ars, no_brackets=False
                ),
                field_name=field_name,
                search_string=search_string,
                filter_by=filter_by,
                filter_operator=filter_operator,
                result_count=result_count,
            )

            return header_values

        # Extract the study uids to use database level filtering for these
        # instead of service level filtering
        if filter_operator is None or filter_operator == FilterOperator.AND:
            study_uids = extract_filtering_values(filter_by, "study_uid")
        else:
            study_uids = None

        objective_selection_ars = repos.study_objective_repository.find_all(
            project_name=project_name,
            project_number=project_number,
            study_uids=study_uids,
        )

        # In order for filtering to work, we need to unwind the aggregated AR object first
        # Unwind ARs
        selections = []
        for ar in objective_selection_ars:
            parsed_selections = self._transform_all_to_response_model(
                ar, no_brackets=False
            )
            for selection in parsed_selections:
                selections.append(selection)

        # Do filtering, sorting, pagination and count
        header_values = service_level_generic_header_filtering(
            items=selections,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            result_count=result_count,
        )
        # Return values for field_name
        return header_values

    @db.transaction
    def get_all_selection(
        self,
        study_uid: str,
        no_brackets: bool,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        page_number: int = 1,
        page_size: int = 0,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> GenericFilteringReturn[models.StudySelectionObjective]:
        repos = self._repos
        try:
            objective_selection_ar = repos.study_objective_repository.find_by_study(
                study_uid, study_value_version=study_value_version
            )
            assert objective_selection_ar is not None

            simple_filters = build_simple_filters(
                self._vo_to_ar_filter_map, filter_by, None
            )
            if simple_filters:
                # Filtering only needs data that is already available in the AR
                items = list(objective_selection_ar.study_objectives_selection)
                filtered_items = generic_item_filtering(
                    items=items,
                    filter_by=simple_filters["filter_by"],
                    filter_operator=filter_operator,
                    sort_by=simple_filters["sort_by"],
                )

                # Do count
                count = len(filtered_items) if total_count else 0

                # Do pagination
                filtered_items = generic_pagination(
                    items=filtered_items,
                    page_number=page_number,
                    page_size=page_size,
                )
                # Put the sorted and filtered items back into the AR and transform them to the response model
                objective_selection_ar.study_objectives_selection = filtered_items
                filtered_items = self._transform_all_to_response_model(
                    objective_selection_ar,
                    no_brackets=no_brackets,
                    study_value_version=study_value_version,
                )
                return GenericFilteringReturn.create(filtered_items, count)

            # Fall back to full generic filtering
            selections = []
            parsed_selections = self._transform_all_to_response_model(
                objective_selection_ar,
                no_brackets=no_brackets,
                study_value_version=study_value_version,
            )
            for selection in parsed_selections:
                selections.append(selection)

            # Do filtering, sorting, pagination and count
            filtered_items = service_level_generic_filtering(
                items=selections,
                filter_by=filter_by,
                filter_operator=filter_operator,
                total_count=total_count,
                page_number=page_number,
                page_size=page_size,
            )
            return filtered_items
        finally:
            repos.close()

    def _transform_history_to_response_model(
        self, study_selection_history: list[SelectionHistory], study_uid: str
    ) -> list[models.StudySelectionObjectiveCore]:
        result = []
        for history in study_selection_history:
            result.append(
                models.StudySelectionObjectiveCore.from_study_selection_history(
                    study_selection_history=history,
                    study_uid=study_uid,
                    get_objective_by_uid_version_callback=self._transform_objective_model,
                    get_ct_term_objective_level=self._find_by_uid_or_raise_not_found,
                )
            )
        return result

    @db.transaction
    def get_all_selection_audit_trail(
        self, study_uid: str
    ) -> list[models.StudySelectionObjectiveCore]:
        repos = self._repos
        try:
            try:
                selection_history = (
                    repos.study_objective_repository.find_selection_history(study_uid)
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(value_error.args[0])

            return self._transform_history_to_response_model(
                selection_history, study_uid
            )
        finally:
            repos.close()

    @db.transaction
    def get_specific_selection_audit_trail(
        self, study_uid: str, study_selection_uid: str
    ) -> list[models.StudySelectionObjectiveCore]:
        repos = self._repos
        try:
            selection_history = repos.study_objective_repository.find_selection_history(
                study_uid, study_selection_uid
            )

            return self._transform_history_to_response_model(
                selection_history, study_uid
            )
        finally:
            repos.close()

    @db.transaction
    def get_specific_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        study_value_version: str | None = None,
    ) -> models.StudySelectionObjective:
        repos = self._repos
        (
            selection_aggregate,
            new_selection,
            order,
        ) = self._get_specific_objective_selection_by_uids(
            study_uid, study_selection_uid, study_value_version=study_value_version
        )
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_uid,
            study_value_version=study_value_version,
        )
        if new_selection.is_instance:
            return models.StudySelectionObjective.from_study_selection_objectives_ar_and_order(
                study_selection_objectives_ar=selection_aggregate,
                order=order,
                accepted_version=new_selection.accepted_version,
                get_objective_by_uid_callback=self._transform_latest_objective_model,
                get_objective_by_uid_version_callback=self._transform_objective_model,
                get_ct_term_by_uid=self._find_by_uid_or_raise_not_found,
                get_study_endpoint_count_callback=self._repos.study_endpoint_repository.quantity_of_study_endpoints_in_study_objective_uid,
                find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )

        return models.StudySelectionObjective.from_study_selection_objective_template_ar_and_order(
            study_selection_objective_ar=selection_aggregate,
            order=order,
            accepted_version=new_selection.accepted_version,
            get_objective_template_by_uid_callback=self._transform_latest_objective_template_model,
            get_objective_template_by_uid_version_callback=self._transform_objective_template_model,
            find_project_by_study_uid=repos.project_repository.find_by_study_uid,
        )

    @db.transaction
    def delete_selection(self, study_uid: str, study_selection_uid: str):
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = repos.study_objective_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # update any study endpoints using the selection
            self._check_for_study_endpoints_and_update(
                study_uid=study_uid, study_objective_uid=study_selection_uid
            )

            # remove the connection
            assert selection_aggregate is not None
            selection_aggregate.remove_objective_selection(study_selection_uid)

            # sync with DB and save the update
            repos.study_objective_repository.save(selection_aggregate, self.author)
        finally:
            repos.close()

    @db.transaction
    def set_new_order(
        self, study_uid: str, study_selection_uid: str, new_order: int
    ) -> models.StudySelectionObjective:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = repos.study_objective_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # remove the connection
            assert selection_aggregate is not None
            selection_aggregate.set_new_order_for_selection(
                study_selection_uid, new_order, self.author
            )

            # sync with DB and save the update
            repos.study_objective_repository.save(selection_aggregate, self.author)

            # Fetch the new selection which was just added
            _, order = selection_aggregate.get_specific_objective_selection(
                study_selection_uid
            )
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )
            # add the objective and return
            return models.StudySelectionObjective.from_study_selection_objectives_ar_and_order(
                study_selection_objectives_ar=selection_aggregate,
                order=order,
                get_objective_by_uid_callback=self._transform_latest_objective_model,
                get_objective_by_uid_version_callback=self._transform_objective_model,
                get_ct_term_by_uid=self._find_by_uid_or_raise_not_found,
                get_study_endpoint_count_callback=self._repos.study_endpoint_repository.quantity_of_study_endpoints_in_study_objective_uid,
                find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()

    def _patch_prepare_new_study_objective(
        self,
        request_study_objective: models.StudySelectionObjectiveInput,
        current_study_objective: StudySelectionObjectiveVO,
    ) -> StudySelectionObjectiveVO:
        # transform current to input model
        transformed_current = models.StudySelectionObjectiveInput(
            objective_uid=current_study_objective.objective_uid,
            objective_level_uid=current_study_objective.objective_level_uid,
        )

        # fill the missing from the inputs
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_study_objective,
            reference_base_model=transformed_current,
        )

        # get order from the Objective level CT term
        if request_study_objective.objective_level_uid is not None:
            objective_level_order = (
                self._repos.ct_term_name_repository.term_specific_order_by_uid(
                    uid=request_study_objective.objective_level_uid
                )
            )
        else:
            objective_level_order = None

        requested_objective = self._repos.objective_repository.find_by_uid(
            request_study_objective.objective_uid
        )

        return StudySelectionObjectiveVO.from_input_values(
            objective_uid=request_study_objective.objective_uid,
            objective_version=requested_objective.item_metadata.version,
            objective_level_order=objective_level_order,
            objective_level_uid=request_study_objective.objective_level_uid,
            study_selection_uid=current_study_objective.study_selection_uid,
            user_initials=self.author,
        )

    @db.transaction
    def patch_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        selection_update_input: models.StudySelectionObjectiveInput,
    ) -> models.StudySelectionObjective:
        def load_aggregate():
            selection_aggregate = repos.study_objective_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            assert selection_aggregate is not None

            return selection_aggregate

        repos = self._repos
        try:
            selection_aggregate = load_aggregate()

            template_selection = next(
                (
                    selection
                    for selection in selection_aggregate.study_objectives_selection
                    if not selection.is_instance
                    and selection.study_selection_uid == study_selection_uid
                ),
                None,
            )

            # Load the current VO for updates
            (
                current_vo,
                order,
            ) = selection_aggregate.get_specific_objective_selection(
                study_selection_uid=study_selection_uid
            )

            # merge current with updates
            updated_selection = self._patch_prepare_new_study_objective(
                request_study_objective=selection_update_input,
                current_study_objective=current_vo,
            )

            # if there is a new objective we have to check the state
            objective_repo = self._repos.objective_repository
            if (
                selection_update_input.objective_uid
                and selection_update_input.objective_uid != current_vo.objective_uid
            ):
                objective_ar = objective_repo.find_by_uid(
                    updated_selection.objective_uid, for_update=True
                )
                # if in draft status - approve
                if objective_ar.item_metadata.status == LibraryItemStatus.DRAFT:
                    objective_ar.approve(self.author)
                    objective_repo.save(objective_ar)
                    updated_selection = self._patch_prepare_new_study_objective(
                        request_study_objective=selection_update_input,
                        current_study_objective=current_vo,
                    )
                # if in retired then we return a error
                elif objective_ar.item_metadata.status == LibraryItemStatus.RETIRED:
                    raise exceptions.BusinessLogicException(
                        f"There is no approved objective identified by provided uid ({updated_selection.objective_uid})"
                    )

            # let the aggregate update the value object
            selection_aggregate.update_selection(
                updated_study_objective_selection=updated_selection,
                objective_exist_callback=objective_repo.check_exists_final_version,
                ct_term_level_exist_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
            )
            selection_aggregate.validate()

            # sync with DB and save the update
            repos.study_objective_repository.save(selection_aggregate, self.author)

            if template_selection:
                study_objectives = StudyObjective.nodes.has(
                    study_value=True, has_before=False
                )
                study_objective = next(
                    (so for so in study_objectives if so.uid == study_selection_uid),
                    None,
                )
                objective_template_root = ObjectiveTemplateRoot.nodes.get_or_none(
                    uid=template_selection.objective_uid
                )
                objective_template_value = (
                    objective_template_root.has_latest_value.get()
                )
                study_objective.has_selected_objective_template.disconnect(
                    objective_template_value
                )

                objective_root = ObjectiveRoot.nodes.get_or_none(
                    uid=selection_update_input.objective_uid
                )
                objective_value = objective_root.has_latest_value.get()
                study_objective.has_selected_objective.reconnect(
                    old_node=objective_value, new_node=objective_value
                )

                selection_aggregate = load_aggregate()

            # Fetch the new selection which was just updated
            _, order = selection_aggregate.get_specific_objective_selection(
                study_selection_uid
            )
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )
            # add the objective and return
            return models.StudySelectionObjective.from_study_selection_objectives_ar_and_order(
                study_selection_objectives_ar=selection_aggregate,
                order=order,
                get_objective_by_uid_callback=self._transform_latest_objective_model,
                get_objective_by_uid_version_callback=self._transform_objective_model,
                get_ct_term_by_uid=self._find_by_uid_or_raise_not_found,
                get_study_endpoint_count_callback=self._repos.study_endpoint_repository.quantity_of_study_endpoints_in_study_objective_uid,
                find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()
