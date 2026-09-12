# Custom Tools MCP Server

A modular Model Context Protocol server for custom FPGA optimization tools.
Tools are **auto-discovered** from the `tools/` directory at startup, so
adding a new tool is as simple as dropping a file in `tools/` -- no edits to
`server.py` required.

## Layout

```
CustomToolMCP/
├── server.py                          # MCP server; auto-discovers tools/*.py
├── tools/
│   ├── __init__.py                    # empty (package marker)
│   ├── _template.py                   # annotated reference -- excluded from discovery
│   └── compute_simple_score.py        # trivial test tool
├── example_io/
│   └── compute_simple_score/
│       ├── case_1_input.json          # paired input/output JSON used by test_server.py
│       ├── case_1_output.json
│       ├── case_2_input.json
│       ├── case_2_output.json
│       ├── case_3_input.json
│       └── case_3_output.json
├── requirements.txt
├── test_server.py                     # data-driven runner over example_io/
└── README.md
```

## Tool-file contract

Every file in `tools/` (other than `__init__.py` and files starting with `_`)
must expose four module-level attributes:

| Attribute        | Type                              | Purpose                                                                 |
| ---------------- | --------------------------------- | ----------------------------------------------------------------------- |
| `NAME`           | `str`                             | Unique tool name. The LLM sees it as `custom_<NAME>`.                   |
| `DESCRIPTION`    | `str`                             | One-sentence description shown to the LLM.                              |
| `INPUT_SCHEMA`   | `dict`                            | JSON Schema for the `arguments` dict.                                   |
| `run(arguments)` | `Callable[[dict], dict]`          | Implementation. Receives parsed args, returns a JSON-serializable dict. |

Convention: `run()` should return `{"status": "success", ...}` on success and
`{"status": "error", "error": "<message>"}` on caught failures. Uncaught
exceptions are wrapped by `server.py` into a JSON error response automatically.

Files whose stem starts with `_` (e.g. `_template.py`) are skipped by
discovery, so the template ships as a real reference without being registered.

## Adding a new tool

1. `cp tools/_template.py tools/<your_tool>.py`
2. Edit `NAME`, `DESCRIPTION`, `INPUT_SCHEMA`, and `run()`.
3. (Recommended) ship example I/O cases for testing -- see next section.
4. Restart the server (or restart `dcp_optimizer.py`).
5. The tool surfaces to the LLM as `custom_<NAME>`.

Duplicate `NAME` across files raises an error at server startup -- fail-fast
to avoid silent shadowing.

## Example I/O for testing

Each tool may ship paired input/output cases under `example_io/<NAME>/`:

```
example_io/<NAME>/
├── case_1_input.json    # the `arguments` dict passed to run()
├── case_1_output.json   # the expected return dict (deep equality)
├── case_2_input.json
└── case_2_output.json
```

Cases are numbered starting from `case_1`; add as many as you like. The
runner `test_server.py` auto-discovers each pair, calls `run(input)`, and
compares the result to the expected output via deep equality.

Conventions:

- File names are exactly `case_<N>_input.json` and `case_<N>_output.json`.
  Anything else is ignored (or flagged as orphan if an output has no input).
- A tool with no `example_io/<NAME>/` directory is reported as **skipped**,
  not failed. Shipping cases is recommended but optional.
- Use cases to exercise: required-only inputs, optional-arg defaults, edge
  values (zero, negative, empty strings), and any documented error paths.

## Install

```bash
pip install -r requirements.txt
```

No `setup.sh` is needed -- this server is pure Python.

## Test

In-process, data-driven over `example_io/` (no MCP protocol involved):

```bash
python3 test_server.py
```

The runner discovers tools the same way `server.py` does, then for each
tool walks `example_io/<NAME>/` and validates every paired
`case_<N>_input.json` / `case_<N>_output.json`. Exit code is 0 on full
pass, 1 if any case fails or if orphan output files are detected.

Standalone server smoke test (waits on stdio; Ctrl-C to exit):

```bash
python3 server.py --mcp-log /tmp/custom-mcp.log
```

## Integration with `dcp_optimizer.py`

`dcp_optimizer.py` spawns this server via stdio alongside `RapidWrightMCP`
and `VivadoMCP`. Tools surface to the LLM with the `custom_` prefix; calls
are routed back to this server by the prefix dispatcher in `call_tool()`.
