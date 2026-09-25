# omlx-bench

A small, hermetic coding benchmark for local models on Apple Silicon. It runs
[opencode](https://opencode.ai) against three pinned Qwen models served by
[oMLX](https://github.com/jundot/omlx), over 15 tasks, and prints one table
you can compare with the same table from someone else's Mac.

Each task is a self-contained workspace with a seeded bug or a missing
implementation. The agent gets a plain-English prompt and the workspace. It is
graded afterwards, in a clean process, against a hidden `unittest` suite it
never saw. Stdlib only: no pytest, no Docker. Nothing talks to the network
during a run except opencode talking to your own oMLX server.

What it measures is the whole setup, opencode's agent loop plus the model, not
raw token throughput. `OUT TOK/S` is the number to compare across machines.

Seed result from an M5 Max with 128 GB:

```

[1] Apple M5 Max 128 GB
machine                 [1]         [1]         [1]         
task                    3-Coder-30  3.8-27B-8b  3.8-Flash-  solved
------------------------------------------------------------------
t01-duration-parse      P 10/10     P 10/10     P 10/10     3/3
t02-lru-cache           P 8/8       P 8/8       P 8/8       3/3
t03-csv-quoting         F 9/11      P 11/11     P 11/11     2/3
t04-extract-validation  P 10/10     P 10/10     P 10/10     3/3
t05-perf-dedup          P 9/9       P 9/9       P 9/9       3/3
t06-pagination          P 9/9       P 9/9       P 9/9       3/3
t07-retry-backoff       P 9/9       P 9/9       P 9/9       3/3
t08-cli-feature         F 8/13      P 13/13     P 13/13     2/3
t09-write-tests         P 9/9       P 9/9       P 9/9       3/3
t10-state-machine       P 17/17     P 17/17     P 17/17     3/3
t11-lock-deadlock       P 14/14     P 14/14     P 14/14     3/3
t12-minimal-diff        F 11/12     T 1/12      P 12/12     1/3
t13-di-migration        F 4/11      T 5/11      P 11/11     1/3
t14-aliasing-bug        F 10/15     P 15/15     P 15/15     2/3
t15-match-convention    P 14/14     P 14/14     P 14/14     3/3
------------------------------------------------------------------
PASSED                  10/15       13/15       15/15       
TEST CASES              151/171     154/171     171/171     
WALL CLOCK              21m09s      121m06s     49m34s      
OUT TOKENS              57928       79249       78276       
OUT TOK/S               45.6        10.9        26.3        

P=pass  F=fail  T=timeout  B=broken (suite could not run)
OUT TOK/S = output tokens / agent wall clock, summed over the run.
```

## Requirements

- Apple Silicon Mac, macOS 14 or later, `python3` (3.9 or later, the Xcode
  command line tools version is fine), `curl`
- [oMLX](https://github.com/jundot/omlx) 0.6 or later
- [opencode](https://opencode.ai) 1.17 or later
- Enough unified memory for the models you want to run (see below)

## The models

| model id (directory name under `~/.omlx/models`) | source | disk | minimum Mac |
|---|---|---|---|
| `Qwen3-Coder-30B-A3B-Instruct-MLX-8bit` | `lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-MLX-8bit` | 30 GB | 48 GB |
| `Qwen3.8-27B-MLX-8bit` | `mlx-community/Qwen3.8-27B-8bit` | 28 GB | 48 GB |
| `Qwen3.8-Flash-Next-oQ4e-mtp` | `Jundot/Qwen3.8-Flash-Next-oQ4e-mtp` | 99 GB | 128 GB |

The directory name is the model id oMLX serves and the id this benchmark
pins, so download each model into a directory of exactly that name.
`sweep.sh` runs whichever of the three your server reports and skips the
rest, so a 64 GB machine still produces a valid two-model result.

## Setup

```bash
# oMLX: download the .dmg from https://github.com/jundot/omlx/releases and
# drag it to Applications, or use Homebrew:
brew tap jundot/omlx https://github.com/jundot/omlx && brew install jundot/omlx/omlx

# opencode
curl -fsSL https://opencode.ai/install | bash

# the hf downloader (any of these works)
brew install huggingface-cli        # or: uv tool install huggingface_hub
                                    # or: pipx install huggingface_hub

mkdir -p ~/.omlx/models && cd ~/.omlx/models
hf download lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-MLX-8bit --local-dir Qwen3-Coder-30B-A3B-Instruct-MLX-8bit
hf download mlx-community/Qwen3.8-27B-8bit                            --local-dir Qwen3.8-27B-MLX-8bit
hf download Jundot/Qwen3.8-Flash-Next-oQ4e-mtp                        --local-dir Qwen3.8-Flash-Next-oQ4e-mtp   # 128 GB Macs only

omlx start                          # oMLX's default port is 8000
```

Then, from a clone of this repo:

```bash
./lib/models.sh          # should list the model ids you downloaded
./selftest.sh baseline   # optional: proves the task suite is intact
```

The benchmark uses its own `opencode.json` and its own config directory
(`.opencode/`, git-ignored), so your global opencode settings and plugins are
neither read nor changed. opencode populates that directory on first use,
which needs the network once and takes a few seconds.

The scripts look for oMLX on `http://127.0.0.1:8000` (its default) and then
`http://127.0.0.1:8100`. If you changed the port or run oMLX on another
machine, set `OMLX_URL=http://host:port`. Prefer an IP over `localhost`:
oMLX listens on IPv4 only, and a client that tries IPv6 first can fail to
connect intermittently.

## Run

```bash
./sweep.sh                         # every pinned model your server has
./sweep.sh Qwen3.8-27B-MLX-8bit    # one model
./sweep.sh -o results/<dir>        # resume an interrupted sweep
./run.sh Qwen3.8-27B-MLX-8bit t02-lru-cache t05-perf-dedup   # a few tasks
```

Each model is loaded and given one untimed warm-up request before its first
task, so model load time is not in the wall clock. Expect 20 minutes to two
hours per model depending on the machine; the seed run above took 21, 50 and
121 minutes. A task that exceeds `BENCH_TIMEOUT` (default 900 s) is marked
`T` and counted as failed.

Results land in `results/<chip>-<memory>-<timestamp>/`:

```
results/m5-max-128gb-20260919/
├── machine.txt        chip, memory, macOS, oMLX and opencode versions, a note
├── summary.txt        the combined table
└── <model-id>/
    ├── results.tsv    one row per task
    ├── <task>.agent.log     opencode's transcript   (git-ignored)
    ├── <task>.test.log      grader output           (git-ignored)
    └── <task>/              final workspace state   (git-ignored)
```

Knobs: `BENCH_TIMEOUT` (per-task agent budget, default 900 s),
`BENCH_TEST_TIMEOUT` (grading, default 120 s), `BENCH_NOTE` (free text
saved to `machine.txt`, for anything unusual about the run).

## Compare and contribute

```bash
./score.sh results/*/*/                                    # everything you have
./score.sh results/m5-max-128gb-20260919/*/ results/<yours>/*/
```

The table prints a legend of the machines involved, then per-task results,
then totals including `OUT TOK/S` (output tokens divided by agent wall
clock, summed over the run).

To share your numbers, run `./sweep.sh`, commit the new `results/<dir>/`
(only `machine.txt`, `summary.txt` and `results.tsv` files are tracked;
transcripts and workspaces stay on your machine) and open a pull request.
Please leave `BENCH_TIMEOUT` at its default so timeouts are comparable, and
say in `BENCH_NOTE` if anything else was running on the machine.

## The tasks

| Task | Shape | What it discriminates on |
|---|---|---|
| `t01-duration-parse` | fix a parser | edge cases, input validation |
| `t02-lru-cache` | implement from spec | data structure choice, O(1) requirement |
| `t03-csv-quoting` | fix a parser | state machine reasoning, escaping rules |
| `t04-extract-validation` | multi-file refactor | cross-file edits, resolving drift |
| `t05-perf-dedup` | optimize | recognizing quadratic behaviour |
| `t06-pagination` | fix 3 reported bugs | off-by-one, boundary conditions |
| `t07-retry-backoff` | implement from spec | precise spec adherence, DI for testing |
| `t08-cli-feature` | add a feature | argparse subtleties, not breaking existing output |
| `t09-write-tests` | write a test suite | mutation-graded: catches 7 seeded regressions |
| `t10-state-machine` | implement from spec | transition table completeness, terminal states |
| `t11-lock-deadlock` | fix 3 incidents | lock reentrancy, not holding a lock across a callback |
| `t12-minimal-diff` | implement from spec | LCS/DP; greedy and exponential approaches both fail |
| `t13-di-migration` | migrate 5 modules | removing a global, real instance isolation |
| `t14-aliasing-bug` | debug from a report | shared mutable state; cause is far from the symptom |
| `t15-match-convention` | add a feature | judgement: infer an unstated convention from the codebase |

The first ten are ordinary working-programmer tasks. `t11`-`t15` were added
because frontier models cleared the first ten at *medium* effort — they exist
to discriminate at the top of the range.

Three are worth calling out:

- **`t09`** has no answer key. The agent writes `test_shipping.py`; the grader
  seeds seven distinct bugs into `shipping.py` and counts how many its tests
  catch. Good test design scores; happy-path assertions do not.
- **`t15`** never states the convention. `api/users.py` implements keyset
  cursor pagination with particular parameter names, limits and error codes;
  the prompt only says "consistent with the rest of the API". An agent that
  invents offset paging fails, and the stability test is what catches it.
- **`t11`** is graded on deterministic deadlocks, not on catching a data race.
  Forcing a GIL race to reproduce on demand proved unreliable (the buggy code
  passed 4 runs in 5), so the task was rebuilt around lock reentrancy and
  holding a lock across a callback, both of which fail identically every run.
## Reading the results honestly

- **One run is one sample.** Models are non-deterministic and so is the agent
  loop. Re-run a task a few times before believing a single PASS/FAIL,
  especially a near miss.
- **Wall clock includes opencode.** Reading files, running the smoke test and
  re-planning all count. That is deliberate: it is the setup that is timed.
- **Give oMLX the machine.** Anything else hitting the server, or loading
  another model, can stall requests for minutes while oMLX evicts and
  reloads; one such stall showed a one-token reply taking 400 s. Run a
  sweep with nothing else using the server.
- **`OUT TOK/S` is the cleanest speed comparison** across machines, because
  it divides out how much the model chose to write.
- **`T`** means the per-task cap was hit; **`B`** means the grading suite did
  not run at all, usually because the agent deleted or renamed a module.
  Both are worth a look at the transcript.

## Troubleshooting

- `no oMLX server at ...`: run `omlx start`, or set `OMLX_URL` if the server
  is not on 127.0.0.1 port 8000 or 8100 (check the port in the oMLX app's
  settings, or `~/.omlx/settings.json`).
- `model '...' is not on ...`: the directory name under `~/.omlx/models`
  must match the id exactly; `./lib/models.sh` shows what the server sees.
- `opencode could not complete a trivial request`: the runner stops before
  the first task because opencode failed twice on a one-line prompt. Run
  `OPENCODE_CONFIG=$PWD/opencode.json OPENCODE_CONFIG_DIR=$PWD/.opencode opencode run -m omlx/<model-id> "say hi"`
  by hand to see the error.
- `opencode produced no output in ...s, retrying once`: opencode never
  started the session. The runner feeds opencode `/dev/null` as stdin
  because `opencode run` reads a non-terminal stdin to the end and hangs
  on an open pipe (cron, nohup, CI); if it still hangs, the task is retried
  once from a clean workspace with the clock restarted, and a second hang
  is recorded as `T`.

## Validating the suite

```bash
./selftest.sh baseline    # every task must FAIL untouched (no free points)
./selftest.sh solutions   # reference solutions must PASS (oracles are fair)
```

Both are green as of writing: 0/171 test cases pass at baseline, 171/171 with
`solutions/` applied. Run these after editing any task.

A task is only useful if it fails reliably before the fix and passes reliably
after. For anything timing- or concurrency-sensitive, run `baseline` several
times and confirm the failure count does not move.

`solutions/` is the validation fixture. Agents never see it — `run.sh` copies
only `tasks/<id>/workspace/`.
## Adding a task

```
tasks/<id>/
├── PROMPT.md              # what the agent is told (goal, not solution)
├── workspace/             # starting files; may include a visible smoke test
└── tests/_verify_*.py     # hidden oracle, copied in only at grading time
```

Then add `solutions/<id>/` with the overlay that makes it pass, and confirm
both selftest modes stay green.
