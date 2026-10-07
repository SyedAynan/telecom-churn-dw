"""Extract: fetch the Telco Customer Churn CSV into data/raw/.

Strategy (best-of-both provenance and convenience):
1. If data/raw/Telco-Customer-Churn.csv already exists (e.g. a manual Kaggle
   download), verify its checksum and use it as-is.
2. Otherwise download the IBM GitHub mirror — byte-identical to the Kaggle
   original — and verify the same MD5.

Idempotent: re-running never re-downloads a file that already passes checks.
"""
from __future__ import annotations

import hashlib
import sys
import urllib.request

from etl.paths import (
    DATA_RAW,
    EXPECTED_MD5,
    RAW_CSV_PATH,
    SOURCE_URL,
    ensure_dirs,
)


def md5_of(path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def extract() -> Path:
    ensure_dirs()

    if RAW_CSV_PATH.exists():
        digest = md5_of(RAW_CSV_PATH)
        if digest == EXPECTED_MD5:
            print(f"[extract] {RAW_CSV_PATH.name} already present (md5 ok) — skipping download")
            return RAW_CSV_PATH
        raise SystemExit(
            f"[extract] {RAW_CSV_PATH} exists but md5 {digest} != {EXPECTED_MD5}.\n"
            "Delete the file or replace it with the unmodified Kaggle CSV."
        )

    print(f"[extract] downloading {SOURCE_URL}")
    tmp = DATA_RAW / f"{RAW_CSV_PATH.name}.part"
    urllib.request.urlretrieve(SOURCE_URL, tmp)

    digest = md5_of(tmp)
    if digest != EXPECTED_MD5:
        tmp.unlink(missing_ok=True)
        raise SystemExit(
            f"[extract] downloaded file failed integrity check (md5 {digest}). "
            "Upstream mirror may have changed — please download the Kaggle "
            "dataset 'Telco Customer Churn' manually into data/raw/."
        )

    tmp.rename(RAW_CSV_PATH)
    print(f"[extract] saved {RAW_CSV_PATH} (md5 ok)")
    return RAW_CSV_PATH


if __name__ == "__main__":
    extract()
