import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
from urllib.parse import unquote

_PATH_RE = re.compile(
    r"([a-zA-Z]:%2F[a-zA-Z0-9._\-/]+|[a-zA-Z]:[/\\][a-zA-Z0-9._\-/\\]+)",
    re.IGNORECASE,
)
_FSPATH_RE = re.compile(r'"fsPath"\s*:\s*"([^"]+)"')

ROLE_MAP = {
    1: "user",
    2: "assistant",
}


@dataclass
class ParseResult:
    conversation: Optional[dict[str, Any]]
    missing_bubbles: list[str]
    skipped_bubbles: list[str]


class ConversationParser:

    def __init__(self, bubble_parser, errors_log: str | Path | None = None):
        self.bubble_parser = bubble_parser
        self.errors_log = Path(errors_log) if errors_log else None

    def parse(self, composer: dict[str, Any]) -> ParseResult:
        messages = []
        missing_bubbles: list[str] = []
        skipped_bubbles: list[str] = []
        title = composer.get("name") or "Untitled"

        for header in composer.get("fullConversationHeadersOnly") or []:
            bubble_id = header["bubbleId"]
            bubble = self.bubble_parser.load(bubble_id)
            if bubble is None:
                missing_bubbles.append(bubble_id)
                continue

            text = bubble.get("text", "").strip()

            if not text:
                skipped_bubbles.append(bubble_id)
                continue

            role = ROLE_MAP.get(bubble.get("type", header.get("type")), "unknown")

            messages.append(
                {
                    "role": role,
                    "text": text,
                    "bubbleId": bubble_id,
                    "createdAt": bubble.get("createdAt"),
                }
            )

        if self.errors_log and (missing_bubbles or skipped_bubbles):
            self._write_errors(title, missing_bubbles, skipped_bubbles)

        conversation = None
        if messages:
            conversation = {
                "metadata": {
                    "title": title,
                    "workspace": _extract_workspace(composer),
                    "composerId": composer.get("composerId"),
                    "createdAt": composer.get("createdAt"),
                    "updatedAt": composer.get("lastUpdatedAt"),
                    "messageCount": len(messages),
                },
                "messages": messages,
            }

        return ParseResult(
            conversation=conversation,
            missing_bubbles=missing_bubbles,
            skipped_bubbles=skipped_bubbles,
        )

    def _write_errors(
        self,
        title: str,
        missing_bubbles: list[str],
        skipped_bubbles: list[str],
    ) -> None:
        lines = [f"Conversation: {title}", ""]

        if missing_bubbles:
            lines.append("Bubble missing:")
            lines.extend(missing_bubbles)
            lines.append("")

        if skipped_bubbles:
            lines.append("Skipped.")
            lines.extend(skipped_bubbles)
            lines.append("")

        self.errors_log.parent.mkdir(parents=True, exist_ok=True)
        with self.errors_log.open("a", encoding="utf-8") as log_file:
            log_file.write("\n".join(lines))


def _extract_workspace(composer: dict[str, Any]) -> str:
    candidates: list[str] = []

    workspace_identifier = composer.get("workspaceIdentifier")
    if isinstance(workspace_identifier, dict):
        uri = workspace_identifier.get("uri") or {}
        for key in ("fsPath", "external", "path"):
            value = uri.get(key)
            if value:
                candidates.append(_normalize_workspace_path(value))

    for uri in composer.get("workspaceUris") or []:
        if uri:
            candidates.append(_normalize_workspace_path(uri))

    context = composer.get("context") or {}
    for selection_key in ("folderSelections", "fileSelections"):
        for item in context.get(selection_key) or []:
            path = _path_from_selection(item)
            workspace = _workspace_from_file_path(path)
            if workspace:
                candidates.append(workspace)

    for match in _PATH_RE.finditer(json.dumps(composer)):
        path = _decode_path(match.group(1))
        workspace = _workspace_from_file_path(path)
        if workspace:
            candidates.append(workspace)

    for match in _FSPATH_RE.finditer(json.dumps(composer)):
        workspace = _workspace_from_file_path(match.group(1))
        if workspace:
            candidates.append(workspace)

    return _best_workspace(candidates)


def _best_workspace(candidates: list[str]) -> str:
    valid = [candidate for candidate in candidates if _looks_like_workspace(candidate)]
    if not valid:
        return ""
    return max(valid, key=_workspace_rank)


def _workspace_rank(path: str) -> tuple[int, int]:
    path = path.replace("\\", "/")
    parts = [part for part in path.split("/") if part]
    score = 0

    if parts and re.match(r"^[a-zA-Z]:$", parts[0]):
        score += 10

    if 2 <= len(parts) <= 5:
        score += 5

    return (score, len(path))


def _looks_like_workspace(path: str) -> bool:
    if len(path) <= 3:
        return False

    path = path.replace("\\", "/")
    parts = [part for part in path.split("/") if part]

    if len(parts) < 2:
        return False

    if not re.match(r"^[a-zA-Z]:$", parts[0]):
        return False

    if parts[1].startswith("d-") and "-" in parts[1]:
        return False

    if any(len(part) > 64 for part in parts):
        return False

    return True


def _path_from_selection(item: Any) -> str:
    if isinstance(item, str):
        return item

    if not isinstance(item, dict):
        return ""

    for key in ("fsPath", "path", "relativePath", "external"):
        value = item.get(key)
        if value:
            return _normalize_workspace_path(value)

    uri = item.get("uri")
    if isinstance(uri, dict):
        for key in ("fsPath", "path", "external"):
            value = uri.get(key)
            if value:
                return _normalize_workspace_path(value)
    elif isinstance(uri, str):
        return _normalize_workspace_path(uri)

    return ""


def _decode_path(path: str) -> str:
    return unquote(path.replace("%2F", "/").replace("%3A", ":"))


def _normalize_workspace_path(path: str) -> str:
    path = _decode_path(path)
    if path.startswith("file:///"):
        path = path.removeprefix("file:///")
    return path.replace("\\", "/")


def _workspace_from_file_path(path: str) -> str:
    if not path:
        return ""

    path = _normalize_workspace_path(path)
    parts = [part for part in path.split("/") if part]

    if not parts:
        return ""

    if "." in parts[-1] and not parts[-1].startswith("."):
        parts = parts[:-1]

    if not parts:
        return ""

    if re.match(r"^[a-zA-Z]:$", parts[0]):
        if len(parts) >= 3:
            return "/".join(parts[:3])
        return "/".join(parts)

    if len(parts) >= 2:
        return "/".join(parts[:2])

    return parts[0]
