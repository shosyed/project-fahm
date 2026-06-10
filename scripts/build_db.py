"""
build_db.py — Build the faithful text SQLite database for project-fahm.

Downloads Arabic text (Tanzil Uthmani), two English translations (Yusuf Ali,
Pickthall), and two Arabic tafsirs (al-Jalalayn, Ibn Kathir) from authoritative
open sources and inserts them verbatim into quran.db.

CRITICAL: Arabic text and translations are stored verbatim. Do not normalise,
strip diacritics, change Unicode normalisation forms, or otherwise alter the text.

Usage:
    python scripts/build_db.py
    python scripts/build_db.py --output /path/to/output.db
    python scripts/build_db.py --limit 3   # first 3 surahs only (for testing)
"""

import argparse
import gzip
import re
import shutil
import sqlite3
import sys
from datetime import date, timezone, datetime
from pathlib import Path

import requests
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

TANZIL_ARABIC_URL = (
    "https://tanzil.net/pub/download/index.php"
    "?quranType=uthmani&outType=txt-2&marks=true&sajdah=true&agree=true"
)
TANZIL_YUSUFALI_URL = "https://tanzil.net/trans/en.yusufali"
TANZIL_PICKTHALL_URL = "https://tanzil.net/trans/en.pickthall"

ALQURAN_JALALAYN_URL = "https://api.alquran.cloud/v1/quran/ar.jalalayn"

# Quran.com API for Ibn Kathir Arabic tafsir (resource id=14, slug=ar-tafsir-ibn-kathir)
QURANCOM_IBNKATHIR_CHAPTER_URL = (
    "https://api.quran.com/api/v4/tafsirs/14/by_chapter/{chapter}?per_page=500"
)

TODAY = date.today().isoformat()


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS ayahs (
            surah  INTEGER NOT NULL,
            ayah   INTEGER NOT NULL,
            arabic TEXT    NOT NULL,
            PRIMARY KEY (surah, ayah)
        );

        CREATE TABLE IF NOT EXISTS translations (
            surah INTEGER NOT NULL,
            ayah  INTEGER NOT NULL,
            key   TEXT    NOT NULL,
            text  TEXT    NOT NULL,
            PRIMARY KEY (surah, ayah, key)
        );

        CREATE TABLE IF NOT EXISTS tafsirs (
            surah INTEGER NOT NULL,
            ayah  INTEGER NOT NULL,
            key   TEXT    NOT NULL,
            text  TEXT    NOT NULL,
            PRIMARY KEY (surah, ayah, key)
        );

        CREATE TABLE IF NOT EXISTS metadata (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    conn.commit()


def upsert_metadata(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
        (key, value),
    )


# ---------------------------------------------------------------------------
# Fetch helpers
# ---------------------------------------------------------------------------

def fetch_text(url: str, description: str) -> str:
    """Download a URL and return the response body as text. Exits on error."""
    print(f"  Fetching {description} ...")
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"ERROR: Failed to download {description}: {exc}", file=sys.stderr)
        sys.exit(1)
    return resp.text


def fetch_json(url: str, description: str) -> dict:
    """Download a URL and return parsed JSON. Exits on error."""
    print(f"  Fetching {description} ...")
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"ERROR: Failed to download {description}: {exc}", file=sys.stderr)
        sys.exit(1)
    try:
        return resp.json()
    except ValueError as exc:
        print(f"ERROR: Invalid JSON from {description}: {exc}", file=sys.stderr)
        sys.exit(1)


def parse_tanzil_pipe(text: str) -> list[tuple[int, int, str]]:
    """
    Parse Tanzil pipe-separated format: surah|ayah|text
    Comment lines start with '#'. Returns list of (surah, ayah, text) tuples.
    """
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("|", 2)
        if len(parts) != 3:
            print(f"WARNING: Skipping malformed line: {line[:80]!r}", file=sys.stderr)
            continue
        try:
            surah = int(parts[0])
            ayah = int(parts[1])
        except ValueError:
            print(f"WARNING: Non-integer surah/ayah: {line[:80]!r}", file=sys.stderr)
            continue
        rows.append((surah, ayah, parts[2]))
    return rows


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_arabic(conn: sqlite3.Connection, limit: int | None) -> int:
    """Fetch Tanzil Uthmani Arabic text and insert into ayahs table."""
    print("\n[1/5] Arabic text (Tanzil Uthmani)")
    raw = fetch_text(TANZIL_ARABIC_URL, "Tanzil Uthmani Arabic")

    rows = parse_tanzil_pipe(raw)
    if limit is not None:
        rows = [r for r in rows if r[0] <= limit]

    with conn:
        for surah, ayah, text in tqdm(rows, desc="  Inserting Arabic", unit="ayah"):
            conn.execute(
                "INSERT OR REPLACE INTO ayahs (surah, ayah, arabic) VALUES (?, ?, ?)",
                (surah, ayah, text),
            )
        upsert_metadata(conn, "arabic_source", "Tanzil Uthmani v1.1")
        upsert_metadata(conn, "arabic_url", TANZIL_ARABIC_URL)
        upsert_metadata(conn, "arabic_retrieved", TODAY)

    count = conn.execute("SELECT COUNT(*) FROM ayahs").fetchone()[0]
    print(f"  Rows in ayahs: {count}")
    return count


def load_translation(conn: sqlite3.Connection, key: str, url: str, limit: int | None) -> int:
    """Fetch a Tanzil translation and insert into translations table."""
    print(f"\n[?] Translation: {key}")
    raw = fetch_text(url, f"Tanzil {key}")

    rows = parse_tanzil_pipe(raw)
    if limit is not None:
        rows = [r for r in rows if r[0] <= limit]

    with conn:
        for surah, ayah, text in tqdm(rows, desc=f"  Inserting {key}", unit="ayah"):
            conn.execute(
                "INSERT OR REPLACE INTO translations (surah, ayah, key, text) VALUES (?, ?, ?, ?)",
                (surah, ayah, key, text),
            )
        upsert_metadata(conn, f"translation_{key}_source", f"Tanzil.net en.{key}")
        upsert_metadata(conn, f"translation_{key}_url", url)
        upsert_metadata(conn, f"translation_{key}_retrieved", TODAY)

    count = conn.execute(
        "SELECT COUNT(*) FROM translations WHERE key=?", (key,)
    ).fetchone()[0]
    print(f"  Rows for {key}: {count}")
    return count


def load_jalalayn(conn: sqlite3.Connection, limit: int | None) -> int:
    """Fetch Tafsir al-Jalalayn from AlQuran.cloud and insert into tafsirs table."""
    print("\n[4/5] Tafsir al-Jalalayn (AlQuran.cloud ar.jalalayn)")
    data = fetch_json(ALQURAN_JALALAYN_URL, "al-Jalalayn tafsir")

    if data.get("status") != "OK":
        print(
            f"ERROR: AlQuran.cloud returned status {data.get('status')!r} for jalalayn",
            file=sys.stderr,
        )
        sys.exit(1)

    surahs = data.get("data", {}).get("surahs", [])
    if not surahs:
        print("ERROR: No surahs in al-Jalalayn response", file=sys.stderr)
        sys.exit(1)

    if limit is not None:
        surahs = surahs[:limit]

    inserted = 0
    with conn:
        for surah_data in tqdm(surahs, desc="  Inserting jalalayn", unit="surah"):
            surah_num = surah_data["number"]
            for ayah_data in surah_data["ayahs"]:
                ayah_num = ayah_data["numberInSurah"]
                text = ayah_data["text"]
                conn.execute(
                    "INSERT OR REPLACE INTO tafsirs (surah, ayah, key, text) VALUES (?, ?, ?, ?)",
                    (surah_num, ayah_num, "jalalayn", text),
                )
                inserted += 1

        upsert_metadata(conn, "tafsir_jalalayn_source", "AlQuran.cloud ar.jalalayn")
        upsert_metadata(conn, "tafsir_jalalayn_url", ALQURAN_JALALAYN_URL)
        upsert_metadata(conn, "tafsir_jalalayn_retrieved", TODAY)

    count = conn.execute(
        "SELECT COUNT(*) FROM tafsirs WHERE key='jalalayn'"
    ).fetchone()[0]
    print(f"  Rows for jalalayn: {count}")
    return count


def load_ibnkathir(conn: sqlite3.Connection, limit: int | None) -> int:
    """Fetch Tafsir Ibn Kathir (Arabic) from Quran.com API and insert into tafsirs table."""
    print("\n[5/5] Tafsir Ibn Kathir (Quran.com ar-tafsir-ibn-kathir, id=14)")

    num_chapters = limit if limit is not None else 114
    inserted = 0

    with conn:
        for chapter in tqdm(range(1, num_chapters + 1), desc="  Fetching Ibn Kathir chapters", unit="surah"):
            url = QURANCOM_IBNKATHIR_CHAPTER_URL.format(chapter=chapter)
            try:
                resp = requests.get(url, timeout=60)
                resp.raise_for_status()
            except requests.RequestException as exc:
                print(
                    f"\nERROR: Failed to fetch Ibn Kathir chapter {chapter}: {exc}",
                    file=sys.stderr,
                )
                sys.exit(1)

            try:
                data = resp.json()
            except ValueError as exc:
                print(
                    f"\nERROR: Invalid JSON for Ibn Kathir chapter {chapter}: {exc}",
                    file=sys.stderr,
                )
                sys.exit(1)

            tafsirs = data.get("tafsirs", [])
            if not tafsirs:
                # Some short surahs may have combined entries; warn but continue
                print(
                    f"\nWARNING: No Ibn Kathir entries for chapter {chapter}",
                    file=sys.stderr,
                )
                continue

            for entry in tafsirs:
                verse_key = entry.get("verse_key", "")
                try:
                    s_str, a_str = verse_key.split(":")
                    surah_num = int(s_str)
                    ayah_num = int(a_str)
                except (ValueError, AttributeError):
                    print(
                        f"\nWARNING: Malformed verse_key {verse_key!r}",
                        file=sys.stderr,
                    )
                    continue

                text = entry.get("text", "")
                conn.execute(
                    "INSERT OR REPLACE INTO tafsirs (surah, ayah, key, text) VALUES (?, ?, ?, ?)",
                    (surah_num, ayah_num, "ibnkathir", text),
                )
                inserted += 1

        upsert_metadata(conn, "tafsir_ibnkathir_source", "Quran.com ar-tafsir-ibn-kathir (resource id=14)")
        upsert_metadata(
            conn,
            "tafsir_ibnkathir_url",
            "https://api.quran.com/api/v4/tafsirs/14/by_chapter/{chapter}",
        )
        upsert_metadata(conn, "tafsir_ibnkathir_retrieved", TODAY)

    count = conn.execute(
        "SELECT COUNT(*) FROM tafsirs WHERE key='ibnkathir'"
    ).fetchone()[0]
    print(f"  Rows for ibnkathir: {count}")
    return count


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    repo_root = Path(__file__).parent.parent
    default_output = repo_root / "public" / "quran.db"

    parser = argparse.ArgumentParser(
        description="Build the faithful-text SQLite database for project-fahm."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help="Output path for quran.db (default: public/quran.db relative to repo root)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Process only the first N surahs (for testing)",
    )
    args = parser.parse_args()

    output_path: Path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Output: {output_path}")
    if args.limit:
        print(f"Limit:  first {args.limit} surah(s)")

    conn = sqlite3.connect(output_path)
    conn.execute("PRAGMA journal_mode=WAL")

    print("\nCreating schema...")
    create_schema(conn)

    # 1. Arabic text
    arabic_count = load_arabic(conn, args.limit)

    # 2. Yusuf Ali
    load_translation(conn, "yusufali", TANZIL_YUSUFALI_URL, args.limit)

    # 3. Pickthall
    load_translation(conn, "pickthall", TANZIL_PICKTHALL_URL, args.limit)

    # 4. al-Jalalayn
    load_jalalayn(conn, args.limit)

    # 5. Ibn Kathir
    load_ibnkathir(conn, args.limit)

    # Summary
    print("\n" + "=" * 50)
    print("Build complete. Row counts:")
    for table in ("ayahs", "translations", "tafsirs", "metadata"):
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {n}")

    translations_ya = conn.execute(
        "SELECT COUNT(*) FROM translations WHERE key='yusufali'"
    ).fetchone()[0]
    translations_pt = conn.execute(
        "SELECT COUNT(*) FROM translations WHERE key='pickthall'"
    ).fetchone()[0]
    tafsirs_jl = conn.execute(
        "SELECT COUNT(*) FROM tafsirs WHERE key='jalalayn'"
    ).fetchone()[0]
    tafsirs_ik = conn.execute(
        "SELECT COUNT(*) FROM tafsirs WHERE key='ibnkathir'"
    ).fetchone()[0]

    print(f"    translations[yusufali]  = {translations_ya}")
    print(f"    translations[pickthall] = {translations_pt}")
    print(f"    tafsirs[jalalayn]       = {tafsirs_jl}")
    print(f"    tafsirs[ibnkathir]      = {tafsirs_ik}")

    conn.close()
    print(f"\nDatabase written to: {output_path}")

    # Compress to .gz for deployment (Cloudflare Pages 25 MB file limit)
    gz_path = output_path.with_suffix(output_path.suffix + '.gz')
    with open(output_path, 'rb') as f_in, gzip.open(gz_path, 'wb', compresslevel=9) as f_out:
        shutil.copyfileobj(f_in, f_out)
    gz_mb = gz_path.stat().st_size / 1_048_576
    print(f"Compressed to:        {gz_path}  ({gz_mb:.1f} MB)")

    if args.limit is None:
        expected = 6236
        if arabic_count != expected:
            print(
                f"\nERROR: Expected {expected} ayahs, got {arabic_count}",
                file=sys.stderr,
            )
            sys.exit(1)


if __name__ == "__main__":
    main()
