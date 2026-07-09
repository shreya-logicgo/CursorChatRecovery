from pathlib import Path

from db import CursorDB
from composer import ComposerParser
from bubble import BubbleParser
from conversation import ConversationParser
from exporter import ConversationExporter
from markdown_exporter import MarkdownExporter
from validator import ConversationValidator


DB_PATH = r"C:\Users\LOGICGO\AppData\Roaming\Cursor\User\globalStorage\state.vscdb"
ERRORS_LOG = Path(__file__).resolve().parent.parent / "output" / "errors.log"

db = CursorDB(DB_PATH)

composer = ComposerParser(db)

bubbleParser = BubbleParser(db)

ERRORS_LOG.parent.mkdir(parents=True, exist_ok=True)
ERRORS_LOG.write_text("", encoding="utf-8")

conversationParser = ConversationParser(bubbleParser, errors_log=ERRORS_LOG)
validator = ConversationValidator()

conversations = composer.find_project("Viteezy-phase1")

exporter = ConversationExporter("output")
markdownExporter = MarkdownExporter("output/markdown")

exported = 0
parse_results = []

for composer in conversations:

    result = conversationParser.parse(composer)
    parse_results.append(result)

    if result.conversation is None:
        continue

    path = exporter.export(result.conversation)
    markdown_path = markdownExporter.export(result.conversation)

    print(f"Exported -> {path}")
    print(f"Exported -> {markdown_path}")

    exported += 1

print()
print(f"Recovered {exported} conversations.")
print()
validator.print_report(conversations, parse_results)
