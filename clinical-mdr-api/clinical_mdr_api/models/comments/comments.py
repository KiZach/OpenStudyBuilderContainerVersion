from datetime import datetime
from typing import Callable, Self

from pydantic import Field

from clinical_mdr_api.domains.comments.comments import (
    CommentReplyAR,
    CommentThreadAR,
    CommentThreadStatus,
    CommentTopicAR,
)
from clinical_mdr_api.models.utils import BaseModel


class CommentReply(BaseModel):
    uid: str = Field(
        ...,
        title="uid",
        description="Unique id of comment reply",
    )
    comment_thread_uid: str = Field(
        ...,
        description="Unique id of comment thread that this comment replies to",
    )

    text: str = Field(...)
    author: str = Field(...)
    author_display_name: str = Field(...)
    created_at: datetime = Field(...)
    modified_at: datetime | None = Field(
        None,
        nullable=True,
    )

    @classmethod
    def from_uid(
        cls,
        uid: str,
        find_by_uid: Callable[[str], CommentReplyAR | None],
    ) -> Self | None:
        item = None
        item_ar: CommentReplyAR = find_by_uid(uid)
        if item_ar is not None:
            item = CommentReply.from_ar(item_ar)
        return item

    @classmethod
    def from_ar(
        cls,
        comment_thread_ar: CommentReplyAR,
    ) -> Self:
        return CommentReply(
            uid=comment_thread_ar.uid,
            comment_thread_uid=comment_thread_ar.comment_thread_uid,
            text=comment_thread_ar.text,
            author=comment_thread_ar.author,
            author_display_name=comment_thread_ar.author_display_name,
            created_at=comment_thread_ar.created_at,
            modified_at=comment_thread_ar.modified_at,
        )


class CommentReplyCreateInput(BaseModel):
    text: str = Field(..., description="", min_length=1)
    thread_status: CommentThreadStatus | None = Field(
        None, description="New comment thread status after reply"
    )


class CommentReplyEditInput(BaseModel):
    text: str | None = Field(None, description="Updated reply text", min_length=1)


class CommentThread(BaseModel):
    uid: str = Field(
        ...,
        title="uid",
        description="Unique id of comment thread",
    )

    text: str = Field(...)
    topic_path: str = Field(...)
    author: str = Field(...)
    author_display_name: str = Field(...)
    status: CommentThreadStatus = Field(...)
    created_at: datetime = Field(...)
    modified_at: datetime | None = Field(
        None,
        nullable=True,
    )
    status_modified_at: datetime | None = Field(
        None,
        nullable=True,
    )
    status_modified_by: str | None = Field(
        None,
        nullable=True,
    )
    replies: list[CommentReply] = Field([])

    @classmethod
    def from_uid(
        cls,
        uid: str,
        find_by_uid: Callable[[str], CommentThreadAR | None],
    ) -> Self | None:
        comment_thread = None
        comment_thread_ar: CommentThreadAR = find_by_uid(uid)
        if comment_thread_ar is not None:
            comment_thread = CommentThread.from_ar(comment_thread_ar)
        return comment_thread

    @classmethod
    def from_ar(
        cls,
        comment_thread_ar: CommentThreadAR,
    ) -> Self:
        return CommentThread(
            uid=comment_thread_ar.uid,
            text=comment_thread_ar.text,
            topic_path=comment_thread_ar.topic_path,
            status=comment_thread_ar.status,
            author=comment_thread_ar.author,
            author_display_name=comment_thread_ar.author_display_name,
            created_at=comment_thread_ar.created_at,
            modified_at=comment_thread_ar.modified_at,
            status_modified_at=comment_thread_ar.status_modified_at,
            status_modified_by=comment_thread_ar.status_modified_by,
            replies=[
                CommentReply.from_ar(reply_ar) for reply_ar in comment_thread_ar.replies
            ],
        )


class CommentThreadCreateInput(BaseModel):
    text: str = Field(..., description="", min_length=1)
    topic_path: str = Field(..., min_length=1)


class CommentThreadEditInput(BaseModel):
    text: str | None = Field(None, description="Updated thread text", min_length=1)
    status: CommentThreadStatus | None = Field(
        None, description="Updated thread status"
    )


class CommentTopic(BaseModel):
    uid: str = Field(
        ...,
        title="uid",
        description="Unique id of comment topic",
    )

    topic_path: str = Field(...)
    threads_active_count: int = Field(...)
    threads_resolved_count: int = Field(...)

    @classmethod
    def from_uid(
        cls,
        uid: str,
        find_by_uid: Callable[[str], CommentThreadAR | None],
    ) -> Self | None:
        comment_thread = None
        comment_thread_ar: CommentThreadAR = find_by_uid(uid)
        if comment_thread_ar is not None:
            comment_thread = CommentThread.from_ar(comment_thread_ar)
        return comment_thread

    @classmethod
    def from_ar(
        cls,
        comment_topic_ar: CommentTopicAR,
    ) -> Self:
        return CommentTopic(
            uid=comment_topic_ar.uid,
            topic_path=comment_topic_ar.topic_path,
            threads_active_count=comment_topic_ar.threads_active_count,
            threads_resolved_count=comment_topic_ar.threads_resolved_count,
        )
