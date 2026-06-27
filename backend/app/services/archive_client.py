from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ArchiveMessage:
    seq: int
    msg_id: str
    action: str
    from_user: str
    to_user: str
    msg_type: str
    content: str
    msg_time: int
    room_id: str | None = None


class ChatArchiveClient:
    async def fetch_messages(self, seq: int, limit: int = 100) -> list[ArchiveMessage]:
        raise NotImplementedError


class StubArchiveClient(ChatArchiveClient):
    async def fetch_messages(self, seq: int, limit: int = 100) -> list[ArchiveMessage]:
        return []


class FinanceSdkArchiveClient(ChatArchiveClient):
    def __init__(self, sdk_path: str, corp_id: str, secret: str, private_key_path: str):
        self.sdk_path = sdk_path
        self.corp_id = corp_id
        self.secret = secret
        self.private_key_path = private_key_path

    async def fetch_messages(self, seq: int, limit: int = 100) -> list[ArchiveMessage]:
        raise RuntimeError(
            "Official WeCom Finance SDK is not loaded. Mount libWeWorkFinanceSdk_C.so "
            "and implement ctypes binding in FinanceSdkArchiveClient for Linux production."
        )


def parse_plaintext_message(raw: dict[str, Any]) -> ArchiveMessage | None:
    if raw.get("roomid"):
        return None
    if raw.get("msgtype") != "text":
        return None
    text = raw.get("text") or {}
    return ArchiveMessage(
        seq=int(raw["seq"]),
        msg_id=raw["msgid"],
        action=raw.get("action", "send"),
        from_user=raw.get("from", ""),
        to_user=(raw.get("tolist") or [""])[0],
        msg_type="text",
        content=text.get("content", ""),
        msg_time=int(raw.get("msgtime", 0)),
        room_id=None,
    )
