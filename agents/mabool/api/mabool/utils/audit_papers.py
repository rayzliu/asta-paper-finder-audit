from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock
from typing import Iterable

from mabool.utils.paths import project_root

_ENABLED = bool(os.environ.get("AUDIT_PAPERS"))
_retrieved: set[str] = set()
_final: set[str] = set()
_lock = Lock()


def _report_path() -> Path:
    out = os.environ.get("AUDIT_PAPERS_REPORT")
    if out:
        return Path(out)
    return project_root() / "audit_papers_report.json"


def record_retrieved(corpus_ids: Iterable[str]) -> None:
    """Record papers that were retrieved into the candidate pool.

    No-op unless `AUDIT_PAPERS` env var is set.
    """
    if not _ENABLED:
        return
    with _lock:
        for cid in corpus_ids:
            if cid:
                _retrieved.add(cid)


def record_final(corpus_ids: Iterable[str]) -> None:
    """Record final papers included in the report and write an audit report.

    No-op unless `AUDIT_PAPERS` env var is set.
    """
    if not _ENABLED:
        return
    with _lock:
        for cid in corpus_ids:
            if cid:
                _final.add(cid)

        sideloaded = sorted(list(_final - _retrieved))
        retrieved_only = sorted(list(_retrieved - _final))
        both = sorted(list(_final & _retrieved))

        payload = {
            "sideloaded": sideloaded,
            "retrieved_only": retrieved_only,
            "final_included": both,
            "counts": {"retrieved": len(_retrieved), "final": len(_final), "sideloaded": len(sideloaded)},
        }

        try:
            path = _report_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2)
        except Exception:
            # Best-effort only for debugging
            pass
