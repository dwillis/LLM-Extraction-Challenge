# fundraising-emails smevals eval

This directory wires the `fundraising-emails` committee/sender extraction
task into [smevals](https://github.com/prime-radiant-inc/smevals), a
YAML + executable-script eval framework. It runs **alongside** the
existing pipeline (`../email_llm.py`, `../matcher.py`, the leaderboard,
and CI) rather than replacing it — nothing outside this directory is
touched.

Each of the 1,000 emails in `../training.csv` becomes its own smevals
task, so a model's mean score under the default grader is directly
comparable to the `Accuracy` column in `../summary_all_json.csv`.

## Install

```bash
# smevals itself
uv tool install smevals   # or: pip install smevals

# this eval's own dependencies (the `llm` library + pyyaml)
pip install -r requirements.txt

# API keys for whichever provider(s) you want to evaluate
llm keys set openai
llm keys set anthropic
llm keys set gemini
```

## Generate tasks

Task YAMLs are generated from `../training.csv` and are **not** committed
to the repo (see `.gitignore`) — they duplicate the full email bodies and
are fully reproducible from the CSV, so regenerate them locally:

```bash
python3 generate_tasks.py            # all 1,000 tasks
python3 generate_tasks.py --limit 5  # just the first 5, for a smoke test
```

## Run

```bash
# smoke test against a couple of tasks
smevals run . -m gpt-4.1-nano -t email-0000 -t email-0001 -g

# full run against one or more models
smevals run . -m gpt-4.1-nano -m claude-haiku-4.5 -g

# multiple runs per task/model pair
smevals run . -m gpt-4.1-nano -n 3 -g
```

A full run is **1,000 sequential model calls per model** — expect
multi-minute (fast hosted models) to multi-hour (slow local models) wall
time, and budget API cost accordingly. smevals does not currently expose
a concurrency flag.

## Grade / report

The default grader (`graders/default.yaml`) scores only the `committee`
field, using the same normalization as `../matcher.py`
(`None`/empty → `"none"`, lowercase, stripped) — its exact-match
semantics, not fuzzy matching. This makes the mean score directly
comparable to `matcher.py`'s `Accuracy` column, **for `*_prompt2.json`
runs only** (the prompt here is the "prompt2" text from `../email_llm.py`).

```bash
smevals grade .                  # (or pass -g at `run` time, as above)
smevals report . --by-task
```

Sender extraction is not scored by the repo's leaderboard, but a second,
informational grader is provided:

```bash
smevals grade . -g sender
smevals report . -g sender
```

## Serve

```bash
smevals serve .
```

## Notes / caveats

- The prompt (`generate_tasks.py`) and JSON schema (`run-llm`) are
  verbatim copies of `../email_llm.py`. If you change the prompt or
  schema in one place, update the other — otherwise scores here stop
  being comparable to the leaderboard.
- `matcher.py` also merges JSON output with the CSV on several metadata
  columns and can drop rows in that merge; its `Total Records` can vary
  by file. This eval scores every generated task directly, with no such
  merge step. It also does not reproduce `matcher.py`'s macro
  precision/recall/F1 (which treats each committee name as its own
  class) — only accuracy is comparable.
- Model output that isn't valid JSON is treated as a model-quality
  failure (checker score `0`), not a runner crash.
