#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "reproduction" / "results"

REQUIRED_PATHS = [
    "data",
    "outputs",
    "data/flight",
    "data/flight/images",
    "data/flight/transforms.json",
    "outputs/flight/splatfacto/2024-09-12_172434/config.yml",
    "outputs/flight/splatfacto/2024-09-12_172434/nerfstudio_models",
    "outputs/stonehenge/splatfacto/2024-09-11_100724/config.yml",
    "outputs/statues/splatfacto/2024-09-11_095852/config.yml",
    "outputs/old_union2/splatfacto/2024-09-02_151414/config.yml",
]


def count_limited(path: Path, limit: int = 100000) -> int:
    if not path.exists() or not path.is_dir():
        return 0
    count = 0
    for _, _, files in os.walk(path):
        count += len(files)
        if count >= limit:
            return count
    return count


def path_kind(path: Path) -> str:
    if not path.exists():
        return "missing"
    if path.is_symlink():
        target = os.readlink(path)
        if path.is_dir():
            return f"symlink_dir->{target}"
        if path.is_file():
            return f"symlink_file->{target}"
        return f"symlink_other->{target}"
    if path.is_dir():
        return "dir"
    if path.is_file():
        return "file"
    return "other"


def choose_phase(explicit: str | None) -> str:
    if explicit:
        return explicit
    return "after_download" if (ROOT / "data").exists() or (ROOT / "outputs").exists() else "before_download"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check official SAFER-Splat data/output paths.")
    parser.add_argument("--phase", choices=["before_download", "after_download"], default=None)
    args = parser.parse_args()

    RESULTS.mkdir(parents=True, exist_ok=True)
    phase = choose_phase(args.phase)
    output = RESULTS / f"official_data_path_check_{phase}.csv"
    rows = []
    for rel in REQUIRED_PATHS:
        path = ROOT / rel
        rows.append({
            "path": rel,
            "exists": str(path.exists()),
            "kind": path_kind(path),
            "file_count_limited": str(count_limited(path) if path.is_dir() else 0),
            "size_bytes": str(path.stat().st_size if path.exists() and path.is_file() else ""),
        })
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "exists", "kind", "file_count_limited", "size_bytes"])
        writer.writeheader()
        writer.writerows(rows)
    present = sum(row["exists"] == "True" for row in rows)
    print(f"phase={phase}")
    print(f"output={output}")
    print(f"present={present}/{len(rows)}")
    for row in rows:
        print(f"{row['exists']:5s} {row['kind']:35s} {row['path']}")
    return 0 if present == len(rows) else 2


if __name__ == "__main__":
    raise SystemExit(main())