import copy
from datetime import datetime

from neomodel import db  # type: ignore

from clinical_mdr_api import exceptions, models
from clinical_mdr_api.domains.comments.comments import (
    CommentReplyAR,
    CommentThreadAR,
    CommentThreadStatus,
    CommentTopicAR,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.oauth import user
from clinical_mdr_api.services._meta_repository import MetaRepository  # type: ignore


class CommentsService:
    def __init__(self):
        self.user_info = user()
        self.repos = MetaRepository()

    def get_all_comment_topics(
        self,
        topic_path: str | None = None,
        topic_path_partial_match: bool = False,
        page_number: int = 1,
        page_size: int = 0,
    ) -> GenericFilteringReturn[models.CommentTopic]:
        try:
            items, total = self.repos.comments_repository.find_all_comment_topics(
                topic_path=topic_path,
                topic_path_partial_match=topic_path_partial_match,
                page_number=page_number,
                page_size=page_size,
            )

            all_topics = GenericFilteringReturn.create(items, total)
            all_topics.items = [
                models.CommentTopic.from_ar(item_ar) for item_ar in all_topics.items
            ]
            return all_topics
        finally:
            self.repos.close()

    def get_all_comment_threads(
        self,
        topic_path: str | None = None,
        topic_path_partial_match: bool = False,
        status: CommentThreadStatus | None = None,
        page_number: int = 1,
        page_size: int = 0,
    ) -> GenericFilteringReturn[models.CommentThread]:
        try:
            items, total = self.repos.comments_repository.find_all_comment_threads(
                topic_path=topic_path,
                topic_path_partial_match=topic_path_partial_match,
                status=status,
                page_number=page_number,
                page_size=page_size,
            )

            all_threads = GenericFilteringReturn.create(items, total)
            all_threads.items = [
                models.CommentThread.from_ar(item_ar) for item_ar in all_threads.items
            ]
            return all_threads
        finally:
            self.repos.close()

    def get_comment_thread(self, uid: str) -> models.CommentThread:
        repos = MetaRepository()
        try:
            comment_thread = models.CommentThread.from_uid(
                uid, repos.comments_repository.find_comment_thread_by_uid
            )
            if comment_thread is None:
                raise exceptions.NotFoundException(
                    f"Comment thread with the specified uid '{uid}' could not be found.",
                )
            comment_thread.replies = [
                models.CommentReply.from_ar(reply_ar)
                for reply_ar in self.repos.comments_repository.find_all_comment_thread_replies(
                    uid
                )
            ]
            return comment_thread
        finally:
            self.repos.close()

    @db.transaction
    def create_comment_thread(
        self, comment_thread_create_input: models.CommentThreadCreateInput
    ) -> models.CommentThread:
        try:
            comment_thread_ar = CommentThreadAR.from_input_values(
                text=comment_thread_create_input.text,
                topic_path=comment_thread_create_input.topic_path,
                author=self.user_info.id(),
                author_display_name=self.user_info.name,
                status=CommentThreadStatus.ACTIVE,
                created_at=datetime.now(),
                generate_uid_callback=self.repos.comments_repository.generate_thread_uid,
            )

            # Retrieve existing topic or create one if not found
            comment_topic_ar = self.repos.comments_repository.find_topic_by_path(
                comment_thread_create_input.topic_path
            )
            if not comment_topic_ar:
                comment_topic_ar = CommentTopicAR.from_input_values(
                    topic_path=comment_thread_create_input.topic_path,
                    generate_uid_callback=self.repos.comments_repository.generate_topic_uid,
                )
                self.repos.comments_repository.save_comment_topic(comment_topic_ar)

            self.repos.comments_repository.save_comment_thread(comment_thread_ar)
            return models.CommentThread.from_uid(
                comment_thread_ar.uid,
                self.repos.comments_repository.find_comment_thread_by_uid,
            )
        finally:
            self.repos.close()

    def _edit_comment_thread(
        self, uid: str, comment_thread_edit_input: models.CommentThreadEditInput
    ) -> models.CommentThread:
        try:
            comment_thread_latest = (
                self.repos.comments_repository.find_comment_thread_by_uid(uid)
            )
            if comment_thread_latest is None:
                raise exceptions.NotFoundException(
                    f"Comment thread with the specified uid '{uid}' could not be found.",
                )

            comment_thread_previous = copy.deepcopy(comment_thread_latest)

            if comment_thread_edit_input.text is not None:
                if comment_thread_latest.author != self.user_info.id():
                    raise exceptions.ForbiddenException(
                        "Only the author can edit a comment thread."
                    )
                comment_thread_latest.text = comment_thread_edit_input.text

            if comment_thread_edit_input.status is not None:
                comment_thread_latest.status = comment_thread_edit_input.status

            if comment_thread_previous != comment_thread_latest:
                self.repos.comments_repository.edit_comment_thread(
                    comment_thread_latest,
                    comment_thread_previous,
                    self.user_info.id(),
                )

            return models.CommentThread.from_uid(
                comment_thread_latest.uid,
                self.repos.comments_repository.find_comment_thread_by_uid,
            )
        finally:
            self.repos.close()

    @db.transaction
    def edit_comment_thread(
        self, uid: str, comment_thread_edit_input: models.CommentThreadEditInput
    ) -> models.CommentThread:
        return self._edit_comment_thread(uid, comment_thread_edit_input)

    @db.transaction
    def delete_comment_thread(self, uid: str):
        comment_thread = self.repos.comments_repository.find_comment_thread_by_uid(uid)
        if comment_thread and comment_thread.author != self.user_info.id():
            raise exceptions.ForbiddenException(
                "Only the author can delete a comment thread."
            )
        self.repos.comments_repository.delete_comment_thread(uid)

    def get_all_comment_thread_replies(
        self, thread_uid: str
    ) -> list[models.CommentReply]:
        try:
            all_items = self.repos.comments_repository.find_all_comment_thread_replies(
                thread_uid
            )
            self.repos.comments_repository.close()
            return [models.CommentReply.from_ar(item_ar) for item_ar in all_items]
        finally:
            self.repos.close()

    def get_comment_thread_reply(self, uid: str) -> models.CommentReply:
        repos = MetaRepository()
        try:
            item = models.CommentReply.from_uid(
                uid, repos.comments_repository.find_comment_reply_by_uid
            )
            if item is None:
                raise exceptions.NotFoundException(
                    f"Comment reply with the specified uid '{uid}' could not be found.",
                )
            return item
        finally:
            self.repos.close()

    @db.transaction
    def create_comment_reply(
        self, thread_uid: str, create_input: models.CommentReplyCreateInput
    ) -> models.CommentReply:
        try:
            comment_reply_ar = CommentReplyAR.from_input_values(
                text=create_input.text,
                comment_thread_uid=thread_uid,
                author=self.user_info.id(),
                author_display_name=self.user_info.name,
                created_at=datetime.now(),
                generate_uid_callback=self.repos.comments_repository.generate_reply_uid,
            )

            # Validate that the comment thread exists
            if not self.repos.comments_repository.find_comment_thread_by_uid(
                thread_uid
            ):
                raise exceptions.NotFoundException(
                    f"Comment thread with the specified uid '{thread_uid}' could not be found."
                )

            if create_input.thread_status:
                self._edit_comment_thread(
                    thread_uid,
                    models.CommentThreadEditInput(
                        status=create_input.thread_status,
                    ),
                )

            self.repos.comments_repository.save_comment_reply(comment_reply_ar)
            return models.CommentReply.from_uid(
                comment_reply_ar.uid,
                self.repos.comments_repository.find_comment_reply_by_uid,
            )
        finally:
            self.repos.close()

    @db.transaction
    def edit_comment_thread_reply(
        self, uid: str, reply_edit_input: models.CommentReplyEditInput
    ) -> models.CommentReply:
        try:
            reply_latest = self.repos.comments_repository.find_comment_reply_by_uid(uid)
            if reply_latest is None:
                raise exceptions.NotFoundException(
                    f"Comment thread reply with the specified uid '{uid}' could not be found.",
                )

            reply_previous = copy.deepcopy(reply_latest)

            if reply_edit_input.text != reply_latest.text:
                if reply_latest.author != self.user_info.id():
                    raise exceptions.ForbiddenException(
                        "Only the author can edit a comment thread reply."
                    )
                reply_latest.text = reply_edit_input.text

                self.repos.comments_repository.edit_comment_reply(
                    reply_latest, reply_previous
                )

            return models.CommentReply.from_uid(
                reply_latest.uid,
                self.repos.comments_repository.find_comment_reply_by_uid,
            )
        finally:
            self.repos.close()

    @db.transaction
    def delete_comment_reply(self, uid: str):
        comment_reply = self.repos.comments_repository.find_comment_reply_by_uid(uid)
        if comment_reply and comment_reply.author != self.user_info.id():
            raise exceptions.ForbiddenException(
                "Only the author can delete a comment reply."
            )
        self.repos.comments_repository.delete_comment_reply(uid)
