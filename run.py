#!/usr/bin/env python3
"""Run the paper's target recovery, individual adaptation, ranking and evaluation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import runpy
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PKG = ROOT


def read_config(path: Path) -> dict:
    namespace = runpy.run_path(str(path))
    config = namespace.get("CONFIG")
    if not isinstance(config, dict):
        raise ValueError("Python configuration must define a CONFIG dictionary")
    required = {
        'dataset',
        'model',
        'provider',
        'base_url',
        'api_key_env',
        'api_pool',
        'repo_root',
        'official_python',
        'output',
        'docker_host',
        'top_code',
        'top_tests',
        'rounds',
        'repetitions',
        'temperature',
        'target_temperature',
        'validation_temperature',
        'workers',
        'max_tokens',
        'execution_timeout',
        'limit',
        'instance_ids',
        'compute_coverage',
        'evaluate',
        'resume',
        'runtime_environment',
    }
    if set(config) != required:
        raise ValueError(f"Configuration keys differ: {sorted(set(config) ^ required)}")
    if config["dataset"] not in {"swt", "tdd"}:
        raise ValueError("dataset must be swt or tdd")
    if config["provider"] not in {"gpt", "deepseek"}:
        raise ValueError("provider must be gpt or deepseek (OpenAI-compatible API)")
    for name in ("workers", "top_code", "top_tests", "rounds", "repetitions", "max_tokens", "execution_timeout"):
        if type(config[name]) is not int or config[name] < 1:
            raise ValueError(f"{name} must be a positive integer")
    if config["rounds"] > 10:
        raise ValueError("rounds must be <= 10; paper default is 5 including initial adaptation")
    if config["limit"] is not None and (type(config["limit"]) is not int or config["limit"] < 1):
        raise ValueError("limit must be None or a positive integer")
    for name in ("temperature", "target_temperature", "validation_temperature"):
        if type(config[name]) not in (int, float) or not 0 <= config[name] <= 2:
            raise ValueError(f"{name} must be between 0 and 2")
    for name in ("resume", "evaluate", "compute_coverage"):
        if type(config[name]) is not bool:
            raise ValueError(f"{name} must be a boolean")
    if not isinstance(config["instance_ids"], list) or not all(isinstance(x, str) for x in config["instance_ids"]):
        raise ValueError("instance_ids must be a list of strings")
    if not config["model"] or not config["base_url"].startswith(("https://", "http://")):
        raise ValueError("model and a valid base_url are required")
    if not isinstance(config["runtime_environment"], dict) or any(
        not key.startswith("BRT") or not isinstance(value, str)
        for key, value in config["runtime_environment"].items()
    ):
        raise ValueError("runtime_environment must map BRT environment names to strings")
    advanced = config["runtime_environment"]
    if advanced.get("BRT_THINKING_PARAMETER", "reasoning_effort") not in {
        "reasoning_effort", "thinking", "enable_thinking"
    }:
        raise ValueError("Unsupported BRT_THINKING_PARAMETER")
    if "BRT_GENERATION_MAX_TOKENS" in advanced:
        if int(advanced["BRT_GENERATION_MAX_TOKENS"]) < 1:
            raise ValueError("BRT_GENERATION_MAX_TOKENS must be positive")
    for key in ("BRT_REASONING_EFFORT", "BRT_GENERATION_REASONING_EFFORT", "BRT_PLANNING_REASONING_EFFORT"):
        if key in advanced and advanced[key] not in {"none", "minimal", "low", "medium", "high", "xhigh"}:
            raise ValueError(f"Unsupported reasoning effort: {key}")
    return config


def resolve(value: str) -> Path:
    path = Path(value).expanduser()
    return (ROOT / path).resolve() if not path.is_absolute() else path.resolve()


def release_digest() -> str:
    digest = hashlib.sha256()
    # Read source directly; no distributed checksum file is required.
    files = set(ROOT.glob("*.py")) - {ROOT / "config.py"}
    for directory in ("core", "context", "execution", "generation", "issue", "llm",
                      "mutation", "pipeline", "prompts", "prompts_en", "retrieval",
                      "runtime", "scripts", "io", "evaluation", "validation", "vendor",
                      "environment"):
        files.update(path for path in (ROOT / directory).rglob("*")
                     if path.is_file() and path.suffix in
                     {".py", ".md", ".sh", ".txt", ".toml", ".cfg", ".yml", ".whl"})
    for path in sorted(files):
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def selected_issues(config: dict) -> list[dict]:
    rows = json.loads((ROOT / "data" / config["dataset"] / "issues.json").read_text())
    requested = set(config["instance_ids"])
    missing = requested - {row["instance_id"] for row in rows}
    if missing:
        raise ValueError(f"Unknown instance IDs: {sorted(missing)}")
    if requested:
        rows = [row for row in rows if row["instance_id"] in requested]
    return rows[:config["limit"]] if config["limit"] else rows


def build_commands(config: dict, output: Path) -> list[list[str]]:
    source = ROOT / "data" / config["dataset"]
    issues = output / "issues.json"
    swt = PKG / "evaluation/vendor/swtbench"
    tdd = ROOT / "vendor/TDD-Bench-Verified"
    common = ["--instances_path", str(issues), "--code_retrieval_path", str(source / "code_retrieval.json"),
              "--test_retrieval_path", str(source / "test_retrieval.json"), "--llm-provider", config["provider"],
              "--model", config["model"], "--base_url", config["base_url"], "--max_workers", str(config["workers"]),
              "--max_tokens", str(config["max_tokens"]), "--top_code", str(config["top_code"]),
              "--top_tests", str(config["top_tests"])]
    if config["resume"]:
        common += ["--resume"]
    commands = [
        [sys.executable, "-m", "tait.pipeline.run_issue_rewrite", *common,
         "--temperature", str(config["target_temperature"]), "--output_dir", str(output / "issue_rewrite")],
        [sys.executable, "-m", "tait.pipeline.run", *common,
         "--temperature", str(config["temperature"]), "--output_dir", str(output / "generation"),
         "--repo_root_base", str(resolve(config["repo_root"])), "--dataset_mode", config["dataset"],
         "--runtime_backend", "official_docker", "--official_harness_python", str(resolve(config["official_python"])),
         "--swtbench_root", str(swt), "--tddbench_root", str(tdd), "--max_semantic_rounds", str(config["rounds"]),
         "--timeout", str(config["execution_timeout"]), "--validation_mode", "buggy_only",
         "--enable_behavior_target", "true", "--enable_seed_mutation", "true", "--enable_semantic_delta", "true",
         "--enable_specialized_feedback", "true", "--enable_environment_feedback", "true",
         "--enable_trigger_feedback", "true", "--enable_assertion_feedback", "true"],
        [sys.executable, str(PKG / "scripts/run_generation_strict_icore.py"), "--generation", str(output / "generation"),
         "--output", str(output / "selected"), "--issues", str(issues), "--workers", str(config["workers"])]
    ]
    if config["evaluate"]:
        commands.append([
            sys.executable, str(PKG / "scripts/run_official_eval_after_generation.py"), "--dataset", config["dataset"],
            "--outputs-dir", str(output / "selected/generation"), "--dataset-file", str(issues),
            "--evaluation-dir", str(output / "evaluation"), "--max-workers", str(config["workers"]),
            "--timeout", str(config["execution_timeout"]), "--run-id", output.parent.name + "_" + output.name,
            "--model-name", config["model"], "--compute-coverage", str(config["compute_coverage"]).lower(),
            "--official-python", str(resolve(config["official_python"])), "--swtbench-root", str(swt),
            "--tddbench-root", str(tdd), "--official-dataset-name", str(source / "official.json")])
    return commands


def build_environment(config: dict, output: Path) -> dict:
    # A prior experiment's switches must not silently change the submitted method.
    env = {k: v for k, v in os.environ.items() if not k.startswith(("BRT", "GPT_", "DEEPSEEK_", "OPENAI_"))}
    env.update(config["runtime_environment"])
    env.update({"PYTHONPATH": str(ROOT.parent), "BRT_WORKSPACE_ROOT": str(ROOT),
                "BRT_LLM_PROVIDER": config["provider"], "BRT_MODEL_ID": config["model"],
                "BRT_VALIDATION_TEMPERATURE": str(config["validation_temperature"]), "DOCKER_HOST": config["docker_host"],
                "BRT_COST_DIR": str(output), "BRT_BEHAVIOR_CACHE_DIR": str(output / "issue_rewrite"),
                "BRT_OFFICIAL_DOCKER_STARTUP_TIMEOUT": str(config["execution_timeout"]),
                "OFFICIAL_HARNESS_PYTHON": str(resolve(config["official_python"])), "TMPDIR": str(output / "tmp")})
    prefix = "GPT" if config["provider"] == "gpt" else "DEEPSEEK"
    env[prefix + "_MODEL"] = config["model"]
    env[prefix + "_BASE_URL"] = config["base_url"]
    key = os.environ.get(config["api_key_env"], "")
    if key:
        env[prefix + "_API_KEY"] = key
    if config["api_pool"]:
        env["BRT_API_POOL_FILE"] = str(resolve(config["api_pool"]))
    return env


def run(config: dict, dry_run: bool = False) -> None:
    rows = selected_issues(config)
    output_root = resolve(config["output"])
    if output_root == ROOT or any(output_root == ROOT / x or ROOT / x in output_root.parents
                                 for x in ("core", "context", "execution", "generation", "issue", "llm", "mutation", "pipeline", "prompts", "prompts_en", "retrieval", "runtime", "scripts", "io", "evaluation", "validation", "data", "vendor", "tests", "environment")):
        raise ValueError("output must not overwrite submission source or data")
    if not dry_run:
        for path in (resolve(config["repo_root"]), resolve(config["official_python"])):
            if not path.exists():
                raise ValueError(f"Required path does not exist: {path}; edit config.py")
        if config["api_pool"]:
            if not resolve(config["api_pool"]).is_file():
                raise ValueError("Configured API pool file does not exist")
        elif not os.environ.get(config["api_key_env"]):
            raise ValueError(f"Set {config['api_key_env']} or api_pool before running")
    for repetition in range(1, config["repetitions"] + 1):
        output = output_root / f"repeat_{repetition}"
        commands = build_commands(config, output)
        if dry_run:
            print(json.dumps({"repetition": repetition, "instances": len(rows), "commands": commands}, indent=2))
            continue
        identity = {"config": config, "instance_ids": [r["instance_id"] for r in rows],
                    "inputs": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in (ROOT / "data" / config["dataset"]).glob("*.json")},
                    "source": release_digest()}
        saved = output / "run_config.json"
        if saved.exists() and (not config["resume"] or json.loads(saved.read_text()) != identity):
            raise ValueError("Resume configuration, input data, or source differs; use a new output directory")
        if output.exists() and any(output.iterdir()) and not saved.exists():
            raise ValueError("Nonempty output has no run identity; choose a new output directory")
        (output / "logs").mkdir(parents=True, exist_ok=True)
        (output / "tmp").mkdir(exist_ok=True)
        saved.write_text(json.dumps(identity, indent=2))
        (output / "issues.json").write_text(json.dumps(rows))
        (output / "commands.json").write_text(json.dumps(commands, indent=2))
        env = build_environment(config, output)
        for index, command in enumerate(commands, 1):
            print(f"Repetition {repetition}/{config['repetitions']}, stage {index}/{len(commands)}: {output / 'logs'}", flush=True)
            with (output / "logs" / f"{index}.log").open("a") as log:
                subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
            if index == 1:
                missing = [r["instance_id"] for r in rows if not (output / "issue_rewrite" / r["instance_id"] / "behavior_target.json").is_file()]
                if missing:
                    raise RuntimeError(f"Target recovery incomplete: {missing}; resume this run")
    if not dry_run and config["evaluate"]:
        summarize_repetitions(config, output_root)


def summarize_repetitions(config: dict, output_root: Path) -> dict:
    records = []
    for repetition in range(1, config["repetitions"] + 1):
        path = output_root / f"repeat_{repetition}" / "evaluation/metrics.json"
        metrics = json.loads(path.read_text())
        if metrics["total_instances"] != len(selected_issues(config)):
            raise ValueError(f"Evaluation denominator differs from selected inputs: {path}")
        records.append({"repetition": repetition, "metrics": metrics})
    keys = ("f2p_at_1_percent", "patch_cov_at_1_percent", "patch_cov_delta_at_1_percent")
    result = {"dataset": config["dataset"], "model": config["model"],
              "repetitions": records, "median": {
                  key: statistics.median(record["metrics"][key] for record in records)
                  for key in keys if all(type(record["metrics"].get(key)) in (int, float) for record in records)}}
    (output_root / "summary.json").write_text(json.dumps(result, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config.py")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without calling APIs or Docker")
    args = parser.parse_args()
    try:
        run(read_config(args.config), args.dry_run)
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Configuration error: {exc}\n")


if __name__ == "__main__":
    main()
