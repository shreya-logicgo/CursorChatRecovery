import json
from dataclasses import dataclass
from typing import Any, Optional

COMPOSER_KEY_PREFIX = "composerData:"

USER_MESSAGE = 1
ASSISTANT_MESSAGE = 2


@dataclass
class MessageHeader:
    bubble_id: str
    type: int
    server_bubble_id: Optional[str] = None

    @property
    def is_user(self) -> bool:
        return self.type == USER_MESSAGE

    @property
    def is_assistant(self) -> bool:
        return self.type == ASSISTANT_MESSAGE


@dataclass
class Composer:
    composer_id: str
    name: str
    headers: list[MessageHeader]
    raw: dict[str, Any]
    created_at: Optional[int] = None
    last_updated_at: Optional[int] = None
    unified_mode: Optional[str] = None
    status: Optional[str] = None
    is_agentic: Optional[bool] = None
    model_name: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "Composer":
        return cls.from_key_value(row["key"], row["value"])

    @classmethod
    def from_key_value(cls, key: str, value: str | bytes) -> "Composer":
        composer_id = key.removeprefix(COMPOSER_KEY_PREFIX)
        data = _load_json(value)
        return cls.from_data(composer_id, data)

    @classmethod
    def from_data(cls, composer_id: str, data: dict[str, Any]) -> "Composer":
        model_config = data.get("modelConfig") or {}
        return cls(
            composer_id=data.get("composerId") or composer_id,
            name=data.get("name") or "Untitled",
            headers=_parse_headers(data),
            raw=data,
            created_at=data.get("createdAt"),
            last_updated_at=data.get("lastUpdatedAt"),
            unified_mode=data.get("unifiedMode"),
            status=data.get("status"),
            is_agentic=data.get("isAgentic"),
            model_name=model_config.get("modelName"),
        )

    @property
    def message_count(self) -> int:
        return len(self.headers)

    @property
    def uses_legacy_map(self) -> bool:
        return bool(self.raw.get("conversationMap"))

    def bubble_ids(self) -> list[str]:
        return [header.bubble_id for header in self.headers]


def _load_json(value: str | bytes) -> dict[str, Any]:
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    return json.loads(value)


def _parse_headers(data: dict[str, Any]) -> list[MessageHeader]:
    headers = []
    for item in data.get("fullConversationHeadersOnly") or []:
        headers.append(
            MessageHeader(
                bubble_id=item["bubbleId"],
                type=item["type"],
                server_bubble_id=item.get("serverBubbleId"),
            )
        )
    return headers


def parse_composer_row(row) -> Composer:
    return Composer.from_row(row)


def load_composers(db) -> list[Composer]:
    composers = []
    for row in db.composer_records():
        if not row["value"]:
            continue
        composers.append(parse_composer_row(row))
    return composers


class ComposerParser:

    def __init__(self, db):
        self.db = db

    def find_project(self, project_name: str) -> list[dict[str, Any]]:
        conversations = []
        for row in self.db.composer_records():
            if not row["value"]:
                continue
            if project_name not in row["value"]:
                continue
            conversations.append(_load_json(row["value"]))
        return conversations
