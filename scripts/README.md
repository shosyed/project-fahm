# Data Pipeline Scripts

These offline scripts build the data assets (`quran.db`, `embeddings.bin`) that the app ships with.
They are NOT part of the app bundle — run them locally to regenerate assets.

See GitHub Issues #3, #4, #5 for implementation details.

## Prerequisites
- Python 3.10+
- See each script for its own requirements

## Scripts (to be added in subsequent issues)
- `build_db.py` — fetches Arabic text, translations, and tafsirs and builds `quran.db`
- `build_crossrefs.py` — ingests QUL cross-reference datasets into `quran.db`
- `build_embeddings.py` — precomputes multilingual embeddings into `embeddings.bin`
