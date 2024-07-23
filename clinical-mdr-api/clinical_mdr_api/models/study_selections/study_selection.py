import re
from datetime import datetime
from typing import Callable, Iterable, Self

from pydantic import Field, root_validator

from clinical_mdr_api.domain_repositories.study_selections.study_activity_instance_repository import (
    SelectionHistory as StudyActivityInstanceSelectionHistory,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_repository import (
    SelectionHistory as StudyActivitySelectionHistory,
)
from clinical_mdr_api.domain_repositories.study_selections.study_arm_repository import (
    SelectionHistoryArm,
)
from clinical_mdr_api.domain_repositories.study_selections.study_branch_arm_repository import (
    SelectionHistoryBranchArm,
)
from clinical_mdr_api.domain_repositories.study_selections.study_cohort_repository import (
    SelectionHistoryCohort,
)
from clinical_mdr_api.domain_repositories.study_selections.study_compound_dosing_repository import (
    SelectionHistory as StudyCompoundDosingSelectionHistory,
)
from clinical_mdr_api.domain_repositories.study_selections.study_compound_repository import (
    StudyCompoundSelectionHistory,
)
from clinical_mdr_api.domain_repositories.study_selections.study_criteria_repository import (
    SelectionHistory as StudyCriteriaSelectionHistory,
)
from clinical_mdr_api.domain_repositories.study_selections.study_element_repository import (
    SelectionHistoryElement,
)
from clinical_mdr_api.domain_repositories.study_selections.study_objective_repository import (
    SelectionHistory as StudyObjectiveSelectionHistory,
)
from clinical_mdr_api.domains.concepts.simple_concepts.numeric_value_with_unit import (
    NumericValueWithUnitAR,
)
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.domains.study_selections.study_activity_instruction import (
    StudyActivityInstructionVO,
)
from clinical_mdr_api.domains.study_selections.study_activity_schedule import (
    StudyActivityScheduleVO,
)
from clinical_mdr_api.domains.study_selections.study_compound_dosing import (
    StudyCompoundDosingVO,
)
from clinical_mdr_api.domains.study_selections.study_design_cell import (
    StudyDesignCellVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity import (
    StudySelectionActivityVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity_group import (
    StudySelectionActivityGroupVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity_instance import (
    StudyActivityInstanceState,
    StudySelectionActivityInstanceVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity_subgroup import (
    StudySelectionActivitySubGroupVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_arm import (
    StudySelectionArmVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_branch_arm import (
    StudySelectionBranchArmVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_cohort import (
    StudySelectionCohortVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_compound import (
    StudySelectionCompoundVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_criteria import (
    StudySelectionCriteriaAR,
    StudySelectionCriteriaVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_element import (
    StudySelectionElementVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_endpoint import (
    EndpointUnitItem,
    EndpointUnits,
    StudyEndpointSelectionHistory,
    StudySelectionEndpointsAR,
    StudySelectionEndpointVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_objective import (
    StudySelectionObjectivesAR,
)
from clinical_mdr_api.domains.study_selections.study_soa_group_selection import (
    StudySoAGroupVO,
)
from clinical_mdr_api.models.concepts.activities.activity import (
    Activity,
    ActivityForStudyActivity,
)
from clinical_mdr_api.models.concepts.activities.activity_instance import (
    ActivityInstance,
)
from clinical_mdr_api.models.concepts.compound import Compound
from clinical_mdr_api.models.concepts.compound_alias import CompoundAlias
from clinical_mdr_api.models.concepts.concept import SimpleNumericValueWithUnit
from clinical_mdr_api.models.controlled_terminologies.ct_term import SimpleTermModel
from clinical_mdr_api.models.controlled_terminologies.ct_term_name import CTTermName
from clinical_mdr_api.models.error import BatchErrorResponse
from clinical_mdr_api.models.study_selections.duration import DurationJsonModel
from clinical_mdr_api.models.syntax_instances.activity_instruction import (
    ActivityInstructionCreateInput,
)
from clinical_mdr_api.models.syntax_instances.criteria import (
    Criteria,
    CriteriaCreateInput,
)
from clinical_mdr_api.models.syntax_instances.endpoint import (
    Endpoint,
    EndpointCreateInput,
)
from clinical_mdr_api.models.syntax_instances.objective import (
    Objective,
    ObjectiveCreateInput,
)
from clinical_mdr_api.models.syntax_instances.timeframe import Timeframe
from clinical_mdr_api.models.syntax_templates.criteria_template import CriteriaTemplate
from clinical_mdr_api.models.syntax_templates.endpoint_template import EndpointTemplate
from clinical_mdr_api.models.syntax_templates.objective_template import (
    ObjectiveTemplate,
)
from clinical_mdr_api.models.syntax_templates.template_parameter_multi_select_input import (
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.models.utils import BaseModel, get_latest_on_datetime_str

STUDY_UID_DESC = "The uid of the study"
STUDY_ACTIVITY_UID_DESC = "uid for the study activity"
STUDY_ACTIVITY_INSTANCE_UID_DESC = "uid for the study activity instance"
STUDY_ARM_UID_DESC = "the uid of the related study arm"
STUDY_EPOCH_UID_DESC = "the uid of the related study epoch"
STUDY_ELEMENT_UID_DESC = "the uid of the related study element"
STUDY_BRANCH_ARM_UID_DESC = "the uid of the related study branch arm"
ARM_UID_DESC = "uid for the study arm"
ELEMENT_UID_DESC = "uid for the study element"
ACCEPTED_VERSION_DESC = "Accepted Version"
TRANSITION_RULE_DESC = "transition rule for the cell"
ORDER_DESC = "The ordering of the selection"
OBJECTIVE_LEVEL_DESC = "level defining the objective"
START_DATE_DESC = (
    "The most recent point in time when the study selection was edited. "
    "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone."
)
USER_INITIALS_DESC = "User initials for the version"

AFTER_DATE_QUALIFIER = "has_after.date"
AFTER_USER_QUALIFIER = "has_after.user_initials"

STUDY_UID_FIELD = Field(
    ...,
    title="study_uid",
    description=STUDY_UID_DESC,
    source="has_after.audit_trail.uid",
)
STUDY_OBJECTIVE_UID_FIELD = Field(
    None,
    title="study_objective_uid",
    description="uid for a study objective to connect with",
)
END_DATE_FIELD = Field(
    None, title="end_date", description="End date for the version", nullable=True
)
STATUS_FIELD = Field(None, title="status", description="Change status", nullable=True)
RESPONSE_CODE_FIELD = Field(
    ...,
    title="response_code",
    description="The HTTP response code related to input operation",
)
METHOD_FIELD = Field(
    ..., title="method", description="HTTP method corresponding to operation type"
)
CHANGE_TYPE_FIELD = Field(
    None,
    title="change_type",
    description="Type of last change for the version",
    nullable=True,
)
SHOW_ACTIVITY_SUBGROUP_IN_PROTOCOL_FLOWCHART_FIELD = Field(
    None,
    title="show_activity_subgroup_in_protocol_flowchart",
    description="show activity subgroup in protocol flow chart",
)
SHOW_ACTIVITY_GROUP_IN_PROTOCOL_FLOWCHART_FIELD = Field(
    None,
    title="show_activity_group_in_protocol_flowchart",
    description="show activity group in protocol flow chart",
)
SHOW_SOA_GROUP_IN_PROTOCOL_FLOWCHART_FIELD = Field(
    False,
    title="show_soa_group_in_protocol_flowchart",
    description="show soa group in protocol flow chart",
)
SHOW_ACTIVITY_INSTANCE_IN_PROTOCOL_FLOWCHART_FIELD = Field(
    False,
    title="show_activity_instance_in_protocol_flowchart",
    description="show activity instance in operational flow chart",
)


class StudySelection(BaseModel):
    study_uid: str | None = Field(
        ...,
        title="study_uid",
        description=STUDY_UID_DESC,
    )

    study_version: str | None = Field(
        None,
        title="study version or date information",
        description="Study version number, if specified, otherwise None.",
    )

    order: int = Field(
        ...,
        title="order",
        description=ORDER_DESC,
    )

    project_number: str | None = Field(
        None,
        title="project_number",
        description="Number property of the project that the study belongs to",
    )

    project_name: str | None = Field(
        None,
        title="project_name",
        description="Name property of the project that the study belongs to",
    )

    @classmethod
    def remove_brackets_from_name_property(cls, object_to_clear):
        """
        Method removes brackets that surround template parameter used in the StudySelection object
        :param object_to_clear:
        :return:
        """

        # Check that the object has "parameter_terms".
        # Syntax instances do, but syntax templates do not.
        # We can encounter both types here.
        if hasattr(object_to_clear, "parameter_terms"):
            used_template_parameters = []
            for parameter_term in object_to_clear.parameter_terms:
                for term in parameter_term.terms:
                    used_template_parameters.append(term.name)
            for template_parameter in used_template_parameters:
                object_to_clear.name = re.sub(
                    rf"\[?{re.escape(template_parameter)}\]?",
                    template_parameter,
                    object_to_clear.name,
                )


# Study objectives


class StudySelectionObjectiveCore(StudySelection):
    study_objective_uid: str | None = Field(
        ...,
        title="study_objective_uid",
        description="uid for the study objective",
    )

    objective_level: CTTermName | None = Field(
        None,
        title="objective_level",
        description=OBJECTIVE_LEVEL_DESC,
        nullable=True,
    )

    objective: Objective | None = Field(
        None,
        title="objective",
        description="the objective selected for the study",
        nullable=True,
    )

    objective_template: ObjectiveTemplate | None = Field(
        None,
        title="objective_template",
        description="the objective template selected for the study",
        nullable=True,
    )
    start_date: datetime | None = Field(
        ...,
        title="start_date",
        description=START_DATE_DESC,
    )

    user_initials: str | None = Field(
        None,
        title="user_initials",
        description=USER_INITIALS_DESC,
        nullable=True,
    )

    end_date: datetime | None = END_DATE_FIELD

    status: str | None = STATUS_FIELD

    change_type: str | None = CHANGE_TYPE_FIELD

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: StudyObjectiveSelectionHistory,
        study_uid: str,
        get_ct_term_objective_level: Callable[[str], CTTermName],
        get_objective_by_uid_version_callback: Callable[[str], Objective],
    ) -> Self:
        if study_selection_history.objective_level_uid:
            objective_level = get_ct_term_objective_level(
                study_selection_history.objective_level_uid,
                codelist_name="Objective Level",
            )
        else:
            objective_level = None

        return cls(
            study_objective_uid=study_selection_history.study_selection_uid,
            order=study_selection_history.order,
            study_uid=study_uid,
            objective_level=objective_level,
            start_date=study_selection_history.start_date,
            objective=get_objective_by_uid_version_callback(
                study_selection_history.objective_uid,
                study_selection_history.objective_version,
            ),
            end_date=study_selection_history.end_date,
            status=study_selection_history.status,
            change_type=study_selection_history.change_type,
            user_initials=study_selection_history.user_initials,
        )


class StudySelectionObjective(StudySelectionObjectiveCore):
    endpoint_count: int | None = Field(
        None,
        title="endpoint_count",
        description="Number of study endpoints related to given study objective.",
        nullable=True,
    )

    latest_objective: Objective | None = Field(
        None,
        title="latest_objective",
        description="Latest version of objective selected for study.",
        nullable=True,
    )
    accepted_version: bool | None = Field(
        None,
        title=ACCEPTED_VERSION_DESC,
        description="Denotes if user accepted obsolete objective versions",
        nullable=True,
    )

    @classmethod
    def from_study_selection_objective_template_ar_and_order(
        cls,
        study_selection_objective_ar: StudySelectionObjectivesAR,
        order: int,
        get_objective_template_by_uid_callback: Callable[[str], ObjectiveTemplate],
        get_objective_template_by_uid_version_callback: Callable[
            [str], ObjectiveTemplate
        ],
        find_project_by_study_uid: Callable,
        accepted_version: bool = False,
        study_value_version: str | None = None,
    ) -> "StudySelectionObjective":
        study_uid = study_selection_objective_ar.study_uid

        project = find_project_by_study_uid(study_uid)
        assert project is not None

        single_study_selection = (
            study_selection_objective_ar.study_objectives_selection[order - 1]
        )
        study_objective_uid = single_study_selection.study_selection_uid
        objective_template_uid = single_study_selection.objective_uid
        #
        assert objective_template_uid is not None
        latest_objective_template = get_objective_template_by_uid_callback(
            objective_template_uid
        )
        if (
            latest_objective_template
            and latest_objective_template.version
            == single_study_selection.objective_version
        ):
            selected_objective_template = latest_objective_template
            latest_objective_template = None
        else:
            selected_objective_template = (
                get_objective_template_by_uid_version_callback(
                    objective_template_uid, single_study_selection.objective_version
                )
            )
        return StudySelectionObjective(
            study_objective_uid=study_objective_uid,
            order=order,
            accepted_version=accepted_version,
            study_uid=study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            start_date=single_study_selection.start_date,
            objective_template=selected_objective_template,
            user_initials=single_study_selection.user_initials,
            project_name=project.name,
            project_number=project.project_number,
        )

    @classmethod
    def from_study_selection_objectives_ar_and_order(
        cls,
        study_selection_objectives_ar: StudySelectionObjectivesAR,
        order: int,
        get_objective_by_uid_callback: Callable[[str], Objective],
        get_objective_by_uid_version_callback: Callable[[str], Objective],
        get_ct_term_by_uid: Callable[[str], CTTermName],
        get_study_endpoint_count_callback: Callable[[str], int],
        find_project_by_study_uid: Callable,
        terms_at_specific_datetime: datetime | None,
        no_brackets: bool = False,
        study_value_version: str | None = None,
        accepted_version: bool = False,
    ) -> Self:
        study_objective_selection = (
            study_selection_objectives_ar.study_objectives_selection
        )
        study_uid = study_selection_objectives_ar.study_uid
        single_study_selection = study_objective_selection[order - 1]
        study_objective_uid = single_study_selection.study_selection_uid
        objective_uid = single_study_selection.objective_uid
        project = find_project_by_study_uid(study_uid)
        assert project is not None

        endpoint_count = get_study_endpoint_count_callback(
            study_selection_objectives_ar.study_uid,
            single_study_selection.study_selection_uid,
            study_value_version,
        )

        if single_study_selection.objective_level_uid:
            objective_level = get_ct_term_by_uid(
                single_study_selection.objective_level_uid,
                codelist_name="Objective Level",
                at_specific_date=terms_at_specific_datetime,
            )
        else:
            objective_level = None

        latest_objective = None
        selected_objective = None
        if objective_uid:
            latest_objective = get_objective_by_uid_callback(objective_uid)
            if (
                latest_objective
                and latest_objective.version == single_study_selection.objective_version
            ):
                selected_objective = latest_objective
                latest_objective = None
            else:
                selected_objective = get_objective_by_uid_version_callback(
                    objective_uid, single_study_selection.objective_version
                )
            if no_brackets:
                cls.remove_brackets_from_name_property(selected_objective)
                if latest_objective is not None:
                    cls.remove_brackets_from_name_property(latest_objective)

        return cls(
            study_objective_uid=study_objective_uid,
            order=order,
            accepted_version=accepted_version,
            study_uid=study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            objective_level=objective_level,
            start_date=single_study_selection.start_date,
            latest_objective=latest_objective,
            objective=selected_objective,
            endpoint_count=endpoint_count,
            user_initials=single_study_selection.user_initials,
            project_name=project.name,
            project_number=project.project_number,
        )


class StudySelectionObjectiveCreateInput(BaseModel):
    objective_level_uid: str | None = Field(
        None,
        title="objective_level",
        description=OBJECTIVE_LEVEL_DESC,
    )
    objective_data: ObjectiveCreateInput = Field(
        ...,
        title="objective_data",
        description="Objective data to create new objective",
    )


class StudySelectionObjectiveInput(BaseModel):
    objective_uid: str = Field(
        None,
        title="objective_uid",
        description="Uid of the selected objective",
    )

    objective_level_uid: str | None = Field(
        None,
        title="objective_level",
        description=OBJECTIVE_LEVEL_DESC,
    )


class StudySelectionObjectiveTemplateSelectInput(BaseModel):
    objective_template_uid: str = Field(
        ...,
        title="objective_template_uid",
        description="The unique id of the objective template that is to be selected.",
    )
    parameter_terms: list[TemplateParameterMultiSelectInput] = Field(
        [],
        title="parameter_terms",
        description="An ordered list of selected parameter terms that are used to replace the parameters of the objective template.",
    )
    library_name: str = Field(
        None,
        title="library_name",
        description="If specified: The name of the library to which the objective will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* objective can help. And \n"
        "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true. \n\n"
        "If not specified: The library of the objective template will be used.",
    )


class StudySelectionObjectiveNewOrder(BaseModel):
    new_order: int = Field(
        ...,
        title="new_order",
        description="Uid of the selected objective",
    )


# Study endpoints


class EndpointUnitsInput(BaseModel):
    units: list[str] | None = Field(
        ...,
        title="units",
        description="list of uids of the endpoint units selected for the study endpoint",
    )

    separator: str | None = Field(
        None,
        title="separator",
        description="separator if more than one endpoint units selected for the study endpoint",
    )


class StudySelectionEndpoint(StudySelection):
    study_endpoint_uid: str | None = Field(
        ...,
        title="study_endpoint_uid",
        description="uid for the study endpoint",
    )

    study_objective: StudySelectionObjective | None = Field(
        None,
        title="study_objective_uid",
        description="uid for the study objective which the study endpoints connects to",
        nullable=True,
    )

    endpoint_level: CTTermName | None = Field(
        None,
        title="endpoint_level",
        description="level defining the endpoint",
        nullable=True,
    )

    endpoint_sublevel: CTTermName | None = Field(
        None,
        title="endpoint_sublevel",
        description="sub level defining the endpoint",
        nullable=True,
    )
    endpoint_units: EndpointUnits | None = Field(
        None,
        title="endpoint_units",
        description="the endpoint units selected for the study endpoint",
        nullable=True,
    )

    endpoint: Endpoint | None = Field(
        None,
        title="endpoint",
        description="the endpoint selected for the study",
        nullable=True,
    )

    timeframe: Timeframe | None = Field(
        None,
        title="timeframe",
        description="the timeframe selected for the study",
        nullable=True,
    )

    latest_endpoint: Endpoint | None = Field(
        None,
        title="latest_endpoint",
        description="Latest version of the endpoint selected for the study (if available else none)",
        nullable=True,
    )

    latest_timeframe: Timeframe | None = Field(
        None,
        title="latest_timeframe",
        description="Latest version of the timeframe selected for the study (if available else none)",
        nullable=True,
    )
    endpoint_template: EndpointTemplate | None = Field(
        None,
        title="endpoint_template",
        description="the endpoint template selected for the study",
        nullable=True,
    )

    start_date: datetime | None = Field(
        ...,
        title="start_date",
        description=START_DATE_DESC,
    )

    user_initials: str | None = Field(
        None,
        title="user_initials",
        description=USER_INITIALS_DESC,
        nullable=True,
    )

    end_date: datetime | None = END_DATE_FIELD

    status: str | None = STATUS_FIELD

    change_type: str | None = CHANGE_TYPE_FIELD
    accepted_version: bool | None = Field(
        None,
        title=ACCEPTED_VERSION_DESC,
        description="Denotes if user accepted obsolete endpoint versions",
        nullable=True,
    )

    @classmethod
    def from_study_selection_endpoint_template_ar_and_order(
        cls,
        study_selection_endpoint_ar: StudySelectionEndpointsAR,
        order: int,
        get_endpoint_template_by_uid_callback: Callable[[str], EndpointTemplate],
        get_endpoint_template_by_uid_version_callback: Callable[
            [str], EndpointTemplate
        ],
        get_study_objective_by_uid: Callable[[str], StudySelectionObjective],
        find_project_by_study_uid: Callable,
        accepted_version: bool = False,
    ) -> "StudySelectionEndpoint":
        study_uid = study_selection_endpoint_ar.study_uid

        project = find_project_by_study_uid(study_uid)
        assert project is not None

        single_study_selection = study_selection_endpoint_ar.study_endpoints_selection[
            order - 1
        ]
        study_endpoint_uid = single_study_selection.study_selection_uid
        endpoint_template_uid = single_study_selection.endpoint_uid
        #
        assert endpoint_template_uid is not None
        latest_endpoint_template = get_endpoint_template_by_uid_callback(
            endpoint_template_uid
        )
        if (
            latest_endpoint_template
            and latest_endpoint_template.version
            == single_study_selection.endpoint_version
        ):
            selected_endpoint_template = latest_endpoint_template
            latest_endpoint_template = None
        else:
            selected_endpoint_template = get_endpoint_template_by_uid_version_callback(
                endpoint_template_uid, single_study_selection.endpoint_version
            )

        if single_study_selection.study_objective_uid is None:
            study_obj_model = None
        else:
            study_obj_model = get_study_objective_by_uid(
                study_uid, single_study_selection.study_objective_uid
            )

        return cls(
            study_endpoint_uid=study_endpoint_uid,
            order=order,
            accepted_version=accepted_version,
            study_uid=study_uid,
            study_objective=study_obj_model,
            start_date=single_study_selection.start_date,
            endpoint_template=selected_endpoint_template,
            user_initials=single_study_selection.user_initials,
            project_name=project.name,
            project_number=project.project_number,
        )

    @classmethod
    def from_study_selection_endpoint(
        cls,
        study_selection: StudySelectionEndpointVO,
        study_uid: str,
        order: int,
        get_endpoint_by_uid_and_version: Callable[[str], Endpoint],
        get_latest_endpoint_by_uid: Callable[[str], Endpoint],
        get_timeframe_by_uid_and_version: Callable[[str], Timeframe],
        get_latest_timeframe: Callable[[str], Timeframe],
        get_ct_term_by_uid: Callable[[str], CTTermName],
        get_study_objective_by_uid: Callable[[str], StudySelectionObjective],
        find_project_by_study_uid: Callable,
        terms_at_specific_datetime: datetime | None,
        accepted_version: bool = False,
        no_brackets: bool = False,
        study_value_version: str | None = None,
    ) -> Self:
        project = find_project_by_study_uid(study_uid)
        assert project is not None

        if study_selection.endpoint_uid is None:
            end_model = None
            latest_end_model = None
        else:
            end_model = get_endpoint_by_uid_and_version(
                study_selection.endpoint_uid, study_selection.endpoint_version
            )
            latest_end_model = get_latest_endpoint_by_uid(study_selection.endpoint_uid)
            if end_model.version == latest_end_model.version:
                latest_end_model = None
            if no_brackets:
                cls.remove_brackets_from_name_property(object_to_clear=end_model)
                if latest_end_model is not None:
                    cls.remove_brackets_from_name_property(
                        object_to_clear=latest_end_model
                    )
        if study_selection.timeframe_uid is None:
            time_model = None
            latest_time_model = None
        else:
            time_model = get_timeframe_by_uid_and_version(
                study_selection.timeframe_uid, study_selection.timeframe_version
            )
            latest_time_model = get_latest_timeframe(study_selection.timeframe_uid)
            if time_model.version == latest_time_model.version:
                latest_time_model = None
            if no_brackets:
                cls.remove_brackets_from_name_property(object_to_clear=time_model)
                if latest_time_model is not None:
                    cls.remove_brackets_from_name_property(
                        object_to_clear=latest_time_model
                    )
        if study_selection.study_objective_uid is None:
            study_obj_model = None
        else:
            study_obj_model = get_study_objective_by_uid(
                study_uid,
                study_selection.study_objective_uid,
                no_brackets=no_brackets,
                study_value_version=study_value_version,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
            if no_brackets:
                cls.remove_brackets_from_name_property(
                    object_to_clear=study_obj_model.objective
                )
        if study_selection.endpoint_level_uid:
            endpoint_level = get_ct_term_by_uid(
                study_selection.endpoint_level_uid,
                codelist_name="Endpoint Level",
                at_specific_date=terms_at_specific_datetime,
            )
        else:
            endpoint_level = None
        if study_selection.endpoint_sublevel_uid:
            endpoint_sublevel = get_ct_term_by_uid(
                study_selection.endpoint_sublevel_uid,
                codelist_name="Endpoint Sub Level",
                at_specific_date=terms_at_specific_datetime,
            )
        else:
            endpoint_sublevel = None

        model = (
            {"endpoint": end_model}
            if study_selection.is_instance
            else {"endpoint_template": end_model}
        )

        return StudySelectionEndpoint(
            study_objective=study_obj_model,
            study_uid=study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            order=order,
            accepted_version=accepted_version,
            study_endpoint_uid=study_selection.study_selection_uid,
            endpoint_units=EndpointUnits(
                units=tuple(
                    EndpointUnitItem(**u) for u in study_selection.endpoint_units
                ),
                separator=study_selection.unit_separator,
            ),
            endpoint_level=endpoint_level,
            endpoint_sublevel=endpoint_sublevel,
            start_date=study_selection.start_date,
            latest_endpoint=latest_end_model,
            timeframe=time_model,
            latest_timeframe=latest_time_model,
            user_initials=study_selection.user_initials,
            project_name=project.name,
            project_number=project.project_number,
            **model,
        )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: StudyEndpointSelectionHistory,
        study_uid: str,
        get_endpoint_by_uid: Callable[[str], Endpoint],
        get_timeframe_by_uid: Callable[[str], Timeframe],
        get_ct_term_by_uid: Callable[[str], CTTermName],
        get_study_objective_by_uid: Callable[[str], StudySelectionObjective],
    ) -> Self:
        if study_selection_history.endpoint_uid:
            endpoint = get_endpoint_by_uid(
                study_selection_history.endpoint_uid,
                study_selection_history.endpoint_version,
            )
        else:
            endpoint = None
        if study_selection_history.timeframe_uid:
            timeframe = get_timeframe_by_uid(
                study_selection_history.timeframe_uid,
                study_selection_history.timeframe_version,
            )
        else:
            timeframe = None
        if study_selection_history.study_objective_uid:
            study_objective = get_study_objective_by_uid(
                study_uid,
                study_selection_history.study_objective_uid,
                terms_at_specific_datetime=None,
            )
        else:
            study_objective = None
        if study_selection_history.endpoint_level:
            endpoint_level = get_ct_term_by_uid(
                study_selection_history.endpoint_level, codelist_name="Endpoint Level"
            )
        else:
            endpoint_level = None
        if study_selection_history.endpoint_sublevel:
            endpoint_sublevel = get_ct_term_by_uid(
                study_selection_history.endpoint_sublevel,
                codelist_name="Endpoint Sub Level",
            )
        else:
            endpoint_sublevel = None

        units = None
        if study_selection_history.endpoint_units:
            units = tuple(
                EndpointUnitItem(**u)
                for u in study_selection_history.endpoint_units
                if u.get("uid")
            )
        if units:
            units = EndpointUnits(
                units=units,
                separator=study_selection_history.unit_separator,
            )
        else:
            units = None

        return cls(
            study_uid=study_uid,
            study_endpoint_uid=study_selection_history.study_selection_uid,
            study_objective=study_objective,
            endpoint_level=endpoint_level,
            endpoint_sublevel=endpoint_sublevel,
            endpoint_units=units,
            endpoint=endpoint,
            timeframe=timeframe,
            start_date=study_selection_history.start_date,
            user_initials=study_selection_history.user_initials,
            end_date=study_selection_history.end_date,
            status=study_selection_history.status,
            change_type=study_selection_history.change_type,
            order=study_selection_history.order,
        )


class StudySelectionEndpointCreateInput(BaseModel):
    study_objective_uid: str | None = STUDY_OBJECTIVE_UID_FIELD
    endpoint_level_uid: str | None = Field(
        None,
        title="endpoint level",
        description="level defining the endpoint",
    )
    endpoint_sublevel_uid: str | None = Field(
        None,
        title="endpoint sub level",
        description="sub level defining the endpoint",
    )
    endpoint_data: EndpointCreateInput = Field(
        ..., title="endpoint_data", description="endpoint data to create new endpoint"
    )
    endpoint_units: EndpointUnitsInput | None = Field(
        None,
        title="endpoint_units",
        description="endpoint units used in the study endpoint",
    )
    timeframe_uid: str | None = Field(
        None,
        title="timeframe_uid",
        description="uid for a timeframe",
    )


class StudySelectionEndpointInput(BaseModel):
    study_objective_uid: str | None = STUDY_OBJECTIVE_UID_FIELD

    endpoint_uid: str | None = Field(
        None,
        title="endpoint_uid",
        description="uid for a library endpoint to connect with",
    )

    endpoint_level_uid: str | None = Field(
        None,
        title="endpoint level",
        description="level for the endpoint",
    )
    endpoint_sublevel_uid: str | None = Field(
        None,
        title="endpoint sub level",
        description="sub level for the endpoint",
    )
    timeframe_uid: str | None = Field(
        None,
        title="timeframe_uid",
        description="uid for a timeframe",
    )

    endpoint_units: EndpointUnitsInput | None = Field(
        None,
        title="endpoint_units",
        description="hold the units used in the study endpoint",
    )


class StudySelectionEndpointTemplateSelectInput(BaseModel):
    endpoint_template_uid: str = Field(
        ...,
        title="endpoint_template_uid",
        description="The unique id of the endpoint template that is to be selected.",
    )
    study_objective_uid: str | None = STUDY_OBJECTIVE_UID_FIELD
    parameter_terms: list[TemplateParameterMultiSelectInput] = Field(
        [],
        title="parameter_terms",
        description="An ordered list of selected parameter terms that are used to replace the parameters of the endpoint template.",
    )
    library_name: str = Field(
        None,
        title="library_name",
        description="If specified: The name of the library to which the endpoint will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
        "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true. \n\n"
        "If not specified: The library of the endpoint template will be used.",
    )


class StudySelectionEndpointNewOrder(BaseModel):
    new_order: int = Field(
        ...,
        title="new_order",
        description="Uid of the selected endpoint",
    )


# Study compounds


class StudySelectionCompound(StudySelection):
    @classmethod
    def from_study_compound_ar(
        cls,
        study_uid: str,
        selection: StudySelectionCompoundVO,
        order: int,
        compound_model: Compound | None,
        compound_alias_model: CompoundAlias | None,
        find_simple_term_model_name_by_term_uid: Callable,
        find_project_by_study_uid: Callable,
        find_unit_by_uid: Callable[[str], UnitDefinitionAR | None],
        find_numeric_value_by_uid: Callable[[str], NumericValueWithUnitAR | None],
        terms_at_specific_datetime: datetime | None,
        study_value_version: str | None = None,
    ):
        project = find_project_by_study_uid(study_uid)
        return cls(
            order=order,
            study_uid=study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            study_compound_uid=selection.study_selection_uid,
            compound=compound_model,
            compound_alias=compound_alias_model,
            type_of_treatment=find_simple_term_model_name_by_term_uid(
                selection.type_of_treatment_uid,
                at_specific_date=terms_at_specific_datetime,
            ),
            route_of_administration=find_simple_term_model_name_by_term_uid(
                selection.route_of_administration_uid,
                at_specific_date=terms_at_specific_datetime,
            ),
            strength_value=SimpleNumericValueWithUnit.from_concept_uid(
                uid=selection.strength_value_uid,
                find_unit_by_uid=find_unit_by_uid,
                find_numeric_value_by_uid=find_numeric_value_by_uid,
            ),
            dosage_form=find_simple_term_model_name_by_term_uid(
                selection.dosage_form_uid, at_specific_date=terms_at_specific_datetime
            ),
            dispensed_in=find_simple_term_model_name_by_term_uid(
                selection.dispensed_in_uid, at_specific_date=terms_at_specific_datetime
            ),
            device=find_simple_term_model_name_by_term_uid(
                selection.device_uid, at_specific_date=terms_at_specific_datetime
            ),
            formulation=find_simple_term_model_name_by_term_uid(
                selection.formulation_uid, at_specific_date=terms_at_specific_datetime
            ),
            other_info=selection.other_info,
            reason_for_missing_null_value=find_simple_term_model_name_by_term_uid(
                selection.reason_for_missing_value_uid,
                at_specific_date=terms_at_specific_datetime,
            ),
            start_date=selection.start_date,
            user_initials=selection.user_initials,
            project_name=project.name,
            project_number=project.project_number,
            study_compound_dosing_count=selection.study_compound_dosing_count,
        )

    study_compound_uid: str = Field(
        ...,
        title="study_compound_uid",
        description="uid for the study compound",
        source="uid",
    )

    compound: Compound | None = Field(
        None,
        title="compound",
        description="the connected compound model",
        nullable=True,
    )

    compound_alias: CompoundAlias | None = Field(
        None,
        title="compound_alias",
        description="the connected compound alias",
        nullable=True,
    )

    type_of_treatment: SimpleTermModel | None = Field(
        None,
        title="type_of_treatment",
        description="type of treatment uid defined for the selection",
        nullable=True,
    )

    route_of_administration: SimpleTermModel | None = Field(
        None,
        title="route_of_administration",
        description="route of administration defined for the study selection",
        nullable=True,
    )

    strength_value: SimpleNumericValueWithUnit | None = Field(
        None,
        title="strength",
        description="compound strength defined for the study selection",
        nullable=True,
    )

    dosage_form: SimpleTermModel | None = Field(
        None,
        title="dosage_form",
        description="dosage form defined for the study selection",
        nullable=True,
    )

    dispensed_in: SimpleTermModel | None = Field(
        None,
        title="dispensed_in",
        description="dispense method defined for the study selection",
        nullable=True,
    )

    device: SimpleTermModel | None = Field(
        None,
        title="device",
        description="device used for the compound in the study selection",
        nullable=True,
    )

    formulation: SimpleTermModel | None = Field(
        None,
        title="formulation",
        description="formulation defined for the study selection",
        nullable=True,
    )

    other_info: str | None = Field(
        None,
        title="other_info",
        description="any other information logged regarding the study compound",
        nullable=True,
    )

    reason_for_missing_null_value: SimpleTermModel | None = Field(
        None,
        title="reason_for_missing_null_value",
        description="Reason why no compound is used in the study selection, e.g. exploratory study",
        nullable=True,
    )

    study_compound_dosing_count: int | None = Field(
        None,
        description="Number of compound dosing linked to Study Compound",
        nullable=True,
    )

    start_date: datetime | None = Field(
        ...,
        title="start_date",
        description=START_DATE_DESC,
    )

    user_initials: str | None = Field(
        ..., title="user_initials", description=USER_INITIALS_DESC
    )

    end_date: datetime | None = END_DATE_FIELD

    status: str | None = STATUS_FIELD

    change_type: str | None = CHANGE_TYPE_FIELD

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: StudyCompoundSelectionHistory,
        study_uid: str,
        get_compound_by_uid: Callable[[str], Compound],
        get_compound_alias_by_uid: Callable[[str], CompoundAlias],
        find_simple_term_model_name_by_term_uid: Callable,
        find_unit_by_uid: Callable[[str], UnitDefinitionAR | None],
        find_numeric_value_by_uid: Callable[[str], NumericValueWithUnitAR | None],
    ) -> Self:
        if study_selection_history.compound_uid:
            compound = get_compound_by_uid(study_selection_history.compound_uid)
        else:
            compound = None
        if study_selection_history.compound_alias_uid:
            compound_alias = get_compound_alias_by_uid(
                study_selection_history.compound_alias_uid
            )
        else:
            compound_alias = None
        return cls(
            study_compound_uid=study_selection_history.study_selection_uid,
            order=study_selection_history.order,
            study_uid=study_uid,
            type_of_treatment=find_simple_term_model_name_by_term_uid(
                study_selection_history.type_of_treatment_uid
            ),
            route_of_administration=find_simple_term_model_name_by_term_uid(
                study_selection_history.route_of_administration_uid
            ),
            strength_value=SimpleNumericValueWithUnit.from_concept_uid(
                uid=study_selection_history.strength_value_uid,
                find_unit_by_uid=find_unit_by_uid,
                find_numeric_value_by_uid=find_numeric_value_by_uid,
            ),
            dosage_form=find_simple_term_model_name_by_term_uid(
                study_selection_history.dosage_form_uid
            ),
            dispensed_in=find_simple_term_model_name_by_term_uid(
                study_selection_history.dispensed_in_uid
            ),
            device=find_simple_term_model_name_by_term_uid(
                study_selection_history.device_uid
            ),
            formulation=find_simple_term_model_name_by_term_uid(
                study_selection_history.formulation_uid
            ),
            other_info=study_selection_history.other_info,
            reason_for_missing_null_value=find_simple_term_model_name_by_term_uid(
                study_selection_history.reason_for_missing_value_uid
            ),
            start_date=study_selection_history.start_date,
            compound=compound,
            compound_alias=compound_alias,
            end_date=study_selection_history.end_date,
            status=study_selection_history.status,
            change_type=study_selection_history.change_type,
            user_initials=study_selection_history.user_initials,
        )


class StudySelectionCompoundInput(BaseModel):
    compound_alias_uid: str = Field(
        None,
        title="compound_alias_uid",
        description="uid for the library compound alias",
    )

    type_of_treatment_uid: str | None = Field(
        None,
        title="type_of_treatment_uid",
        description="type of treatment defined for the selection",
    )

    route_of_administration_uid: str | None = Field(
        None,
        title="route_of_administration_uid",
        description="route of administration defined for the study selection",
    )

    strength_value_uid: str | None = Field(
        None,
        title="strength_value_uid",
        description="compound strength defined for the study selection",
    )

    dosage_form_uid: str | None = Field(
        None,
        title="dosage_form_uid",
        description="dosage form defined for the study selection",
    )

    dispensed_in_uid: str | None = Field(
        None,
        title="dispensed_in_uid",
        description="dispense method defined for the study selection",
    )

    device_uid: str | None = Field(
        None,
        title="device_uid",
        description="device used for the compound in the study selection",
    )

    formulation_uid: str | None = Field(
        None,
        title="formulation_uid",
        description="formulation defined for the study selection",
    )

    other_info: str | None = Field(
        None,
        title="other_info",
        description="any other information logged regarding the study compound",
    )

    reason_for_missing_null_value_uid: str | None = Field(
        None,
        title="reason_for_missing_null_value_uid",
        description="Reason why no compound is used in the study selection, e.g. exploratory study",
    )


class StudySelectionCompoundNewOrder(BaseModel):
    new_order: int = Field(
        ...,
        title="new_order",
        description="new order selected for the study compound",
    )


# Study criteria


class StudySelectionCriteriaCore(StudySelection):
    study_criteria_uid: str | None = Field(
        ...,
        title="study_criteria_uid",
        description="uid for the study criteria",
    )

    criteria_type: CTTermName | None = Field(
        None, title="criteria_type", description="Type of criteria", nullable=True
    )

    criteria: Criteria | None = Field(
        None,
        title="criteria",
        description="the criteria selected for the study",
        nullable=True,
    )

    criteria_template: CriteriaTemplate | None = Field(
        None,
        title="criteria_template",
        description="the criteria template selected for the study",
        nullable=True,
    )

    start_date: datetime | None = Field(
        ...,
        title="start_date",
        description=START_DATE_DESC,
    )

    user_initials: str | None = Field(
        None,
        title="user_initials",
        description=USER_INITIALS_DESC,
        nullable=True,
    )

    end_date: datetime | None = END_DATE_FIELD

    status: str | None = STATUS_FIELD

    change_type: str | None = CHANGE_TYPE_FIELD
    key_criteria: bool | None = Field(
        False, title="key_criteria", description="", nullable=True
    )

    @classmethod
    def from_study_selection_template_history(
        cls,
        study_selection_history: StudyCriteriaSelectionHistory,
        study_uid: str,
        get_criteria_template_by_uid_version_callback: Callable[
            [str], CriteriaTemplate
        ],
    ) -> Self:
        return cls(
            study_criteria_uid=study_selection_history.study_selection_uid,
            order=study_selection_history.criteria_type_order,
            study_uid=study_uid,
            start_date=study_selection_history.start_date,
            criteria_template=get_criteria_template_by_uid_version_callback(
                study_selection_history.syntax_object_uid,
                study_selection_history.syntax_object_version,
            ),
            end_date=study_selection_history.end_date,
            status=study_selection_history.status,
            change_type=study_selection_history.change_type,
            user_initials=study_selection_history.user_initials,
            key_criteria=study_selection_history.key_criteria,
        )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: StudyCriteriaSelectionHistory,
        study_uid: str,
        get_criteria_by_uid_version_callback: Callable[[str], Criteria],
    ) -> Self:
        return cls(
            study_criteria_uid=study_selection_history.study_selection_uid,
            order=study_selection_history.criteria_type_order,
            study_uid=study_uid,
            start_date=study_selection_history.start_date,
            criteria=get_criteria_by_uid_version_callback(
                study_selection_history.syntax_object_uid,
                study_selection_history.syntax_object_version,
            ),
            end_date=study_selection_history.end_date,
            status=study_selection_history.status,
            change_type=study_selection_history.change_type,
            user_initials=study_selection_history.user_initials,
            key_criteria=study_selection_history.key_criteria,
        )


class StudySelectionCriteria(StudySelectionCriteriaCore):
    latest_criteria: Criteria | None = Field(
        None,
        title="latest_criteria",
        description="Latest version of criteria selected for study.",
    )
    latest_template: CriteriaTemplate | None = Field(
        None,
        title="latest_template",
        description="Latest version of criteria template selected for study.",
    )
    accepted_version: bool | None = Field(
        None,
        title=ACCEPTED_VERSION_DESC,
        description="Denotes if user accepted obsolete criteria versions",
    )

    @classmethod
    def from_study_selection_criteria_template_ar_and_order(
        cls,
        study_selection_criteria_ar: StudySelectionCriteriaAR,
        criteria_type_uid: str,
        criteria_type_order: int,
        get_criteria_template_by_uid_callback: Callable[[str], CriteriaTemplate],
        get_criteria_template_by_uid_version_callback: Callable[
            [str], CriteriaTemplate
        ],
        get_ct_term_criteria_type: Callable[[str], CTTermName],
        find_project_by_study_uid: Callable,
        terms_at_specific_datetime: datetime | None,
        accepted_version: bool = False,
        study_value_version: str | None = None,
    ) -> Self:
        study_uid = study_selection_criteria_ar.study_uid

        project = find_project_by_study_uid(study_uid)
        assert project is not None

        # Filter criteria list on criteria type before selecting with order property
        study_criteria_selection_with_type = [
            x
            for x in study_selection_criteria_ar.study_criteria_selection
            if x.criteria_type_uid == criteria_type_uid
        ]
        single_study_selection = study_criteria_selection_with_type[
            criteria_type_order - 1
        ]
        study_criteria_uid = single_study_selection.study_selection_uid
        criteria_template_uid = single_study_selection.syntax_object_uid

        criteria_type = get_ct_term_criteria_type(
            criteria_type_uid,
            at_specific_date=terms_at_specific_datetime,
        )

        assert criteria_template_uid is not None
        latest_criteria_template = get_criteria_template_by_uid_callback(
            criteria_template_uid
        )
        if (
            latest_criteria_template
            and latest_criteria_template.version
            == single_study_selection.syntax_object_version
        ):
            selected_criteria_template = latest_criteria_template
            latest_criteria_template = None
        else:
            selected_criteria_template = get_criteria_template_by_uid_version_callback(
                criteria_template_uid, single_study_selection.syntax_object_version
            )

        return cls(
            study_criteria_uid=study_criteria_uid,
            criteria_type=criteria_type,
            order=criteria_type_order,
            accepted_version=accepted_version,
            study_uid=study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            start_date=single_study_selection.start_date,
            criteria_template=selected_criteria_template,
            user_initials=single_study_selection.user_initials,
            project_name=project.name,
            project_number=project.project_number,
            key_criteria=single_study_selection.key_criteria,
        )

    @classmethod
    def from_study_selection_criteria_ar_and_order(
        cls,
        study_selection_criteria_ar: StudySelectionCriteriaAR,
        criteria_type_uid: str,
        criteria_type_order: int,
        get_criteria_by_uid_callback: Callable[[str], Criteria],
        get_criteria_by_uid_version_callback: Callable[[str], Criteria],
        get_ct_term_criteria_type: Callable[[str], CTTermName],
        find_project_by_study_uid: Callable,
        terms_at_specific_datetime: datetime | None,
        no_brackets: bool = False,
        accepted_version: bool = False,
        study_value_version: str | None = None,
    ) -> Self:
        study_uid = study_selection_criteria_ar.study_uid

        project = find_project_by_study_uid(study_uid)
        assert project is not None

        # Filter criteria list on criteria type before selecting with order property
        study_criteria_selection_with_type = [
            x
            for x in study_selection_criteria_ar.study_criteria_selection
            if x.criteria_type_uid == criteria_type_uid
        ]
        single_study_selection = study_criteria_selection_with_type[
            criteria_type_order - 1
        ]
        study_criteria_uid = single_study_selection.study_selection_uid
        criteria_uid = single_study_selection.syntax_object_uid

        criteria_type = get_ct_term_criteria_type(
            criteria_type_uid,
            at_specific_date=terms_at_specific_datetime,
        )

        assert criteria_uid is not None
        latest_criteria = get_criteria_by_uid_callback(criteria_uid)
        if (
            latest_criteria
            and latest_criteria.version == single_study_selection.syntax_object_version
        ):
            selected_criteria = latest_criteria
            latest_criteria = None
        else:
            selected_criteria = get_criteria_by_uid_version_callback(
                criteria_uid, single_study_selection.syntax_object_version
            )
        if no_brackets:
            cls.remove_brackets_from_name_property(selected_criteria)
            if latest_criteria is not None:
                cls.remove_brackets_from_name_property(latest_criteria)

        return cls(
            study_criteria_uid=study_criteria_uid,
            criteria_type=criteria_type,
            order=criteria_type_order,
            accepted_version=accepted_version,
            study_uid=study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            start_date=single_study_selection.start_date,
            latest_criteria=latest_criteria,
            criteria=selected_criteria,
            user_initials=single_study_selection.user_initials,
            project_name=project.name,
            project_number=project.project_number,
            key_criteria=single_study_selection.key_criteria,
        )

    @classmethod
    def from_study_selection_criteria_template_ar(
        cls,
        study_selection_criteria_ar: StudySelectionCriteriaAR,
        study_selection_criteria_vo: StudySelectionCriteriaVO,
        get_criteria_template_by_uid_callback: Callable[[str], CriteriaTemplate],
        get_criteria_template_by_uid_version_callback: Callable[
            [str], CriteriaTemplate
        ],
        get_ct_term_criteria_type: Callable[[str], CTTermName],
        find_project_by_study_uid: Callable,
        terms_at_specific_datetime: datetime | None,
        accepted_version: bool = False,
        study_value_version: str | None = None,
    ) -> Self:
        study_uid = study_selection_criteria_ar.study_uid

        project = find_project_by_study_uid(study_uid)
        assert project is not None

        study_criteria_uid = study_selection_criteria_vo.study_selection_uid
        criteria_template_uid = study_selection_criteria_vo.syntax_object_uid

        criteria_type = get_ct_term_criteria_type(
            study_selection_criteria_vo.criteria_type_uid,
            at_specific_date=terms_at_specific_datetime,
        )

        assert criteria_template_uid is not None
        latest_criteria_template = get_criteria_template_by_uid_callback(
            criteria_template_uid
        )
        if (
            latest_criteria_template
            and latest_criteria_template.version
            == study_selection_criteria_vo.syntax_object_version
        ):
            selected_criteria_template = latest_criteria_template
            latest_criteria_template = None
        else:
            selected_criteria_template = get_criteria_template_by_uid_version_callback(
                criteria_template_uid, study_selection_criteria_vo.syntax_object_version
            )

        return cls(
            study_criteria_uid=study_criteria_uid,
            criteria_type=criteria_type,
            order=study_selection_criteria_vo.criteria_type_order,
            accepted_version=accepted_version,
            study_uid=study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            start_date=study_selection_criteria_vo.start_date,
            criteria_template=selected_criteria_template,
            user_initials=study_selection_criteria_vo.user_initials,
            project_name=project.name,
            project_number=project.project_number,
            key_criteria=study_selection_criteria_vo.key_criteria,
        )

    @classmethod
    def from_study_selection_criteria_ar(
        cls,
        study_selection_criteria_ar: StudySelectionCriteriaAR,
        study_selection_criteria_vo: StudySelectionCriteriaVO,
        get_criteria_by_uid_callback: Callable[[str], Criteria],
        get_criteria_by_uid_version_callback: Callable[[str], Criteria],
        get_ct_term_criteria_type: Callable[[str], CTTermName],
        find_project_by_study_uid: Callable,
        terms_at_specific_datetime: datetime | None,
        no_brackets: bool = False,
        accepted_version: bool = False,
        study_value_version: str | None = None,
    ) -> Self:
        study_uid = study_selection_criteria_ar.study_uid

        project = find_project_by_study_uid(study_uid)
        assert project is not None

        study_criteria_uid = study_selection_criteria_vo.study_selection_uid
        criteria_uid = study_selection_criteria_vo.syntax_object_uid

        criteria_type = get_ct_term_criteria_type(
            study_selection_criteria_vo.criteria_type_uid,
            at_specific_date=terms_at_specific_datetime,
        )

        assert criteria_uid is not None
        latest_criteria = get_criteria_by_uid_callback(criteria_uid)
        if (
            latest_criteria
            and latest_criteria.version
            == study_selection_criteria_vo.syntax_object_version
        ):
            selected_criteria = latest_criteria
            latest_criteria = None
        else:
            selected_criteria = get_criteria_by_uid_version_callback(
                criteria_uid, study_selection_criteria_vo.syntax_object_version
            )
        if no_brackets:
            cls.remove_brackets_from_name_property(selected_criteria)
            if latest_criteria is not None:
                cls.remove_brackets_from_name_property(latest_criteria)

        return cls(
            study_criteria_uid=study_criteria_uid,
            criteria_type=criteria_type,
            order=study_selection_criteria_vo.criteria_type_order,
            accepted_version=accepted_version,
            study_uid=study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            start_date=study_selection_criteria_vo.start_date,
            latest_criteria=latest_criteria,
            criteria=selected_criteria,
            user_initials=study_selection_criteria_vo.user_initials,
            project_name=project.name,
            project_number=project.project_number,
            key_criteria=study_selection_criteria_vo.key_criteria,
        )


class StudySelectionCriteriaCreateInput(BaseModel):
    criteria_data: CriteriaCreateInput = Field(
        ..., title="criteria_data", description="Criteria data to create new criteria"
    )


class StudySelectionCriteriaInput(BaseModel):
    criteria_uid: str = Field(
        None,
        title="criteria_uid",
        description="Uid of the selected criteria",
    )


class StudySelectionCriteriaTemplateSelectInput(BaseModel):
    criteria_template_uid: str = Field(
        ...,
        title="criteria_template_uid",
        description="The unique id of the criteria template that is to be selected.",
    )
    parameter_terms: list[TemplateParameterMultiSelectInput] = Field(
        [],
        title="parameter_terms",
        description="An ordered list of selected parameter terms that are used to replace the parameters of the criteria template.",
    )
    library_name: str = Field(
        None,
        title="library_name",
        description="If specified: The name of the library to which the criteria will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* criteria can help. And \n"
        "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true. \n\n"
        "If not specified: The library of the criteria template will be used.",
    )


class StudySelectionCriteriaNewOrder(BaseModel):
    new_order: int = Field(
        ...,
        title="new_order",
        description="New value to set for the order property of the selection",
    )


class StudySelectionCriteriaKeyCriteria(BaseModel):
    key_criteria: bool = Field(
        ...,
        title="key_criteria",
        description="New value to set for the key_criteria property of the selection",
    )


#
# Study Activity
#
class DetailedSoAHistory(BaseModel):
    object_type: str = Field(
        ...,
    )
    description: str = Field(
        ...,
    )
    action: str = CHANGE_TYPE_FIELD
    user_initials: str = USER_INITIALS_DESC
    start_date: datetime = START_DATE_DESC
    end_date: datetime | None = END_DATE_FIELD

    @classmethod
    def from_history(cls, detailed_soa_history_item: dict):
        return cls(
            object_type=detailed_soa_history_item.get("object_type"),
            description=detailed_soa_history_item.get("description"),
            action=detailed_soa_history_item.get("change_type"),
            user_initials=detailed_soa_history_item.get("user_initials"),
            start_date=detailed_soa_history_item.get("start_date"),
            end_date=detailed_soa_history_item.get("end_date"),
        )


class SimpleStudyActivitySubGroup(BaseModel):
    study_activity_subgroup_uid: str | None = Field(
        None,
        nullable=True,
    )
    activity_subgroup_uid: str | None = Field(
        None,
        nullable=True,
    )
    activity_subgroup_name: str | None = Field(
        None,
        nullable=True,
    )


class SimpleStudyActivityGroup(BaseModel):
    study_activity_group_uid: str | None = Field(
        None,
        nullable=True,
    )
    activity_group_uid: str | None = Field(
        None,
        nullable=True,
    )
    activity_group_name: str | None = Field(
        None,
        nullable=True,
    )


class SimpleStudySoAGroup(BaseModel):
    study_soa_group_uid: str = Field(...)
    soa_group_term_uid: str = Field(...)
    soa_group_name: str = Field(...)


class StudySelectionActivityCore(StudySelection):
    show_activity_in_protocol_flowchart: bool | None = Field(
        None,
        title="show_activity_in_protocol_flowchart",
        description="show activity in protocol flow chart",
    )
    show_activity_subgroup_in_protocol_flowchart: bool | None = (
        SHOW_ACTIVITY_SUBGROUP_IN_PROTOCOL_FLOWCHART_FIELD
    )
    show_activity_group_in_protocol_flowchart: bool | None = (
        SHOW_ACTIVITY_GROUP_IN_PROTOCOL_FLOWCHART_FIELD
    )
    show_soa_group_in_protocol_flowchart: bool = (
        SHOW_SOA_GROUP_IN_PROTOCOL_FLOWCHART_FIELD
    )
    study_activity_uid: str | None = Field(
        ...,
        title="study_activity_uid",
        description=STUDY_ACTIVITY_UID_DESC,
        source="uid",
    )
    study_activity_subgroup: SimpleStudyActivitySubGroup | None
    study_activity_group: SimpleStudyActivityGroup | None
    study_soa_group: SimpleStudySoAGroup
    activity: ActivityForStudyActivity | None = Field(
        ...,
        title="activity",
        description="the activity selected for the study",
    )
    start_date: datetime | None = Field(
        ...,
        title="start_date",
        description=START_DATE_DESC,
        source=AFTER_DATE_QUALIFIER,
    )
    user_initials: str | None = Field(
        ...,
        title="user_initials",
        description=USER_INITIALS_DESC,
        source=AFTER_USER_QUALIFIER,
    )
    end_date: datetime | None = END_DATE_FIELD
    status: str | None = STATUS_FIELD
    change_type: str | None = CHANGE_TYPE_FIELD

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: StudyActivitySelectionHistory,
        study_uid: str,
        get_ct_term_flowchart_group: Callable[[str], CTTermName],
        get_activity_by_uid_version_callback: Callable[[str], ActivityForStudyActivity],
    ) -> Self:
        flowchart_group = get_ct_term_flowchart_group(
            study_selection_history.soa_group_term_uid
        )
        activity = get_activity_by_uid_version_callback(
            study_selection_history.activity_uid,
            study_selection_history.activity_version,
        )
        activity_subgroup_name = next(
            (
                activity_grouping.activity_subgroup_name
                for activity_grouping in activity.activity_groupings
                if activity_grouping.activity_subgroup_uid
                == study_selection_history.activity_subgroup_uid
            ),
            None,
        )
        activity_group_name = next(
            (
                activity_grouping.activity_group_name
                for activity_grouping in activity.activity_groupings
                if activity_grouping.activity_group_uid
                == study_selection_history.activity_group_uid
            ),
            None,
        )
        return cls(
            study_uid=study_uid,
            study_activity_uid=study_selection_history.study_selection_uid,
            study_activity_subgroup=SimpleStudyActivitySubGroup(
                study_activity_subgroup_uid=study_selection_history.study_activity_subgroup_uid,
                activity_subgroup_uid=study_selection_history.activity_subgroup_uid,
                activity_subgroup_name=activity_subgroup_name,
            ),
            study_activity_group=SimpleStudyActivityGroup(
                study_activity_group_uid=study_selection_history.study_activity_group_uid,
                activity_group_uid=study_selection_history.activity_group_uid,
                activity_group_name=activity_group_name,
            ),
            study_soa_group=SimpleStudySoAGroup(
                study_soa_group_uid=study_selection_history.study_soa_group_uid,
                soa_group_term_uid=flowchart_group.term_uid,
                soa_group_name=flowchart_group.sponsor_preferred_name,
            ),
            order=study_selection_history.activity_order,
            show_activity_group_in_protocol_flowchart=study_selection_history.show_activity_group_in_protocol_flowchart,
            show_activity_subgroup_in_protocol_flowchart=study_selection_history.show_activity_subgroup_in_protocol_flowchart,
            show_activity_in_protocol_flowchart=study_selection_history.show_activity_in_protocol_flowchart,
            show_soa_group_in_protocol_flowchart=study_selection_history.show_soa_group_in_protocol_flowchart,
            start_date=study_selection_history.start_date,
            activity=activity,
            end_date=study_selection_history.end_date,
            change_type=study_selection_history.change_type,
            user_initials=study_selection_history.user_initials,
        )


class StudySelectionActivity(StudySelectionActivityCore):
    class Config:
        orm_mode = True

    latest_activity: ActivityForStudyActivity | None = Field(
        None,
        title="latest_activity",
        description="Latest version of activity selected for study.",
        nullable=True,
    )
    accepted_version: bool | None = Field(
        None,
        title=ACCEPTED_VERSION_DESC,
        description="Denotes if user accepted obsolete activity versions",
        nullable=True,
    )

    @classmethod
    def from_study_selection_activity_vo_and_order(
        cls,
        study_uid: str,
        specific_selection: StudySelectionActivityVO,
        activity_order: int,
        get_activity_by_uid_callback: Callable[[str], ActivityForStudyActivity],
        get_activity_by_uid_version_callback: Callable[[str], ActivityForStudyActivity],
        get_ct_term_flowchart_group: Callable[[str], CTTermName],
        terms_at_specific_datetime: datetime | None,
        accepted_version: bool = False,
        study_value_version: str | None = None,
    ) -> Self:
        single_study_selection = specific_selection
        study_activity_uid = specific_selection.study_selection_uid
        activity_uid = single_study_selection.activity_uid

        flowchart_group = get_ct_term_flowchart_group(
            single_study_selection.soa_group_term_uid,
            at_specific_date=terms_at_specific_datetime,
        )

        assert activity_uid is not None
        latest_activity = get_activity_by_uid_callback(activity_uid)
        if (
            latest_activity
            and latest_activity.version == single_study_selection.activity_version
        ):
            selected_activity = latest_activity
            latest_activity = None
        else:
            selected_activity = get_activity_by_uid_version_callback(
                activity_uid, single_study_selection.activity_version
            )
        activity_subgroup_name = single_study_selection.activity_subgroup_name
        activity_group_name = single_study_selection.activity_group_name
        return cls(
            study_activity_uid=study_activity_uid,
            study_activity_subgroup=SimpleStudyActivitySubGroup(
                study_activity_subgroup_uid=single_study_selection.study_activity_subgroup_uid,
                activity_subgroup_uid=single_study_selection.activity_subgroup_uid,
                activity_subgroup_name=activity_subgroup_name,
            ),
            study_activity_group=SimpleStudyActivityGroup(
                study_activity_group_uid=single_study_selection.study_activity_group_uid,
                activity_group_uid=single_study_selection.activity_group_uid,
                activity_group_name=activity_group_name,
            ),
            study_soa_group=SimpleStudySoAGroup(
                study_soa_group_uid=single_study_selection.study_soa_group_uid,
                soa_group_term_uid=flowchart_group.term_uid,
                soa_group_name=flowchart_group.sponsor_preferred_name,
            ),
            activity=selected_activity,
            latest_activity=latest_activity,
            order=activity_order,
            show_activity_group_in_protocol_flowchart=single_study_selection.show_activity_group_in_protocol_flowchart,
            show_activity_subgroup_in_protocol_flowchart=single_study_selection.show_activity_subgroup_in_protocol_flowchart,
            show_activity_in_protocol_flowchart=single_study_selection.show_activity_in_protocol_flowchart,
            show_soa_group_in_protocol_flowchart=single_study_selection.show_soa_group_in_protocol_flowchart,
            accepted_version=accepted_version,
            study_uid=study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            start_date=single_study_selection.start_date,
            user_initials=single_study_selection.user_initials,
        )


class StudySelectionActivityCreateInput(BaseModel):
    soa_group_term_uid: str = Field(
        title="soa_group_term_uid",
        description="flowchart CT term uid",
    )
    activity_uid: str = Field(title="activity_uid", description="activity uid")
    activity_subgroup_uid: str | None = Field(None, title="activity_subgroup_uid")
    activity_group_uid: str | None = Field(None, title="activity_group_uid")
    activity_instance_uid: str | None = Field(
        None, title="activity_instance_uid", description="activity instance uid"
    )


class StudySelectionActivityInput(BaseModel):
    show_activity_in_protocol_flowchart: bool | None = Field(
        None,
        title="show_activity_in_protocol_flowchart",
        description="show activity in protocol flow chart",
    )
    show_activity_subgroup_in_protocol_flowchart: bool | None = (
        SHOW_ACTIVITY_SUBGROUP_IN_PROTOCOL_FLOWCHART_FIELD
    )
    show_activity_group_in_protocol_flowchart: bool | None = (
        SHOW_ACTIVITY_GROUP_IN_PROTOCOL_FLOWCHART_FIELD
    )
    show_soa_group_in_protocol_flowchart: bool = (
        SHOW_SOA_GROUP_IN_PROTOCOL_FLOWCHART_FIELD
    )
    soa_group_term_uid: str | None = Field(
        title="soa_group_term_uid",
        description="flowchart CT term uid",
    )


class StudySelectionActivityRequestEditInput(StudySelectionActivityInput):
    soa_group_term_uid: str | None = Field(
        None,
        title="soa_group_term_uid",
        description="flowchart CT term uid",
    )
    activity_group_uid: str | None = Field(None, title="activity_group_uid")
    activity_subgroup_uid: str | None = Field(None, title="activity_subgroup_uid")
    activity_uid: str | None = Field(
        None, title="activity_uid", description="activity uid"
    )
    activity_name: str | None = Field(
        None, title="activity_name", description="activity_name uid"
    )
    request_rationale: str | None = None
    is_data_collected: bool | None = None
    is_request_final: bool | None = None


class UpdateActivityPlaceholderToSponsorActivity(StudySelectionActivityInput):
    activity_group_uid: str = Field(..., title="activity_group_uid")
    activity_subgroup_uid: str = Field(..., title="activity_subgroup_uid")
    activity_uid: str = Field(..., title="activity_uid", description="activity uid")


class StudySelectionActivityNewOrder(BaseModel):
    new_order: int = Field(
        ...,
        title="new_order",
        description="new order selected for the study activity",
    )


class StudySelectionActivityBatchUpdateInput(BaseModel):
    study_activity_uid: str = Field(
        ...,
        title="study_activity_uid",
        description="UID of the Study Activity to update",
    )
    content: StudySelectionActivityInput


class StudySelectionActivityBatchDeleteInput(BaseModel):
    study_activity_uid: str = Field(
        ...,
        title="study_activity_uid",
        description="UID of the study activity to delete",
    )


class StudySelectionActivityBatchInput(BaseModel):
    method: str = METHOD_FIELD
    content: (
        StudySelectionActivityBatchUpdateInput
        | StudySelectionActivityCreateInput
        | StudySelectionActivityBatchDeleteInput
    )


class StudySelectionActivityBatchOutput(BaseModel):
    response_code: int = RESPONSE_CODE_FIELD
    content: StudySelectionActivity | None | BatchErrorResponse


class StudyActivitySubGroupEditInput(BaseModel):
    show_activity_subgroup_in_protocol_flowchart: bool | None = (
        SHOW_ACTIVITY_SUBGROUP_IN_PROTOCOL_FLOWCHART_FIELD
    )


class StudyActivitySubGroup(BaseModel):
    show_activity_subgroup_in_protocol_flowchart: bool | None = (
        SHOW_ACTIVITY_SUBGROUP_IN_PROTOCOL_FLOWCHART_FIELD
    )
    study_uid: str | None = Field(
        ...,
        title="study_uid",
        description=STUDY_UID_DESC,
    )
    study_activity_subgroup_uid: str = Field(
        ...,
        title="study_activity_subgroup_uid",
        source="uid",
    )

    @classmethod
    def from_study_selection_activity_vo(
        cls,
        study_uid: str,
        specific_selection: StudySelectionActivitySubGroupVO,
    ) -> Self:
        single_study_selection = specific_selection
        study_activity_subgroup_uid = single_study_selection.study_selection_uid

        return cls(
            study_activity_subgroup_uid=study_activity_subgroup_uid,
            show_activity_subgroup_in_protocol_flowchart=single_study_selection.show_activity_subgroup_in_protocol_flowchart,
            study_uid=study_uid,
        )


class StudyActivityGroupEditInput(BaseModel):
    show_activity_group_in_protocol_flowchart: bool | None = (
        SHOW_ACTIVITY_GROUP_IN_PROTOCOL_FLOWCHART_FIELD
    )


class StudyActivityGroup(BaseModel):
    show_activity_group_in_protocol_flowchart: bool | None = (
        SHOW_ACTIVITY_GROUP_IN_PROTOCOL_FLOWCHART_FIELD
    )
    study_uid: str | None = Field(
        ...,
        title="study_uid",
        description=STUDY_UID_DESC,
    )
    study_activity_group_uid: str = Field(
        ...,
        title="study_activity_group_uid",
        source="uid",
    )

    @classmethod
    def from_study_selection_activity_vo(
        cls,
        study_uid: str,
        specific_selection: StudySelectionActivityGroupVO,
    ) -> Self:
        single_study_selection = specific_selection
        study_activity_group_uid = single_study_selection.study_selection_uid

        return cls(
            study_activity_group_uid=study_activity_group_uid,
            show_activity_group_in_protocol_flowchart=single_study_selection.show_activity_group_in_protocol_flowchart,
            study_uid=study_uid,
        )


class StudySoAGroupEditInput(BaseModel):
    show_soa_group_in_protocol_flowchart: bool = (
        SHOW_SOA_GROUP_IN_PROTOCOL_FLOWCHART_FIELD
    )


class StudySoAGroup(BaseModel):
    show_soa_group_in_protocol_flowchart: bool = (
        SHOW_SOA_GROUP_IN_PROTOCOL_FLOWCHART_FIELD
    )
    study_uid: str | None = Field(
        ...,
        title="study_uid",
        description=STUDY_UID_DESC,
    )
    study_soa_group_uid: str = Field(
        ...,
        title="study_soa_group_uid",
        source="uid",
    )

    @classmethod
    def from_study_selection_activity_vo(
        cls,
        study_uid: str,
        specific_selection: StudySoAGroupVO,
    ) -> Self:
        single_study_selection = specific_selection
        study_soa_group_uid = single_study_selection.study_selection_uid

        return cls(
            study_soa_group_uid=study_soa_group_uid,
            show_soa_group_in_protocol_flowchart=single_study_selection.show_soa_group_in_protocol_flowchart,
            study_uid=study_uid,
        )


#
# Study Activity Instance
#
class StudySelectionActivityInstance(BaseModel):
    study_uid: str | None = Field(
        ...,
        title="study_uid",
        description=STUDY_UID_DESC,
    )

    show_activity_instance_in_protocol_flowchart: bool = (
        SHOW_ACTIVITY_INSTANCE_IN_PROTOCOL_FLOWCHART_FIELD
    )
    study_activity_instance_uid: str | None = Field(
        ...,
        title="study_activity_instance_uid",
        description=STUDY_ACTIVITY_INSTANCE_UID_DESC,
    )
    study_activity_uid: str | None = Field(
        ...,
        title="study_activity_uid",
        description=STUDY_ACTIVITY_UID_DESC,
    )
    study_version: str | None = Field(
        None,
        title="study version or date information",
        description="Study version number, if specified, otherwise None.",
    )
    activity: Activity
    activity_instance: ActivityInstance | None
    start_date: datetime | None = Field(
        ...,
        title="start_date",
        description=START_DATE_DESC,
    )
    user_initials: str | None = Field(
        ...,
        title="user_initials",
        description=USER_INITIALS_DESC,
    )
    end_date: datetime | None = END_DATE_FIELD
    status: str | None = STATUS_FIELD
    change_type: str | None = CHANGE_TYPE_FIELD
    latest_activity: Activity | None = Field(
        None,
        title="latest_activity",
        description="Latest version of activity selected for study.",
        nullable=True,
    )
    latest_activity_instance: ActivityInstance | None = Field(
        None,
        title="latest_activity_instance",
        description="Latest version of activity instace selected for study.",
        nullable=True,
    )
    state: StudyActivityInstanceState
    study_activity_subgroup: SimpleStudyActivitySubGroup | None
    study_activity_group: SimpleStudyActivityGroup | None
    study_soa_group: SimpleStudySoAGroup | None

    @classmethod
    def _get_state_out_of_activity_and_activity_instance(
        cls, activity: Activity, activity_instance: ActivityInstance
    ) -> StudyActivityInstanceState:
        if activity.is_data_collected:
            if activity_instance:
                if activity_instance.is_required_for_activity:
                    return StudyActivityInstanceState.REQUIRED
                if activity_instance.is_default_selected_for_activity:
                    return StudyActivityInstanceState.DEFAULTED
                return StudyActivityInstanceState.SUGGESTION
            return StudyActivityInstanceState.MISSING_SELECTION
        return StudyActivityInstanceState.NOT_REQUIRED

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: StudyActivityInstanceSelectionHistory,
        study_uid: str,
        get_activity_by_uid_version_callback: Callable[[str, str], Activity],
        get_activity_instance_by_uid_version_callback: Callable[
            [str, str], ActivityInstance
        ],
    ) -> Self:
        activity = get_activity_by_uid_version_callback(
            study_selection_history.activity_uid,
            study_selection_history.activity_version,
        )
        activity_instance = None
        if study_selection_history.activity_instance_uid:
            activity_instance = get_activity_instance_by_uid_version_callback(
                study_selection_history.activity_instance_uid,
                study_selection_history.activity_instance_version,
            )
        return cls(
            study_uid=study_uid,
            study_activity_instance_uid=study_selection_history.study_selection_uid,
            study_activity_uid=study_selection_history.study_activity_uid,
            show_activity_instance_in_protocol_flowchart=study_selection_history.show_activity_instance_in_protocol_flowchart,
            start_date=study_selection_history.start_date,
            activity=activity,
            activity_instance=activity_instance,
            end_date=study_selection_history.end_date,
            change_type=study_selection_history.change_type,
            user_initials=study_selection_history.user_initials,
            state=cls._get_state_out_of_activity_and_activity_instance(
                activity=activity, activity_instance=activity_instance
            ),
        )

    @classmethod
    def from_study_selection_activity_instance_vo_and_order(
        cls,
        study_uid: str,
        specific_selection: StudySelectionActivityInstanceVO,
        get_activity_by_uid_callback: Callable[[str], Activity],
        get_activity_by_uid_version_callback: Callable[[str, str], Activity],
        get_activity_instance_by_uid_callback: Callable[[str], ActivityInstance],
        get_activity_instance_by_uid_version_callback: Callable[
            [str, str], ActivityInstance
        ],
    ) -> Self:
        single_study_selection = specific_selection
        study_activity_instance_uid = single_study_selection.study_selection_uid
        activity_uid = single_study_selection.activity_uid
        activity_instance_uid = single_study_selection.activity_instance_uid

        assert activity_uid is not None
        latest_activity = get_activity_by_uid_callback(activity_uid)
        if (
            latest_activity
            and latest_activity.version == single_study_selection.activity_version
        ):
            selected_activity = latest_activity
            latest_activity = None
        else:
            selected_activity = get_activity_by_uid_version_callback(
                activity_uid, single_study_selection.activity_version
            )

        if activity_instance_uid:
            latest_activity_instance = get_activity_instance_by_uid_callback(
                activity_instance_uid
            )
            if (
                latest_activity_instance
                and latest_activity_instance.version
                == single_study_selection.activity_instance_version
            ):
                selected_activity_instance = latest_activity_instance
                latest_activity_instance = None
            else:
                selected_activity_instance = (
                    get_activity_instance_by_uid_version_callback(
                        activity_instance_uid,
                        single_study_selection.activity_instance_version,
                    )
                )
        else:
            selected_activity_instance = None
            latest_activity_instance = None
        return cls(
            study_activity_instance_uid=study_activity_instance_uid,
            study_activity_uid=single_study_selection.study_activity_uid,
            activity=selected_activity,
            latest_activity=latest_activity,
            activity_instance=selected_activity_instance,
            latest_activity_instance=latest_activity_instance,
            show_activity_instance_in_protocol_flowchart=single_study_selection.show_activity_instance_in_protocol_flowchart,
            study_uid=study_uid,
            start_date=single_study_selection.start_date,
            user_initials=single_study_selection.user_initials,
            state=cls._get_state_out_of_activity_and_activity_instance(
                activity=selected_activity, activity_instance=selected_activity_instance
            ),
            study_activity_subgroup=(
                SimpleStudyActivitySubGroup(
                    study_activity_subgroup_uid=single_study_selection.study_activity_subgroup_uid,
                    activity_subgroup_uid=single_study_selection.activity_subgroup_uid,
                    activity_subgroup_name=single_study_selection.activity_subgroup_name,
                )
                if single_study_selection.study_activity_subgroup_uid
                else None
            ),
            study_activity_group=(
                SimpleStudyActivityGroup(
                    study_activity_group_uid=single_study_selection.study_activity_group_uid,
                    activity_group_uid=single_study_selection.activity_group_uid,
                    activity_group_name=single_study_selection.activity_group_name,
                )
                if single_study_selection.study_activity_group_uid
                else None
            ),
            study_soa_group=(
                SimpleStudySoAGroup(
                    study_soa_group_uid=single_study_selection.study_soa_group_uid,
                    soa_group_term_uid=single_study_selection.soa_group_term_uid,
                    soa_group_name=single_study_selection.soa_group_term_name,
                )
                if single_study_selection.study_soa_group_uid
                else None
            ),
        )


class StudySelectionActivityInstanceCreateInput(BaseModel):
    activity_instance_uid: str | None = Field(
        None,
        title="activity_instance_uid",
        description="uid of the activity instance",
    )
    study_activity_uid: str = Field(
        ..., title="study_activity_uid", description="study_activity uid"
    )
    show_activity_instance_in_protocol_flowchart: bool = (
        SHOW_ACTIVITY_INSTANCE_IN_PROTOCOL_FLOWCHART_FIELD
    )


class StudySelectionActivityInstanceEditInput(BaseModel):
    activity_instance_uid: str | None = Field(
        None,
        title="activity_instance_uid",
        description="uid of the activity instance",
    )
    study_activity_uid: str | None = Field(
        None, title="study_activity_uid", description="study_activity uid"
    )
    show_activity_instance_in_protocol_flowchart: bool = (
        SHOW_ACTIVITY_INSTANCE_IN_PROTOCOL_FLOWCHART_FIELD
    )


#
# Study Activity Schedule
#
class StudyActivitySchedule(BaseModel):
    class Config:
        orm_mode = True

    study_uid: str = STUDY_UID_FIELD

    study_version: str | None = Field(
        None,
        title="study version or date information",
        description="Study version number, if specified, otherwise None",
    )

    study_activity_schedule_uid: str | None = Field(
        ...,
        title="study_activity_schedule_uid",
        description="uid for the study activity schedule",
        source="uid",
    )

    study_activity_uid: str = Field(
        ...,
        title="study_activity_uid",
        description="The related study activity UID",
        source="study_activity.uid",
    )
    study_activity_instance_uid: str | None = Field(
        None,
        title="study_activity_instance_uid",
        description="The related study activity instance UID",
        source="study_activity.study_activity_has_study_activity_instance.uid",
    )
    study_visit_uid: str = Field(
        title="study_visit_uid",
        description="The related study visit UID",
        source="study_visit.uid",
    )
    start_date: datetime | None = Field(
        ...,
        title="start_date",
        description=START_DATE_DESC,
        source=AFTER_DATE_QUALIFIER,
    )

    user_initials: str | None = Field(
        None,
        title="user_initials",
        description=USER_INITIALS_DESC,
        source=AFTER_USER_QUALIFIER,
        nullable=True,
    )

    end_date: datetime | None = END_DATE_FIELD

    @classmethod
    def from_vo(
        cls,
        schedule_vo: StudyActivityScheduleVO,
        study_value_version: str | None = None,
    ) -> Self:
        return cls(
            study_activity_schedule_uid=schedule_vo.uid,
            study_uid=schedule_vo.study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            study_activity_uid=schedule_vo.study_activity_uid,
            study_activity_instance_uid=schedule_vo.study_activity_instance_uid,
            study_visit_uid=schedule_vo.study_visit_uid,
            start_date=schedule_vo.start_date,
            user_initials=schedule_vo.user_initials,
        )


class StudyActivityScheduleHistory(BaseModel):
    study_uid: str = Field(
        ...,
        title="study_uid",
        description=STUDY_UID_DESC,
    )

    study_activity_schedule_uid: str = Field(
        ...,
        title="study_activity_schedule_uid",
        description="uid for the study activity schedule",
    )
    study_activity_uid: str = Field(
        ...,
        title="study_activity_uid",
        description=STUDY_ACTIVITY_UID_DESC,
    )
    study_activity_instance_uid: str | None = Field(
        None,
        title="study_activity_instance_uid",
        description=STUDY_ACTIVITY_INSTANCE_UID_DESC,
    )
    study_visit_uid: str = Field(
        ...,
        title="study_visit_uid",
        description="uid for the study visit",
    )

    modified: datetime | None = Field(
        None, title="modified", description="Date of last modification", nullable=True
    )


class StudyActivityScheduleCreateInput(BaseModel):
    study_activity_uid: str = Field(
        ..., title="study_activity_uid", description="The related study activity uid"
    )
    study_visit_uid: str = Field(
        ..., title="study_visit_uid", description="The related study visit uid"
    )


class StudyActivityScheduleDeleteInput(BaseModel):
    uid: str = Field(
        ..., title="uid", description="UID of the study activity schedule to delete"
    )


class StudyActivityScheduleBatchInput(BaseModel):
    method: str = METHOD_FIELD
    content: StudyActivityScheduleCreateInput | StudyActivityScheduleDeleteInput


class StudyActivityScheduleBatchOutput(BaseModel):
    response_code: int = RESPONSE_CODE_FIELD
    content: StudyActivitySchedule | None | BatchErrorResponse


# Study design cells


class StudyDesignCell(BaseModel):
    class Config:
        orm_mode = True

    study_uid: str = STUDY_UID_FIELD

    study_version: str | None = Field(
        None,
        title="study version or date information",
        description="Study version number, if specified, otherwise None",
    )

    design_cell_uid: str | None = Field(
        None,
        title="design_cell_uid",
        description="uid for the study cell",
        source="uid",
        nullable=True,
    )

    study_arm_uid: str | None = Field(
        None,
        title="study_arm_uid",
        description=STUDY_ARM_UID_DESC,
        source="study_arm.uid",
        nullable=True,
    )

    study_arm_name: str | None = Field(
        None,
        title="study_arm_name",
        description="the name of the related study arm",
        source="study_arm.name",
        nullable=True,
    )

    study_branch_arm_uid: str | None = Field(
        None,
        title="study_branch_arm_uid",
        description=STUDY_BRANCH_ARM_UID_DESC,
        source="study_branch_arm.uid",
        nullable=True,
    )

    study_branch_arm_name: str | None = Field(
        None,
        title="study_branch_arm_name",
        description="the name of the related study branch arm",
        source="study_branch_arm.name",
        nullable=True,
    )

    study_epoch_uid: str = Field(
        ...,
        title="study_epoch_uid",
        description=STUDY_EPOCH_UID_DESC,
        source="study_epoch.uid",
    )

    study_epoch_name: str = Field(
        ...,
        title="study_epoch_name",
        description="the name of the related study epoch",
        source="study_epoch.has_epoch.has_name_root.has_latest_value.name",
    )

    study_element_uid: str = Field(
        ...,
        title="study_element_uid",
        description=STUDY_ELEMENT_UID_DESC,
        source="study_element.uid",
    )

    study_element_name: str = Field(
        ...,
        title="study_element_name",
        description="the name of the related study element",
        source="study_element.name",
    )

    transition_rule: str | None = Field(
        None,
        title="transition_rule",
        description=TRANSITION_RULE_DESC,
        nullable=True,
    )

    start_date: datetime | None = Field(
        ...,
        title="start_date",
        description=START_DATE_DESC,
        source=AFTER_DATE_QUALIFIER,
    )

    user_initials: str | None = Field(
        None,
        title="user_initials",
        description=USER_INITIALS_DESC,
        source=AFTER_USER_QUALIFIER,
        nullable=True,
    )

    end_date: datetime | None = END_DATE_FIELD

    order: int | None = Field(
        None, title="order", description=ORDER_DESC, nullable=True
    )

    @classmethod
    def from_vo(
        cls,
        design_cell_vo: StudyDesignCellVO,
        study_value_version: str | None = None,
    ) -> Self:
        return cls(
            design_cell_uid=design_cell_vo.uid,
            study_uid=design_cell_vo.study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            study_arm_uid=design_cell_vo.study_arm_uid,
            study_arm_name=design_cell_vo.study_arm_name,
            study_branch_arm_uid=design_cell_vo.study_branch_arm_uid,
            study_branch_arm_name=design_cell_vo.study_branch_arm_name,
            study_epoch_uid=design_cell_vo.study_epoch_uid,
            study_epoch_name=design_cell_vo.study_epoch_name,
            study_element_uid=design_cell_vo.study_element_uid,
            study_element_name=design_cell_vo.study_element_name,
            transition_rule=design_cell_vo.transition_rule,
            start_date=design_cell_vo.start_date,
            user_initials=design_cell_vo.user_initials,
            order=design_cell_vo.order,
        )


class StudyDesignCellHistory(BaseModel):
    study_uid: str = Field(..., title="study_uid", description=STUDY_UID_DESC)

    study_design_cell_uid: str = Field(
        ..., title="study_design_cell_uid", description="uid for the study design cell"
    )

    study_arm_uid: str | None = Field(
        None, title="study_arm_uid", description=STUDY_ARM_UID_DESC
    )

    study_branch_arm_uid: str | None = Field(
        None,
        title="study_branch_arm_uid",
        description=STUDY_BRANCH_ARM_UID_DESC,
    )

    study_epoch_uid: str = Field(
        ..., title="study_epoch_uid", description=STUDY_EPOCH_UID_DESC
    )

    study_element_uid: str = Field(
        None,
        title="study_element_uid",
        description=STUDY_ELEMENT_UID_DESC,
    )

    transition_rule: str = Field(
        None, title="transition_rule", description=TRANSITION_RULE_DESC
    )

    change_type: str | None = CHANGE_TYPE_FIELD

    modified: datetime | None = Field(
        None, title="modified", description="Date of last modification"
    )

    order: int | None = Field(
        None,
        title="order",
        description=ORDER_DESC,
    )


class StudyDesignCellVersion(StudyDesignCellHistory):
    changes: dict


class StudyDesignCellCreateInput(BaseModel):
    study_arm_uid: str | None = Field(
        None, title="study_arm_uid", description=STUDY_ARM_UID_DESC
    )

    study_branch_arm_uid: str | None = Field(
        None,
        title="study_branch_arm_uid",
        description=STUDY_BRANCH_ARM_UID_DESC,
    )

    study_epoch_uid: str = Field(
        ..., title="study_epoch_uid", description=STUDY_EPOCH_UID_DESC
    )

    study_element_uid: str = Field(
        ...,
        title="study_element_uid",
        description=STUDY_ELEMENT_UID_DESC,
    )

    transition_rule: str | None = Field(
        None,
        title="transition_rule",
        description="Optionally, a transition rule for the cell",
    )

    order: int | None = Field(
        None,
        title="order",
        description=ORDER_DESC,
    )


class StudyDesignCellEditInput(BaseModel):
    study_design_cell_uid: str = Field(
        ..., title="study_design_cell_uid", description="uid for the study design cell"
    )
    study_arm_uid: str | None = Field(
        None, title="study_arm_uid", description=STUDY_ARM_UID_DESC
    )
    study_branch_arm_uid: str | None = Field(
        None,
        title="study_branch_arm_uid",
        description=STUDY_BRANCH_ARM_UID_DESC,
    )
    study_element_uid: str | None = Field(
        None,
        title="study_element_uid",
        description=STUDY_ELEMENT_UID_DESC,
    )
    order: int | None = Field(
        None,
        title="order",
        description=ORDER_DESC,
    )
    transition_rule: str | None = Field(
        None,
        title="transition_rule",
        description=TRANSITION_RULE_DESC,
    )


class StudyDesignCellDeleteInput(BaseModel):
    uid: str = Field(
        ..., title="uid", description="UID of the study design cell to delete"
    )


class StudyDesignCellBatchInput(BaseModel):
    method: str = METHOD_FIELD
    content: (
        StudyDesignCellCreateInput
        | StudyDesignCellDeleteInput
        | StudyDesignCellEditInput
    )


class StudyDesignCellBatchOutput(BaseModel):
    response_code: int = RESPONSE_CODE_FIELD
    content: StudyDesignCell | None | BatchErrorResponse


# Study brancharms without ArmRoot


class StudySelectionBranchArmWithoutStudyArm(StudySelection):
    branch_arm_uid: str | None = Field(
        ...,
        title="study_branch_arm_uid",
        description="uid for the study BranchArm",
    )

    name: str = Field(
        ...,
        title="study_branch_arm_name",
        description="name for the study Brancharm",
    )

    short_name: str = Field(
        ...,
        title="study_branch_arm_short_name",
        description="short name for the study Brancharm",
    )

    code: str | None = Field(
        None,
        title="study_branch_arm_code",
        description="code for the study Brancharm",
        nullable=True,
    )

    description: str | None = Field(
        None,
        title="study_branch_arm_description",
        description="description for the study Brancharm",
        nullable=True,
    )

    colour_code: str | None = Field(
        None,
        title="study_branch_armcolour_code",
        description="colour_code for the study Brancharm",
        nullable=True,
    )

    randomization_group: str | None = Field(
        None,
        title="study_branch_arm_randomization_group",
        description="randomization group for the study Brancharm",
        nullable=True,
    )

    number_of_subjects: int | None = Field(
        None,
        title="study_branch_arm_number_of_subjects",
        description="number of subjects for the study Brancharm",
    )

    start_date: datetime | None = Field(
        ...,
        title="start_date",
        description=START_DATE_DESC,
    )

    user_initials: str | None = Field(
        None,
        title="user_initials",
        description=USER_INITIALS_DESC,
        nullable=True,
    )

    end_date: datetime | None = END_DATE_FIELD

    status: str | None = STATUS_FIELD

    change_type: str | None = CHANGE_TYPE_FIELD

    accepted_version: bool | None = Field(
        None,
        title=ACCEPTED_VERSION_DESC,
        description="Denotes if user accepted obsolete branch arm versions",
        nullable=True,
    )

    @classmethod
    def from_study_selection_branch_arm_ar_and_order(
        cls,
        study_uid: str,
        selection: StudySelectionBranchArmVO,
        order: int,
    ):
        return cls(
            study_uid=study_uid,
            branch_arm_uid=selection.study_selection_uid,
            name=selection.name,
            short_name=selection.short_name,
            code=selection.code,
            description=selection.description,
            colour_code=selection.colour_code,
            order=order,
            randomization_group=selection.randomization_group,
            number_of_subjects=selection.number_of_subjects,
            start_date=selection.start_date,
            user_initials=selection.user_initials,
            end_date=selection.end_date,
            status=selection.status,
            change_type=selection.change_type,
            accepted_version=selection.accepted_version,
        )


# Study arms


class StudySelectionArm(StudySelection):
    arm_uid: str | None = Field(
        ...,
        title="study_arm_uid",
        description=ARM_UID_DESC,
    )

    name: str = Field(
        ...,
        title="study_arm_name",
        description="name for the study arm",
    )

    short_name: str = Field(
        ...,
        title="study_arm_short_name",
        description="short name for the study arm",
    )

    code: str | None = Field(
        None,
        title="study_arm_code",
        description="code for the study arm",
        nullable=True,
    )

    description: str | None = Field(
        None,
        title="study_arm_description",
        description="description for the study arm",
        nullable=True,
    )

    arm_colour: str | None = Field(
        None,
        title="study_arm_colour",
        description="colour for the study arm",
        nullable=True,
    )

    randomization_group: str | None = Field(
        None,
        title="study_arm_randomization_group",
        description="randomization group for the study arm",
        nullable=True,
    )

    number_of_subjects: int | None = Field(
        None,
        title="study_arm_number_of_subjects",
        description="number of subjects for the study arm",
        nullable=True,
    )

    arm_type: CTTermName | None = Field(
        None,
        title="study_arm_type",
        description="type for the study arm",
        nullable=True,
    )

    start_date: datetime | None = Field(
        ...,
        title="start_date",
        description=START_DATE_DESC,
    )

    user_initials: str | None = Field(
        None,
        title="user_initials",
        description=USER_INITIALS_DESC,
        nullable=True,
    )

    end_date: datetime | None = END_DATE_FIELD

    status: str | None = STATUS_FIELD

    change_type: str | None = CHANGE_TYPE_FIELD

    accepted_version: bool | None = Field(
        None,
        title=ACCEPTED_VERSION_DESC,
        description="Denotes if user accepted obsolete arm versions",
        nullable=True,
    )

    @classmethod
    def from_study_selection_arm_ar_and_order(
        cls,
        study_uid: str,
        selection: StudySelectionArmVO,
        order: int,
        find_simple_term_arm_type_by_term_uid: Callable,
        terms_at_specific_datetime: datetime | None,
    ):
        if selection.arm_type_uid:
            arm_type_call_back = find_simple_term_arm_type_by_term_uid(
                term_uid=selection.arm_type_uid,
                at_specific_date=terms_at_specific_datetime,
            )
        else:
            arm_type_call_back = None

        return cls(
            study_uid=study_uid,
            arm_uid=selection.study_selection_uid,
            name=selection.name,
            short_name=selection.short_name,
            code=selection.code,
            description=selection.description,
            arm_colour=selection.arm_colour,
            order=order,
            randomization_group=selection.randomization_group,
            number_of_subjects=selection.number_of_subjects,
            arm_type=arm_type_call_back,
            start_date=selection.start_date,
            user_initials=selection.user_initials,
            end_date=selection.end_date,
            status=selection.status,
            change_type=selection.change_type,
            accepted_version=selection.accepted_version,
        )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: SelectionHistoryArm,
        study_uid: str,
        get_ct_term_arm_type: Callable[[str], CTTermName],
    ) -> Self:
        if study_selection_history.arm_type:
            arm_type_call_back = get_ct_term_arm_type(study_selection_history.arm_type)
        else:
            arm_type_call_back = None

        return cls(
            study_uid=study_uid,
            order=study_selection_history.order,
            arm_uid=study_selection_history.study_selection_uid,
            name=study_selection_history.arm_name,
            short_name=study_selection_history.arm_short_name,
            code=study_selection_history.arm_code,
            description=study_selection_history.arm_description,
            arm_colour=study_selection_history.arm_colour,
            randomization_group=study_selection_history.arm_randomization_group,
            number_of_subjects=study_selection_history.arm_number_of_subjects,
            arm_type=arm_type_call_back,
            start_date=study_selection_history.start_date,
            user_initials=study_selection_history.user_initials,
            end_date=study_selection_history.end_date,
            status=study_selection_history.status,
            change_type=study_selection_history.change_type,
            accepted_version=study_selection_history.accepted_version,
        )


class StudySelectionArmWithConnectedBranchArms(StudySelectionArm):
    arm_connected_branch_arms: list[
        StudySelectionBranchArmWithoutStudyArm
    ] | None = Field(
        None,
        title="study_branch_arms",
        description="lsit of study branch arms connected to arm",
        nullable=True,
    )

    @classmethod
    def from_study_selection_arm_ar__order__connected_branch_arms(
        cls,
        study_uid: str,
        selection: StudySelectionArmVO,
        order: int,
        find_simple_term_arm_type_by_term_uid: Callable,
        find_multiple_connected_branch_arm: Callable,
        terms_at_specific_datetime: datetime | None,
        study_value_version: str | None = None,
    ):
        if selection.arm_type_uid:
            arm_type_call_back = find_simple_term_arm_type_by_term_uid(
                term_uid=selection.arm_type_uid,
                at_specific_date=terms_at_specific_datetime,
            )
        else:
            arm_type_call_back = None

        return cls(
            study_uid=study_uid,
            arm_uid=selection.study_selection_uid,
            name=selection.name,
            short_name=selection.short_name,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            code=selection.code,
            description=selection.description,
            arm_colour=selection.arm_colour,
            order=order,
            randomization_group=selection.randomization_group,
            number_of_subjects=selection.number_of_subjects,
            arm_type=arm_type_call_back,
            arm_connected_branch_arms=find_multiple_connected_branch_arm(
                study_uid=study_uid,
                study_arm_uid=selection.study_selection_uid,
                user_initials=selection.user_initials,
                study_value_version=study_value_version,
            ),
            start_date=selection.start_date,
            user_initials=selection.user_initials,
            end_date=selection.end_date,
            status=selection.status,
            change_type=selection.change_type,
            accepted_version=selection.accepted_version,
        )


class StudySelectionArmCreateInput(BaseModel):
    name: str = Field(
        None,
        title="study_arm_name",
        description="name for the study arm",
    )

    short_name: str = Field(
        None,
        title="study_arm_short_name",
        description="short name for the study arm",
    )

    code: str | None = Field(
        None,
        title="study_arm_code",
        description="code for the study arm",
    )

    description: str | None = Field(
        None,
        title="study_description",
        description="description for the study arm",
    )

    arm_colour: str | None = Field(
        None,
        title="study_arm_colour",
        description="colour for the study arm",
    )

    randomization_group: str | None = Field(
        None,
        title="study_arm_randomization_group",
        description="randomization group for the study arm",
    )

    number_of_subjects: int | None = Field(
        None,
        title="study_arm_number_of_subjects",
        description="number of subjects for the study arm",
    )

    arm_type_uid: str | None = Field(
        None,
        title="study_arm_type_uid",
        description=ARM_UID_DESC,
    )


class StudySelectionArmInput(StudySelectionArmCreateInput):
    arm_uid: str = Field(
        None,
        title="study_arm_uid",
        description=ARM_UID_DESC,
    )


class StudySelectionArmNewOrder(BaseModel):
    new_order: int = Field(
        ...,
        title="new_order",
        description="new order of the selected arm",
    )


class StudySelectionArmVersion(StudySelectionArm):
    changes: dict


# Study Activity Instructions


class StudyActivityInstruction(BaseModel):
    class Config:
        orm_mode = True

    study_activity_instruction_uid: str | None = Field(
        ...,
        title="study_activity_instruction_uid",
        description="uid for the study activity instruction",
        source="uid",
    )

    study_uid: str = STUDY_UID_FIELD

    study_version: str | None = Field(
        None,
        title="study version or date information",
        description="Study version number, if specified, otherwise None",
    )
    study_version: str | None = Field(
        None,
        title="study version or date information",
        description="Study version number, if specified, otherwise None.",
    )
    study_activity_uid: str | None = Field(
        ...,
        title="study_activity_uid",
        description=STUDY_ACTIVITY_UID_DESC,
        source="study_activity.uid",
    )

    activity_instruction_uid: str = Field(
        title="activity_instruction_uid",
        description="The related activity instruction UID",
        source="activity_instruction_value.activity_instruction_root.uid",
    )

    activity_instruction_name: str = Field(
        title="activity_instruction_name",
        description="The related activity instruction name",
        source="activity_instruction_value.name",
    )

    start_date: datetime | None = Field(
        ...,
        title="start_date",
        description=START_DATE_DESC,
        source=AFTER_DATE_QUALIFIER,
    )

    user_initials: str | None = Field(
        ...,
        title="user_initials",
        description=USER_INITIALS_DESC,
        source=AFTER_USER_QUALIFIER,
    )

    end_date: datetime | None = END_DATE_FIELD

    @classmethod
    def from_vo(
        cls,
        instruction_vo: StudyActivityInstructionVO,
        study_value_version: str | None = None,
    ) -> Self:
        return cls(
            study_activity_instruction_uid=instruction_vo.uid,
            study_uid=instruction_vo.study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            study_activity_uid=instruction_vo.study_activity_uid,
            activity_instruction_name=instruction_vo.activity_instruction_name,
            activity_instruction_uid=instruction_vo.activity_instruction_uid,
            start_date=instruction_vo.start_date,
            user_initials=instruction_vo.user_initials,
        )


class StudyActivityInstructionCreateInput(BaseModel):
    activity_instruction_data: ActivityInstructionCreateInput | None = Field(
        None,
        title="activity_instruction_data",
        description="Data to create new activity instruction",
    )

    activity_instruction_uid: str | None = Field(
        None,
        title="activity_instruction_uid",
        description="The uid of an existing activity instruction",
    )

    study_activity_uid: str = Field(
        ..., title="study_activity_uid", description=STUDY_ACTIVITY_UID_DESC
    )

    @root_validator(pre=False)
    @classmethod
    def check_required_fields(cls, values):
        data, uid = values.get("activity_instruction_data"), values.get(
            "activity_instruction_uid"
        )
        if not data and not uid:
            raise ValueError(
                "You must provide activity_instruction_data or activity_instruction_uid"
            )
        return values


class StudyActivityInstructionDeleteInput(BaseModel):
    study_activity_instruction_uid: str | None = Field(
        ...,
        title="study_activity_instruction_uid",
        description="uid for the study activity instruction",
        source="uid",
    )


class StudyActivityInstructionBatchInput(BaseModel):
    method: str = METHOD_FIELD
    content: StudyActivityInstructionCreateInput | StudyActivityInstructionDeleteInput


class StudyActivityInstructionBatchOutput(BaseModel):
    response_code: int = RESPONSE_CODE_FIELD
    content: StudyActivityInstruction | None | BatchErrorResponse


# Study elements


class StudySelectionElement(StudySelection):
    element_uid: str | None = Field(
        ...,
        title="study_element_uid",
        description=ELEMENT_UID_DESC,
    )

    name: str | None = Field(
        ...,
        title="study_element_name",
        description="name for the study element",
    )

    short_name: str | None = Field(
        ...,
        title="study_element_short_name",
        description="short name for the study element",
    )

    code: str | None = Field(
        ...,
        title="study_element_code",
        description="code for the study element",
    )

    description: str | None = Field(
        ...,
        title="study_element_description",
        description="description for the study element",
    )

    planned_duration: DurationJsonModel | None = Field(
        ...,
        title="study_element_planned_duration",
        description="planned_duration for the study element",
    )

    start_rule: str | None = Field(
        ...,
        title="study_element_start_rule",
        description="start_rule for the study element",
    )

    end_rule: str | None = Field(
        ...,
        title="study_element_end_rule",
        description="end_rule for the study element",
    )

    element_colour: str | None = Field(
        ...,
        title="study_elementelement_colour",
        description="element_colour for the study element",
    )

    element_subtype: CTTermName | None = Field(
        ..., title="study_element_subtype", description="subtype for the study element"
    )

    element_type: CTTermName | None = Field(
        ..., title="study_element_type", description="type for the study element"
    )

    study_compound_dosing_count: int | None = Field(
        None,
        description="Number of compound dosing linked to Study Element",
        nullable=True,
    )

    start_date: datetime | None = Field(
        ...,
        title="start_date",
        description=START_DATE_DESC,
    )

    user_initials: str | None = Field(
        ..., title="user_initials", description=USER_INITIALS_DESC
    )

    end_date: datetime | None = END_DATE_FIELD

    status: str | None = STATUS_FIELD

    change_type: str | None = CHANGE_TYPE_FIELD

    accepted_version: bool | None = Field(
        None,
        title=ACCEPTED_VERSION_DESC,
        description="Denotes if user accepted obsolete element versions",
        nullable=True,
    )

    @classmethod
    def from_study_selection_element_ar_and_order(
        cls,
        study_uid: str,
        selection: StudySelectionElementVO,
        order: int,
        find_simple_term_element_by_term_uid: Callable[[str], CTTermName],
        get_term_element_type_by_element_subtype: Callable[[str], CTTermName],
        find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
        terms_at_specific_datetime: datetime | None,
        study_value_version: str | None = None,
    ) -> Self:
        element_subtype = find_simple_term_element_by_term_uid(
            selection.element_subtype_uid, at_specific_date=terms_at_specific_datetime
        )
        term_element_type = get_term_element_type_by_element_subtype(
            selection.element_subtype_uid
        )
        element_type = (
            find_simple_term_element_by_term_uid(
                term_element_type,
                at_specific_date=terms_at_specific_datetime,
            )
            if term_element_type
            else None
        )
        return cls(
            study_uid=study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            element_uid=selection.study_selection_uid,
            name=selection.name,
            short_name=selection.short_name,
            code=selection.code,
            description=selection.description,
            planned_duration=(
                DurationJsonModel.from_duration_object(
                    duration=selection.planned_duration,
                    find_all_study_time_units=find_all_study_time_units,
                )
                if selection.planned_duration is not None
                else None
            ),
            start_rule=selection.start_rule,
            end_rule=selection.end_rule,
            element_colour=selection.element_colour,
            order=order,
            element_subtype=element_subtype,
            element_type=element_type,
            study_compound_dosing_count=selection.study_compound_dosing_count,
            start_date=selection.start_date,
            user_initials=selection.user_initials,
            end_date=selection.end_date,
            status=selection.status,
            change_type=selection.change_type,
            accepted_version=selection.accepted_version,
        )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: SelectionHistoryElement,
        study_uid: str,
        get_ct_term_element_subtype: Callable[[str], CTTermName],
        get_term_element_type_by_element_subtype: Callable[[str], CTTermName],
        find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
    ) -> Self:
        element_subtype = get_ct_term_element_subtype(
            study_selection_history.element_subtype
        )
        element_type = (
            get_ct_term_element_subtype(
                get_term_element_type_by_element_subtype(
                    study_selection_history.element_subtype
                )
            )
            if get_term_element_type_by_element_subtype(
                study_selection_history.element_subtype
            )
            else None
        )
        return cls(
            study_uid=study_uid,
            order=study_selection_history.order,
            element_uid=study_selection_history.study_selection_uid,
            name=study_selection_history.element_name,
            short_name=study_selection_history.element_short_name,
            code=study_selection_history.element_code,
            description=study_selection_history.element_description,
            planned_duration=(
                DurationJsonModel.from_duration_object(
                    duration=study_selection_history.element_planned_duration,
                    find_all_study_time_units=find_all_study_time_units,
                )
                if study_selection_history.element_planned_duration is not None
                else None
            ),
            start_rule=study_selection_history.element_start_rule,
            end_rule=study_selection_history.element_end_rule,
            element_colour=study_selection_history.element_colour,
            element_subtype=element_subtype,
            element_type=element_type,
            start_date=study_selection_history.start_date,
            user_initials=study_selection_history.user_initials,
            end_date=study_selection_history.end_date,
            status=study_selection_history.status,
            change_type=study_selection_history.change_type,
            accepted_version=study_selection_history.accepted_version,
        )


class StudySelectionElementCreateInput(BaseModel):
    name: str = Field(
        None,
        title="study_element_name",
        description="name for the study element",
    )

    short_name: str = Field(
        None,
        title="study_element_short_name",
        description="short name for the study element",
    )

    code: str | None = Field(
        None,
        title="study_element_code",
        description="code for the study element",
    )

    description: str | None = Field(
        None,
        title="study_description",
        description="description for the study element",
    )

    planned_duration: DurationJsonModel | None = Field(
        None,
        title="study_element_planned_duration",
        description="planned_duration for the study element",
    )

    start_rule: str | None = Field(
        None,
        title="study_element_start_rule",
        description="start_rule for the study element",
    )

    end_rule: str | None = Field(
        None,
        title="study_element_end_rule",
        description="end_rule for the study element",
    )

    element_colour: str | None = Field(
        None,
        title="studyelement_colour",
        description="element_colour for the study element",
    )

    element_subtype_uid: str = Field(
        None,
        title="study_element_subtype_uid",
        description=ELEMENT_UID_DESC,
    )


class StudySelectionElementInput(StudySelectionElementCreateInput):
    element_uid: str = Field(
        None,
        title="study_element_uid",
        description=ELEMENT_UID_DESC,
    )

    @classmethod
    def from_study_selection_element(
        cls,
        selection: StudySelectionElementVO,
        find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
    ) -> Self:
        return cls(
            element_uid=selection.study_selection_uid,
            name=selection.name,
            short_name=selection.short_name,
            code=selection.code,
            description=selection.description,
            planned_duration=(
                DurationJsonModel.from_duration_object(
                    duration=selection.planned_duration,
                    find_all_study_time_units=find_all_study_time_units,
                )
                if selection.planned_duration is not None
                else None
            ),
            start_rule=selection.start_rule,
            end_rule=selection.end_rule,
            element_colour=selection.element_colour,
            element_subtype_uid=selection.element_subtype_uid,
        )


class StudyElementTypes(BaseModel):
    type: str = Field(..., title="Type uid", description="Element type uid")
    type_name: str = Field(..., title="Type name", description="Element type name")
    subtype: str = Field(..., title="Subtype", description="Element subtype uid")
    subtype_name: str = Field(
        ..., title="Subtype name", description="Element subtype name"
    )


class StudySelectionElementNewOrder(BaseModel):
    new_order: int = Field(
        ...,
        title="new_order",
        description="new order of the selected element",
    )


class StudySelectionElementVersion(StudySelectionElement):
    changes: dict


# Study brancharms adding Arm Root parameter


class StudySelectionBranchArm(StudySelectionBranchArmWithoutStudyArm):
    arm_root: StudySelectionArm = Field(
        ..., title="study_arm_root", description="Root for the study branch arm"
    )

    @classmethod
    def from_study_selection_branch_arm_ar_and_order(
        cls,
        study_uid: str,
        selection: StudySelectionBranchArmVO,
        order: int,
        find_simple_term_branch_arm_root_by_term_uid: Callable,
        terms_at_specific_datetime: datetime | None,
        study_value_version: str | None = None,
    ):
        return cls(
            study_uid=study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            branch_arm_uid=selection.study_selection_uid,
            name=selection.name,
            short_name=selection.short_name,
            code=selection.code,
            description=selection.description,
            colour_code=selection.colour_code,
            order=order,
            randomization_group=selection.randomization_group,
            number_of_subjects=selection.number_of_subjects,
            arm_root=find_simple_term_branch_arm_root_by_term_uid(
                study_uid=study_uid,
                study_selection_uid=selection.arm_root_uid,
                study_value_version=study_value_version,
                terms_at_specific_datetime=terms_at_specific_datetime,
            ),
            start_date=selection.start_date,
            user_initials=selection.user_initials,
            end_date=selection.end_date,
            status=selection.status,
            change_type=selection.change_type,
            accepted_version=selection.accepted_version,
        )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: SelectionHistoryBranchArm,
        study_uid: str,
        find_simple_term_branch_arm_root_by_term_uid: Callable[[str], CTTermName],
    ) -> Self:
        return cls(
            study_uid=study_uid,
            order=study_selection_history.order,
            branch_arm_uid=study_selection_history.study_selection_uid,
            name=study_selection_history.branch_arm_name,
            short_name=study_selection_history.branch_arm_short_name,
            code=study_selection_history.branch_arm_code,
            description=study_selection_history.branch_arm_description,
            colour_code=study_selection_history.branch_arm_colour_code,
            randomization_group=study_selection_history.branch_arm_randomization_group,
            number_of_subjects=study_selection_history.branch_arm_number_of_subjects,
            arm_root=find_simple_term_branch_arm_root_by_term_uid(
                study_uid, study_selection_history.arm_root
            ),
            start_date=study_selection_history.start_date,
            user_initials=study_selection_history.user_initials,
            end_date=study_selection_history.end_date,
            status=study_selection_history.status,
            change_type=study_selection_history.change_type,
            accepted_version=study_selection_history.accepted_version,
        )


class StudySelectionBranchArmHistory(StudySelectionBranchArmWithoutStudyArm):
    """
    Class created to describe Study BranchArm History, it specifies the ArmRootUid instead of ArmRoot to handle non longer existent Arms
    """

    arm_root_uid: str = Field(
        ..., title="study_arm_root_uid", description="Uid Root for the study branch arm"
    )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: SelectionHistoryBranchArm,
        study_uid: str,
    ) -> Self:
        return cls(
            study_uid=study_uid,
            order=study_selection_history.order,
            branch_arm_uid=study_selection_history.study_selection_uid,
            name=study_selection_history.branch_arm_name,
            short_name=study_selection_history.branch_arm_short_name,
            code=study_selection_history.branch_arm_code,
            description=study_selection_history.branch_arm_description,
            colour_code=study_selection_history.branch_arm_colour_code,
            randomization_group=study_selection_history.branch_arm_randomization_group,
            number_of_subjects=study_selection_history.branch_arm_number_of_subjects,
            arm_root_uid=study_selection_history.arm_root,
            start_date=study_selection_history.start_date,
            user_initials=study_selection_history.user_initials,
            end_date=study_selection_history.end_date,
            status=study_selection_history.status,
            change_type=study_selection_history.change_type,
            accepted_version=study_selection_history.accepted_version,
        )


class StudySelectionBranchArmCreateInput(BaseModel):
    name: str = Field(
        None,
        title="study_branch_arm_name",
        description="name for the study Brancharm",
    )

    short_name: str = Field(
        None,
        title="study_branch_arm_short_name",
        description="short name for the study Brancharm",
    )

    code: str | None = Field(
        None,
        title="study_branch_arm_code",
        description="code for the study Brancharm",
    )

    description: str | None = Field(
        None,
        title="study_description",
        description="description for the study Brancharm",
    )

    colour_code: str | None = Field(
        None,
        title="studycolour_code",
        description="colour_code for the study Brancharm",
    )

    randomization_group: str | None = Field(
        None,
        title="study_branch_arm_randomization_group",
        description="randomization group for the study Brancharm",
    )

    number_of_subjects: int | None = Field(
        None,
        title="study_branch_arm_number_of_subjects",
        description="number of subjects for the study Brancharm",
    )

    arm_uid: str = Field(
        None,
        title="study_armt_uid",
        description=ARM_UID_DESC,
    )


class StudySelectionBranchArmEditInput(StudySelectionBranchArmCreateInput):
    branch_arm_uid: str = Field(
        None,
        title="study_branch_arm_uid",
        description="uid for the study branch arm",
    )


class StudySelectionBranchArmNewOrder(BaseModel):
    new_order: int = Field(
        ...,
        title="new_order",
        description="new order of the selected branch arm",
    )


class StudySelectionBranchArmVersion(StudySelectionBranchArmHistory):
    changes: dict


# Study cohorts


class StudySelectionCohortWithoutArmBranArmRoots(StudySelection):
    cohort_uid: str | None = Field(
        ...,
        title="study_cohort_uid",
        description="uid for the study Cohort",
    )

    name: str = Field(
        ...,
        title="study_cohort_name",
        description="name for the study Cohort",
    )

    short_name: str = Field(
        ...,
        title="study_cohort_short_name",
        description="short name for the study Cohort",
    )

    code: str | None = Field(
        None,
        title="study_cohort_code",
        description="code for the study Cohort",
        nullable=True,
    )

    description: str | None = Field(
        ...,
        title="study_cohort_description",
        description="description for the study Cohort",
    )

    colour_code: str | None = Field(
        ...,
        title="study_cohort_colour_code",
        description="colour code for the study Cohort",
    )

    number_of_subjects: int | None = Field(
        ...,
        title="study_cohort_number_of_subjects",
        description="number of subjects for the study Cohort",
    )

    start_date: datetime | None = Field(
        ...,
        title="start_date",
        description=START_DATE_DESC,
    )

    user_initials: str | None = Field(
        ..., title="user_initials", description=USER_INITIALS_DESC
    )

    end_date: datetime | None = END_DATE_FIELD

    status: str | None = STATUS_FIELD

    change_type: str | None = CHANGE_TYPE_FIELD

    accepted_version: bool | None = Field(
        None,
        title=ACCEPTED_VERSION_DESC,
        description="Denotes if user accepted obsolete cohort versions",
        nullable=True,
    )


class StudySelectionCohort(StudySelectionCohortWithoutArmBranArmRoots):
    branch_arm_roots: list[StudySelectionBranchArm] | None = Field(
        None,
        title="study_branch_arm_roots",
        description="Branch Arm Roots for the study Cohort",
    )

    arm_roots: list[StudySelectionArm] | None = Field(
        None, title="study_arm_roots", description="ArmRoots for the study Cohort"
    )

    @classmethod
    def from_study_selection_cohort_ar_and_order(
        cls,
        study_uid: str,
        selection: StudySelectionCohortVO,
        order: int,
        terms_at_specific_datetime: datetime | None,
        find_arm_root_by_uid: Callable | None = None,
        find_branch_arm_root_cohort_by_uid: Callable | None = None,
        study_value_version: str | None = None,
    ):
        """
        Factory method
        :param study_uid
        :param selection
        :param order
        :param find_project_by_study_uid
        :param find_arm_root_by_uid
        :param find_branch_arm_root_cohort_by_uid
        :return:
        """
        if selection.branch_arm_root_uids:
            branch_arm_roots = [
                find_branch_arm_root_cohort_by_uid(
                    study_uid,
                    branch_arm_root_uid,
                    study_value_version=study_value_version,
                    terms_at_specific_datetime=terms_at_specific_datetime,
                )
                for branch_arm_root_uid in selection.branch_arm_root_uids
            ]
        else:
            branch_arm_roots = None

        if selection.arm_root_uids:
            arm_roots = [
                find_arm_root_by_uid(
                    study_uid,
                    arm_root_uid,
                    study_value_version=study_value_version,
                    terms_at_specific_datetime=terms_at_specific_datetime,
                )
                for arm_root_uid in selection.arm_root_uids
            ]
        else:
            arm_roots = None

        return cls(
            study_uid=study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            cohort_uid=selection.study_selection_uid,
            name=selection.name,
            short_name=selection.short_name,
            code=selection.code,
            description=selection.description,
            order=order,
            colour_code=selection.colour_code,
            number_of_subjects=selection.number_of_subjects,
            branch_arm_roots=branch_arm_roots,
            arm_roots=arm_roots,
            start_date=selection.start_date,
            user_initials=selection.user_initials,
            end_date=selection.end_date,
            status=selection.status,
            change_type=selection.change_type,
            accepted_version=selection.accepted_version,
        )


class StudySelectionCohortHistory(StudySelectionCohortWithoutArmBranArmRoots):
    branch_arm_roots_uids: list[str] | None = Field(
        None,
        title="study_branch_arm_roots_uids",
        description="Branch Arm Roots Uids for the study Cohort",
    )

    arm_roots_uids: list[str] | None = Field(
        None,
        title="study_arm_roots_uids",
        description="ArmRoots Uids for the study Cohort",
    )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: SelectionHistoryCohort,
        study_uid: str,
    ) -> Self:
        if study_selection_history.branch_arm_roots:
            branch_arm_roots_uids = study_selection_history.branch_arm_roots
        else:
            branch_arm_roots_uids = None

        if study_selection_history.arm_roots:
            arm_roots_uids = study_selection_history.arm_roots
        else:
            arm_roots_uids = None

        return cls(
            study_uid=study_uid,
            order=study_selection_history.order,
            cohort_uid=study_selection_history.study_selection_uid,
            name=study_selection_history.cohort_name,
            short_name=study_selection_history.cohort_short_name,
            code=study_selection_history.cohort_code,
            description=study_selection_history.cohort_description,
            colour_code=study_selection_history.cohort_colour_code,
            number_of_subjects=study_selection_history.cohort_number_of_subjects,
            branch_arm_roots_uids=branch_arm_roots_uids,
            arm_roots_uids=arm_roots_uids,
            start_date=study_selection_history.start_date,
            user_initials=study_selection_history.user_initials,
            end_date=study_selection_history.end_date,
            status=study_selection_history.status,
            change_type=study_selection_history.change_type,
            accepted_version=study_selection_history.accepted_version,
        )


class StudySelectionCohortCreateInput(BaseModel):
    name: str = Field(
        None,
        title="study_cohort_name",
        description="name for the study Cohort",
    )

    short_name: str = Field(
        None,
        title="study_cohort_short_name",
        description="short name for the study Cohort",
    )

    code: str | None = Field(
        None,
        title="study_cohort_code",
        description="code for the study Cohort",
    )

    description: str | None = Field(
        None,
        title="study_description",
        description="description for the study Cohort",
    )

    colour_code: str | None = Field(
        None,
        title="study_cohort_colour_code",
        description="colour code for the study Cohort",
    )

    number_of_subjects: int | None = Field(
        None,
        title="study_cohort_number_of_subjects",
        description="number of subjects for the study Cohort",
    )

    branch_arm_uids: list[str] | None = Field(
        None,
        title="studybranch_arm_uid",
        description="uid for the study branch arm",
    )

    arm_uids: list[str] | None = Field(
        None,
        title="study_armt_uid",
        description=ARM_UID_DESC,
    )


class StudySelectionCohortEditInput(StudySelectionCohortCreateInput):
    cohort_uid: str = Field(
        None,
        title="study_cohort_uid",
        description="uid for the study Cohort",
    )


class StudySelectionCohortNewOrder(BaseModel):
    new_order: int = Field(
        ...,
        title="new_order",
        description="new order of the selected Cohort",
    )


class StudySelectionCohortVersion(StudySelectionCohortHistory):
    changes: dict


#
# Study compound dosing
#


class StudyCompoundDosing(StudySelection):
    study_compound_dosing_uid: str | None = Field(
        ...,
        title="study_compound_dosing_uid",
        description="uid for the study compound dosing",
    )

    study_compound: StudySelectionCompound = Field(
        ..., title="study_compound", description="The related study compound"
    )

    study_element: StudySelectionElement = Field(
        ..., title="study_element", description="The related study element"
    )

    dose_value: SimpleNumericValueWithUnit | None = Field(
        None,
        title="dose",
        description="compound dose defined for the study selection",
        nullable=True,
    )

    dose_frequency: SimpleTermModel | None = Field(
        None,
        title="dose_frequency",
        description="dose frequency defined for the study selection",
        nullable=True,
    )

    start_date: datetime | None = Field(
        ...,
        title="start_date",
        description=START_DATE_DESC,
    )

    user_initials: str | None = Field(
        None,
        title="user_initials",
        description=USER_INITIALS_DESC,
        nullable=True,
    )

    end_date: datetime | None = END_DATE_FIELD
    change_type: str | None = CHANGE_TYPE_FIELD

    @classmethod
    def from_vo(
        cls,
        compound_dosing_vo: StudyCompoundDosingVO,
        order: int,
        study_compound_model: StudySelectionCompound,
        study_element_model: StudySelectionElement,
        find_simple_term_model_name_by_term_uid: Callable,
        find_unit_by_uid: Callable[[str], UnitDefinitionAR | None],
        find_numeric_value_by_uid: Callable[[str], NumericValueWithUnitAR | None],
        terms_at_specific_datetime: datetime | None,
        study_value_version: str | None = None,
    ) -> Self:
        return cls(
            order=order,
            study_compound_dosing_uid=compound_dosing_vo.study_selection_uid,
            study_uid=compound_dosing_vo.study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            study_compound=study_compound_model,
            study_element=study_element_model,
            dose_value=SimpleNumericValueWithUnit.from_concept_uid(
                uid=compound_dosing_vo.dose_value_uid,
                find_unit_by_uid=find_unit_by_uid,
                find_numeric_value_by_uid=find_numeric_value_by_uid,
            ),
            dose_frequency=find_simple_term_model_name_by_term_uid(
                compound_dosing_vo.dose_frequency_uid,
                at_specific_date=terms_at_specific_datetime,
            ),
            start_date=compound_dosing_vo.start_date,
            user_initials=compound_dosing_vo.user_initials,
        )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: StudyCompoundDosingSelectionHistory,
        study_uid: str,
        order: int,
        study_compound_model: StudySelectionCompound,
        study_element_model: StudySelectionElement,
        find_simple_term_model_name_by_term_uid: Callable,
        find_unit_by_uid: Callable[[str], UnitDefinitionAR | None],
        find_numeric_value_by_uid: Callable[[str], NumericValueWithUnitAR | None],
    ) -> Self:
        return cls(
            study_compound_dosing_uid=study_selection_history.study_selection_uid,
            study_uid=study_uid,
            order=order,
            study_compound=study_compound_model,
            study_element=study_element_model,
            dose_value=SimpleNumericValueWithUnit.from_concept_uid(
                uid=study_selection_history.dose_value_uid,
                find_unit_by_uid=find_unit_by_uid,
                find_numeric_value_by_uid=find_numeric_value_by_uid,
            ),
            dose_frequency=find_simple_term_model_name_by_term_uid(
                study_selection_history.dose_frequency_uid
            ),
            start_date=study_selection_history.start_date,
            end_date=study_selection_history.end_date,
            change_type=study_selection_history.change_type,
            user_initials=study_selection_history.user_initials,
        )


class StudyCompoundDosingInput(BaseModel):
    study_compound_uid: str = Field(
        ...,
        title="study_compound_uid",
        description="The related study compound uid",
        min_length=1,
    )

    study_element_uid: str = Field(
        ...,
        title="study_element_uid",
        description="The related study element uid",
        min_length=1,
    )

    dose_value_uid: str | None = Field(
        None,
        title="dose_value_uid",
        description="compound dose defined for the study selection",
    )

    dose_frequency_uid: str | None = Field(
        None,
        title="dose_frequency_uid",
        description="dose frequency defined for the study selection",
    )
