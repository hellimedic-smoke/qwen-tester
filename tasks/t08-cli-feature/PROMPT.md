`todo.py` is a small command-line todo tool backed by a JSON file. It currently
supports `add`, `list` and `done`.

Add two things without breaking existing behaviour:

1. A global `--json` flag that makes every subcommand print machine-readable
   JSON to stdout instead of human text:
   - `add` prints the created task object
   - `list` prints a JSON array of task objects
   - `done` prints the updated task object
   Task objects have the keys `id`, `text`, and `done`.

2. A new `stats` subcommand printing a one-line summary in the human format
   `3 tasks, 1 done, 2 open` and, under `--json`, an object with the keys
   `total`, `done`, and `open`.

The `--json` flag must work before or after the subcommand name. Existing
human-readable output for `add`, `list` and `done` must stay exactly as it is.
The data file path comes from `--file` and defaults to `todo.json`.
