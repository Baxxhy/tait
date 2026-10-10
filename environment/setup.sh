#!/usr/bin/env bash
set -euo pipefail
bundle_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
bootstrap_python=${PYTHON:-python3.12}
"$bootstrap_python" -c 'import sys; assert sys.version_info >= (3, 11), "Python 3.11+ is required"'
for name in controller swt tdd; do
    "$bootstrap_python" -m venv "$bundle_root/environments/$name"
done
"$bundle_root/environments/controller/bin/python" -m pip install -r "$bundle_root/requirements.txt"
"$bundle_root/environments/swt/bin/python" -m pip install -r "$bundle_root/requirements.txt" fire
"$bundle_root/environments/tdd/bin/python" -m pip install beautifulsoup4 'datasets==3.6.0' docker ghapi python-dotenv requests unidiff tqdm pytest 'cldk==1.0.6'
"$bundle_root/environments/tdd/bin/python" -m pip install --no-deps -e "$bundle_root/vendor/TDD-Bench-Verified"
PYTHONPATH="$bundle_root/evaluation/vendor/swtbench:$bundle_root/evaluation/vendor/swtbench/src" "$bundle_root/environments/swt/bin/python" -c 'import src.main'
"$bundle_root/environments/tdd/bin/python" -c 'import tddbench.harness.run_evaluation'
PYTHONPATH="$(dirname "$bundle_root")" "$bundle_root/environments/controller/bin/python" -c 'import tait.pipeline.run; import tait.pipeline.run_issue_rewrite'
