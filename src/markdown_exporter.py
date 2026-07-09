import os
import re
from datetime import datetime, timezone


class MarkdownExporter:

    def __init__(self, output_dir="output/markdown"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _safe_filename(self, name: str) -> str:
        if not name:
            name = "Untitled"

        name = re.sub(r'[<>:"/\\|?*]', "_", name)
        return name[:150]

    def _format_created_at(self, value) -> str:
        if value is None:
            return ""

        if isinstance(value, (int, float)):
            created = datetime.fromtimestamp(value / 1000, tz=timezone.utc)
            return created.strftime("%Y-%m-%d")

        if isinstance(value, str):
            return value[:10]

        return str(value)

    def _role_heading(self, role: str) -> str:
        if role == "user":
            return "## 👤 User"
        if role == "assistant":
            return "## 🤖 Assistant"
        return f"## {role.title()}"

    def export(self, conversation) -> str:
        metadata = conversation["metadata"]
        title = metadata["title"]

        lines = [
            f"# {title}",
            "",
            f"**Workspace:** {metadata.get('workspace', '')}",
            "",
            f"**Created:** {self._format_created_at(metadata.get('createdAt'))}",
            "",
            "---",
            "",
        ]

        for message in conversation["messages"]:
            lines.extend(
                [
                    self._role_heading(message["role"]),
                    "",
                    message["text"],
                    "",
                    "---",
                    "",
                ]
            )

        path = os.path.join(self.output_dir, self._safe_filename(title) + ".md")

        with open(path, "w", encoding="utf-8") as file:
            file.write("\n".join(lines).rstrip() + "\n")

        return path
