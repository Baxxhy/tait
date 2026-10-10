"""Read issue fields permitted for candidate ranking."""
from __future__ import annotations
import json
from pathlib import Path

ISSUE_KEYS = ('instance_id','repo','version','base_commit','environment_setup_commit','problem_statement')


def load_safe_issues(path: Path) -> dict:
    payload = json.loads(path.read_text())
    rows = payload.values() if isinstance(payload,dict) else payload
    return {r['instance_id']:{k:r.get(k) for k in ISSUE_KEYS} for r in rows}
