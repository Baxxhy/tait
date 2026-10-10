"""Prompt compatibility constants loaded from markdown prompt files."""

from __future__ import annotations

from ..prompts.loader import load_prompt


ISSUE_REWRITE_SYSTEM_PROMPT = load_prompt("issue_rewrite", "system")
ISSUE_REWRITE_USER_PROMPT = load_prompt("issue_rewrite", "user")



MUTATION_GENERATION_SYSTEM_PROMPT = load_prompt("generation", "system")
MUTATION_GENERATION_USER_PROMPT = load_prompt("generation", "user")



BUGGY_ONLY_VERIFIER_SYSTEM_PROMPT = load_prompt("verifier", "system")
BUGGY_ONLY_VERIFIER_USER_PROMPT = load_prompt("verifier", "user")


PROTOCOL_RECOVERY_SYSTEM_PROMPT = load_prompt("protocol_recovery", "system")
PROTOCOL_RECOVERY_USER_PROMPT = load_prompt("protocol_recovery", "user")

SEED_MUTATION_PLAN_SYSTEM_PROMPT = load_prompt("mutation_plan", "system")
SEED_MUTATION_PLAN_USER_PROMPT = load_prompt("mutation_plan", "user")


STRICT_SEMANTIC_VERIFIER_SYSTEM_PROMPT = load_prompt("strict_semantic_verifier", "system")
STRICT_SEMANTIC_VERIFIER_USER_PROMPT = load_prompt("strict_semantic_verifier", "user")
