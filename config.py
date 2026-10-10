"""Editable Tait experiment settings. Run with: python run.py."""

CONFIG = {
    # Model and credentials (keep actual keys outside this file).
    'dataset': 'swt',
    'model': 'gpt-5.4-mini',
    'provider': 'gpt',
    'base_url': 'https://api.openai.com/v1',
    'api_key_env': 'OPENAI_API_KEY',
    'api_pool': None,

    # Paths are relative to this submission directory unless absolute.
    'repo_root': 'repositories',
    'official_python': 'environments/swt/bin/python',
    'output': 'runs/swt',
    'docker_host': 'unix:///var/run/docker.sock',

    # Paper settings: five branches, five total rounds, three repetitions.
    'top_code': 6,
    'top_tests': 5,
    'rounds': 5,
    'repetitions': 3,
    'temperature': 0.1,
    'target_temperature': 0.0,
    'validation_temperature': 0.0,

    # Execution and optional subset. None means the complete dataset.
    'workers': 4,
    'max_tokens': 4096,
    'execution_timeout': 7200,
    'limit': None,
    'instance_ids': [],
    'compute_coverage': True,
    'evaluate': True,
    'resume': True,

    # Advanced API and Docker settings.
    'runtime_environment': {
        'BRT_LLM_REQUEST_TIMEOUT': '1200',
        'BRT_LLM_MAX_ATTEMPTS': '6',
        'BRT_LLM_BACKOFF_BASE': '15',
        'BRT_LLM_RATE_LIMIT_BACKOFF': '30',
        'BRT_LLM_POOL_ROTATION_ATTEMPTS': '10',
        'BRT_LLM_STREAM': '1',
        'BRT_DISABLE_THINKING': '1',
        'BRT_REASONING_EFFORT': 'none',
        'BRT_THINKING_PARAMETER': 'reasoning_effort',
        'BRT_DOCKER_MIN_FREE_GB': '120',
        'BRT_REJECT_DOCKER_VFS': '1',
        'BRT_GENERATION_MAX_TOKENS': '8192',
        'BRT_GENERATION_REASONING_EFFORT': 'low',
        'BRT_PLANNING_REASONING_EFFORT': 'low',
    },
}
