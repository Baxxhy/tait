"""AST utilities for describing a candidate's explicit Oracle contract."""

from __future__ import annotations

import ast
import re


_ORACLE_CALLS = {
    "raises", "raisesregex", "warns", "warnsregex", "assertwarns",
    "assertwarnsregex", "assertlogs", "assertnlogs", "fail", "fnmatch_lines",
    "match_lines", "re_match_lines", "snapshot", "match",
}


def _name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _is_oracle_call(node: ast.Call) -> bool:
    leaf = _name(node.func).rsplit(".", 1)[-1].lower()
    return leaf.startswith("assert") or leaf in _ORACLE_CALLS


def _contains_explicit_failure(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Raise):
            raised = _name(child.exc.func) if isinstance(child.exc, ast.Call) else _name(child.exc)
            if raised in {"AssertionError", "pytest.fail"}:
                return True
        if isinstance(child, ast.Call) and _name(child.func).lower() in {
            "pytest.fail", "unittest.fail", "self.fail",
        }:
            return True
    return False


def oracle_kinds(code: str) -> list[str]:
    kinds: set[str] = set()
    marker = re.search(r"BRT_ORACLE_TYPE:\s*([A-Z_]+)", code)
    if marker:
        kinds.add(marker.group(1))
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return sorted(kinds)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            kinds.add("ASSERT_EXPRESSION")
        elif isinstance(node, ast.Call):
            leaf = _name(node.func).lower().rsplit(".", 1)[-1]
            if leaf in {"raises", "raisesregex"} or leaf.startswith("assertraises"):
                kinds.add("EXCEPTION")
            elif leaf in {"warns", "warnsregex"} or leaf.startswith("assertwarn"):
                kinds.add("WARNING")
            elif leaf in {"assertlogs", "assertnlogs"}:
                kinds.add("LOGGING")
            elif _is_oracle_call(node):
                kinds.add("FRAMEWORK_ASSERTION")
        elif isinstance(node, (ast.If, ast.Try)) and _contains_explicit_failure(node):
            kinds.add("EXPLICIT_FAILURE_GUARD")
    return sorted(kinds)
