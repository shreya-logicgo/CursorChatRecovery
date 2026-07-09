# CursorChatRecovery

Recover and export Cursor Agent/Composer chat history from Cursor's local SQLite database.

This tool reads conversation metadata and message bubbles stored by Cursor, rebuilds each conversation in a stable internal format, validates recovery integrity, and exports results as JSON and Markdown.

It is **read-only** — it never modifies your Cursor database.

---

## What this tool does

1. **Reads** Cursor's global database (`state.vscdb`)
2. **Finds** conversations linked to a project by searching composer records
3. **Loads** message bubbles in Cursor's original order
4. **Skips** missing and empty bubbles
5. **Validates** bubble counts and recovery statistics
6. **Exports** each conversation to:
   - `output/*.json` — structured data with metadata
   - `output/markdown/*.md` — human-readable transcripts
7. **Logs** skipped/missing bubbles to `output/errors.log`

---

## How to run it

### Prerequisites

- Python 3.10+
- Cursor installed (with existing chat history)

### Setup

```bash
git clone <repository-url>
cd CursorChatRecovery

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### Configure

Edit `src/main.py` and set:

1. **`DB_PATH`** — path to your Cursor global database

   Windows (default):

   ```text
   C:\Users\<USERNAME>\AppData\Roaming\Cursor\User\globalStorage\state.vscdb
   ```

   macOS:

   ```text
   ~/Library/Application Support/Cursor/User/globalStorage/state.vscdb
   ```

   Linux:

   ```text
   ~/.config/Cursor/User/globalStorage/state.vscdb
   ```

2. **Project filter** — change the project name passed to `find_project()`:

   ```python
   conversations = composer.find_project("Viteezy-phase1")
   ```

   This matches any composer record whose JSON contains that string (usually a folder or project name).

### Run

From the project root:

```bash
python src/main.py
```

### Output

```text
Exported -> output\Code completeness assessment.json
Exported -> output/markdown\Code completeness assessment.md
...
Recovered 16 conversations.

Conversation
--------------------------------
Title : Code completeness assessment

Messages : 41

User : 12

Assistant : 29

Empty : 39

Recovery Summary
--------------------------------
Recovered Conversations : 16

Skipped Empty Conversations : 12

Recovered Messages : 355

Missing Bubbles : 0

Empty Bubbles : 780
```

---

## Folder structure

```text
CursorChatRecovery/
├── src/
│   ├── main.py              # Entry point
│   ├── db.py                # SQLite access (CursorDB)
│   ├── composer.py          # Composer record parsing
│   ├── bubble.py            # Bubble message loading
│   ├── conversation.py      # Conversation assembly (Version 1 model)
│   ├── exporter.py          # JSON export
│   ├── markdown_exporter.py # Markdown export
│   └── validator.py         # Recovery validation & statistics
├── output/                  # Generated exports (gitignored)
│   ├── *.json
│   ├── markdown/
│   │   └── *.md
│   └── errors.log
├── tests/
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Internal data model (Version 1)

Each exported JSON file uses this structure:

```json
{
  "metadata": {
    "title": "Code completeness assessment",
    "workspace": "D:/shreya_gandhi/Viteezy-phase1",
    "composerId": "dde1dc66-561c-481a-838c-233b0a046019",
    "createdAt": 1775638419625,
    "updatedAt": 1775888502081,
    "messageCount": 41
  },
  "messages": [
    {
      "role": "user",
      "text": "what is missing in this code",
      "bubbleId": "67454574-b756-4306-90a1-48ff14b8395d",
      "createdAt": "2026-04-08T08:58:35.235Z"
    },
    {
      "role": "assistant",
      "text": "I'll quickly inspect `package.json`...",
      "bubbleId": "48646fc4-538c-410b-a135-b72878888605",
      "createdAt": "2026-04-08T08:58:40.541Z"
    }
  ]
}
```

Markdown export example:

```markdown
# Code completeness assessment

**Workspace:** D:/shreya_gandhi/Viteezy-phase1

**Created:** 2026-04-08

---

## 👤 User

what is missing in this code

---

## 🤖 Assistant

I'll quickly inspect `package.json`...
```

---

## How recovery works

```text
state.vscdb
    │
    ├─ composerData:{composerId}     → conversation metadata + message order
    └─ bubbleId:{composerId}:{id}    → individual message content

composer.find_project("project-name")
    ↓
ConversationParser.parse(composer)
    ↓
load bubbles in fullConversationHeadersOnly order
    ↓
skip missing / empty bubbles
    ↓
export JSON + Markdown
```

Message order is taken directly from `fullConversationHeadersOnly`. **No sorting is applied.**

---

## Limitations

- **Hardcoded configuration** — database path and project filter are currently set in `main.py` (no CLI yet).
- **Project matching is string-based** — `find_project()` searches for a substring inside composer JSON, not an exact workspace ID.
- **Empty bubbles are skipped** — assistant placeholders and tool-only bubbles with no text are excluded.
- **Empty conversations are skipped** — composers with zero recoverable messages are not exported.
- **Text-only recovery** — tool calls, diffs, checkpoints, images, and thinking blocks are not exported.
- **Global database only** — reads `globalStorage/state.vscdb`; workspace-level indexes are not used for discovery.
- **Windows-first development** — tested primarily on Windows paths; other platforms require updating `DB_PATH`.
- **Close Cursor for best results** — reading the database while Cursor is writing to it may produce inconsistent results (this tool does not write to the DB).

---

## Supported Cursor version

Tested against Cursor's storage format used in **early 2026 (Cursor 3.x era)** on **Windows**.

Observed during development:

| Item | Value |
|------|-------|
| Database | `globalStorage/state.vscdb` |
| Composer keys | `composerData:{uuid}` |
| Bubble keys | `bubbleId:{composerId}:{bubbleId}` |
| Bubble format version | `_v: 3` |
| Message index | `fullConversationHeadersOnly` |
| Role mapping | `1` → user, `2` → assistant |

Cursor does not publish a stable schema. Storage formats may change between Cursor releases. If recovery breaks after an update, check whether key patterns or JSON structure have changed.

---

## Example recovery results

From a real run filtering project `Viteezy-phase1`:

| Metric | Count |
|--------|-------|
| Composer records matched | 28 |
| Conversations exported | 16 |
| Empty conversations skipped | 12 |
| Messages recovered | 355 |
| Missing bubbles | 0 |
| Empty bubbles skipped | 780 |

Sample conversations recovered:

- Code completeness assessment (41 messages)
- Email communication logic for unsubscribed customers (80 messages)
- Inactive warning modal flow changes (94 messages)

---

## Future roadmap

- [ ] **CLI interface** — `typer`-based commands for DB path, project name, and output directory
- [ ] **Auto-detect database path** — Windows, macOS, and Linux support
- [ ] **Workspace-aware discovery** — match by `workspaceIdentifier` and `composer.composerHeaders`
- [ ] **Export options** — JSON only, Markdown only, or both
- [ ] **Tool call export** — include file edits, terminal commands, and tool results
- [ ] **Checkpoint awareness** — document or export agent workspace snapshots
- [ ] **Search & filter** — by date, title, model, or message content
- [ ] **Import path** — restore or re-attach conversations to a workspace
- [ ] **Automated tests** — fixture-based tests using sample composer/bubble JSON
- [ ] **Batch recovery** — recover all projects in one run

---

## Safety

- This tool **only reads** from `state.vscdb`.
- Exported files may contain **sensitive code, prompts, and project paths** — `output/` is gitignored for this reason.
- Consider backing up your database before experimenting with any recovery tools that write data.

---

## License

Add a license before public distribution.
