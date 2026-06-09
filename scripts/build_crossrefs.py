"""
build_crossrefs.py — Add cross-reference tables to quran.db for project-fahm.

Downloads QUL relationship datasets (Similar Ayahs ~4001, Mutashabihat ~5277,
Ayah Topics ~2512, Ayah Themes ~1049) from the MIT-licensed Quranic Universal
Library and populates the cross-reference tables in quran.db.

Every related-verse recommendation in the app comes from these deterministic
tables — no AI inference, no hallucination possible.

Usage:
    python scripts/build_crossrefs.py
    python scripts/build_crossrefs.py --db /path/to/quran.db

Data source:
    Quranic Universal Library (QUL) by Tarteel AI
    https://github.com/TarteelAI/quranic-universal-library  (MIT License)
    https://qul.tarteel.ai/resources

    All four datasets are publicly accessible on qul.tarteel.ai without
    authentication. This script scrapes the public resource pages to
    extract verse relationships.

    For higher-throughput access (bulk download), QUL also offers
    SQLite/JSON downloads via a free account at https://qul.tarteel.ai.
    Set QUL_EMAIL and QUL_PASSWORD (or QUL_COOKIE) env vars and the script
    will authenticate and use the direct download endpoint instead.
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import requests
    from tqdm import tqdm
except ImportError:
    print("ERROR: Missing dependencies. Run: pip install requests tqdm", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = REPO_ROOT / "public" / "quran.db"

QUL_BASE = "https://qul.tarteel.ai"
QUL_REPO_URL = "https://github.com/TarteelAI/quranic-universal-library"
QUL_RESOURCES_URL = "https://qul.tarteel.ai/resources"

# Resource IDs on qul.tarteel.ai (confirmed from the resources page, June 2026)
SIMILAR_AYAH_RESOURCE_ID = 74   # /resources/similar-ayah/74
MUTASHABIHAT_RESOURCE_ID = 73   # /resources/mutashabihat/73
AYAH_TOPICS_RESOURCE_ID  = 45   # /resources/ayah-topics/45
AYAH_THEME_RESOURCE_ID   = None  # fetched dynamically

# Expected row count ranges (±tolerance)
# Note: these are UNIQUE CANONICAL PAIRS / ROWS, not the raw QUL record counts.
# QUL reports 4001 similar_ayahs records (each pair counted twice: A→B and B→A).
# The scraping approach deduplies into canonical (smaller-first) pairs,
# so canonical pair count ≈ raw_count / 2 for symmetric tables.
# Asymmetric tables (ayah_topics, ayah_themes) keep one row per (surah, ayah, label).
EXPECTED_COUNTS = {
    "similar_ayahs": (1500,  5000),   # QUL: ~4001 records → ~2000-3000 canonical pairs via scraping
    "mutashabihat":  (5000, 80000),   # QUL: ~5277 phrases, each shared by multiple verses → many pairs
    "ayah_topics":   (2000,  8000),   # QUL: ~2512 topics, each with multiple verse associations
    "ayah_themes":   ( 500,  8000),   # QUL: ~1049 theme ranges, each covering 1+ verses
}

# DDL for the four cross-reference tables
TABLE_DDL = """
CREATE TABLE IF NOT EXISTS similar_ayahs (
    surah_a           INTEGER NOT NULL,
    ayah_a            INTEGER NOT NULL,
    surah_b           INTEGER NOT NULL,
    ayah_b            INTEGER NOT NULL,
    relationship_type TEXT,
    score             REAL,
    PRIMARY KEY (surah_a, ayah_a, surah_b, ayah_b)
);

CREATE TABLE IF NOT EXISTS mutashabihat (
    surah_a INTEGER NOT NULL,
    ayah_a  INTEGER NOT NULL,
    surah_b INTEGER NOT NULL,
    ayah_b  INTEGER NOT NULL,
    PRIMARY KEY (surah_a, ayah_a, surah_b, ayah_b)
);

CREATE TABLE IF NOT EXISTS ayah_topics (
    surah INTEGER NOT NULL,
    ayah  INTEGER NOT NULL,
    topic TEXT    NOT NULL,
    PRIMARY KEY (surah, ayah, topic)
);

CREATE TABLE IF NOT EXISTS ayah_themes (
    surah INTEGER NOT NULL,
    ayah  INTEGER NOT NULL,
    theme TEXT    NOT NULL,
    PRIMARY KEY (surah, ayah, theme)
);
"""

# Surah → ayah count (from Quranic text standard; 114 surahs)
SURAH_AYAH_COUNTS = [
    7,286,200,176,120,165,206,75,129,109,123,111,43,52,99,128,111,110,98,135,
    112,78,118,64,77,227,93,88,69,60,34,30,73,54,45,83,182,88,75,85,54,53,89,
    59,37,35,38,29,18,45,60,49,62,55,78,96,29,22,24,13,14,11,11,18,12,12,30,
    52,52,44,28,28,20,56,40,31,50,40,46,42,29,19,36,25,22,17,19,26,30,20,15,
    21,11,8,8,19,5,8,8,11,11,8,3,9,5,4,7,3,6,3,5,4,5,6
]


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def parse_verse_key(key: str):
    """Parse 'surah:ayah' string into (int, int). Raises ValueError on bad input."""
    if not isinstance(key, str):
        raise ValueError(f"Expected str, got {type(key)}")
    parts = key.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid verse key: {key!r}")
    return int(parts[0]), int(parts[1])


def all_verse_keys():
    """Generator yielding all 6236 verse keys as 'surah:ayah' strings."""
    for surah, max_ayah in enumerate(SURAH_AYAH_COUNTS, start=1):
        for ayah in range(1, max_ayah + 1):
            yield f"{surah}:{ayah}"


def create_tables(conn: sqlite3.Connection) -> None:
    """Create the four cross-reference tables (idempotent)."""
    conn.executescript(TABLE_DDL)
    conn.commit()


def record_metadata(conn: sqlite3.Connection, key: str, value: str) -> None:
    """Write a key/value pair to the metadata table if it exists."""
    try:
        conn.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            (key, value),
        )
        conn.commit()
    except sqlite3.OperationalError:
        pass  # metadata table doesn't exist — skip silently


def make_session() -> requests.Session:
    """Build a plain HTTP session with appropriate User-Agent."""
    s = requests.Session()
    s.headers.update({
        "User-Agent": (
            "project-fahm/build_crossrefs "
            "(open-source Quran study app; +https://github.com/shosyed/project-fahm)"
        ),
        "Accept": "text/html,application/json,*/*",
        "Accept-Language": "en-US,en;q=0.9",
    })
    return s


def get_authenticated_session(args) -> requests.Session:
    """
    Return an authenticated QUL session if credentials are available,
    otherwise return a plain (unauthenticated) session.

    Authenticated sessions are needed for direct bulk download.
    Public scraping works without authentication.
    """
    session = make_session()

    cookie_str = args.qul_cookie or os.environ.get("QUL_COOKIE", "")
    email = args.qul_email or os.environ.get("QUL_EMAIL", "")
    password = args.qul_password or os.environ.get("QUL_PASSWORD", "")

    if cookie_str:
        name, _, value = cookie_str.partition("=") if "=" in cookie_str else ("_quran_com-community_session", "=", cookie_str)
        session.cookies.set(name.strip() or "_quran_com-community_session", value.strip() or cookie_str.strip(), domain="qul.tarteel.ai")
        print("  [auth] Using provided session cookie.")
        return session

    if email and password:
        print(f"  [auth] Logging in as {email} …")
        login_page = session.get(f"{QUL_BASE}/users/sign_in", timeout=20)
        csrf = re.search(r'<meta name="csrf-token" content="([^"]+)"', login_page.text)
        if not csrf:
            print("WARNING: Could not get CSRF token — proceeding without auth.")
            return session
        session.post(
            f"{QUL_BASE}/users/sign_in",
            data={
                "authenticity_token": csrf.group(1),
                "user[email]": email,
                "user[password]": password,
                "user[remember_me]": "0",
            },
            headers={"Referer": f"{QUL_BASE}/users/sign_in"},
            allow_redirects=True,
            timeout=20,
        )
        print("  [auth] Login attempted.")

    return session


def fetch_with_retry(session: requests.Session, url: str, retries: int = 3,
                     backoff: float = 2.0, timeout: int = 30) -> requests.Response:
    """GET with exponential backoff on 5xx / network errors."""
    for attempt in range(retries):
        try:
            resp = session.get(url, timeout=timeout)
            if resp.status_code == 429:
                wait = float(resp.headers.get("Retry-After", backoff * (2 ** attempt)))
                time.sleep(wait)
                continue
            if resp.status_code >= 500:
                time.sleep(backoff * (2 ** attempt))
                continue
            return resp
        except requests.RequestException:
            if attempt == retries - 1:
                raise
            time.sleep(backoff * (2 ** attempt))
    raise RuntimeError(f"Failed to fetch {url} after {retries} attempts")


# ---------------------------------------------------------------------------
# Authenticated bulk-download helpers (used when credentials are provided)
# ---------------------------------------------------------------------------

def try_bulk_download_json(session: requests.Session, resource_id: int,
                           resource_slug: str, label: str):
    """
    Attempt to download a QUL resource as JSON via the authenticated download
    endpoint. Returns parsed JSON data, or None if download fails/not authed.
    """
    page_url = f"{QUL_BASE}/resources/{resource_slug}/{resource_id}"
    try:
        resp = fetch_with_retry(session, page_url)
    except Exception as e:
        print(f"  WARNING: Could not fetch resource page: {e}")
        return None

    # Look for download tokens in the page
    token_pattern = rf'/resources/{resource_slug}/{resource_id}/([a-f0-9]{{32}})/download'
    tokens = re.findall(token_pattern, resp.text)
    if not tokens:
        return None  # not logged in or page changed

    # Try first token (JSON)
    token = tokens[0]
    dl_url = f"{QUL_BASE}/resources/{resource_slug}/{resource_id}/{token}/download"
    print(f"  Downloading {label} via authenticated endpoint …")
    try:
        dl_resp = session.get(dl_url, allow_redirects=True, timeout=120, stream=True)
        dl_resp.raise_for_status()
        total = int(dl_resp.headers.get("Content-Length", 0))
        chunks = []
        with tqdm(total=total, unit="B", unit_scale=True, desc=f"  {label}", leave=False) as pbar:
            for chunk in dl_resp.iter_content(chunk_size=65536):
                chunks.append(chunk)
                pbar.update(len(chunk))
        raw = b"".join(chunks)
        return json.loads(raw.decode("utf-8"))
    except Exception as e:
        print(f"  WARNING: Bulk download failed ({e}), falling back to scraping.")
        return None


# ---------------------------------------------------------------------------
# 1. Similar Ayahs
# ---------------------------------------------------------------------------

def _fetch_similar_ayahs_for_verse(session: requests.Session, verse_key: str):
    """
    Fetch similar ayahs for a single verse from the public QUL resource page.
    Returns list of matched verse keys.
    """
    url = f"{QUL_BASE}/resources/similar-ayah/{SIMILAR_AYAH_RESOURCE_ID}?ayah={verse_key}"
    try:
        resp = fetch_with_retry(session, url, timeout=20)
        if resp.status_code != 200:
            return []
        content = resp.text
        # Find verse keys inside the 'Similar Ayah for...' section
        section_match = re.search(r'Similar Ayah for', content)
        if not section_match:
            return []
        section = content[section_match.start():section_match.start() + 8000]
        # Matched verse keys are shown in badge divs
        matched = re.findall(
            r'<div class="badge[^"]*"[^>]*>[\s\n]*(\d{1,3}:\d{1,3})[\s\n]*</div>',
            section
        )
        # Remove the source verse itself
        return [k for k in matched if k != verse_key]
    except Exception:
        return []


def populate_similar_ayahs_by_scraping(
    conn: sqlite3.Connection, session: requests.Session,
    workers: int = 8, delay: float = 0.05
) -> int:
    """
    Scrape the QUL similar-ayah resource page for each verse and insert pairs.
    Uses threaded requests with a small delay to be polite.
    """
    print("  Scraping similar ayahs per verse …")
    verse_keys = list(all_verse_keys())
    rows: set[tuple] = set()

    def fetch(vk):
        time.sleep(delay)
        matched = _fetch_similar_ayahs_for_verse(session, vk)
        return vk, matched

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch, vk): vk for vk in verse_keys}
        with tqdm(total=len(verse_keys), desc="  similar_ayahs", unit="verse") as pbar:
            for future in as_completed(futures):
                vk_a, matched = future.result()
                pbar.update(1)
                try:
                    sa, aa = parse_verse_key(vk_a)
                except ValueError:
                    continue
                for vk_b in matched:
                    try:
                        sb, ab = parse_verse_key(vk_b)
                    except ValueError:
                        continue
                    # Canonical order
                    if (sa, aa) <= (sb, ab):
                        rows.add((sa, aa, sb, ab, "morphological_match", None))
                    else:
                        rows.add((sb, ab, sa, aa, "morphological_match", None))

    conn.executemany(
        "INSERT OR REPLACE INTO similar_ayahs "
        "(surah_a, ayah_a, surah_b, ayah_b, relationship_type, score) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        list(rows),
    )
    conn.commit()
    return len(rows)


def populate_similar_ayahs_from_json(conn: sqlite3.Connection, data: dict) -> int:
    """
    Insert similar_ayahs from QUL bulk JSON download.

    QUL JSON format:
    {
      "1:1": [
        {"matched_ayah_key": "27:30", "score": 85, ...},
        ...
      ]
    }
    """
    rows = []
    for verse_key, matches in data.items():
        try:
            sa, aa = parse_verse_key(verse_key)
        except (ValueError, TypeError):
            continue
        if not isinstance(matches, list):
            continue
        for m in matches:
            matched_key = m.get("matched_ayah_key") or m.get("matched_verse_key", "")
            try:
                sb, ab = parse_verse_key(matched_key)
            except (ValueError, TypeError):
                continue
            score = m.get("score")
            rows.append((sa, aa, sb, ab, "morphological_match", score))

    conn.executemany(
        "INSERT OR REPLACE INTO similar_ayahs "
        "(surah_a, ayah_a, surah_b, ayah_b, relationship_type, score) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    return len(rows)


def populate_similar_ayahs(conn, session, args) -> int:
    """Download and insert similar_ayahs. Tries bulk download first, falls back to scraping."""
    print("\n[1/4] similar_ayahs")

    if args.data_dir:
        return _load_from_data_dir_similar(conn, args.data_dir)

    # Try authenticated bulk download first
    data = try_bulk_download_json(session, SIMILAR_AYAH_RESOURCE_ID, "similar-ayah", "Similar Ayahs")
    if data is not None:
        n = populate_similar_ayahs_from_json(conn, data)
    else:
        print("  Falling back to public page scraping (slower but no auth needed) …")
        n = populate_similar_ayahs_by_scraping(conn, session, workers=args.workers, delay=args.delay)

    print(f"  Inserted {n} rows into similar_ayahs")
    return n


def _load_from_data_dir_similar(conn, data_dir: Path) -> int:
    for fname in ("similar_ayahs.json", "similar_ayahs.db", "similar_ayahs.sqlite", "matching_ayah.json"):
        f = data_dir / fname
        if f.exists():
            print(f"  Loading from {f}")
            if fname.endswith(".json"):
                with open(f, encoding="utf-8") as fh:
                    data = json.load(fh)
                n = populate_similar_ayahs_from_json(conn, data)
                print(f"  Inserted {n} rows into similar_ayahs")
                return n
            else:
                return _load_sqlite_similar(conn, f)
    raise FileNotFoundError(f"No similar_ayahs data file found in {data_dir}")


def _load_sqlite_similar(conn, src_path: Path) -> int:
    src = sqlite3.connect(src_path)
    rows = []
    try:
        for row in src.execute(
            "SELECT verse_key, matched_ayah_key, score FROM similar_ayahs"
        ):
            try:
                sa, aa = parse_verse_key(row[0])
                sb, ab = parse_verse_key(row[1])
                rows.append((sa, aa, sb, ab, "morphological_match", row[2]))
            except (ValueError, TypeError):
                continue
    finally:
        src.close()
    conn.executemany(
        "INSERT OR REPLACE INTO similar_ayahs "
        "(surah_a, ayah_a, surah_b, ayah_b, relationship_type, score) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    n = len(rows)
    print(f"  Inserted {n} rows into similar_ayahs")
    return n


# ---------------------------------------------------------------------------
# 2. Mutashabihat
# ---------------------------------------------------------------------------

def _fetch_phrase_ids_for_verse(session: requests.Session, verse_key: str) -> list[int]:
    """
    Fetch mutashabihat phrase IDs for a single verse.
    Uses /resources/mutashabihat/{ID}?ayah=VERSE_KEY to get links to
    /morphology_phrases/{phrase_id}/phrase_verses.
    Returns list of integer phrase IDs.
    """
    url = f"{QUL_BASE}/resources/mutashabihat/{MUTASHABIHAT_RESOURCE_ID}?ayah={verse_key}"
    try:
        resp = fetch_with_retry(session, url, timeout=20)
        if resp.status_code != 200:
            return []
        ids = re.findall(r'/morphology_phrases/(\d+)/phrase_verses', resp.text)
        return list({int(i) for i in ids})
    except Exception:
        return []


def _fetch_verse_keys_for_phrase(session: requests.Session, phrase_id: int) -> list[str]:
    """
    Fetch all verse keys associated with a morphology phrase.
    Uses /morphology_phrases/{phrase_id}/phrase_verses to get the verse list.
    """
    url = f"{QUL_BASE}/morphology_phrases/{phrase_id}/phrase_verses"
    try:
        resp = fetch_with_retry(session, url, timeout=20)
        if resp.status_code != 200:
            return []
        # Verse keys appear as plain text patterns in the page
        vks = list(set(re.findall(r'\b(\d{1,3}:\d{1,3})\b', resp.text)))
        return vks
    except Exception:
        return []


def _scrape_mutashabihat_via_phrases(
    session: requests.Session, workers: int = 10, delay: float = 0.05
) -> set[tuple]:
    """
    Scrape mutashabihat data using the two-step phrase approach:
    1. For each verse, get its phrase IDs from the mutashabihat resource page.
    2. For each unique phrase ID, get all its associated verse keys.
    3. Build canonical verse pairs from phrases shared by 2+ verses.

    Returns a set of (surah_a, ayah_a, surah_b, ayah_b) canonical pairs.
    """
    print("  Step 1: Collecting phrase IDs per verse …")
    verse_keys = list(all_verse_keys())
    verse_to_phrases: dict[str, list[int]] = {}

    def fetch_phrases(vk):
        time.sleep(delay)
        return vk, _fetch_phrase_ids_for_verse(session, vk)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch_phrases, vk): vk for vk in verse_keys}
        with tqdm(total=len(verse_keys), desc="  mutashabihat-phrases", unit="verse") as pbar:
            for future in as_completed(futures):
                vk, phrase_ids = future.result()
                pbar.update(1)
                if phrase_ids:
                    verse_to_phrases[vk] = phrase_ids

    # Build reverse map: phrase_id → [verse_keys]
    phrase_to_verses: dict[int, list[str]] = {}
    for vk, phrase_ids in verse_to_phrases.items():
        for pid in phrase_ids:
            phrase_to_verses.setdefault(pid, []).append(vk)

    # For phrases with only 1 verse from our initial scan, fetch them explicitly
    # to ensure completeness
    single_phrases = [pid for pid, vks in phrase_to_verses.items() if len(vks) < 2]
    all_phrase_ids = set(phrase_to_verses.keys())
    print(f"  Found {len(all_phrase_ids)} unique phrases, {len(single_phrases)} need expansion …")

    if single_phrases:
        print(f"  Step 2: Fetching complete verse lists for {len(single_phrases)} phrases …")

        def fetch_vks(pid):
            time.sleep(delay)
            return pid, _fetch_verse_keys_for_phrase(session, pid)

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(fetch_vks, pid): pid for pid in single_phrases}
            with tqdm(total=len(single_phrases), desc="  phrase-expansion", unit="phrase") as pbar:
                for future in as_completed(futures):
                    pid, vks = future.result()
                    pbar.update(1)
                    if len(vks) >= 2:
                        phrase_to_verses[pid] = vks

    # Build canonical pairs from phrases
    pairs: set[tuple] = set()
    for pid, vks in phrase_to_verses.items():
        if len(vks) < 2:
            continue
        unique_vks = list(set(vks))
        for i, a in enumerate(unique_vks):
            for b in unique_vks[i + 1:]:
                try:
                    sa, aa = parse_verse_key(a)
                    sb, ab = parse_verse_key(b)
                    if (sa, aa) <= (sb, ab):
                        pairs.add((sa, aa, sb, ab))
                    else:
                        pairs.add((sb, ab, sa, aa))
                except (ValueError, TypeError):
                    pass

    return pairs


def populate_mutashabihat_from_json(conn: sqlite3.Connection, data) -> int:
    """
    Insert mutashabihat from QUL bulk JSON (phrase_verses format).

    Two accepted formats:
    1. phrase_verses: {verse_key: [phrase_id, ...]}
    2. phrases: {phrase_id: {ayah: {verse_key: [[from, to]], ...}}}
    """
    pairs: set[tuple] = set()

    if isinstance(data, dict):
        # Detect format by looking at values
        first_val = next(iter(data.values()), None) if data else None

        if isinstance(first_val, list):
            # phrase_verses format: {verse_key: [phrase_id, ...]}
            phrase_to_verses: dict[int, list] = {}
            for verse_key, phrase_ids in data.items():
                if not isinstance(phrase_ids, list):
                    continue
                for pid in phrase_ids:
                    phrase_to_verses.setdefault(int(pid), []).append(verse_key)
            for pid, vks in phrase_to_verses.items():
                if len(vks) < 2:
                    continue
                for i, a in enumerate(vks):
                    for b in vks[i+1:]:
                        try:
                            sa, aa = parse_verse_key(a)
                            sb, ab = parse_verse_key(b)
                            if (sa, aa) <= (sb, ab):
                                pairs.add((sa, aa, sb, ab))
                            else:
                                pairs.add((sb, ab, sa, aa))
                        except (ValueError, TypeError):
                            pass

        elif isinstance(first_val, dict):
            # phrases format: {phrase_id: {source: ..., ayah: {vk: [...]}}}
            for pid, phrase_data in data.items():
                if not isinstance(phrase_data, dict):
                    continue
                ayah_map = phrase_data.get("ayah", {})
                vks = list(ayah_map.keys())
                if len(vks) < 2:
                    continue
                for i, a in enumerate(vks):
                    for b in vks[i+1:]:
                        try:
                            sa, aa = parse_verse_key(a)
                            sb, ab = parse_verse_key(b)
                            if (sa, aa) <= (sb, ab):
                                pairs.add((sa, aa, sb, ab))
                            else:
                                pairs.add((sb, ab, sa, aa))
                        except (ValueError, TypeError):
                            pass

    rows = list(pairs)
    conn.executemany(
        "INSERT OR REPLACE INTO mutashabihat (surah_a, ayah_a, surah_b, ayah_b) VALUES (?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    return len(rows)


def populate_mutashabihat(conn, session, args) -> int:
    """Download and insert mutashabihat pairs."""
    print("\n[2/4] mutashabihat")

    if args.data_dir:
        return _load_from_data_dir_mutashabihat(conn, args.data_dir)

    # Try bulk download (if authed)
    data = try_bulk_download_json(session, MUTASHABIHAT_RESOURCE_ID, "mutashabihat", "Mutashabihat")
    if data is not None:
        n = populate_mutashabihat_from_json(conn, data)
        print(f"  Inserted {n} rows into mutashabihat")
        return n

    # Fall back to phrase-based scraping (per-verse phrase IDs → phrase verse keys)
    print("  Falling back to phrase-based scraping …")
    pairs = _scrape_mutashabihat_via_phrases(
        session, workers=args.workers, delay=args.delay
    )
    rows = list(pairs)
    conn.executemany(
        "INSERT OR REPLACE INTO mutashabihat (surah_a, ayah_a, surah_b, ayah_b) VALUES (?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    n = len(rows)
    print(f"  Inserted {n} rows into mutashabihat")
    return n


def _load_from_data_dir_mutashabihat(conn, data_dir: Path) -> int:
    # Check for phrases + phrase_verses combo dir
    phrases_dir = data_dir / "mutashabihat"
    if phrases_dir.is_dir():
        pv_file = phrases_dir / "phrase_verses.json"
        if pv_file.exists():
            with open(pv_file, encoding="utf-8") as f:
                data = json.load(f)
            n = populate_mutashabihat_from_json(conn, data)
            print(f"  Inserted {n} rows into mutashabihat")
            return n
    # Single file
    for fname in ("mutashabihat.json", "phrase_verses.json"):
        f = data_dir / fname
        if f.exists():
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
            n = populate_mutashabihat_from_json(conn, data)
            print(f"  Inserted {n} rows into mutashabihat")
            return n
    raise FileNotFoundError(f"No mutashabihat data file found in {data_dir}")


# ---------------------------------------------------------------------------
# 3. Ayah Topics
# ---------------------------------------------------------------------------

def _scrape_all_topic_names(session: requests.Session) -> dict:
    """
    Scrape the QUL topics listing to get {topic_id: topic_name} for all topics.

    The listing is paginated (~26 pages of 100 topics each).
    """
    print("  Building topic name index …")
    topic_names = {}

    # Determine how many pages there are
    first_url = f"{QUL_BASE}/resources/ayah-topics/{AYAH_TOPICS_RESOURCE_ID}?per_page=100&page=1&sort_by=name&sort_direction=asc"
    resp = fetch_with_retry(session, first_url, timeout=30)
    pages = re.findall(r'page=(\d+)', resp.text)
    max_page = max((int(p) for p in pages if int(p) < 1000), default=1)

    def parse_topic_names(content: str, names_dict: dict):
        """
        Parse topic ID→name from the listing page.

        Each <tr> contains:
          col1: <div class="font-medium text-gray-900">TOPIC NAME</div>
          last col: <a href="/resources/ayah-topics/ID?topic_id=TID">View</a>
        Both are in the same <tr>, so we parse row by row.
        """
        rows = re.findall(r'<tr[^>]*class="hover:bg-gray-50[^"]*"[^>]*>([\s\S]*?)</tr>', content)
        for row in rows:
            name_m = re.search(r'font-medium text-gray-900">\s*([^\n<]{1,120})\s*</div>', row)
            tid_m  = re.search(r'topic_id=(\d+)', row)
            if not name_m or not tid_m:
                continue
            name = name_m.group(1).strip()
            if name and name != "-" and not re.match(r'^\d+:\d+', name):
                names_dict[int(tid_m.group(1))] = name

    parse_topic_names(resp.text, topic_names)

    for page in tqdm(range(2, max_page + 1), desc="  topic name pages"):
        url = f"{QUL_BASE}/resources/ayah-topics/{AYAH_TOPICS_RESOURCE_ID}?per_page=100&page={page}&sort_by=name&sort_direction=asc"
        try:
            r = fetch_with_retry(session, url, timeout=30)
            parse_topic_names(r.text, topic_names)
            time.sleep(0.1)
        except Exception:
            pass

    print(f"  Found {len(topic_names)} topic names")
    return topic_names


def _fetch_topic_verse_keys(session: requests.Session, topic_id: int) -> list:
    """
    Fetch the verse keys associated with a specific topic.
    Returns list of verse keys.
    """
    url = f"{QUL_BASE}/resources/ayah-topics/{AYAH_TOPICS_RESOURCE_ID}?topic_id={topic_id}"
    try:
        resp = fetch_with_retry(session, url, timeout=30)
        if resp.status_code != 200:
            return []
        # Verse keys appear in h5 elements like "2:255 - Al-Baqarah"
        verse_keys = re.findall(r'<h5[^>]*>[\s\n]*(\d{1,3}:\d{1,3})\s*[-—]', resp.text)
        if not verse_keys:
            # Try badge pattern
            verse_keys = re.findall(
                r'<div class="badge[^"]*"[^>]*>[\s\n]*(\d{1,3}:\d{1,3})[\s\n]*</div>',
                resp.text
            )
        return verse_keys
    except Exception:
        return []


def _scrape_verse_topic_ids(session: requests.Session, verse_key: str) -> list:
    """Get topic IDs for a single verse from /ayah/VERSE/topics."""
    url = f"{QUL_BASE}/ayah/{verse_key}/topics"
    try:
        resp = fetch_with_retry(session, url, timeout=20)
        if resp.status_code != 200:
            return []
        # data-url="/ayah/2:255/topics/73" patterns
        ids = re.findall(rf'data-url="/ayah/{re.escape(verse_key)}/topics/(\d+)"', resp.text)
        return [int(i) for i in ids]
    except Exception:
        return []


def populate_ayah_topics_from_json(conn: sqlite3.Connection, data) -> int:
    """
    Insert ayah_topics from QUL bulk JSON.

    Expected format (SQLite export converted to JSON):
    [{"topic_id": 1, "name": "Faith", "ayahs": "2:3, 2:4, 2:177", ...}]
    OR dict keyed by topic_id.
    """
    rows = []
    items = data if isinstance(data, list) else list(data.values())
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("topic") or ""
        if not name:
            continue
        ayahs_raw = item.get("ayahs") or item.get("verse_keys") or ""
        if isinstance(ayahs_raw, list):
            keys = ayahs_raw
        else:
            keys = [k.strip() for k in str(ayahs_raw).split(",") if k.strip()]
        for key in keys:
            try:
                s, a = parse_verse_key(key)
                rows.append((s, a, name))
            except (ValueError, TypeError):
                continue

    conn.executemany(
        "INSERT OR REPLACE INTO ayah_topics (surah, ayah, topic) VALUES (?, ?, ?)",
        rows,
    )
    conn.commit()
    return len(rows)


def populate_ayah_topics(conn, session, args) -> int:
    """Download and insert ayah_topics."""
    print("\n[3/4] ayah_topics")

    if args.data_dir:
        return _load_from_data_dir_topics(conn, args.data_dir)

    # Try bulk download first
    data = try_bulk_download_json(session, AYAH_TOPICS_RESOURCE_ID, "ayah-topics", "Ayah Topics")
    if data is not None:
        n = populate_ayah_topics_from_json(conn, data)
        print(f"  Inserted {n} rows into ayah_topics")
        return n

    # Public scraping approach:
    # Strategy A: scrape topic names from listing, then fetch verse keys per topic
    print("  Scraping all topic names from listing …")
    topic_names = _scrape_all_topic_names(session)
    if not topic_names:
        print("  WARNING: Could not scrape topic names", file=sys.stderr)
        return 0

    print(f"  Fetching verse keys for {len(topic_names)} topics …")
    rows = []

    def fetch_topic(tid, tname):
        time.sleep(args.delay)
        vks = _fetch_topic_verse_keys(session, tid)
        result = []
        for vk in vks:
            try:
                s, a = parse_verse_key(vk)
                result.append((s, a, tname))
            except (ValueError, TypeError):
                pass
        return result

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(fetch_topic, tid, tname): tid
                   for tid, tname in topic_names.items()}
        with tqdm(total=len(topic_names), desc="  ayah_topics", unit="topic") as pbar:
            for future in as_completed(futures):
                rows.extend(future.result())
                pbar.update(1)

    conn.executemany(
        "INSERT OR REPLACE INTO ayah_topics (surah, ayah, topic) VALUES (?, ?, ?)",
        rows,
    )
    conn.commit()
    n = len(rows)
    print(f"  Inserted {n} rows into ayah_topics")
    return n


def _load_from_data_dir_topics(conn, data_dir: Path) -> int:
    for fname in ("ayah_topics.json", "ayah_topics.db", "ayah_topics.sqlite", "topics.db"):
        f = data_dir / fname
        if f.exists():
            print(f"  Loading from {f}")
            if fname.endswith(".json"):
                with open(f, encoding="utf-8") as fh:
                    data = json.load(fh)
                n = populate_ayah_topics_from_json(conn, data)
                print(f"  Inserted {n} rows into ayah_topics")
                return n
            else:
                return _load_sqlite_topics(conn, f)
    raise FileNotFoundError(f"No ayah_topics data file found in {data_dir}")


def _load_sqlite_topics(conn, src_path: Path) -> int:
    src = sqlite3.connect(src_path)
    rows = []
    try:
        for row in src.execute("SELECT name, ayahs FROM topics WHERE ayahs IS NOT NULL"):
            name, ayahs_raw = row
            if not name:
                continue
            for key in str(ayahs_raw).split(","):
                key = key.strip()
                try:
                    s, a = parse_verse_key(key)
                    rows.append((s, a, name))
                except (ValueError, TypeError):
                    pass
    except sqlite3.OperationalError as e:
        print(f"  WARNING: {e}")
    finally:
        src.close()
    conn.executemany(
        "INSERT OR REPLACE INTO ayah_topics (surah, ayah, topic) VALUES (?, ?, ?)",
        rows,
    )
    conn.commit()
    n = len(rows)
    print(f"  Inserted {n} rows into ayah_topics")
    return n


# ---------------------------------------------------------------------------
# 4. Ayah Themes
# ---------------------------------------------------------------------------

def _fetch_ayah_theme(session: requests.Session, verse_key: str):
    """
    Fetch the theme for a single verse from /ayah/VERSE/theme.
    Returns theme name string or None.
    """
    url = f"{QUL_BASE}/ayah/{verse_key}/theme"
    try:
        resp = fetch_with_retry(session, url, timeout=20)
        if resp.status_code != 200:
            return None
        # Theme text is in: <div class="text-sm text-gray-900">THEME</div>
        # The /ayah/VERSE/theme endpoint returns a small HTML fragment (~1 KB)
        theme_match = re.search(
            r'<div[^>]*class="text-sm text-gray-900"[^>]*>([^<]{3,200})</div>',
            resp.text
        )
        if theme_match:
            theme = theme_match.group(1).strip()
            theme = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), theme)
            theme = re.sub(r'&amp;', '&', theme)
            theme = re.sub(r'&quot;', '"', theme)
            theme = re.sub(r'&#39;', "'", theme)
            if theme and len(theme) > 1:
                return theme
        # Fallback: meta description "Ayah theme(VK) - THEME TEXT"
        meta_match = re.search(r'Ayah theme\([^)]+\)\s*[-–]\s*([^"<]{3,200})', resp.text)
        if meta_match:
            return meta_match.group(1).strip()
        return None
    except Exception:
        return None


def _fetch_theme_resource_id(session: requests.Session) -> int | None:
    """Find the ayah-theme resource ID from the QUL resources page."""
    url = f"{QUL_BASE}/resources/ayah-theme"
    try:
        resp = fetch_with_retry(session, url, timeout=20)
        ids = re.findall(r'/resources/ayah-theme/(\d+)', resp.text)
        if ids:
            from collections import Counter
            return int(Counter(ids).most_common(1)[0][0])
    except Exception:
        pass
    return None


def _scrape_themes_from_resource(session: requests.Session, resource_id: int) -> list:
    """
    Scrape the ayah-theme resource page to get all theme records.
    Returns list of (surah, ayah_from, ayah_to, theme).
    """
    print(f"  Scraping theme resource {resource_id} …")
    results = []

    url = f"{QUL_BASE}/resources/ayah-theme/{resource_id}"
    resp = fetch_with_retry(session, url, timeout=30)

    # Determine pagination
    pages = re.findall(r'page=(\d+)', resp.text)
    max_page = max((int(p) for p in pages if int(p) < 1000), default=1)

    def parse_page(content: str):
        """Extract theme rows from an ayah-theme listing page."""
        # Each row shows: theme name, surah number, ayah range
        rows_html = re.findall(r'<tr[^>]*>([\s\S]*?)</tr>', content)
        for row in rows_html:
            # Look for theme name in font-medium div or similar
            theme_m = re.search(r'font-medium[^>]*>[\s\n]*([^<\n]{2,100})[\s\n]*</div>', row)
            if not theme_m:
                continue
            theme = theme_m.group(1).strip()
            if not theme or theme.lower() in ('theme', 'surah', 'ayah', 'from', 'to'):
                continue

            # Look for surah number
            surah_m = re.search(r'\b(1\d{2}|[1-9]\d?)\b', row)
            # Look for ayah range
            ayah_ms = re.findall(r'\b(\d{1,3})\b', row)

            # Try to extract (surah, from, to) from table cells
            cells = re.findall(r'<td[^>]*>([\s\S]*?)</td>', row)
            if len(cells) >= 3:
                nums = []
                for cell in cells:
                    num_m = re.search(r'\b(\d{1,3})\b', cell)
                    if num_m:
                        nums.append(int(num_m.group(1)))
                if len(nums) >= 3:
                    surah, ayah_from, ayah_to = nums[0], nums[1], nums[2]
                    if 1 <= surah <= 114 and ayah_from <= ayah_to:
                        for a in range(ayah_from, ayah_to + 1):
                            results.append((surah, a, theme))

    parse_page(resp.text)
    for page in tqdm(range(2, max_page + 1), desc="  ayah_theme pages"):
        try:
            r = fetch_with_retry(session, f"{url}?page={page}", timeout=30)
            parse_page(r.text)
            time.sleep(0.1)
        except Exception:
            pass

    return results


def populate_ayah_themes_from_json(conn: sqlite3.Connection, data) -> int:
    """
    Insert ayah_themes from QUL bulk JSON.

    QUL JSON format (from export_ayah_theme.rb):
    [
      {
        "theme": "Mercy of Allah",
        "surah_number": 1,
        "ayah_from": 1,
        "ayah_to": 7,
        ...
      }
    ]
    """
    rows = []
    items = data if isinstance(data, list) else list(data.values())
    for item in items:
        if not isinstance(item, dict):
            continue
        theme = item.get("theme") or ""
        if not theme:
            continue
        surah = item.get("surah_number") or item.get("surah") or item.get("chapter_id")
        ayah_from = item.get("ayah_from") or item.get("verse_number_from") or item.get("ayah")
        ayah_to = item.get("ayah_to") or item.get("verse_number_to") or ayah_from
        if surah is None or ayah_from is None:
            continue
        try:
            surah = int(surah)
            ayah_from = int(ayah_from)
            ayah_to = int(ayah_to or ayah_from)
        except (ValueError, TypeError):
            continue
        for a in range(ayah_from, ayah_to + 1):
            rows.append((surah, a, theme))

    conn.executemany(
        "INSERT OR REPLACE INTO ayah_themes (surah, ayah, theme) VALUES (?, ?, ?)",
        rows,
    )
    conn.commit()
    return len(rows)


def populate_ayah_themes_by_verse_scraping(
    conn: sqlite3.Connection, session: requests.Session,
    workers: int = 8, delay: float = 0.05
) -> int:
    """
    Scrape /ayah/VERSE/theme for each verse to get its theme.
    Only includes verses that actually have a theme (most won't).
    """
    print("  Scraping themes per verse …")
    verse_keys = list(all_verse_keys())
    rows = []

    def fetch(vk):
        time.sleep(delay)
        theme = _fetch_ayah_theme(session, vk)
        return vk, theme

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch, vk): vk for vk in verse_keys}
        with tqdm(total=len(verse_keys), desc="  ayah_themes", unit="verse") as pbar:
            for future in as_completed(futures):
                vk, theme = future.result()
                pbar.update(1)
                if theme:
                    try:
                        s, a = parse_verse_key(vk)
                        rows.append((s, a, theme))
                    except (ValueError, TypeError):
                        pass

    conn.executemany(
        "INSERT OR REPLACE INTO ayah_themes (surah, ayah, theme) VALUES (?, ?, ?)",
        rows,
    )
    conn.commit()
    return len(rows)


def populate_ayah_themes(conn, session, args) -> int:
    """Download and insert ayah_themes."""
    print("\n[4/4] ayah_themes")

    if args.data_dir:
        return _load_from_data_dir_themes(conn, args.data_dir)

    # Try bulk download
    rid = _fetch_theme_resource_id(session)
    if rid:
        data = try_bulk_download_json(session, rid, "ayah-theme", "Ayah Themes")
        if data is not None:
            n = populate_ayah_themes_from_json(conn, data)
            print(f"  Inserted {n} rows into ayah_themes")
            return n

        # Try scraping the listing page
        records = _scrape_themes_from_resource(session, rid)
        if records:
            conn.executemany(
                "INSERT OR REPLACE INTO ayah_themes (surah, ayah, theme) VALUES (?, ?, ?)",
                records,
            )
            conn.commit()
            n = len(records)
            print(f"  Inserted {n} rows into ayah_themes")
            return n

    # Per-verse scraping fallback
    print("  Falling back to per-verse theme scraping …")
    n = populate_ayah_themes_by_verse_scraping(
        conn, session, workers=args.workers, delay=args.delay
    )
    print(f"  Inserted {n} rows into ayah_themes")
    return n


def _load_from_data_dir_themes(conn, data_dir: Path) -> int:
    for fname in ("ayah_themes.json", "ayah_themes.db", "ayah_themes.sqlite", "themes.db"):
        f = data_dir / fname
        if f.exists():
            print(f"  Loading from {f}")
            if fname.endswith(".json"):
                with open(f, encoding="utf-8") as fh:
                    data = json.load(fh)
                n = populate_ayah_themes_from_json(conn, data)
                print(f"  Inserted {n} rows into ayah_themes")
                return n
            else:
                return _load_sqlite_themes(conn, f)
    raise FileNotFoundError(f"No ayah_themes data file found in {data_dir}")


def _load_sqlite_themes(conn, src_path: Path) -> int:
    src = sqlite3.connect(src_path)
    rows = []
    try:
        for row in src.execute(
            "SELECT theme, surah_number, ayah_from, ayah_to FROM themes WHERE theme IS NOT NULL"
        ):
            theme, surah, ayah_from, ayah_to = row
            if not theme:
                continue
            try:
                surah = int(surah)
                ayah_from = int(ayah_from)
                ayah_to = int(ayah_to or ayah_from)
            except (ValueError, TypeError):
                continue
            for a in range(ayah_from, ayah_to + 1):
                rows.append((surah, a, theme))
    except sqlite3.OperationalError as e:
        print(f"  WARNING: {e}")
    finally:
        src.close()
    conn.executemany(
        "INSERT OR REPLACE INTO ayah_themes (surah, ayah, theme) VALUES (?, ?, ?)",
        rows,
    )
    conn.commit()
    n = len(rows)
    print(f"  Inserted {n} rows into ayah_themes")
    return n


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify_counts(conn: sqlite3.Connection) -> bool:
    """
    Check row counts are within expected ranges.
    Returns True if all counts are within range.
    """
    print("\n--- Row count verification ---")
    all_ok = True
    for table, (lo, hi) in EXPECTED_COUNTS.items():
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        ok = lo <= count <= hi
        symbol = "OK  " if ok else "WARN"
        print(f"  {symbol}  {table:<20} {count:>6} rows  (expected {lo}–{hi})")
        if not ok:
            all_ok = False
    return all_ok


def spot_check(conn: sqlite3.Connection) -> None:
    """Spot-check surah 2, ayah 255 cross-references."""
    print("\n--- Spot check: Surah 2, Ayah 255 (Al-Baqarah:255 — Ayat al-Kursi) ---")
    checks = [
        ("similar_ayahs",
         "SELECT COUNT(*) FROM similar_ayahs WHERE (surah_a=2 AND ayah_a=255) OR (surah_b=2 AND ayah_b=255)"),
        ("mutashabihat",
         "SELECT COUNT(*) FROM mutashabihat WHERE (surah_a=2 AND ayah_a=255) OR (surah_b=2 AND ayah_b=255)"),
        ("ayah_topics",
         "SELECT GROUP_CONCAT(topic, ', ') FROM (SELECT DISTINCT topic FROM ayah_topics WHERE surah=2 AND ayah=255 LIMIT 5)"),
        ("ayah_themes",
         "SELECT GROUP_CONCAT(theme, ', ') FROM (SELECT DISTINCT theme FROM ayah_themes WHERE surah=2 AND ayah=255 LIMIT 3)"),
    ]
    found_any = False
    for name, sql in checks:
        val = conn.execute(sql).fetchone()[0]
        display = val if val else "(none)"
        print(f"  {name:<20} {display}")
        if val and val != 0:
            found_any = True
    if not found_any:
        print(
            "\n  NOTE: No cross-references found for 2:255.\n"
            "        This may indicate a scraping issue or that the data genuinely\n"
            "        does not include this verse in the cross-reference tables."
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(
        description="Populate QUL cross-reference tables in quran.db",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--db",
        default=str(DEFAULT_DB),
        help=f"Path to quran.db (default: {DEFAULT_DB})",
    )
    p.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help=(
            "Directory containing pre-downloaded QUL data files. "
            "Expected files: similar_ayahs.json, mutashabihat/phrase_verses.json "
            "(or mutashabihat.json), ayah_topics.json (or ayah_topics.db), "
            "ayah_themes.json (or ayah_themes.db). "
            "Skips QUL authentication and HTTP scraping."
        ),
    )
    p.add_argument(
        "--qul-email",
        default=None,
        help="QUL account email for authenticated bulk download (or set QUL_EMAIL env var).",
    )
    p.add_argument(
        "--qul-password",
        default=None,
        help="QUL account password (or set QUL_PASSWORD env var).",
    )
    p.add_argument(
        "--qul-cookie",
        default=None,
        help=(
            "QUL session cookie value for authenticated bulk download "
            "(or set QUL_COOKIE env var). "
            "Get it from DevTools → Application → Cookies → qul.tarteel.ai → "
            "_quran_com-community_session after signing in."
        ),
    )
    p.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Number of parallel HTTP workers for scraping (default: 8).",
    )
    p.add_argument(
        "--delay",
        type=float,
        default=0.05,
        help="Delay (seconds) between requests per worker (default: 0.05).",
    )
    return p.parse_args()


def main():
    args = parse_args()
    db_path = Path(args.db)

    print("project-fahm  build_crossrefs.py")
    print(f"  Source:  QUL — {QUL_REPO_URL} (MIT)")
    print(f"  DB:      {db_path}")
    if args.data_dir:
        print(f"  Data:    {args.data_dir} (pre-downloaded)")
    print()

    # Connect (create if needed)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")

    # Create tables
    print("Creating cross-reference tables (idempotent) …")
    create_tables(conn)

    # Build HTTP session (auth if possible)
    session = make_session()
    if not args.data_dir:
        has_auth = bool(
            args.qul_cookie or os.environ.get("QUL_COOKIE") or
            (args.qul_email or os.environ.get("QUL_EMAIL")) and
            (args.qul_password or os.environ.get("QUL_PASSWORD"))
        )
        if has_auth:
            print("Authenticating with QUL for direct download …")
            session = get_authenticated_session(args)
        else:
            print("No QUL credentials — using public page scraping.")
            print("  (Set QUL_EMAIL+QUL_PASSWORD or QUL_COOKIE for faster bulk download.)")
        print()

    # Populate tables
    counts = {}
    counts["similar_ayahs"] = populate_similar_ayahs(conn, session, args)
    counts["mutashabihat"]  = populate_mutashabihat(conn, session, args)
    counts["ayah_topics"]   = populate_ayah_topics(conn, session, args)
    counts["ayah_themes"]   = populate_ayah_themes(conn, session, args)

    # Record data provenance in metadata table
    import datetime
    today = datetime.date.today().isoformat()
    record_metadata(conn, "crossrefs_source",
                    f"TarteelAI/quranic-universal-library (MIT) — {QUL_REPO_URL}")
    record_metadata(conn, "crossrefs_url",    QUL_RESOURCES_URL)
    record_metadata(conn, "crossrefs_retrieved", today)
    record_metadata(conn, "crossrefs_license",   "MIT (Copyright 2024-present Tarteel, Inc)")

    # Verification
    ok = verify_counts(conn)
    spot_check(conn)

    conn.close()

    print("\n--- Summary ---")
    for table, n in counts.items():
        lo, hi = EXPECTED_COUNTS[table]
        status = "OK" if lo <= n <= hi else "OUTSIDE RANGE"
        print(f"  {table:<20} {n:>6} rows  [{status}]")

    if not ok:
        print(
            "\nWARNING: One or more tables have counts outside expected ranges.\n"
            "         Check output above. If scraping was used, consider running again\n"
            "         with --workers 4 --delay 0.2 to reduce rate limiting, or use\n"
            "         authenticated download (set QUL_EMAIL + QUL_PASSWORD).",
            file=sys.stderr,
        )
        sys.exit(1)

    print("\nDone.")


if __name__ == "__main__":
    main()
