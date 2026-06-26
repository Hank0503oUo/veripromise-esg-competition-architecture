"""Build the v39d structurally safe explicit-year timeline variant.

Inputs:
  OUTPUT/submission_v25_evjudge.csv
  esg_competition/data/v35_timeline_anchor_features_test.csv
  esg_competition/outputs/v18C_test_probas.csv

Output:
  OUTPUT/submission_v39d_timeline_explicit_year_tau070_structsafe.csv

This is a cleaned, path-portable version of the final-day timeline script.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = [
    "id",
    "promise_status",
    "verification_timeline",
    "evidence_status",
    "evidence_quality",
]

TIMELINE_CLASSES = [
    "N/A",
    "already",
    "between_2_and_5_years",
    "more_than_5_years",
    "within_2_years",
]

TIMELINE_OFFSETS = np.array([-0.2, 0.3, 0.3, 0.2, 0.0], dtype=float)
VALID_TIMELINE = set(TIMELINE_CLASSES)


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


def validate_and_write(df: pd.DataFrame, path: Path) -> None:
    if list(df.columns) != REQUIRED_COLUMNS:
        raise ValueError(f"bad columns for {path}: {list(df.columns)}")
    if len(df) != 2000:
        raise ValueError(f"bad row count for {path}: {len(df)}")
    if df["id"].duplicated().any():
        raise ValueError(f"duplicate ids in {path}")
    if list(df["id"]) != sorted(df["id"], key=lambda x: int(x)):
        raise ValueError(f"ids are not sorted in {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8", lineterminator="\n")
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or b"\r\n" in raw or raw.count(b"\n") - 1 != 2000:
        raise ValueError(f"CSV encoding/newline validation failed for {path}")


def load_v18c_timeline_margin(v18c_test_probas: Path) -> pd.DataFrame:
    p = pd.read_csv(v18c_test_probas, dtype=str, keep_default_na=False)
    p["id"] = p["id"].astype(str)
    cols = [f"verification_timeline|{c}" for c in TIMELINE_CLASSES]
    missing = [c for c in cols if c not in p.columns]
    if missing:
        raise ValueError(f"{v18c_test_probas} missing columns: {missing}")
    arr = p[cols].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy(float)
    adjusted = arr + TIMELINE_OFFSETS.reshape(1, -1)
    order = np.argsort(-adjusted, axis=1)
    top1 = order[:, 0]
    top2 = order[:, 1]
    return pd.DataFrame(
        {
            "id": p["id"],
            "v18c_timeline_pred": [TIMELINE_CLASSES[i] for i in top1],
            "v18c_timeline_margin": adjusted[np.arange(len(adjusted)), top1]
            - adjusted[np.arange(len(adjusted)), top2],
        }
    )


def apply_v39d(base: pd.DataFrame, anchors: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = base.copy()
    work = df.merge(anchors, on="id", how="left")
    pred = work["anchor_pred"].fillna("").astype(str)
    conf = pd.to_numeric(work["anchor_confidence"], errors="coerce").fillna(0.0)
    reason = work["anchor_reason"].fillna("").astype(str)
    margin = pd.to_numeric(work["v18c_timeline_margin"], errors="coerce").fillna(999.0)

    mask = pred.isin(VALID_TIMELINE)
    mask &= conf >= 0.70
    mask &= pred != work["verification_timeline"]
    mask &= reason.isin({"explicit_target_year", "explicit_target_year_range"})
    mask &= work["promise_status"] == "Yes"
    mask &= work["verification_timeline"] != "N/A"

    before = df["verification_timeline"].copy()
    df.loc[mask.to_numpy(), "verification_timeline"] = pred[mask].to_numpy()
    changes = pd.DataFrame(
        {
            "id": work.loc[mask, "id"],
            "from": before[mask.to_numpy()].to_numpy(),
            "to": pred[mask].to_numpy(),
            "confidence": conf[mask].to_numpy(),
            "reason": reason[mask].to_numpy(),
            "v18c_margin": margin[mask].to_numpy(),
        }
    )
    return df, changes


def main() -> None:
    default_root = find_default_root()
    parser = argparse.ArgumentParser(description="Build v39d timeline variant.")
    parser.add_argument("--root", type=Path, default=default_root)
    parser.add_argument("--base", type=Path, default=None)
    parser.add_argument("--anchors", type=Path, default=None)
    parser.add_argument("--v18c-probas", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()

    root = args.root.resolve()
    base_path = args.base or root / "OUTPUT" / "submission_v25_evjudge.csv"
    anchors_path = args.anchors or root / "esg_competition" / "data" / "v35_timeline_anchor_features_test.csv"
    probas_path = args.v18c_probas or root / "esg_competition" / "outputs" / "v18C_test_probas.csv"
    out_path = args.out or root / "OUTPUT" / "submission_v39d_timeline_explicit_year_tau070_structsafe.csv"
    report_path = args.report or root / "esg_competition" / "outputs" / "v39d_repro_report.json"

    base = read_submission(base_path)
    anchors = pd.read_csv(anchors_path, dtype=str, keep_default_na=False)
    anchors["id"] = anchors["id"].astype(str)
    anchors = anchors.merge(load_v18c_timeline_margin(probas_path), on="id", how="left")

    out, changes = apply_v39d(base, anchors)
    validate_and_write(out, out_path)
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": "v39d explicit-year timeline anchor, tau=0.70, promise_status=Yes, keep current N/A",
        "inputs": {
            "base": {"path": str(base_path), "sha256": sha256_file(base_path)},
            "anchors": {"path": str(anchors_path), "sha256": sha256_file(anchors_path)},
            "v18c_probas": {"path": str(probas_path), "sha256": sha256_file(probas_path)},
        },
        "output": {"path": str(out_path), "sha256": sha256_file(out_path)},
        "n_changes": int(len(changes)),
        "from_to": {
            f"{a}->{b}": int(n) for (a, b), n in Counter(zip(changes["from"], changes["to"])).items()
        },
        "timeline_distribution": dict(Counter(out["verification_timeline"])),
        "changes_preview": changes.head(30).to_dict(orient="records"),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
