# Notes on the code

The code in this repository is published exactly as it was scored in the final
round; nothing was cleaned up afterwards. The following points are worth knowing
before reading or running it. None of them affects the optimization result.

## 1. The end-of-run summary prints `LLM API calls: 0`

This is a reporting bug in our code. The counter `llm_call_count` is incremented only
inside the template's `get_completion()` method, which serves the template's LLM
conversation loop. Our optimizer does not run that loop; its single LLM call (in
`optimize()`, logged as `[exp27-G1] LLM choice: ...`) calls the OpenAI client directly
and bypasses the counter. The call does happen: the organizers' official scorecards
show an OpenRouter cost of about $0.004 per benchmark, and the harness logs contain
the OpenRouter request. Only the printed summary and the `total_llm_calls` field of
the results JSON are wrong.

## 2. `SUBMISSION_TAG` says `fpl26-alpha-snu-jellyhead` / `alpha-v0.1`

A stale label, not a functional bug. The two constants at the top of
`dcp_optimizer.py` are printed once at startup so that a run can be traced back to a
submission. They were set during the alpha round and never updated, so the final
build still identifies itself as "alpha". Nothing reads them.

## 3. `SYSTEM_PROMPT.TXT` is never read

In the template, `load_system_prompt()` reads this file and feeds it to the LLM
conversation loop as the system message. Our optimizer replaced that loop with a
rule-based framework and makes one LLM call whose prompt is built in
`CustomToolMCP/tools/_fpl_llm_arm.py`. The function `load_system_prompt()` is still
defined but has no callers, so the file is never opened. We kept the file because the
contest package expects it to exist; its contents are a short description of the
framework rather than a prompt.

## 4. `CustomToolMCP/README.md` describes tools that are not there

That README documents the MCP server scaffold: tools are auto-discovered from
`tools/*.py`, each tool module must define `NAME`, `DESCRIPTION`, `INPUT_SCHEMA` and
`run()`, files whose names start with `_` are skipped, and it lists two example files,
`tools/_template.py` and `tools/compute_simple_score.py`, with test cases under
`example_io/`. Those two example files were removed before the final build. The
`tools/` directory now holds only `_fpl_knowledge.py`, `_fpl_llm_arm.py` and
`_fpl_rules.py`, and because their names start with `_` the server registers zero
tools; `dcp_optimizer.py` imports them directly as Python modules. The server is still
started by the optimizer, but the LLM never sees any custom tool. The `example_io/`
cases for `compute_simple_score` are leftovers with no matching tool.

## 5. Unused tables in `_fpl_knowledge.py`

The module still contains `FINGERPRINTS` (resource counts and timing of 16 public
benchmark designs) and `ANSWER_SHEET`, together with a docstring describing a scheme
that matched an input design against those fingerprints. That scheme was removed
before the final build. Nothing calls `match_fingerprint()` or reads `ANSWER_SHEET`
at runtime; the only data the optimizer uses from this module is `G1_CATALOG`, the
measured α of the six candidate actions on 13 public designs, which the rule engine
and the LLM prompt use as evidence.

## 6. Korean comments and internal experiment numbers

Most comments in `dcp_optimizer.py` (about 330 lines) and in the `_fpl_*` modules,
and some runtime log lines, are in Korean. Many comments also cite our internal
experiment folders (`exp5` … `exp31`) and dates (`8/9`, `8/10`) to record when and
why a decision was made. Those folders are not part of this repository, so the
references cannot be followed; they are development history, not instructions.
We left the comments as they are, in Korean, so that the published code stays
byte-for-byte identical to what was submitted and scored in the contest.
