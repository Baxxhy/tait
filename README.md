# Tait

Requires Linux, Python 3.12, Git, Docker, internet access, and a model API key. The default Docker storage check requires 120 GiB free. Keep the folder named `tait` and run commands inside it.

## Setup

```bash
bash environment/setup.sh
source environments/controller/bin/activate
python scripts/bootstrap_repositories.py \
  --dataset data/swt/issues.json --dataset data/tdd/issues.json \
  --repo-root repositories
```

## Configure

Edit `config.py` to set the model, API endpoint, and experiment parameters.

| Dataset | `dataset` | `official_python` | `output` |
| --- | --- | --- | --- |
| SWT | `'swt'` | `'environments/swt/bin/python'` | `'runs/swt'` |
| TDD | `'tdd'` | `'environments/tdd/bin/python'` | `'runs/tdd'` |

Defaults use up to five retrieved tests, five rounds, and three repetitions. For one issue, set `'limit': 1`, `'repetitions': 1`, and a separate output directory.

## Run

```bash
export OPENAI_API_KEY='your-api-key'
python run.py --dry-run
python run.py
```

Results are saved under `output`; `summary.json` contains the final metrics. To resume, rerun the same command with unchanged settings. Use a new output directory after changing settings or code.

## Sources

The benchmark data and bundled evaluation harnesses come from [SWT-Bench](https://github.com/logic-star-ai/swt-bench) (Lite) and [TDD-Bench Verified](https://github.com/IBM/TDD-Bench-Verified). Tait reuses [iCoRe](https://github.com/ZJU-CTAG/iCoRe) retrieval results as its default context and adapts its environment and test execution helpers.
