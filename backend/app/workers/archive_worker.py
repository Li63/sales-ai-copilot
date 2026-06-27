from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import ChatMessage
from app.services.archive_client import ChatArchiveClient


class ArchiveWorker:
    def __init__(self, db: Session, archive_client: ChatArchiveClient):
        self.db = db
        self.archive_client = archive_client

    async def pull_once(self, seq: int) -> int:
        latest_seq = seq
        messages = await self.archive_client.fetch_messages(seq)
        for item in messages:
            latest_seq = max(latest_seq, item.seq)
            if item.room_id or item.msg_type != "text":
                continue
            self.db.add(
                ChatMessage(
                    msg_id=item.msg_id,
                    seq=item.seq,
                    action=item.action,
                    from_user=item.from_user,
                    to_user=item.to_user,
                    msg_type=item.msg_type,
                    content=item.content,
                    msg_time=datetime.fromtimestamp(item.msg_time / 1000 if item.msg_time > 10_000_000_000 else item.msg_time),
                    room_id=None,
                )
            )
            try:
                self.db.commit()
            except IntegrityError:
                self.db.rollback()
        return latest_seq
