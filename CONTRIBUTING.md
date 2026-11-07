# Contributing

Thanks for helping. trustgate stays small on purpose: standard library only, no network,
and it never executes anything it scans.

## Setup

```sh
git clone https://github.com/kirtanbhatt10/trustgate
cd trustgate
python -m unittest discover -s tests -t tests -v
python -m trustgate scan .
```

No virtualenv or dependencies are needed. Python 3.9 is the oldest supported version, so
avoid newer syntax such as `match` statements and `X | Y` type unions.

## Adding a rule

1. Register it in `trustgate/models.py` with an id, name, default severity, summary and fix.
   Ids are grouped by area: `TG0xx` generic, `TG1xx` VS Code, `TG2xx` AI agents,
   `TG3xx` npm, `TG4xx` Python, `TG5xx` dev containers, `TG6xx` git hooks and shell,
   `TG7xx` CI workflows.
2. Implement the detection in the matching module under `trustgate/checks/`.
   If the rule needs a new file name, add it to `AUTORUN_NAMES` in `trustgate/scanner.py`.
3. Add tests in `tests/test_checks.py` for one positive case and one look-alike that must
   not be flagged.
4. Update `docs/rules.md` and the coverage table in `README.md`.

## Guidelines

- Report what is configured to run, with the exact command, file and line.
- Prefer precise matching on documented config keys over broad text searches.
- Every new finding should come with a concrete fix in its rule's remediation text.
- Keep messages short and specific; they are read in terminals and code-scanning UIs.
