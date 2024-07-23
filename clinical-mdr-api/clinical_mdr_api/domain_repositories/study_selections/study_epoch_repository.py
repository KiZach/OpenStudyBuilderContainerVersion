import datetime

from neomodel import db

from clinical_mdr_api import config as settings
from clinical_mdr_api import exceptions
from clinical_mdr_api.domain_repositories.generic_repository import (
    manage_previous_connected_study_selection_relationships,
)
from clinical_mdr_api.domain_repositories.models._utils import to_relation_trees
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
)
from clinical_mdr_api.domain_repositories.models.study_epoch import StudyEpoch
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections import study_epoch
from clinical_mdr_api.domains.study_selections.study_epoch import (
    StudyEpochHistoryVO,
    StudyEpochVO,
)
from clinical_mdr_api.models.study_selections.study_epoch import (
    StudyEpochOGM,
    StudyEpochOGMVer,
)


def get_ctlist_terms_by_name(
    code_list_name: str, effective_date: datetime.datetime | None = None
):
    if not effective_date:
        ctterm_name_match = "(:CTTermNameRoot)-[:LATEST_FINAL]->(ctnv:CTTermNameValue)"
    else:
        ctterm_name_match = """(ctnr:CTTermNameRoot)-[hv:HAS_VERSION]->(ctnv:CTTermNameValue)
            WHERE (hv.start_date<= datetime($effective_date) < datetime(hv.end_date)) OR (hv.end_date IS NULL AND (hv.start_date <= datetime($effective_date)))
        """
    cypher_query = f"""
        MATCH (:CTCodelistNameValue {{name: $code_list_name}})<-[:LATEST_FINAL]-(:CTCodelistNameRoot)<-[:HAS_NAME_ROOT]-
        (:CTCodelistRoot)-[:HAS_TERM]->
        (tr:CTTermRoot)-[:HAS_NAME_ROOT]->
        {ctterm_name_match}
        return tr.uid, ctnv.name
        """
    items, _ = db.cypher_query(
        cypher_query,
        {
            "code_list_name": code_list_name,
            "effective_date": effective_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            if effective_date
            else None,
        },
    )
    return {a[0]: a[1] for a in items}


class StudyEpochRepository:
    def __init__(self, author: str):
        self.author = author

    def fetch_ctlist(
        self, code_list_name: str, effective_date: datetime.datetime | None = None
    ):
        return get_ctlist_terms_by_name(code_list_name, effective_date=effective_date)

    def get_allowed_configs(self, effective_date: datetime.datetime | None = None):
        if effective_date:
            subtype_name_value_match = """MATCH (term_subtype_name_root)-[hv:HAS_VERSION]->(term_subtype_name_value:CTTermNameValue)
                WHERE (hv.start_date<= datetime($effective_date) < hv.end_date) OR (hv.end_date IS NULL AND (hv.start_date <= datetime($effective_date)))
            """
            type_name_value_match = """MATCH (term_type_name_root)-[hv_type:HAS_VERSION]->(term_type_name_value:CTTermNameValue)
                WHERE (hv_type.start_date<= datetime($effective_date) < hv_type.end_date) OR (hv_type.end_date IS NULL AND (hv_type.start_date <= datetime($effective_date)))
            """
        else:
            subtype_name_value_match = "MATCH (term_subtype_name_root:CTTermNameRoot)-[:LATEST_FINAL]->(term_subtype_name_value:CTTermNameValue)"
            type_name_value_match = "MATCH (term_type_name_root)-[:LATEST_FINAL]->(term_type_name_value:CTTermNameValue)"

        cypher_query = f"""
            MATCH (:CTCodelistNameValue {{name: $code_list_name}})<-[:LATEST_FINAL]-(:CTCodelistNameRoot)<-[:HAS_NAME_ROOT]
            -(:CTCodelistRoot)-[:HAS_TERM]->(term_subtype_root:CTTermRoot)-[:HAS_NAME_ROOT]->(term_subtype_name_root:CTTermNameRoot)
            {subtype_name_value_match}
            MATCH (term_subtype_root)-[:HAS_PARENT_TYPE]->(term_type_root:CTTermRoot)-
            [:HAS_NAME_ROOT]->(term_type_name_root)
            {type_name_value_match}

            return term_subtype_root.uid, term_subtype_name_value.name, term_type_root.uid, term_type_name_value.name
        """
        items, _ = db.cypher_query(
            cypher_query,
            {
                "code_list_name": settings.STUDY_EPOCH_SUBTYPE_NAME,
                "effective_date": effective_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                if effective_date
                else None,
            },
        )
        return items

    def get_basic_epoch(self, study_uid: str) -> str | None:
        cypher_query = """
        MATCH (study_root:StudyRoot {uid:$study_uid})-[:LATEST]->(:StudyValue)-[:HAS_STUDY_EPOCH]->(study_epoch:StudyEpoch)-[:HAS_EPOCH_SUB_TYPE]->(:CTTermRoot)-
        [:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:HAS_VERSION]->(:CTTermNameValue {name:$basic_epoch_name})
        WHERE NOT exists((:Delete)-[:BEFORE]->(study_epoch))
        return study_epoch.uid
        """
        basic_visit, _ = db.cypher_query(
            cypher_query,
            {"basic_epoch_name": settings.BASIC_EPOCH_NAME, "study_uid": study_uid},
        )
        return basic_visit[0][0] if len(basic_visit) > 0 else None

    def find_all_epochs_by_study(
        self, study_uid: str, study_value_version: str | None = None
    ) -> list[StudyEpochVO]:
        if study_value_version:
            filters = {
                "study_value__has_version|version": study_value_version,
                "study_value__has_version__uid": study_uid,
            }
        else:
            filters = {"study_value__latest_value__uid": study_uid}

        return [
            self._from_neomodel_to_vo(
                study_epoch_ogm_input=StudyEpochOGM.from_orm(sas_node)
            )
            for sas_node in to_relation_trees(
                StudyEpoch.nodes.fetch_relations(
                    "has_epoch",
                    "has_epoch_subtype",
                    "has_epoch_type",
                    "has_after__audit_trail",
                )
                .fetch_optional_relations("has_duration_unit")
                .filter(**filters)
                .order_by("order")
            ).distinct()
        ]

    def epoch_specific_has_connected_design_cell(
        self, study_uid: str, epoch_uid: str
    ) -> bool:
        """
        Returns True if StudyEpoch with specified uid has connected at least one StudyDesignCell.
        :return:
        """

        sdc_node = to_relation_trees(
            StudyEpoch.nodes.fetch_relations(
                "has_design_cell__study_value",
                "has_after",
                "has_after__audit_trail",
            ).filter(study_value__latest_value__uid=study_uid, uid=epoch_uid)
        )
        return len(sdc_node) > 0

    def find_by_uid(
        self, uid: str, study_uid: str, study_value_version: str | None = None
    ) -> StudyEpochVO:
        if study_value_version:
            filters = {
                "uid": uid,
                "study_value__has_version__uid": study_uid,
                "study_value__has_version|version": study_value_version,
            }
        else:
            filters = {
                "uid": uid,
                "study_value__latest_value__uid": study_uid,
            }

        epoch_node = to_relation_trees(
            StudyEpoch.nodes.fetch_relations(
                "has_epoch",
                "has_epoch_subtype",
                "has_epoch_type",
                "has_after__audit_trail",
                "study_value__has_version",
            )
            .fetch_optional_relations("has_duration_unit")
            .filter(**filters)
        ).distinct()

        if len(epoch_node) > 1:
            raise exceptions.ValidationException(
                f"Found more than one StudyEpoch node with uid='{uid}'."
            )
        if len(epoch_node) == 0:
            raise exceptions.ValidationException(
                f"The StudyEpoch with uid='{uid}' could not be found."
            )
        return self._from_neomodel_to_vo(
            study_epoch_ogm_input=StudyEpochOGM.from_orm(epoch_node[0])
        )

    def get_all_versions(self, uid: str, study_uid):
        return sorted(
            [
                self._from_neomodel_to_history_vo(
                    study_epoch_ogm_input=StudyEpochOGMVer.from_orm(se_node)
                )
                for se_node in to_relation_trees(
                    StudyEpoch.nodes.fetch_relations(
                        "has_after__audit_trail",
                        "has_epoch",
                        "has_epoch_subtype",
                        "has_epoch_type",
                    )
                    .fetch_optional_relations("has_duration_unit", "has_before")
                    .filter(uid=uid, has_after__audit_trail__uid=study_uid)
                )
            ],
            key=lambda item: item.start_date,
            reverse=True,
        )

    def get_all_epoch_versions(self, study_uid: str):
        return sorted(
            [
                self._from_neomodel_to_history_vo(
                    study_epoch_ogm_input=StudyEpochOGMVer.from_orm(se_node)
                )
                for se_node in to_relation_trees(
                    StudyEpoch.nodes.fetch_relations(
                        "has_after__audit_trail",
                        "has_epoch",
                        "has_epoch_subtype",
                        "has_epoch_type",
                    )
                    .fetch_optional_relations("has_duration_unit", "has_before")
                    .filter(has_after__audit_trail__uid=study_uid)
                    .order_by("order")
                )
            ],
            key=lambda item: item.start_date,
            reverse=True,
        )

    def _from_neomodel_to_vo(self, study_epoch_ogm_input: StudyEpochOGM):
        return StudyEpochVO(
            uid=study_epoch_ogm_input.uid,
            study_uid=study_epoch_ogm_input.study_uid,
            start_rule=study_epoch_ogm_input.start_rule,
            end_rule=study_epoch_ogm_input.end_rule,
            description=study_epoch_ogm_input.description,
            epoch=study_epoch.StudyEpochEpoch[study_epoch_ogm_input.epoch],
            subtype=study_epoch.StudyEpochSubType[study_epoch_ogm_input.epoch_subtype],
            epoch_type=study_epoch.StudyEpochType[study_epoch_ogm_input.epoch_type],
            order=study_epoch_ogm_input.order,
            status=StudyStatus(study_epoch_ogm_input.status),
            start_date=study_epoch_ogm_input.start_date,
            author=self.author,
            color_hash=study_epoch_ogm_input.color_hash,
        )

    def _from_neomodel_to_history_vo(self, study_epoch_ogm_input: StudyEpochOGMVer):
        return StudyEpochHistoryVO(
            uid=study_epoch_ogm_input.uid,
            study_uid=study_epoch_ogm_input.study_uid,
            start_rule=study_epoch_ogm_input.start_rule,
            end_rule=study_epoch_ogm_input.end_rule,
            description=study_epoch_ogm_input.description,
            epoch=study_epoch.StudyEpochEpoch[study_epoch_ogm_input.epoch],
            subtype=study_epoch.StudyEpochSubType[study_epoch_ogm_input.epoch_subtype],
            epoch_type=study_epoch.StudyEpochType[study_epoch_ogm_input.epoch_type],
            order=study_epoch_ogm_input.order,
            status=StudyStatus(study_epoch_ogm_input.status),
            start_date=study_epoch_ogm_input.start_date,
            author=self.author,
            color_hash=study_epoch_ogm_input.color_hash,
            change_type=study_epoch_ogm_input.change_type,
            end_date=study_epoch_ogm_input.end_date,
        )

    def save(self, epoch: StudyEpochVO):
        # if exists
        if epoch.uid is not None:
            return self._update(epoch, create=False)
        # if has to be created
        return self._update(epoch, create=True)

    def _update(self, item: StudyEpochVO, create: bool = False):
        study_root = StudyRoot.nodes.get(uid=item.study_uid)
        study_value: StudyValue = study_root.latest_value.get_or_none()
        if study_value is None:
            raise exceptions.ValidationException("Study does not have draft version")
        if not create:
            previous_item = study_value.has_study_epoch.get(uid=item.uid)
        new_study_epoch = StudyEpoch(
            uid=item.uid,
            accepted_version=item.accepted_version,
            order=item.order,
            name=item.name,
            short_name=item.short_name,
            description=item.description,
            start_rule=item.start_rule,
            end_rule=item.end_rule,
            color_hash=item.color_hash,
            status=item.status.value,
        )
        if item.uid is not None:
            new_study_epoch.uid = item.uid
        new_study_epoch.save()
        if item.uid is None:
            item.uid = new_study_epoch.uid
        ct_epoch_subtype = CTTermRoot.nodes.get(uid=item.subtype.name)
        new_study_epoch.has_epoch_subtype.connect(ct_epoch_subtype)
        ct_epoch_type = CTTermRoot.nodes.get(uid=item.epoch_type.name)
        new_study_epoch.has_epoch_type.connect(ct_epoch_type)
        ct_epoch = CTTermRoot.nodes.get(uid=item.epoch.name)
        new_study_epoch.has_epoch.connect(ct_epoch)
        if create:
            new_study_epoch.study_value.connect(study_value)
            self.manage_versioning_create(
                study_root=study_root, item=item, new_item=new_study_epoch
            )
        else:
            if item.is_deleted:
                self.manage_versioning_delete(
                    study_root=study_root,
                    item=item,
                    previous_item=previous_item,
                    new_item=new_study_epoch,
                )
            else:
                new_study_epoch.study_value.connect(study_value)
                self.manage_versioning_update(
                    study_root=study_root,
                    item=item,
                    previous_item=previous_item,
                    new_item=new_study_epoch,
                )
            manage_previous_connected_study_selection_relationships(
                previous_item=previous_item,
                study_value_node=study_value,
                new_item=new_study_epoch,
                exclude_study_selection_relationships=[],
            )

        return item

    def manage_versioning_create(
        self, study_root: StudyRoot, item: StudyEpochVO, new_item: StudyEpoch
    ):
        action = Create(
            date=datetime.datetime.now(datetime.timezone.utc),
            status=item.status.value,
            user_initials=item.author,
        )
        action.save()
        action.has_after.connect(new_item)
        study_root.audit_trail.connect(action)

    def manage_versioning_update(
        self,
        study_root: StudyRoot,
        item: StudyEpochVO,
        previous_item: StudyEpoch,
        new_item: StudyEpoch,
    ):
        action = Edit(
            date=datetime.datetime.now(datetime.timezone.utc),
            status=item.status.value,
            user_initials=item.author,
        )
        action.save()
        action.has_before.connect(previous_item)
        action.has_after.connect(new_item)
        study_root.audit_trail.connect(action)

    def manage_versioning_delete(
        self,
        study_root: StudyRoot,
        item: StudyEpochVO,
        previous_item: StudyEpoch,
        new_item: StudyEpoch,
    ):
        action = Delete(
            date=datetime.datetime.now(datetime.timezone.utc),
            status=item.status.value,
            user_initials=item.author,
        )
        action.save()
        action.has_before.connect(previous_item)
        action.has_after.connect(new_item)
        study_root.audit_trail.connect(action)
