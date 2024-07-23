import datetime
from dataclasses import dataclass

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
)


@dataclass
class SelectionHistory:
    """Class for selection history items"""

    study_selection_uid: str
    study_uid: str
    user_initials: str
    change_type: str
    start_date: datetime.datetime
    end_date: datetime.datetime | None


class StudySelectionRepository:
    """
    Base class for study selection.

    We handle common operations here.
    """

    def _from_repository_values(self, study_uid: str, selection):
        """Must be defined by subclasses."""
        raise NotImplementedError

    def perform_save(
        self,
        study_value_node: StudyValue,
        selection_vo,
        author: str,
    ):
        """Must be defined by subclasses."""
        raise NotImplementedError

    def save(self, selection_vo, author: str):
        study_root_node = StudyRoot.nodes.get_or_none(uid=selection_vo.study_uid)
        if study_root_node is None:
            raise exceptions.NotFoundException(
                f"The study with uid {selection_vo.study_uid} was not found"
            )
        latest_study_value_node = study_root_node.latest_value.single()
        selection = self.perform_save(latest_study_value_node, selection_vo, author)
        # Update audit trail
        before_audit_node = None
        if selection_vo.uid is not None:
            before_audit_node = Edit(
                user_initials=author, date=datetime.datetime.now(datetime.timezone.utc)
            )
            before_audit_node.save()
            study_root_node.audit_trail.connect(before_audit_node)
            before_audit_node.has_before.connect(selection)
            after_audit_node = Edit()
        else:
            after_audit_node = Create()

        after_audit_node.user_initials = author
        after_audit_node.date = datetime.datetime.now(datetime.timezone.utc)
        after_audit_node.save()
        study_root_node.audit_trail.connect(after_audit_node)
        after_audit_node.has_after.connect(selection)

        return self._from_repository_values(selection_vo.study_uid, selection)

    def get_study_selection(self, study_value_node: StudyValue, selection_uid: str):
        """Must be defined by subclasses."""
        raise NotImplementedError

    def delete(self, study_uid: str, selection_uid: str, author: str) -> None:
        study_root_node = StudyRoot.nodes.get_or_none(uid=study_uid)
        if study_root_node is None:
            raise exceptions.NotFoundException(
                f"The study with uid {study_uid} was not found"
            )
        latest_study_value_node = study_root_node.latest_value.single()
        selection = self.get_study_selection(latest_study_value_node, selection_uid)
        selection_vo = self._from_repository_values(study_uid, selection)
        new_selection = self.perform_save(latest_study_value_node, selection_vo, author)
        # Audit trail
        audit_node = Delete(
            user_initials=author, date=datetime.datetime.now(datetime.timezone.utc)
        )
        audit_node.save()
        study_root_node.audit_trail.connect(audit_node)
        audit_node.has_before.connect(selection)
        audit_node.has_after.connect(new_selection)
        new_selection.study_value.disconnect(latest_study_value_node)
        # Delete relation
        selection.study_value.disconnect(latest_study_value_node)

    def _get_selection_with_history(
        self, study_uid: str, selection_uid: str | None = None
    ):
        """Must be defined by subclasses."""
        raise NotImplementedError

    def find_selection_history(
        self, study_uid: str, selection_uid: str | None = None
    ) -> list[dict | None]:
        kwargs = {}
        if selection_uid:
            kwargs["selection_uid"] = selection_uid
        return self._get_selection_with_history(study_uid=study_uid, **kwargs)
