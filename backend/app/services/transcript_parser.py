from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class ParsedTranscriptMessage:
    from_user: str
    to_user: str
    content: str
    msg_time: datetime
    from_customer: bool


SALES_PREFIXES = ("销售", "我", "本人", "顾问", "客服", "业务")
CUSTOMER_PREFIXES = ("客户", "对方", "用户", "买家", "他", "她")


def parse_transcript(
    transcript: str,
    sales_userid: str,
    external_userid: str,
    base_time: datetime | None = None,
) -> list[ParsedTranscriptMessage]:
    base = base_time or datetime.utcnow()
    messages: list[ParsedTranscriptMessage] = []
    for raw_line in transcript.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        speaker, content = _split_speaker(line)
        content = content.strip()[:500]
        if not content:
            continue
        from_customer = _is_customer_speaker(speaker)
        from_user = external_userid if from_customer else sales_userid
        to_user = sales_userid if from_customer else external_userid
        messages.append(
            ParsedTranscriptMessage(
                from_user=from_user,
                to_user=to_user,
                content=content,
                msg_time=base + timedelta(seconds=len(messages)),
                from_customer=from_customer,
            )
        )
    return messages


def _split_speaker(line: str) -> tuple[str, str]:
    for separator in ("：", ":"):
        if separator in line:
            speaker, content = line.split(separator, 1)
            return speaker.strip(), content
    return "客户", line


def _is_customer_speaker(speaker: str) -> bool:
    normalized = speaker.strip().lower()
    if any(prefix.lower() in normalized for prefix in SALES_PREFIXES):
        return False
    if any(prefix.lower() in normalized for prefix in CUSTOMER_PREFIXES):
        return True
    return True
