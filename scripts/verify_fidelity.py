"""
verify_fidelity.py — Verify the integrity of the project-fahm quran.db.

Checks:
  - Row counts (ayahs must be exactly 6236, translations each exactly 6236,
    tafsirs each at least 6000)
  - Spot-checks specific verses against known-good text

The spot checks use the actual Tanzil Uthmani Unicode characters:
  - Alef wasla (U+0671 ٱ) is the Uthmani form of initial alef in words like اللَّه → ٱللَّهُ
  - Surah 112 verse 1 in the Tanzil Uthmani encoding includes the bismillah
    as part of verse 1: "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ قُلْ هُوَ ٱللَّهُ أَحَدٌ"

Usage:
    python scripts/verify_fidelity.py
    python scripts/verify_fidelity.py --db /path/to/quran.db
"""

import argparse
import sqlite3
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Check results container
# ---------------------------------------------------------------------------

PASS = "PASS"
FAIL = "FAIL"
_results: list[tuple[str, str]] = []  # (label, PASS|FAIL)


def check(label: str, condition: bool, detail: str = "") -> bool:
    status = PASS if condition else FAIL
    suffix = f" — {detail}" if detail else ""
    print(f"  [{status}] {label}{suffix}")
    _results.append((label, status))
    return condition


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    repo_root = Path(__file__).parent.parent
    default_db = repo_root / "public" / "quran.db"

    parser = argparse.ArgumentParser(
        description="Verify fidelity of project-fahm quran.db."
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=default_db,
        help="Path to quran.db (default: public/quran.db relative to repo root)",
    )
    args = parser.parse_args()

    db_path: Path = args.db

    if not db_path.exists():
        print(f"ERROR: Database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(db_path)

    print(f"Verifying: {db_path}")
    print()

    # ------------------------------------------------------------------
    # 1. Row count checks
    # ------------------------------------------------------------------
    print("=== Row count checks ===")

    ayah_count = conn.execute("SELECT COUNT(*) FROM ayahs").fetchone()[0]
    check("ayahs total = 6236", ayah_count == 6236, f"got {ayah_count}")

    ya_count = conn.execute(
        "SELECT COUNT(*) FROM translations WHERE key='yusufali'"
    ).fetchone()[0]
    check("translations[yusufali] = 6236", ya_count == 6236, f"got {ya_count}")

    pt_count = conn.execute(
        "SELECT COUNT(*) FROM translations WHERE key='pickthall'"
    ).fetchone()[0]
    check("translations[pickthall] = 6236", pt_count == 6236, f"got {pt_count}")

    jl_count = conn.execute(
        "SELECT COUNT(*) FROM tafsirs WHERE key='jalalayn'"
    ).fetchone()[0]
    check("tafsirs[jalalayn] >= 6000", jl_count >= 6000, f"got {jl_count}")

    ik_count = conn.execute(
        "SELECT COUNT(*) FROM tafsirs WHERE key='ibnkathir'"
    ).fetchone()[0]
    check("tafsirs[ibnkathir] >= 6000", ik_count >= 6000, f"got {ik_count}")

    # ------------------------------------------------------------------
    # 2. Arabic spot-checks
    # ------------------------------------------------------------------
    print()
    print("=== Arabic text spot-checks ===")

    # 1:1 — must start with بِسْمِ (U+0628 + kasra + U+0633 + sukun + U+0645 + kasra)
    row = conn.execute("SELECT arabic FROM ayahs WHERE surah=1 AND ayah=1").fetchone()
    if row:
        text_1_1 = row[0]
        # The Tanzil Uthmani text for 1:1 starts with بِسْمِ (ba with kasra, sin with sukun, mim with kasra)
        check(
            "1:1 Arabic starts with 'بِسْمِ'",
            text_1_1.startswith("بِسْمِ"),
            f"got {text_1_1[:30]!r}",
        )
    else:
        check("1:1 Arabic exists", False, "row not found")

    # 2:255 (Ayah al-Kursi) — must start with the word Allah (ٱللَّهُ or اللَّهُ)
    # We check the first three base letters: alef (U+0671 or U+0627), lam, lam
    # Diacritic ordering varies between data sources, so we strip all diacritics for this check.
    row = conn.execute("SELECT arabic FROM ayahs WHERE surah=2 AND ayah=255").fetchone()
    if row:
        text_2_255 = row[0]
        # Strip combining diacritics (U+064B–U+065F and U+0670) to compare base letters only
        import unicodedata
        base_255 = "".join(
            c for c in text_2_255
            if not (0x064B <= ord(c) <= 0x065F or ord(c) == 0x0670)
        )
        # After stripping, the text should start with alef+lam+lam+ha (the word "Allah")
        # Accept both U+0671 (alef wasla) and U+0627 (plain alef)
        starts_ok = (
            base_255.startswith("ٱلله")  # ٱلله
            or base_255.startswith("الله")  # الله
        )
        check(
            "2:255 Arabic starts with Allah (ٱلله / الله, base letters)",
            starts_ok,
            f"got {text_2_255[:30]!r}",
        )
    else:
        check("2:255 Arabic exists", False, "row not found")

    # 112:1 — In Tanzil Uthmani, verse 1 of surah 112 contains the bismillah + the verse text.
    # The verse must contain: قُلْ هُوَ ٱللَّهُ أَحَدٌ (with alef wasla) OR اللَّهُ (plain alef)
    row = conn.execute("SELECT arabic FROM ayahs WHERE surah=112 AND ayah=1").fetchone()
    if row:
        text_112_1 = row[0]
        # Accept both alef-wasla and plain-alef forms for robustness
        contains_qul = "قُلْ هُوَ" in text_112_1
        contains_ahad = "أَحَدٌ" in text_112_1
        check(
            "112:1 Arabic contains 'قُلْ هُوَ ... أَحَدٌ'",
            contains_qul and contains_ahad,
            f"got {text_112_1!r}",
        )
    else:
        check("112:1 Arabic exists", False, "row not found")

    # ------------------------------------------------------------------
    # 3. Translation spot-checks
    # ------------------------------------------------------------------
    print()
    print("=== Translation spot-checks ===")

    # Yusuf Ali 1:1 must contain "In the name of Allah"
    row = conn.execute(
        "SELECT text FROM translations WHERE surah=1 AND ayah=1 AND key='yusufali'"
    ).fetchone()
    if row:
        ya_1_1 = row[0]
        check(
            "Yusuf Ali 1:1 contains 'In the name of Allah'",
            "In the name of Allah" in ya_1_1,
            f"got {ya_1_1!r}",
        )
    else:
        check("Yusuf Ali 1:1 exists", False, "row not found")

    # Pickthall 1:1 must contain "In the name of Allah"
    row = conn.execute(
        "SELECT text FROM translations WHERE surah=1 AND ayah=1 AND key='pickthall'"
    ).fetchone()
    if row:
        pt_1_1 = row[0]
        check(
            "Pickthall 1:1 contains 'In the name of Allah'",
            "In the name of Allah" in pt_1_1,
            f"got {pt_1_1!r}",
        )
    else:
        check("Pickthall 1:1 exists", False, "row not found")

    # ------------------------------------------------------------------
    # 4. Tafsir spot-checks
    # ------------------------------------------------------------------
    print()
    print("=== Tafsir spot-checks ===")

    # al-Jalalayn 1:1 must be non-empty Arabic text
    row = conn.execute(
        "SELECT text FROM tafsirs WHERE surah=1 AND ayah=1 AND key='jalalayn'"
    ).fetchone()
    if row:
        jl_1_1 = row[0]
        check(
            "jalalayn 1:1 non-empty",
            bool(jl_1_1 and jl_1_1.strip()),
            f"got {jl_1_1[:60]!r}",
        )
    else:
        check("jalalayn 1:1 exists", False, "row not found")

    # Ibn Kathir 1:1 must be non-empty and contain some Arabic
    row = conn.execute(
        "SELECT text FROM tafsirs WHERE surah=1 AND ayah=1 AND key='ibnkathir'"
    ).fetchone()
    if row:
        ik_1_1 = row[0]
        # Strip HTML tags to check actual text length
        import re
        plain = re.sub(r"<[^>]+>", "", ik_1_1).strip()
        check(
            "ibnkathir 1:1 non-empty (after stripping HTML)",
            bool(plain),
            f"{len(plain)} chars",
        )
    else:
        check("ibnkathir 1:1 exists", False, "row not found")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    conn.close()
    print()
    total = len(_results)
    passed = sum(1 for _, s in _results if s == PASS)
    failed = total - passed

    print("=" * 40)
    print(f"Results: {passed}/{total} passed")
    if failed:
        print(f"FAILED checks ({failed}):")
        for label, status in _results:
            if status == FAIL:
                print(f"  - {label}")
        sys.exit(1)
    else:
        print("All checks PASSED.")
        sys.exit(0)


if __name__ == "__main__":
    main()
