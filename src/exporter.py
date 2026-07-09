import json
import os
import re


class ConversationExporter:

    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _safe_filename(self, name: str) -> str:
        if not name:
            name = "Untitled"

        name = re.sub(r'[<>:"/\\|?*]', "_", name)
        return name[:150]

    def export(self, conversation):

        filename = self._safe_filename(conversation["metadata"]["title"]) + ".json"

        path = os.path.join(self.output_dir, filename)

        with open(path, "w", encoding="utf8") as f:
            json.dump(
                conversation,
                f,
                indent=2,
                ensure_ascii=False,
            )

        return path
