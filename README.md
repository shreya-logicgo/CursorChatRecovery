# CursorChatRecovery

Recover and export Cursor chat history from local storage.

## Project structure

```
├── src
│   ├── main.py       # CLI entry point
│   ├── db.py         # Database access
│   ├── composer.py   # Composer chat handling
│   ├── bubble.py     # Bubble chat handling
│   ├── exporter.py   # Export logic
│   └── utils.py      # Shared utilities
├── output            # Exported chat files
├── tests
└── requirements.txt
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
