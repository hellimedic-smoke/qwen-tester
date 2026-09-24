# omlx-bench design

Date: 2026-09-24

## Purpose

A standalone, public repository that lets any Apple Silicon Mac owner run the
same 15-task coding benchmark against the same three Qwen models served by
oMLX, and compare speed and accuracy with other machines.

It is extracted from a private harness that also drove Claude Code. Claude
support is dropped. The benchmark measures the whole setup: opencode's agent
loop plus the local model, not raw inference.

Success: someone with a different Mac clones the repo, follows the README,
and produces a results directory that `score.sh` can print side by side with
the seed results, with a tokens-per-second figure that is directly comparable.

## Non-goals

- Supporting other model servers (LM Studio, Ollama, mlx_lm). oMLX only.
- Supporting Claude Code or any hosted API.
- Aggregating results into a leaderboard. Comparison is `score.sh` over
  directories; sharing is by pull request.

## Repository layout

```
omlx-bench/
├── README.md
├── .gitignore
├── opencode.json          # shipped opencode config: omlx provider, 3 models
├── run.sh                 # run one model over the task suite
├── sweep.sh               # run every pinned model, print one summary
├── score.sh               # side-by-side table over result dirs
├── selftest.sh            # validate the task suite itself
├── lib/
│   ├── metrics.py         # parse opencode transcript -> tokens, turns
│   └── machine.sh         # capture hardware + software versions
├── tasks/<id>/            # 15 tasks: PROMPT.md, workspace/, tests/
├── solutions/<id>/        # reference overlays, validation only
└── results/
    └── <machine>-<date>/
        ├── machine.txt
        ├── summary.txt
        └── <model>/results.tsv
```

`tasks/`, `solutions/`, `lib/metrics.py`, `score.sh` and `selftest.sh` are
copied from the source harness. `run.sh` and `sweep.sh` are rewritten
without the Claude branch. `opencode.json`, `lib/machine.sh`, `.gitignore`
and `README.md` are new.

## Pinned models

| model id in oMLX                        | Hugging Face source                                     | disk  | minimum Mac |
|-----------------------------------------|---------------------------------------------------------|-------|-------------|
| Qwen3-Coder-30B-A3B-Instruct-MLX-8bit   | lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-MLX-8bit | 30 GB | 48 GB       |
| Qwen3.8-27B-MLX-8bit                    | mlx-community/Qwen3.8-27B-8bit                          | 28 GB | 48 GB       |
| Qwen3.8-Flash-Next-oQ4e-mtp             | Jundot/Qwen3.8-Flash-Next-oQ4e-mtp                      | 99 GB | 128 GB      |

The model id is the directory name under `~/.omlx/models/`. The README
tells people to download each source repo into a directory of exactly that
name so results line up across machines.

`sweep.sh` queries `GET /v1/models` on the server and runs only the pinned
models that are present. Absent models are reported as `SKIPPED` in the
sweep output and produce no result directory, so a 64 GB machine yields a
valid two-model result.

## opencode configuration

`opencode.json` at the repo root defines a single provider `omlx` using
`@ai-sdk/openai-compatible`, base URL `http://localhost:8100/v1`, no API
key, and the three pinned models with context 200000 / output 32000. Every
opencode invocation from `run.sh` sets `OPENCODE_CONFIG` to this file so
the user's global config is never read or modified.

`OMLX_URL` (default `http://localhost:8100`) overrides the server address
for people running oMLX on another host. When set, `run.sh` writes a
temporary copy of `opencode.json` with the substituted base URL and points
`OPENCODE_CONFIG` at that copy.

## run.sh

```
./run.sh <model-id> [task ...]
```

1. Preflight: `python3`, `opencode` on PATH; `curl $OMLX_URL/v1/models`
   succeeds and lists `<model-id>`. Any failure prints one line saying
   what is missing and exits 2.
2. Warm-up: one small chat completion to `<model-id>` via curl, untimed,
   so model load is excluded from the first task's wall clock.
3. For each task, exactly as the source harness: copy `workspace/`, run
   `opencode run --auto --dir <ws> --format json -m omlx/<model-id>
   "<prompt>"` under `timeout`, then grade in a clean process against
   `tests/_verify_*.py`, then parse the transcript with `lib/metrics.py`.
4. Append a row to `results.tsv`: `task status passed failed agent_secs
   exit out_tokens turns`. The `cost_usd` column from the source harness is
   dropped.

Environment knobs kept: `BENCH_TIMEOUT` (default 900), `BENCH_TEST_TIMEOUT`
(default 120), `BENCH_RUN_DIR`.

Output directory when `BENCH_RUN_DIR` is unset:
`results/<machine-slug>-<YYYYMMDD-HHMMSS>/<model-id>/`, where machine-slug
is derived by `lib/machine.sh` (for example `m5-max-128gb`).

## sweep.sh

```
./sweep.sh                     # all pinned models present on the server
./sweep.sh -o results/<dir>    # resume
./sweep.sh <model-id> ...      # explicit list
```

Creates `results/<machine-slug>-<date>/`, writes `machine.txt` there via
`lib/machine.sh`, runs `run.sh` per model with `BENCH_RUN_DIR` set to the
model subdirectory, skips models already complete or absent from the
server, then runs `score.sh` over the model directories and saves
`summary.txt`.

## lib/machine.sh

Prints key=value lines:

```
chip=Apple M5 Max
memory_gb=128
macos=27.0
omlx=0.6.4
opencode=1.17.14
date=2026-09-24
note=
```

Sources: `sysctl -n machdep.cpu.brand_string`, `sysctl -n hw.memsize`,
`sw_vers -productVersion`, `omlx --version`, `opencode --version`. The
`note` field is free text; `BENCH_NOTE` fills it. The slug is
`<chip lowercased, "apple " stripped, spaces to dashes>-<memory_gb>gb`.

## score.sh

Copied from the source harness with these changes:

- Column label is the model id with `Qwen`, `-MLX`, `-Instruct`, `-oQ4e-mtp`
  stripped, as today.
- `LIST COST` row removed.
- New `OUT TOK/S` row: total output tokens divided by total agent seconds
  across the run, one decimal.
- When a run directory's parent contains `machine.txt`, the header line
  above the table prints each parent's `chip` and `memory_gb` once, so a
  table mixing two machines says which is which.

## selftest.sh

Copied unchanged. Both modes must be green before the first commit of the
tasks.

## .gitignore

```
results/**/*.agent.log
results/**/*.test.log
results/**/t[0-9][0-9]-*/
__pycache__/
```

Transcripts and workspace copies stay local. A contribution is
`machine.txt`, `summary.txt`, and one `results.tsv` per model.

## Seed results

The three existing Qwen runs from the source harness are copied to
`results/m5-max-128gb-20260919/<model-id>/results.tsv` with the
`cost_usd` column removed. `machine.txt` is written by hand for that run
with `note=opencode ran inside a Linux VM on this Mac and reached oMLX
over the VM NAT; timings include that overhead`. No transcripts are
copied, so the Linux username never enters the repo.

## README

Written for someone who has never seen the source harness. Sections:

1. What it is, one paragraph, and a sample of the summary table.
2. Requirements: Apple Silicon, macOS, python3, oMLX 0.6+, opencode.
3. Setup: install oMLX and opencode, download the three models into
   `~/.omlx/models/<model-id>`, start the server on port 8100.
4. Run: `./sweep.sh`, what it prints, where results land, how long to expect
   (from the seed run: roughly 20 minutes to 2 hours per model).
5. Compare: `./score.sh results/*/*/`, and how to contribute results by
   pull request.
6. The tasks table, from the source README.
7. Reading results honestly: one run is one sample, wall clock includes
   opencode's loop, `OUT TOK/S` is the cleanest speed comparison, `T` means
   the 900 s cap was hit.
8. Validating and adding tasks, from the source README.

## Testing

- `./selftest.sh baseline` and `./selftest.sh solutions` both green.
- `./run.sh Qwen3-Coder-30B-A3B-Instruct-MLX-8bit t01-duration-parse`
  against the local oMLX server from a fresh clone in a temp directory,
  producing a PASS row and a machine slug of `m5-max-128gb`.
- `./score.sh` over the seed directory and the fresh run prints both with
  the `OUT TOK/S` row and the machine header.
- A secrets grep over the final tree finds no keys, no `/home/`, no
  `/Users/` paths.
