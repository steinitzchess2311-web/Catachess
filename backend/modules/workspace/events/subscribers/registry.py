from modules.workspace.db.repos.activity_log_repo import ActivityLogRepository
from modules.workspace.db.repos.audit_log_repo import AuditLogRepository
from modules.workspace.db.repos.discussion_reaction_repo import DiscussionReactionRepository
from modules.workspace.db.repos.discussion_reply_repo import DiscussionReplyRepository
from modules.workspace.db.repos.discussion_thread_repo import DiscussionThreadRepository
from modules.workspace.db.repos.node_repo import NodeRepository
from modules.workspace.db.repos.notification_repo import NotificationRepository
from modules.workspace.db.repos.search_index_repo import SearchIndexRepository
from modules.workspace.db.repos.study_repo import StudyRepository
from modules.workspace.db.repos.user_repo import UserRepository
from modules.workspace.db.repos.variation_repo import VariationRepository
from modules.workspace.events.subscribers.activity_logger import ActivityLogger
from modules.workspace.events.subscribers.audit_logger import AuditLogger
from modules.workspace.events.subscribers.mention_notifier import MentionNotifier
from modules.workspace.events.subscribers.notification_creator import NotificationCreator
import logging

from modules.workspace.db.session import get_db_config
from modules.workspace.events.subscribers.search_indexer import SearchIndexer


def register_all_subscribers(bus, session) -> None:
    logger = logging.getLogger(__name__)
    config = get_db_config()

    def _wrap(handler_factory):
        async def _handler(event) -> None:
            async with config.async_session_maker() as sub_session:
                try:
                    handler = handler_factory(sub_session)
                    await handler(event)
                    await sub_session.commit()
                except Exception as exc:
                    await sub_session.rollback()
                    logger.warning("Subscriber failed: %s", exc)
        return _handler

    bus.subscribe(
        _wrap(
            lambda sub_session: SearchIndexer(
                DiscussionThreadRepository(sub_session),
                DiscussionReplyRepository(sub_session),
                SearchIndexRepository(sub_session),
                node_repo=NodeRepository(sub_session),
                study_repo=StudyRepository(sub_session),
                variation_repo=VariationRepository(sub_session),
            ).handle_event
        )
    )

    bus.subscribe(
        _wrap(
            lambda sub_session: MentionNotifier(
                bus,
                DiscussionThreadRepository(sub_session),
                DiscussionReplyRepository(sub_session),
                UserRepository(sub_session),
            ).handle_event
        )
    )
    bus.subscribe(
        _wrap(
            lambda sub_session: NotificationCreator(
                NotificationRepository(sub_session),
                DiscussionThreadRepository(sub_session),
                DiscussionReplyRepository(sub_session),
                DiscussionReactionRepository(sub_session),
            ).handle_event
        )
    )
    bus.subscribe(
        _wrap(lambda sub_session: ActivityLogger(ActivityLogRepository(sub_session)).handle_event)
    )
    bus.subscribe(
        _wrap(lambda sub_session: AuditLogger(AuditLogRepository(sub_session)).handle_event)
    )
