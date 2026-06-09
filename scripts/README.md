# Data Pipeline Scripts

These offline scripts build the data assets (`quran.db`, `embeddings.bin`) that the app ships with.
They are NOT part of the app bundle — run them locally to regenerate assets.

See GitHub Issues #3, #4, #5 for implementation details.

## Prerequisites
- Python 3.10+
- See each script for its own requirements

## Setup

```bash
python3 -m venv scripts/.venv
source scripts/.venv/bin/activate   # Windows: scripts\.venv\Scripts\activate
pip install -r scripts/requirements.txt
```

## `build_db.py` — Faithful text database (Issue #3)

Downloads and stores verbatim:
- **Arabic text**: Tanzil Uthmani v1.1 (with full tashkeel / diacritics)
- **Translations**: Yusuf Ali (1934) and Pickthall (1930) from Tanzil
- **Tafsirs**: al-Jalalayn (Arabic) from AlQuran.cloud and Ibn Kathir (Arabic) from Quran.com

Output: `public/quran.db`

**CRITICAL**: Arabic text is stored byte-for-byte as received from the source. No normalisation,
diacritic stripping, or Unicode NF conversion is performed at any stage.

### Usage

```bash
# Full build (all 114 surahs, ~30 seconds)
python scripts/build_db.py

# Custom output path
python scripts/build_db.py --output /path/to/output.db

# Test run — first 3 surahs only
python scripts/build_db.py --limit 3
```

### Data sources

| Data | Source | URL |
|------|--------|-----|
| Arabic (Uthmani) | Tanzil.net v1.1 | `tanzil.net/pub/download/index.php?quranType=uthmani&outType=txt-2&…` |
| Yusuf Ali translation | Tanzil.net | `tanzil.net/trans/en.yusufali` |
| Pickthall translation | Tanzil.net | `tanzil.net/trans/en.pickthall` |
| Tafsir al-Jalalayn (ar) | AlQuran.cloud | `api.alquran.cloud/v1/quran/ar.jalalayn` |
| Tafsir Ibn Kathir (ar) | Quran.com API | `api.quran.com/api/v4/tafsirs/14/by_chapter/{n}` |

---

## `verify_fidelity.py` — DB integrity checks (Issue #3)

Verifies the generated `quran.db` is complete and contains the expected text.

### Checks performed

**Row counts**
- `ayahs`: must be exactly 6236
- `translations` (yusufali): must be exactly 6236
- `translations` (pickthall): must be exactly 6236
- `tafsirs` (jalalayn): at least 6000
- `tafsirs` (ibnkathir): at least 6000

**Arabic spot-checks** (base-letter comparisons to handle diacritic ordering)
- 1:1 starts with `بِسْمِ`
- 2:255 (Ayat al-Kursi) starts with Allah
- 112:1 contains `قُلْ هُوَ … أَحَدٌ`

**Translation spot-checks**
- Yusuf Ali 1:1 contains "In the name of Allah"
- Pickthall 1:1 contains "In the name of Allah"

**Tafsir spot-checks**
- jalalayn 1:1 non-empty
- ibnkathir 1:1 non-empty (after stripping HTML)

### Usage

```bash
# Verify default database (public/quran.db)
python scripts/verify_fidelity.py

# Verify a custom database
python scripts/verify_fidelity.py --db /path/to/quran.db
```

Exits 0 if all checks pass, 1 if any fail.

---

## Scripts (to be added in subsequent issues)
- `build_crossrefs.py` — ingests QUL cross-reference datasets into `quran.db`
- `build_embeddings.py` — precomputes multilingual embeddings into `embeddings.bin`
