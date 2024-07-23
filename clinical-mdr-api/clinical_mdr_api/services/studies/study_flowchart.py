import logging
from typing import Iterable, Mapping, Sequence

from docx.enum.style import WD_STYLE_TYPE
from neomodel import db

from clinical_mdr_api import config
from clinical_mdr_api.domains.study_selections.study_soa_footnote import SoAItemType
from clinical_mdr_api.exceptions import ValidationException
from clinical_mdr_api.models import (
    Footnote,
    StudyActivitySchedule,
    StudySelectionActivity,
    StudySelectionActivityInstance,
    StudyVisit,
)
from clinical_mdr_api.models.study_selections.study import (
    StudySoaPreferences,
    StudySoaPreferencesInput,
)
from clinical_mdr_api.models.study_selections.study_soa_footnote import StudySoAFootnote
from clinical_mdr_api.oauth.user import user
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_activity_instance_selection import (
    StudyActivityInstanceSelectionService,
)
from clinical_mdr_api.services.studies.study_activity_schedule import (
    StudyActivityScheduleService,
)
from clinical_mdr_api.services.studies.study_activity_selection import (
    StudyActivitySelectionService,
)
from clinical_mdr_api.services.studies.study_soa_footnote import StudySoAFootnoteService
from clinical_mdr_api.services.studies.study_visit import StudyVisitService
from clinical_mdr_api.services.utils.table_f import (
    Ref,
    SimpleFootnote,
    TableCell,
    TableRow,
    TableWithFootnotes,
)
from clinical_mdr_api.telemetry import trace_calls
from clinical_mdr_api.utils.iter import enumerate_letters

NUM_OPERATIONAL_CODE_ROWS = 2
SOA_CHECK_MARK = "X"

# Strings prepared for localization
_ = {
    "study_epoch": "",
    "protocol_section": "Protocol Section",
    "visit_short_name": "Visit short name",
    "study_week": "Study week",
    "study_day": "Study day",
    "visit_window": "Visit window (days)",
    "protocol_flowchart": "Protocol Flowchart",
    "no_study_group": "(not selected)",
    "no_study_subgroup": "(not selected)",
    "topic_code": "Topic Code",
    "adam_param_code": "ADaM Param Code",
}.get

log = logging.getLogger(__name__)

# pylint: disable=no-member
DOCX_STYLES = {
    "table": ("SB Table Condensed", WD_STYLE_TYPE.TABLE),
    "header1": ("Table Header lvl1", WD_STYLE_TYPE.PARAGRAPH),
    "header2": ("Table Header lvl2", WD_STYLE_TYPE.PARAGRAPH),
    "header3": ("Table Header lvl2", WD_STYLE_TYPE.PARAGRAPH),
    "header4": ("Table Header lvl2", WD_STYLE_TYPE.PARAGRAPH),
    "soaGroup": ("Table lvl 1", WD_STYLE_TYPE.PARAGRAPH),
    "group": ("Table lvl 2", WD_STYLE_TYPE.PARAGRAPH),
    "subGroup": ("Table lvl 3", WD_STYLE_TYPE.PARAGRAPH),
    "activity": ("Table lvl 4", WD_STYLE_TYPE.PARAGRAPH),
    "activityInstance": ("Table lvl 4", WD_STYLE_TYPE.PARAGRAPH),
    "cell": ("Table Text", WD_STYLE_TYPE.PARAGRAPH),
    "footnote": ("Table Text", WD_STYLE_TYPE.PARAGRAPH),
}


class StudyFlowchartService:
    """Assemble Study Protocol SoA Flowchart"""

    def __init__(self) -> None:
        self.user = user().id()

    @trace_calls
    def _validate_parameters(
        self,
        study_uid: str,
        study_value_version: str | None = None,
        time_unit: str | None = None,
    ):
        """
        Validates request parameters

        Raises NotFoundException if no Study with study_uid exists, or if Study does not have a version corresponding
        to optional study_value_version. Raises ValidationException if time_unit is not "day" or "week".

        Args:
            study_uid (str): The unique identifier of the study.
            study_value_version (str | None): The version of the study to check. Defaults to None.
            time_unit (str): The preferred time unit, either "day" or "week".
        """
        StudyService().check_if_study_uid_and_version_exists(
            study_uid, study_value_version=study_value_version
        )

        if time_unit not in (None, "day", "week"):
            raise ValidationException("time_unit has to be 'day' or 'week'")

    @trace_calls
    def _get_study_activity_schedules(
        self,
        study_uid: str,
        study_value_version: str | None = None,
        operational: bool = False,
    ) -> list[StudyActivitySchedule]:
        return StudyActivityScheduleService().get_all_schedules(
            study_uid,
            study_value_version=study_value_version,
            operational=operational,
        )

    @trace_calls
    def _get_study_visits(
        self, study_uid: str, study_value_version: str | None = None
    ) -> list[StudyVisit]:
        return (
            StudyVisitService(
                study_uid=study_uid, study_value_version=study_value_version
            )
            .get_all_visits(study_uid, study_value_version=study_value_version)
            .items
        )

    @trace_calls
    def _get_study_footnotes(
        self, study_uid: str, study_value_version: str | None = None
    ) -> list[StudySoAFootnote]:
        return (
            StudySoAFootnoteService()
            .get_all_by_study_uid(
                study_uid,
                sort_by={"order": True},
                study_value_version=study_value_version,
            )
            .items
        )

    @trace_calls
    def _get_study_activities(
        self, study_uid: str, study_value_version: str | None = None
    ) -> list[StudySelectionActivity]:
        return (
            StudyActivitySelectionService()
            .get_all_selection(
                study_uid,
                study_value_version=study_value_version,
                sort_by={"order": True},
            )
            .items
        )

    @trace_calls
    def _get_study_activity_instances(
        self, study_uid: str, study_value_version: str | None = None
    ) -> list[StudySelectionActivity]:
        return (
            StudyActivityInstanceSelectionService()
            .get_all_selection(
                study_uid,
                study_value_version=study_value_version,
                # filter-out activity placeholders
                filter_by={
                    "activity.library_name": {
                        "v": [config.REQUESTED_LIBRARY_NAME],
                        "op": "ne",
                    }
                },
            )
            .items
        )

    @staticmethod
    @trace_calls(args=[1], kwargs=["hide_soa_groups"])
    def _sort_study_activities(
        study_selection_activities: list[StudySelectionActivity],
        hide_soa_groups: bool = False,
    ):
        """Sort StudySelectionActivities in place, grouping by SoAGroup, ActivityGroup, ActivitySubgroup"""

        soa_groups = {}
        activity_groups = {}
        activity_subgroups = {}
        order_keys = {}

        for activity in study_selection_activities:
            key = []

            if hide_soa_groups and not getattr(
                activity, "show_soa_group_in_protocol_flowchart", None
            ):
                key.append(-1)

            else:
                key.append(
                    soa_groups.setdefault(
                        activity.study_soa_group.soa_group_term_uid, len(soa_groups)
                    )
                )

            key.append(
                activity_groups.setdefault(
                    activity.study_activity_group.activity_group_uid,
                    (
                        len(activity_groups)
                        if activity.study_activity_group.activity_group_uid
                        else -1
                    ),
                )
            )

            key.append(
                activity_subgroups.setdefault(
                    activity.study_activity_subgroup.activity_subgroup_uid,
                    len(activity_subgroups),
                )
            )

            order_keys[activity.study_activity_uid] = tuple(key)

        list.sort(
            study_selection_activities,
            key=lambda activity: order_keys.get(activity.study_activity_uid),
        )

    @staticmethod
    @trace_calls
    def _group_visits(
        visits: Iterable[StudyVisit],
    ) -> dict[str, dict[str, list[StudyVisit]]]:
        """
        Builds a graph of visits from nested dict of
        study_epoch_uid -> [ consecutive_visit_group | visit_uid ] -> [Visits]
        """

        grouped = {}
        visits: list[StudyVisit] = sorted(visits, key=lambda v: v.order)

        for visit in visits:
            grouped.setdefault(visit.study_epoch_uid, {}).setdefault(
                visit.consecutive_visit_group or visit.uid, []
            ).append(visit)

        return grouped

    @staticmethod
    @trace_calls
    def _mk_simple_footnotes(
        footnotes: Sequence[StudySoAFootnote],
    ) -> tuple[dict[str, list[str]], dict[str, Footnote]]:
        # mapping of referenced item uid to list of footnote symbols (to display in table cell)
        footnote_symbols_by_ref_uid: dict[str, list[str]] = {}

        # mapping of footnote symbols to SimpleFootnote model to print footnotes at end of document
        simple_footnotes_by_symbol: dict[str, Footnote] = {}
        for symbol, soa_footnote in enumerate_letters(footnotes):
            simple_footnotes_by_symbol[symbol] = SimpleFootnote(
                uid=soa_footnote.uid,
                text_html=(
                    soa_footnote.footnote.name
                    if soa_footnote.footnote
                    else soa_footnote.footnote_template.name
                ),
                text_plain=(
                    soa_footnote.footnote.name_plain
                    if soa_footnote.footnote
                    else soa_footnote.footnote_template.name_plain
                ),
            )

            for ref in soa_footnote.referenced_items:
                footnote_symbols_by_ref_uid.setdefault(ref.item_uid, []).append(symbol)

        return (
            footnote_symbols_by_ref_uid,
            simple_footnotes_by_symbol,
        )

    @trace_calls
    def get_flowchart_item_uid_coordinates(
        self, study_uid: str, study_value_version: str | None = None
    ) -> dict[str, tuple[int, int]]:
        """
        Returns mapping of item uid to [row, column] coordinates of item's position in the detailed SoA.

        Args:
            study_uid (str): The unique identifier of the study.
            study_value_version (str | None): The version of the study to check. Defaults to None.

        Returns:
            dict[str, tuple[int, int]: Mapping item uid to [row, column] coordinates
                                       of item's position in the protocol SoA flowchart.
        """

        self._validate_parameters(study_uid, study_value_version=study_value_version)

        study_activity_schedules: list[
            StudyActivitySchedule
        ] = self._get_study_activity_schedules(
            study_uid, study_value_version=study_value_version
        )

        # StudyActivitySchedules indexed by tuple of [StudyActivity.uid, StudyVisit.uid]
        study_activity_schedules_mapping = {
            (sas.study_activity_uid, sas.study_visit_uid): sas
            for sas in study_activity_schedules
        }

        study_selection_activities: list[
            StudySelectionActivity
        ] = self._get_study_activities(
            study_uid, study_value_version=study_value_version
        )

        self._sort_study_activities(study_selection_activities)

        visits: list[StudyVisit] = self._get_study_visits(
            study_uid, study_value_version=study_value_version
        )

        grouped_visits = self._group_visits(visits)

        coordinates = {}

        col = 1
        for study_epoch_uid, visit_groups in grouped_visits.items():
            coordinates[study_epoch_uid] = (0, col)
            for group in visit_groups.values():
                for visit in group:
                    coordinates[visit.uid] = (1, col)
                col += 1

        row = 4

        prev_soa_group_uid, soa_group_row = False, None
        prev_activity_group_uid, activity_group_row = False, None
        prev_activity_subgroup_uid, activity_subgroup_row = False, None

        study_selection_activity: StudySelectionActivity
        for study_selection_activity in study_selection_activities:
            soa_group_uid = study_selection_activity.study_soa_group.soa_group_term_uid

            if soa_group_uid != prev_soa_group_uid:
                prev_soa_group_uid, soa_group_row = soa_group_uid, row
                prev_activity_group_uid, activity_group_row = False, None
                prev_activity_subgroup_uid, activity_subgroup_row = False, None
                row += 1

            coordinates[
                study_selection_activity.study_soa_group.study_soa_group_uid
            ] = (soa_group_row, 0)

            activity_group_uid = (
                study_selection_activity.study_activity_group.activity_group_uid
            )

            if prev_activity_group_uid != activity_group_uid:
                prev_activity_group_uid, activity_group_row = activity_group_uid, row
                prev_activity_subgroup_uid, activity_subgroup_row = False, None
                row += 1

            if study_selection_activity.study_activity_group.study_activity_group_uid:
                coordinates[
                    study_selection_activity.study_activity_group.study_activity_group_uid
                ] = (activity_group_row, 0)

            activity_subgroup_uid = (
                study_selection_activity.study_activity_subgroup.activity_subgroup_uid
            )

            if prev_activity_subgroup_uid != activity_subgroup_uid:
                prev_activity_subgroup_uid = activity_subgroup_uid
                activity_subgroup_row = row
                row += 1

            if (
                study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid
            ):
                coordinates[
                    study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid
                ] = (activity_subgroup_row, 0)

            coordinates[study_selection_activity.study_activity_uid] = (
                row,
                0,
            )

            col = 0
            for visit_groups in grouped_visits.values():
                for group in visit_groups.values():
                    col += 1

                    for visit in group:
                        study_activity_schedule: StudyActivitySchedule = (
                            study_activity_schedules_mapping.get(
                                (study_selection_activity.study_activity_uid, visit.uid)
                            )
                        )

                        if study_activity_schedule:
                            coordinates[
                                study_activity_schedule.study_activity_schedule_uid
                            ] = (
                                row,
                                col,
                            )

            row += 1

        return coordinates

    @trace_calls
    def get_flowchart_table(
        self,
        study_uid: str,
        time_unit: str | None = None,
        study_value_version: str | None = None,
        operational: bool = False,
        hide_soa_groups: bool = False,
    ) -> TableWithFootnotes:
        """
        Builds protocol or operational SoA flowchart table

        Args:
            study_uid (str): The unique identifier of the study.
            time_unit (str): The preferred time unit, either "day" or "week".
            study_value_version (str | None): The version of the study to check. Defaults to None.
            operational (bool): Defaults to False, gets protocol SoA, or operational SoA when True.

        Returns:
            TableWithFootnotes: Protocol SoA flowchart table with footnotes.
        """

        soa_preferences = self._get_soa_preferences(
            study_uid, study_value_version=study_value_version
        )

        if not time_unit:
            time_unit = self.get_preferred_time_unit(
                study_uid, study_value_version=study_value_version
            )

        self._validate_parameters(
            study_uid, study_value_version=study_value_version, time_unit=time_unit
        )

        if operational:
            selection_activities: list[
                StudySelectionActivityInstance
            ] = self._get_study_activity_instances(
                study_uid, study_value_version=study_value_version
            )
        else:
            selection_activities: list[
                StudySelectionActivity
            ] = self._get_study_activities(
                study_uid, study_value_version=study_value_version
            )

        self._sort_study_activities(
            selection_activities, hide_soa_groups=hide_soa_groups
        )

        activity_schedules: list[
            StudyActivitySchedule
        ] = self._get_study_activity_schedules(
            study_uid,
            study_value_version=study_value_version,
            operational=operational,
        )

        # visible visits
        visits = {
            visit.uid: visit
            for visit in self._get_study_visits(
                study_uid, study_value_version=study_value_version
            )
            if visit.show_visit and visit.study_epoch_name != config.BASIC_EPOCH_NAME
        }
        # group visits in nested dict: study_epoch_uid -> [ consecutive_visit_group |  visit_uid ] -> [Visits]
        grouped_visits = self._group_visits(visits.values())

        # first 4 rows of protocol SoA flowchart contains epochs & visits
        header_rows = self._get_header_rows(
            grouped_visits, time_unit, soa_preferences, operational
        )

        # activity rows with grouping headers and check-marks
        activity_rows = self._get_activity_rows(
            selection_activities,
            activity_schedules,
            grouped_visits,
            operational,
            hide_soa_groups=hide_soa_groups,
        )

        table = TableWithFootnotes(
            rows=header_rows + activity_rows,
            num_header_rows=len(header_rows),
            num_header_cols=1,
            title=_("protocol_flowchart"),
        )

        if not operational:
            footnotes: list[StudySoAFootnote] = self._get_study_footnotes(
                study_uid, study_value_version=study_value_version
            )

            self.add_footnotes(table, footnotes)

        return table

    @staticmethod
    @trace_calls(args=[1, 2], kwargs=["time_unit", "operational"])
    def _get_header_rows(
        grouped_visits: dict[str, dict[str, list[StudyVisit]]],
        time_unit: str,
        soa_preferences: StudySoaPreferencesInput,
        operational: bool = False,
    ) -> list[TableRow]:
        """Builds the 4 header rows of protocol SoA flowchart"""

        if time_unit == "day":
            if soa_preferences.baseline_as_time_zero:
                visit_timing_prop = "study_duration_days"
            else:
                visit_timing_prop = "study_day_number"
        elif soa_preferences.baseline_as_time_zero:
            visit_timing_prop = "study_duration_weeks"
        else:
            visit_timing_prop = "study_week_number"

        rows = [TableRow() for _i in range(4)]

        # Header line-1: Epoch names
        rows[0].cells.append(TableCell(text=_("study_epoch"), style="header1"))
        rows[0].hide = not soa_preferences.show_epochs

        # Header line-2: Visit names
        rows[1].cells.append(TableCell(text=_("visit_short_name"), style="header2"))

        # Header line-3: Visit timing day/week sequence
        if time_unit == "day":
            rows[2].cells.append(TableCell(text=_("study_day"), style="header3"))
        else:
            rows[2].cells.append(TableCell(text=_("study_week"), style="header3"))

        # Header line-4: Visit window
        rows[3].cells.append(TableCell(text=_("visit_window"), style="header4"))

        # Add Operation SoA's extra columns
        if operational:
            rows[0].cells.append(TableCell(text=_("topic_code"), style="header2"))
            rows[0].cells.append(TableCell(text=_("adam_param_code"), style="header2"))
            for i in range(1, 4):
                for _j in range(NUM_OPERATIONAL_CODE_ROWS):
                    rows[i].cells.append(TableCell())

        perv_study_epoch_uid = None
        for study_epoch_uid, visit_groups in grouped_visits.items():
            for group in visit_groups.values():
                visit: StudyVisit = group[0]

                # Open new Epoch column
                if perv_study_epoch_uid != study_epoch_uid:
                    perv_study_epoch_uid = study_epoch_uid

                    rows[0].cells.append(
                        TableCell(
                            text=visit.study_epoch_name,
                            span=len(visit_groups),
                            style="header1",
                            refs=[
                                Ref(
                                    type_=SoAItemType.STUDY_EPOCH.value,
                                    uid=visit.study_epoch_uid,
                                )
                            ],
                        )
                    )

                else:
                    # Add empty cells after Epoch cell with span > 1
                    rows[0].cells.append(TableCell(span=0))

                visit_timing = ""

                # Visit group
                if len(group) > 1:
                    visit_name = visit.consecutive_visit_group

                    if not (
                        getattr(visit, visit_timing_prop) is None
                        or getattr(group[-1], visit_timing_prop) is None
                    ):
                        visit_timing = f"{getattr(visit, visit_timing_prop):d}-{getattr(group[-1], visit_timing_prop):d}"

                # Single Visit
                else:
                    visit_name = visit.visit_short_name

                    if getattr(visit, visit_timing_prop) is not None:
                        visit_timing = f"{getattr(visit, visit_timing_prop):d}"

                # Visit name cell
                rows[1].cells.append(
                    TableCell(
                        visit_name,
                        style="header2",
                        refs=[
                            Ref(type_=SoAItemType.STUDY_VISIT.value, uid=vis.uid)
                            for vis in group
                        ],
                    )
                )

                # Visit timing cell
                rows[2].cells.append(TableCell(visit_timing, style="header3"))

                # Visit window
                visit_window = ""
                if None not in (
                    visit.min_visit_window_value,
                    visit.max_visit_window_value,
                ):
                    if (
                        visit.min_visit_window_value * -1
                        == visit.max_visit_window_value
                    ):
                        # plus-minus sign can be used
                        visit_window = f"±{visit.max_visit_window_value:d}"
                    else:
                        # plus and minus windows are different
                        visit_window = f"{visit.min_visit_window_value:+d}/{visit.max_visit_window_value:+d}"

                # Visit window cell
                rows[3].cells.append(TableCell(visit_window, style="header4"))

        return rows

    @classmethod
    def _get_activity_rows(
        cls,
        study_selection_activities: Sequence[
            StudySelectionActivity | StudySelectionActivityInstance
        ],
        study_activity_schedules: Sequence[StudyActivitySchedule],
        grouped_visits: dict[str, dict[str, list[StudyVisit]]],
        operational: bool = False,
        hide_soa_groups: bool = False,
    ) -> list[TableRow]:
        """Builds activity rows also adding various group header rows when required"""

        # Ordered StudyVisit.uids of visits to show (showing only the first visit of a consecutive_visit_group)
        visible_visit_uids_ordered = tuple(
            visit_group[0].uid
            for epochs_group in grouped_visits.values()
            for visit_group in epochs_group.values()
        )

        num_cols = len(visible_visit_uids_ordered) + 1
        if operational:
            num_cols += NUM_OPERATIONAL_CODE_ROWS

        # StudyActivitySchedules indexed by tuple of [uid, StudyVisit.uid]
        study_activity_schedules_mapping = {
            (
                sas.study_activity_instance_uid or sas.study_activity_uid,
                sas.study_visit_uid,
            ): sas
            for sas in study_activity_schedules
        }

        rows = []

        prev_soa_group_uid = False
        prev_activity_group_uid = False
        prev_activity_subgroup_uid = False
        prev_study_selection_id = False

        study_selection_activity: (
            StudySelectionActivity | StudySelectionActivityInstance
        )
        for study_selection_activity in study_selection_activities:
            soa_group_uid = study_selection_activity.study_soa_group.soa_group_term_uid

            if not hide_soa_groups or getattr(
                study_selection_activity,
                "show_soa_group_in_protocol_flowchart",
                True,
            ):
                # Add SoA Group row
                if soa_group_uid != prev_soa_group_uid:
                    prev_soa_group_uid = soa_group_uid
                    prev_activity_group_uid = False
                    prev_activity_subgroup_uid = False
                    prev_study_selection_id = False

                    soa_group_row = cls._get_soa_group_row(
                        study_selection_activity, num_cols
                    )
                    rows.append(soa_group_row)

                else:
                    # Reference uids of all StudySoAGroups
                    soa_group_row.cells[0].refs.insert(
                        1,
                        Ref(
                            type_=SoAItemType.STUDY_SOA_GROUP.value,
                            uid=study_selection_activity.study_soa_group.study_soa_group_uid,
                        ),
                    )

                    # Unhide SoAGroup row if any of the StudySoAGroup members requests to show it.
                    if getattr(
                        study_selection_activity,
                        "show_soa_group_in_protocol_flowchart",
                        True,
                    ):
                        soa_group_row.hide = False

            # Add Activity Group row
            activity_group_uid = (
                study_selection_activity.study_activity_group.activity_group_uid
            )

            if prev_activity_group_uid != activity_group_uid:
                prev_activity_group_uid = activity_group_uid
                prev_activity_subgroup_uid = False
                prev_study_selection_id = False

                activity_group_row = cls._get_activity_group_row(
                    study_selection_activity, num_cols
                )
                rows.append(activity_group_row)

            else:
                # if there are two ActivityRequests in the same ActivityGroup (None) we shouldn't add them to refs as they don't have uid
                if (
                    study_selection_activity.study_activity_group.study_activity_group_uid
                ):
                    # Reference uids of all StudyActivityGroups
                    activity_group_row.cells[0].refs.insert(
                        1,
                        Ref(
                            type_=SoAItemType.STUDY_ACTIVITY_GROUP.value,
                            uid=study_selection_activity.study_activity_group.study_activity_group_uid,
                        ),
                    )

                # Unhide ActivityGroup row if any of the StudyActivityGroup members requests to show it.
                if getattr(
                    study_selection_activity,
                    "show_activity_group_in_protocol_flowchart",
                    True,
                ):
                    activity_group_row.hide = False

            # Add Activity Sub-Group row
            activity_subgroup_uid = (
                study_selection_activity.study_activity_subgroup.activity_subgroup_uid
            )

            if prev_activity_subgroup_uid != activity_subgroup_uid:
                prev_activity_subgroup_uid = activity_subgroup_uid
                prev_study_selection_id = False

                activity_subgroup_row = cls._get_activity_subgroup_row(
                    study_selection_activity, num_cols
                )
                rows.append(activity_subgroup_row)

            else:
                # if there are two ActivityRequests in the same ActivitySubGroup (None) we shouldn't add them to refs as they don't have uid
                if (
                    study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid
                ):
                    # Reference uids of all StudyActivitySubGroups
                    activity_subgroup_row.cells[0].refs.insert(
                        1,
                        Ref(
                            type_=SoAItemType.STUDY_ACTIVITY_SUBGROUP.value,
                            uid=study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid,
                        ),
                    )

                # Unhide ActivitySubGroup row if any of the StudyActivitySubGroup members requests to show it.
                if getattr(
                    study_selection_activity,
                    "show_activity_subgroup_in_protocol_flowchart",
                    True,
                ):
                    activity_subgroup_row.hide = False

            # Add Activity row
            study_selection_id = study_selection_activity.study_activity_uid

            if prev_study_selection_id != study_selection_id:
                prev_study_selection_id = study_selection_id

                row = cls._get_activity_row(study_selection_activity, operational)

                rows.append(row)

                cls._append_activity_crosses(
                    row,
                    visible_visit_uids_ordered,
                    study_activity_schedules_mapping,
                    study_selection_activity.study_activity_uid,
                )

            # Add Activity Instance row
            if getattr(study_selection_activity, "activity_instance", None):
                row = cls._get_activity_instance_row(study_selection_activity)

                rows.append(row)

                cls._append_activity_crosses(
                    row,
                    visible_visit_uids_ordered,
                    study_activity_schedules_mapping,
                    study_selection_activity.study_activity_instance_uid,
                )

        return rows

    @staticmethod
    def _get_activity_row(study_selection_activity, operational):
        """returns TableRow for Activity"""

        row = TableRow(
            hide=not getattr(
                study_selection_activity,
                "show_activity_in_protocol_flowchart",
                True,
            )
        )

        # Activity name cell (Activity row first column)
        row.cells.append(
            TableCell(
                study_selection_activity.activity.name,
                style="activity",
                refs=[
                    Ref(
                        type_=SoAItemType.STUDY_ACTIVITY.value,
                        uid=study_selection_activity.study_activity_uid,
                    ),
                    Ref(
                        type_="Activity",
                        uid=study_selection_activity.activity.uid,
                    ),
                ],
            )
        )

        if operational:
            for _ in range(NUM_OPERATIONAL_CODE_ROWS):
                row.cells.append(TableCell())

        return row

    @staticmethod
    def _append_activity_crosses(
        row,
        visible_visit_uids_ordered,
        study_activity_schedules_mapping,
        activity_id,
    ):
        """appends TableCells to TableRow with crosses based on Activity Schedules to StudyVisit mapping"""

        # Iterate over the ordered list of visible Visit uids to see if the Activity was scheduled
        for study_visit_uid in visible_visit_uids_ordered:
            study_activity_schedule: StudyActivitySchedule = (
                study_activity_schedules_mapping.get((activity_id, study_visit_uid))
            )

            # Append a cell with tick-mark if Activity was scheduled
            if study_activity_schedule:
                row.cells.append(
                    TableCell(
                        SOA_CHECK_MARK,
                        style="activitySchedule",
                        refs=[
                            Ref(
                                type_=SoAItemType.STUDY_ACTIVITY_SCHEDULE.value,
                                uid=study_activity_schedule.study_activity_schedule_uid,
                            )
                        ],
                    )
                )

            # Append an empty cell if activity was not scheduled
            else:
                row.cells.append(TableCell())

    @staticmethod
    def _get_activity_instance_row(
        study_selection_activity: StudySelectionActivityInstance,
    ):
        """returns TableRow for Activity Instance row"""

        row = TableRow(
            hide=not getattr(
                study_selection_activity,
                "show_activity_instance_in_protocol_flowchart",
                True,
            )
        )

        # Activity name cell (Activity row first column)
        row.cells.append(
            TableCell(
                study_selection_activity.activity_instance.name,
                style="activityInstance",
                refs=[
                    Ref(
                        type_=SoAItemType.STUDY_ACTIVITY_INSTANCE.value,
                        uid=study_selection_activity.study_activity_instance_uid,
                    )
                ],
            )
        )

        row.cells.append(
            TableCell(study_selection_activity.activity_instance.topic_code or "")
        )
        row.cells.append(
            TableCell(study_selection_activity.activity_instance.adam_param_code or "")
        )

        return row

    @staticmethod
    def _get_soa_group_row(
        study_selection_activity: StudySelectionActivity,
        num_cols: int,
    ) -> TableRow:
        """returns TableRow for SoA Group row"""

        row = TableRow(
            hide=not getattr(
                study_selection_activity, "show_soa_group_in_protocol_flowchart", True
            )
        )

        row.cells.append(
            TableCell(
                study_selection_activity.study_soa_group.soa_group_name,
                style="soaGroup",
                refs=[
                    Ref(
                        type_=SoAItemType.STUDY_SOA_GROUP.value,
                        uid=study_selection_activity.study_soa_group.study_soa_group_uid,
                    ),
                    Ref(
                        type_="CTTerm",
                        uid=study_selection_activity.study_soa_group.soa_group_term_uid,
                    ),
                ],
            )
        )

        # fill the row with empty cells for visits #
        row.cells += [TableCell() for _ in range(num_cols - 1)]

        return row

    @staticmethod
    def _get_activity_group_row(
        study_selection_activity: StudySelectionActivity,
        num_cols: int,
    ) -> TableRow:
        """returns TableRow for Activity Group row"""

        group_name = (
            study_selection_activity.study_activity_group.activity_group_name
            if study_selection_activity.study_activity_group.activity_group_uid
            else _("no_study_group")
        )

        for a_g in study_selection_activity.activity.activity_groupings:
            if (
                a_g.activity_group_uid
                == study_selection_activity.study_activity_group.activity_group_uid
            ):
                group_name = a_g.activity_group_name
                break

        row = TableRow(
            hide=not getattr(
                study_selection_activity,
                "show_activity_group_in_protocol_flowchart",
                True,
            )
        )

        row.cells.append(
            TableCell(
                group_name,
                style="group",
                refs=(
                    [
                        Ref(
                            type_=SoAItemType.STUDY_ACTIVITY_GROUP.value,
                            uid=study_selection_activity.study_activity_group.study_activity_group_uid,
                        ),
                        Ref(
                            type_="ActivityGroup",
                            uid=study_selection_activity.study_activity_group.activity_group_uid,
                        ),
                    ]
                    if study_selection_activity.study_activity_group.study_activity_group_uid
                    else []
                ),
            )
        )

        # fill the row with empty cells for visits #
        row.cells += [TableCell() for _ in range(num_cols - 1)]

        return row

    @staticmethod
    def _get_activity_subgroup_row(
        study_selection_activity: StudySelectionActivity,
        num_cols: int,
    ) -> TableRow:
        """returns TableRow for Activity SubGroup row"""

        group_name = (
            study_selection_activity.study_activity_subgroup.activity_subgroup_name
            if study_selection_activity.study_activity_subgroup.activity_subgroup_uid
            else _("no_study_subgroup")
        )

        for a_g in study_selection_activity.activity.activity_groupings:
            if (
                a_g.activity_subgroup_uid
                == study_selection_activity.study_activity_subgroup.activity_subgroup_uid
            ):
                group_name = a_g.activity_subgroup_name
                break

        row = TableRow(
            hide=not getattr(
                study_selection_activity,
                "show_activity_subgroup_in_protocol_flowchart",
                True,
            )
        )

        row.cells.append(
            TableCell(
                group_name,
                style="subGroup",
                refs=(
                    [
                        Ref(
                            type_=SoAItemType.STUDY_ACTIVITY_SUBGROUP.value,
                            uid=study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid,
                        ),
                        Ref(
                            type_="ActivitySubGroup",
                            uid=study_selection_activity.study_activity_subgroup.activity_subgroup_uid,
                        ),
                    ]
                    if study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid
                    else []
                ),
            )
        )

        # fill the row with empty cells for visits #
        row.cells += [TableCell() for _ in range(num_cols - 1)]

        return row

    @classmethod
    @trace_calls
    def add_footnotes(
        cls,
        table: TableWithFootnotes,
        footnotes: list[StudySoAFootnote],
    ):
        """Adds footnote symbols to table rows based on the referenced uids"""

        (
            footnote_symbols_by_ref_uid,
            simple_footnotes_by_symbol,
        ) = cls._mk_simple_footnotes(footnotes)
        for row in table.rows:
            for cell in row.cells:
                footnotes = set(cell.footnotes or [])
                for ref in cell.refs or []:
                    footnotes.update(footnote_symbols_by_ref_uid.get(ref.uid, []))
                cell.footnotes = sorted(list(footnotes)) if footnotes else None

        table.footnotes = simple_footnotes_by_symbol

    @staticmethod
    @trace_calls
    def show_hidden_rows(table: TableWithFootnotes):
        """Modify table in place to for detailed SoA"""

        row: TableRow
        for row in table.rows:
            # unhide all rows
            row.hide = False

    @staticmethod
    @trace_calls
    def propagate_hidden_rows(table: TableWithFootnotes):
        """
        Modify table in place to for Protocol SoA

        For hidden activity rows, up-propagate the crosses and footnotes onto the next visible group level.
        """

        soa_group_term_row = None
        activity_group_row = None
        activity_subgroup_row = None

        row: TableRow
        for row in table.rows:
            if not (row.cells and row.cells[0].refs):
                continue

            if row.cells[0].refs[0].type == SoAItemType.STUDY_SOA_GROUP.value:
                soa_group_term_row = row
                activity_group_row = None
                activity_subgroup_row = None

            elif row.cells[0].refs[0].type == SoAItemType.STUDY_ACTIVITY_GROUP.value:
                activity_group_row = row
                activity_subgroup_row = None

            elif row.cells[0].refs[0].type == SoAItemType.STUDY_ACTIVITY_SUBGROUP.value:
                activity_subgroup_row = row

            elif (
                row.hide
                and row.cells[0].refs[0].type == SoAItemType.STUDY_ACTIVITY.value
            ):
                update_row = None

                if activity_subgroup_row and not activity_subgroup_row.hide:
                    update_row = activity_subgroup_row
                elif activity_group_row and not activity_group_row.hide:
                    update_row = activity_group_row
                elif soa_group_term_row and not soa_group_term_row.hide:
                    update_row = soa_group_term_row

                if update_row and len(update_row.cells) == len(row.cells):
                    cell: TableCell
                    for i, cell in enumerate(row.cells):
                        update_cell: TableCell = update_row.cells[i]

                        if i > 0:
                            update_cell.text = update_cell.text or cell.text

                        if cell.footnotes:
                            if update_cell.footnotes:
                                update_cell.footnotes = sorted(
                                    list(set(update_cell.footnotes + cell.footnotes))
                                )
                            else:
                                update_cell.footnotes = cell.footnotes.copy()

    @staticmethod
    @trace_calls
    def add_protocol_section_column(table: TableWithFootnotes):
        """Add Protocol Section column to table, updates table in place"""

        table.rows[0].cells.insert(
            table.num_header_cols,
            TableCell(text=_("protocol_section"), style="header1"),
        )

        row: TableRow
        for row in table.rows[1:]:
            row.cells.insert(table.num_header_cols, TableCell())

    @staticmethod
    @trace_calls
    def add_coordinates(
        table: TableWithFootnotes, coordinates: Mapping[str, tuple[int, int]]
    ):
        """Append coordinates as if they were footnote references to each table cell"""
        for row in table.rows:
            for cell in row.cells:
                if cell.refs:
                    for ref in cell.refs:
                        if ref.uid in coordinates:
                            cell.footnotes = [
                                f"[{','.join(map(str, coordinates[ref.uid]))}]"
                            ]

    @staticmethod
    @trace_calls
    def add_uid_debug(table: TableWithFootnotes):
        """Append coordinates as if they were footnote references to each table cell"""
        for row in table.rows:
            for cell in row.cells:
                cell.footnotes = [ref.uid for ref in cell.refs or []]

    @trace_calls
    def get_preferred_time_unit(
        self, study_uid: str, study_value_version: str | None = None
    ):
        """Gets preferred time unit of study from the db"""
        return (
            StudyService()
            .get_study_preferred_time_unit(
                study_uid,
                for_protocol_soa=True,
                study_value_version=study_value_version,
            )
            .time_unit_name
        )

    def _get_soa_preferences(
        self, study_uid: str, study_value_version: str | None = None
    ) -> StudySoaPreferences:
        """Gets SoA preferences"""
        return StudyService().get_study_soa_preferences(
            study_uid,
            study_value_version=study_value_version,
        )

    @staticmethod
    @trace_calls
    def download_detailed_soa_content(
        study_uid: str,
        study_value_version: str | None = None,
        protocol_flowchart: bool = False,
    ) -> list[dict]:
        if not study_value_version:
            query = "MATCH (study_root:StudyRoot{uid:$study_uid})-[has_version:LATEST]-(study_value:StudyValue)"
        else:
            query = "MATCH (study_root:StudyRoot{uid:$study_uid})-[has_version:HAS_VERSION {version:$study_value_version}]-(study_value:StudyValue)"
        query += """
            MATCH (study_activity_schedule:StudyActivitySchedule)<-[:HAS_STUDY_ACTIVITY_SCHEDULE]-(study_value)
            MATCH (study_activity_schedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(study_visit:StudyVisit)<-[:HAS_STUDY_VISIT]-(study_value)
            MATCH (study_visit)<-[:STUDY_EPOCH_HAS_STUDY_VISIT]-(study_epoch:StudyEpoch)<-[:HAS_STUDY_EPOCH]-(study_value)
            MATCH (study_activity_schedule)<-[:STUDY_ACTIVITY_HAS_SCHEDULE]-(study_activity:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(study_value)
        """
        query += (
            "WHERE study_activity.show_activity_in_protocol_flowchart=true"
            if protocol_flowchart
            else ""
        )
        query += """
        WITH has_version,study_value, study_activity_schedule, study_visit, study_epoch, study_activity,
            head([(study_activity)-[:HAS_SELECTED_ACTIVITY]->(activity_value:ActivityValue) | activity_value]) as activity,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(:StudyActivitySubGroup)
                -[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue) | activity_subgroup_value]) as activity_subgroup,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(:StudyActivityGroup)
                -[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue) | activity_group_value]) as activity_group,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(:StudySoAGroup)
                -[:HAS_FLOWCHART_GROUP]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(term_name_value:CTTermNameValue) 
                | term_name_value]) as term_name_value,
            head([(study_epoch)-[:HAS_EPOCH]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]-
                (epoch_term:CTTermNameValue) | epoch_term.name]) as epoch_name
        ORDER BY study_activity.order, study_visit.visit_number
        RETURN
            CASE
                WHEN has_version.status = "RELEASED"
                THEN has_version.version
                ELSE "LATEST on "+apoc.temporal.format(datetime(), 'yyyy-MM-dd HH:mm:ss zzz')
            END as study_version,
            study_value.study_number AS study_number,
            study_visit.short_visit_label AS visit,
            epoch_name AS epoch,
            activity.name AS activity,
            activity_subgroup.name AS activity_subgroup,
            activity_group.name AS activity_group,
            term_name_value.name as soa_group
        """

        result_array, attribute_names = db.cypher_query(
            query,
            params={"study_uid": study_uid, "study_value_version": study_value_version},
        )
        content_rows = []
        for soa_content in result_array:
            content_dict = {}
            for content_prop, attribute_name in zip(soa_content, attribute_names):
                content_dict[attribute_name] = content_prop
            content_rows.append(content_dict)
        return content_rows

    @staticmethod
    @trace_calls
    def download_operational_soa_content(
        study_uid: str,
        study_value_version: str | None = None,
    ) -> list[dict]:
        if not study_value_version:
            query = "MATCH (study_root:StudyRoot{uid:$study_uid})-[has_version:LATEST]-(study_value:StudyValue)"
        else:
            query = "MATCH (study_root:StudyRoot{uid:$study_uid})-[has_version:HAS_VERSION {version:$study_value_version}]-(study_value:StudyValue)"
        query += """
            MATCH (study_activity_schedule:StudyActivitySchedule)<-[:HAS_STUDY_ACTIVITY_SCHEDULE]-(study_value)
            MATCH (study_activity_schedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(study_visit:StudyVisit)<-[:HAS_STUDY_VISIT]-(study_value)
            MATCH (study_visit)<-[:STUDY_EPOCH_HAS_STUDY_VISIT]-(study_epoch:StudyEpoch)<-[:HAS_STUDY_EPOCH]-(study_value)
            MATCH (study_activity_schedule)<-[:STUDY_ACTIVITY_HAS_SCHEDULE]-(study_activity:StudyActivity)
                -[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_INSTANCE]->(study_activity_instance:StudyActivityInstance)
                <-[:HAS_STUDY_ACTIVITY_INSTANCE]-(study_value)
            WITH has_version,study_value, study_activity_schedule, study_visit, study_epoch, study_activity_instance, study_activity,
                head([(study_activity)-[:HAS_SELECTED_ACTIVITY]->(activity_value:ActivityValue) | activity_value]) as activity,
                head([(study_activity_instance)-[:HAS_SELECTED_ACTIVITY_INSTANCE]->(activity_instance_value:ActivityInstanceValue) | 
                    activity_instance_value]) as activity_instance,
                head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(:StudyActivitySubGroup)
                    -[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue) | activity_subgroup_value]) as activity_subgroup,
                head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(:StudyActivityGroup)
                    -[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue) | activity_group_value]) as activity_group,
                head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(:StudySoAGroup)
                    -[:HAS_FLOWCHART_GROUP]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(term_name_value:CTTermNameValue) 
                    | term_name_value]) as term_name_value,
                head([(study_epoch)-[:HAS_EPOCH]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]-
                    (epoch_term:CTTermNameValue) | epoch_term.name]) as epoch_name
            ORDER BY study_activity.order, study_visit.visit_number
            RETURN
                CASE
                    WHEN has_version.status = "RELEASED"
                    THEN has_version.version
                    ELSE "LATEST on "+apoc.temporal.format(datetime(), 'yyyy-MM-dd HH:mm:ss zzz')
                END as study_version,
                study_value.study_number AS study_number,
                study_visit.short_visit_label AS visit,
                epoch_name AS epoch,
                activity.name AS activity,
                activity_instance.name AS activity_instance,
                activity_instance.topic_code AS topic_code,
                activity_instance.adam_param_code AS param_code,
                activity_subgroup.name AS activity_subgroup,
                activity_group.name AS activity_group,
                term_name_value.name as soa_group
        """

        result_array, attribute_names = db.cypher_query(
            query,
            params={"study_uid": study_uid, "study_value_version": study_value_version},
        )
        content_rows = []
        for soa_content in result_array:
            content_dict = {}
            for content_prop, attribute_name in zip(soa_content, attribute_names):
                content_dict[attribute_name] = content_prop
            content_rows.append(content_dict)
        return content_rows
