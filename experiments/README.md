# Run the evaluated methods

- Run from the package root after [preparing inputs](../README.md#1-collect-and-prepare-data).
- Use a fresh output directory per run; no automatic retries.
- Keep metadata, oracle labels, hash maps and saved answers outside agent-visible inputs.

## Setup

```sh
python3 -B experiments/prepare_baselines.py --extract
```

- Four [ZIPs](implementations/manifest.json) extract to `dataset/baselines/`; versions, licenses and adapter checksums are included. Existing files are verified, not overwritten.
- **LLM4SZZ:** Claude API adapter and macOS arm64 grammar; original prompts and selection logic.
- **AgentSZZ:** Claude API adapter, cost limits and usage logging; original prompts, tools and search logic.
- **SZZ-Agent / Simple-SZZ-Agent:** one shared ZIP; oracle-based stopping removed, search spaces and stages retained.
- **PySZZ v2:** original algorithms; RA-SZZ uses a dummy origin URL in a temporary local copy without fetching.
- No separate source download or patching is needed.

Study environment:

- Apple Silicon macOS; Python 3.11.11 (LLM/agent baselines), Python 3.11.14 (PySZZ).
- Git 2.48.1, srcML 1.1.0, Java 23.0.2 on `PATH`. LLM4SZZ requires macOS arm64; no Linux port.
- Sonnet 5; Claude Code 2.1.232 with `high` effort for CLI methods. API methods use no explicit effort setting.

Install separate Python 3.11 environments:

```sh
python3.11 -m venv .cache/llm
.cache/llm/bin/pip install -r experiments/config/llm-baselines/requirements-python311.txt
.cache/llm/bin/python -c 'import tiktoken; tiktoken.get_encoding("cl100k_base"); tiktoken.get_encoding("o200k_base")'
python3.11 -m venv .cache/rules
.cache/rules/bin/pip install wheel==0.45.1 -r experiments/config/pyszz/requirements-pyszz-v2-python311.txt
```

- The tokenizer command downloads encoding files, not model responses.

## Run rule-based methods

- All six methods, case 10, no model calls:

```sh
.cache/rules/bin/python -B experiments/rules.py --id 10 --execute --output outputs/rules-10
```

## Live execution (optional)

- These commands consume subscription/API resources; use your own account.
- CLI runs use the host sandbox. Disable subscription extra usage before confirming the flag.
- Claude Code's results directory must be outside this package and all subject repositories.

```sh
python3 -B experiments/claude_code.py all --ids 10 --replicates 3 \
  --execute --model claude-sonnet-5 --max-budget-usd 5 \
  --results-root /absolute/path/to/new-private-results \
  --acknowledge-resource-use I_ACKNOWLEDGE_CLAUDE_RESOURCE_USE \
  --confirm-usage-credits-disabled I_CONFIRMED_USAGE_CREDITS_DISABLED
```

- Omit `--ids 10` for all 79 cases; add `--message-free` to use prepared message-free inputs.
- Limits: 600 seconds per invocation; 3,600 seconds across SZZ-Agent's stages; USD 5 stopping threshold, not a billing cap.
- For LLM4SZZ/AgentSZZ, supply `ANTHROPIC_API_KEY` through the environment, not a file or command argument:

```sh
.cache/llm/bin/python -B experiments/baselines.py --method agentszz --id 10 \
  --execute --output outputs/agentszz-10-r01 \
  --acknowledge-resource-use --acknowledge-api-billing
```

- SZZ-Agent/Simple-SZZ-Agent: change `--method` and replace `--acknowledge-api-billing` with `--confirm-usage-credits-disabled` (subscription only).
- Repeat LLM/agent baselines three times per case (`r01`, `r02`, `r03`); PySZZ once. Use IDs from `dataset/metadata/cases.json`, one case per process, stopping on errors.
- RA-SZZ's recorded extended timeout: `--ra-timeout-seconds 3600`; no automatic retry.
- Historical HTTP-body capture and retry scheduling are not reproduced. Use saved logs for the paper's exact results.
