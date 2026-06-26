"""Reproduce the final v43 submission from deterministic CSV artifacts.

Final private submission:
  OUTPUT/submission_v43_tlonly_v39d.csv

Definition:
  v43 = v25 base submission with ONLY verification_timeline replaced by the
  v39d structurally safe explicit-year timeline variant.

This script does not call any LLM and does not train models. It is the final
deterministic assembly step used for the private-counting upload.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [
    "id",
    "promise_status",
    "verification_timeline",
    "evidence_status",
    "evidence_quality",
]

EXPECTED_FINAL_SHA256 = "17fd3822058bf413b4b0475881af0268b88a1a3d290f29376ef1b06b124c896a"


def find_default_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [Path.cwd(), *here.parents]:
        if (candidate / "OUTPUT").exists() and (candidate / "esg_competition").exists():
            return candidate
    return here.parents[4]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_submission(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{path} missing columns: {missing}")
    df = df[REQUIRED_COLUMNS].copy()
    df["id"] = df["id"].astype(str)
    return df


def validate_submission(df: pd.DataFrame, path: Path) -> None:
    if list(df.columns) != REQUIRED_COLUMNS:
        raise ValueError(f"bad columns for {path}: {list(df.columns)}")
    if len(df) != 2000:
        raise ValueError(f"bad row count for {path}: {len(df)}")
    if df["id"].duplicated().any():
        raise ValueError(f"duplicate ids in {path}")
    if list(df["id"]) != sorted(df["id"], key=lambda x: int(x)):
        raise ValueError(f"ids are not sorted in {path}")

    allowed = {
        "promise_status": {"Yes", "No"},
        "verification_timeline": {
            "N/A",
            "already",
            "within_2_years",
            "between_2_and_5_years",
            "more_than_5_years",
        },
        "evidence_status": {"N/A", "Yes", "No"},
        "evidence_quality": {"N/A", "Clear", "Not Clear", "Misleading"},
    }
    for col, values in allowed.items():
        bad = sorted(set(df[col]) - values)
        if bad:
            raise ValueError(f"{path} has invalid {col} labels: {bad}")


def write_submission(df: pd.DataFrame, path: Path) -> None:
    validate_submission(df, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8", lineterminator="\n")
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"{path} has UTF-8 BOM")
    if b"\r\n" in raw:
        raise ValueError(f"{path} has CRLF newlines")
    if raw.count(b"\n") - 1 != 2000:
        raise ValueError(f"{path} newline/row-count validation failed")


def distribution(df: pd.DataFrame) -> dict[str, dict[str, int]]:
    return {col: dict(Counter(df[col])) for col in REQUIRED_COLUMNS[1:]}


def main() -> None:
    default_root = find_default_root()
    parser = argparse.ArgumentParser(description="Reproduce final v43 submission.")
    parser.add_argument("--root", type=Path, default=default_root)
    parser.add_argument("--base", type=Path, default=None)
    parser.add_argument("--timeline-source", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--expected-sha256", default=EXPECTED_FINAL_SHA256)
    args = parser.parse_args()

    root = args.root.resolve()
    base_path = args.base or root / "OUTPUT" / "submission_v25_evjudge.csv"
    timeline_path = args.timeline_source or root / "OUTPUT" / "submission_v39d_timeline_explicit_year_tau070_structsafe.csv"
    out_path = args.out or root / "OUTPUT" / "submission_v43_tlonly_v39d.csv"
    report_path = args.report or root / "esg_competition" / "outputs" / "v43_repro_report.json"

    base = read_submission(base_path)
    timeline = read_submission(timeline_path)
    validate_submission(base, base_path)
    validate_submission(timeline, timeline_path)

    timeline_by_id = timeline.set_index("id")["verification_timeline"]
    if set(base["id"]) != set(timeline_by_id.index):
        raise ValueError("base and timeline-source id sets differ")

    out = base.copy()
    out["verification_timeline"] = base["id"].map(timeline_by_id).to_numpy()
    write_submission(out, out_path)

    final_sha = sha256_file(out_path)
    diff_vs_base = {
        col: int((out[col] != base[col]).sum()) for col in REQUIRED_COLUMNS[1:]
    }
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": "v43 = v25 base + verification_timeline column from v39d timeline source",
        "root": str(root),
        "inputs": {
            "base": {"path": str(base_path), "sha256": sha256_file(base_path)},
            "timeline_source": {"path": str(timeline_path), "sha256": sha256_file(timeline_path)},
        },
        "output": {"path": str(out_path), "sha256": final_sha},
        "expected_sha256": args.expected_sha256,
        "sha256_matches_expected": final_sha == args.expected_sha256,
        "diff_vs_base": diff_vs_base,
        "distribution": distribution(out),
        "format_validation": {
            "rows": len(out),
            "columns": REQUIRED_COLUMNS,
            "sorted_ids": list(out["id"]) == sorted(out["id"], key=lambda x: int(x)),
            "utf8_no_bom_lf_newlines": True,
        },
        "private_leaderboard": {
            "score": 0.6457201,
            "rank": "6/143",
            "submitted_file": "submission_v43_tlonly_v39d.csv",
            "submitted_at": "2026-06-18 21:58:59",
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["sha256_matches_expected"]:
        raise SystemExit(f"SHA256 mismatch: {final_sha} != {args.expected_sha256}")


if __name__ == "__main__":
    main()
